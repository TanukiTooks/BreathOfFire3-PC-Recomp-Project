$ErrorActionPreference='Stop'
# Isolate process launching: exercise the real runner without opening the game or its cards.
$global:Bof3TurboTestExit=0
$global:Bof3TurboTestObserved=$null
function Start-Process {
 param($FilePath,$ArgumentList,$WorkingDirectory,[switch]$NoNewWindow,[switch]$Wait,[switch]$PassThru)
 $global:Bof3TurboTestObserved=$env:PSX_FAST_FORWARD_SPEED
 [pscustomobject]@{ExitCode=$global:Bof3TurboTestExit}
}
$python=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$prefs=(& $python (Join-Path $PSScriptRoot 'bof3_display_settings.py') show)|ConvertFrom-Json
$env:PSX_FAST_FORWARD_SPEED='13'
& (Join-Path $PSScriptRoot 'Run-Bof3.ps1') -Tool PSXRecomp
if($global:Bof3TurboTestObserved -ne [string]$prefs.turbo_speed -or $env:PSX_FAST_FORWARD_SPEED -ne '13'){throw 'Turbo preference or environment restoration failed.'}
$global:Bof3TurboTestExit=7;$caught=$false
try{& (Join-Path $PSScriptRoot 'Run-Bof3.ps1') -Tool PSXRecomp}catch{$caught=$true}
if(-not $caught -or $env:PSX_FAST_FORWARD_SPEED -ne '13'){throw 'Failure path did not restore the environment.'}
Write-Output 'PASS: real launcher selects saved Turbo speed; parent environment restored on success and failure. Process creation mocked; original cards unopened.'
