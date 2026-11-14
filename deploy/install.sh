#!/usr/bin/env bash
#
# Provision the pension case system on a fresh Ubuntu 22.04 / 24.04 EC2 instance.
#
#   sudo bash deploy/install.sh
#
# Installs the runtime, LibreOffice (which makes the PDFs in place of Word),
# Devanagari and Times-compatible fonts, then builds the templates and the web
# interface and registers a systemd service behind nginx.
set -euo pipefail

APP_USER="${APP_USER:-pension}"
APP_DIR="${APP_DIR:-/opt/pension}"
DATA_DIR="${DATA_DIR:-/var/lib/pension}"
SERVER_NAME="${SERVER_NAME:-_}"

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo." >&2
  exit 1
fi

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Installing packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  python3 python3-venv python3-pip \
  libreoffice-writer \
  fonts-liberation fonts-noto-core fonts-noto-devanagari fonts-lohit-deva \
  nginx curl ca-certificates gnupg rsync sqlite3

# Node is only needed to build the web interface.
if ! command -v node >/dev/null 2>&1; then
  echo "==> Installing Node.js 20"
  mkdir -p /etc/apt/keyrings
  curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
    | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
  echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" \
    > /etc/apt/sources.list.d/nodesource.list
  apt-get update -qq
  apt-get install -y -qq nodejs
fi

echo "==> Creating $APP_USER and directories"
id -u "$APP_USER" >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin "$APP_USER"
mkdir -p "$APP_DIR" "$DATA_DIR/storage"

echo "==> Copying the application to $APP_DIR"
rsync -a --delete \
  --exclude '.venv' --exclude 'node_modules' --exclude 'dist' \
  --exclude 'storage' --exclude 'pension.db' --exclude '.secret' \
  --exclude '__pycache__' \
  "$SOURCE_DIR/" "$APP_DIR/"

echo "==> Python environment"
python3 -m venv "$APP_DIR/backend/.venv"
"$APP_DIR/backend/.venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/backend/.venv/bin/pip" install --quiet -r "$APP_DIR/backend/requirements.txt"

echo "==> Building the web interface"
( cd "$APP_DIR/frontend" && npm ci --silent && npm run build --silent )

# The fonts named inside the .docx files must exist on this machine, so the
# templates are rebuilt here with the Linux font names. Liberation Serif is
# metric-compatible with Times New Roman, so the layouts do not shift.
echo "==> Building the form templates with Linux fonts"
cd "$APP_DIR/backend"
export PENSION_FONT_LATIN="${PENSION_FONT_LATIN:-Liberation Serif}"
export PENSION_FONT_DEVANAGARI="${PENSION_FONT_DEVANAGARI:-Noto Sans Devanagari}"
export PENSION_DB="$DATA_DIR/pension.db"
export PENSION_STORAGE="$DATA_DIR/storage"
export PENSION_SECRET="$DATA_DIR/.secret"
"$APP_DIR/backend/.venv/bin/python" build_templates.py
"$APP_DIR/backend/.venv/bin/python" -m app.seed --no-sample

chown -R "$APP_USER:$APP_USER" "$APP_DIR" "$DATA_DIR"

echo "==> systemd service"
sed -e "s|@APP_DIR@|$APP_DIR|g" \
    -e "s|@DATA_DIR@|$DATA_DIR|g" \
    -e "s|@APP_USER@|$APP_USER|g" \
    -e "s|@FONT_LATIN@|$PENSION_FONT_LATIN|g" \
    -e "s|@FONT_DEVANAGARI@|$PENSION_FONT_DEVANAGARI|g" \
    "$SOURCE_DIR/deploy/pension.service" > /etc/systemd/system/pension.service
systemctl daemon-reload
systemctl enable --now pension.service

echo "==> nginx"
sed -e "s|@SERVER_NAME@|$SERVER_NAME|g" \
    "$SOURCE_DIR/deploy/nginx.conf" > /etc/nginx/sites-available/pension
ln -sf /etc/nginx/sites-available/pension /etc/nginx/sites-enabled/pension
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo
echo "Done."
echo "  Service : systemctl status pension"
echo "  Logs    : journalctl -u pension -f"
echo "  Data    : $DATA_DIR"
echo "  Sign in : admin / ${PENSION_DEFAULT_PASSWORD:-ChangeMe@123}  (change it from the Account page)"
echo
echo "Open http://<your-ec2-public-dns>/ in a browser."
echo "For HTTPS: sudo apt install certbot python3-certbot-nginx && sudo certbot --nginx"
