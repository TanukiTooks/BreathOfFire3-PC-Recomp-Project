$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$harness=Join-Path $workspace 'BoF3 Research\coverage\command-scenarios'
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$vsRoot=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
& (Join-Path $vsRoot 'Common7\Tools\Launch-VsDevShell.ps1') -Arch amd64 -HostArch amd64 -SkipAutomaticLocation | Out-Null
$env:PATH=(Join-Path $vsRoot 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja')+';'+$env:PATH
cmake -S "$harness\harness" -B "$harness\build" -G Ninja -DCMAKE_BUILD_TYPE=Release
if($LASTEXITCODE -ne 0){throw 'Harness configuration failed'}
cmake --build "$harness\build"
if($LASTEXITCODE -ne 0){throw 'Harness build failed'}
