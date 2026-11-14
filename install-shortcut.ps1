# Puts "Pension Case System" on the Desktop and in the Start menu.
#
# Run once on the office machine, after setup.bat:
#     powershell -ExecutionPolicy Bypass -File install-shortcut.ps1
#
# Both shortcuts point at pension.ps1 in this folder, so moving or renaming the
# folder means running this again.

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$name = 'Pension Case System'

$targets = @(
    [Environment]::GetFolderPath('Desktop'),
    (Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs')
)

$shell = New-Object -ComObject WScript.Shell
foreach ($dir in $targets) {
    if (-not (Test-Path $dir)) { continue }
    $path = Join-Path $dir "$name.lnk"
    $lnk = $shell.CreateShortcut($path)
    $lnk.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $lnk.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f (Join-Path $root 'pension.ps1')
    $lnk.WorkingDirectory = $root
    $lnk.IconLocation = '{0},0' -f (Join-Path $root 'pension.ico')
    $lnk.Description = 'Retirement Gratuity (DCRG) case papers'
    $lnk.WindowStyle = 7          # start minimised; the launcher shows nothing
    $lnk.Save()
    Write-Host "Created: $path"
}

Write-Host ''
Write-Host 'Double-click the shortcut to start. It opens in your browser.'
Write-Host 'To shut the system down again, run stop.bat in this folder.'
