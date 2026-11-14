# Closes copies of the app left running from earlier sessions.
#
# Only Python and Node processes listening on the ports start.bat itself uses
# are stopped, so another project's dev server on the same machine is untouched.
# Called by stop.bat; run it directly with -Ports to widen the search.
param(
  [int[]] $Ports = @(8000, 8001, 8002, 8003, 5173, 5174, 5175, 5176),
  [switch] $WhatIfOnly
)

$ours = @('python', 'pythonw', 'node')
$stopped = 0

$listening = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $Ports -contains $_.LocalPort } |
  Select-Object LocalPort, OwningProcess -Unique |
  Sort-Object LocalPort

foreach ($c in $listening) {
  $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
  if (-not $p) {
    Write-Host ("Port {0} is held by a process that has already gone." -f $c.LocalPort)
    continue
  }
  if ($ours -notcontains $p.ProcessName) {
    Write-Host ("Leaving {0} (pid {1}) on port {2} alone." -f $p.ProcessName, $p.Id, $c.LocalPort)
    continue
  }
  if ($WhatIfOnly) {
    Write-Host ("Would stop {0} (pid {1}) on port {2}." -f $p.ProcessName, $p.Id, $c.LocalPort)
  } else {
    Write-Host ("Stopping {0} (pid {1}) on port {2}." -f $p.ProcessName, $p.Id, $c.LocalPort)
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
  }
  $stopped += 1
}

if ($stopped -eq 0) { Write-Host 'Nothing of ours was running.' }
