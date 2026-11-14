# Launcher for the desktop shortcut.
#
# One process: the API serves the built web interface out of frontend\dist, so
# there is no Vite server, no second console, and nothing to configure. Node is
# not needed on this machine at all.
#
# Run it twice and it does not start a second copy -- it finds the one already
# answering and just opens the browser at it.

$ErrorActionPreference = 'Stop'
$root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root 'backend'
$pythonw = Join-Path $backend '.venv\Scripts\pythonw.exe'
$ports   = 8000..8003          # the same range stop.bat knows how to close

function Show-Problem($text) {
    Add-Type -AssemblyName System.Windows.Forms | Out-Null
    [System.Windows.Forms.MessageBox]::Show(
        $text, 'Pension Case System',
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
}

function Test-Server($port) {
    # It is not enough that something answers: an older copy of this app, or an
    # unrelated service, can be sitting on one of these ports. Only a desktop
    # run of the current code will report local_desktop, so only that is adopted
    # -- otherwise the shortcut would open the browser on the wrong system.
    try {
        $r = Invoke-RestMethod "http://127.0.0.1:$port/api/health" -TimeoutSec 2
        return ($r.status -eq 'ok') -and ($r.local_desktop -eq $true)
    } catch { return $false }
}

if (-not (Test-Path $pythonw)) {
    Show-Problem "This copy has not been set up yet.`n`nRun setup.bat in:`n$root"
    exit 1
}
if (-not (Test-Path (Join-Path $root 'frontend\dist\index.html'))) {
    Show-Problem "The web interface has not been built.`n`nRun setup.bat in:`n$root"
    exit 1
}

# Already running? Then just show it, rather than starting a rival copy.
foreach ($p in $ports) {
    if (Test-Server $p) { Start-Process "http://127.0.0.1:$p/"; exit 0 }
}

$port = $null
foreach ($p in $ports) {
    $busy = Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue
    if (-not $busy) { $port = $p; break }
}
if (-not $port) {
    Show-Problem "Ports 8000 to 8003 are all in use.`n`nRestart the computer, or run stop.bat."
    exit 1
}

$logDir = Join-Path $backend 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir 'server.log'
$out = Join-Path $logDir 'server.out.log'

# Both streams have to go somewhere real. pythonw.exe has no console, so an
# unredirected sys.stdout is None, and uvicorn's logging setup dies on it with
# "Unable to configure formatter 'default'" before the server ever listens.

# Sign-in is skipped for this desktop run; the API still trusts it only for
# requests coming from this machine.
$env:PENSION_LOCAL_MODE = '1'
Start-Process -FilePath $pythonw `
    -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', "$port") `
    -WorkingDirectory $backend -WindowStyle Hidden `
    -RedirectStandardOutput $out -RedirectStandardError $log

# First start of the day also runs the database migration, so allow a while.
$ready = $false
foreach ($i in 1..60) {
    Start-Sleep -Milliseconds 500
    if (Test-Server $port) { $ready = $true; break }
}

if (-not $ready) {
    $tail = if (Test-Path $log) { (Get-Content $log -Tail 12) -join "`n" } else { '(no log written)' }
    Show-Problem "The system did not start.`n`nLast lines of $log :`n`n$tail"
    exit 1
}

Start-Process "http://127.0.0.1:$port/"
