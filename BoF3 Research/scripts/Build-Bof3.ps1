param(
    [Parameter(Mandatory)][ValidateSet('PSXRecomp', 'RecompOne')][string]$Tool,
    [switch]$Regenerate
)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
function Check-Exit([string]$Stage) {
    if ($LASTEXITCODE -ne 0) { throw "$Stage failed with exit code $LASTEXITCODE" }
}
if ($Tool -eq 'PSXRecomp') {
    $gameRoot = Join-Path $workspace 'BoF3 PSXRecomp\BreathOfFireIII'
    $framework = Join-Path $workspace 'BoF3 PSXRecomp\psxrecomp-src-nightly-20260910-ed55299be3'
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    $vsRoot = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if (-not $vsRoot) { throw 'Visual Studio C++ tools are required.' }
    & (Join-Path $vsRoot 'Common7\Tools\Launch-VsDevShell.ps1') -Arch amd64 -HostArch amd64 -SkipAutomaticLocation | Out-Null
    $env:PATH = (Join-Path $vsRoot 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja') + ';' + $env:PATH
    if ($Regenerate) {
        $pythonExe = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
        if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Set pythonExe to a supported modern Python interpreter.' }
        cmake -S "$framework\recompiler" -B "$gameRoot\build-recompiler" -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSXRECOMP_ENABLE_CHD=OFF -DBUILD_TESTING=OFF
        Check-Exit 'Emitter configuration'
        cmake --build "$gameRoot\build-recompiler" --target psxrecomp-game psxrecomp-bios -j 6
        Check-Exit 'Emitter build'
        $cue = Join-Path $workspace 'iso\Breath of Fire III (USA)\Breath of Fire III (USA).cue'
        & $pythonExe "$framework\psxrecomp_cli.py" generate --config "$gameRoot\game.toml" --project-root $gameRoot --disc $cue --no-toolchain-download
        Check-Exit 'PSXRecomp generation'
        & $pythonExe (Join-Path $PSScriptRoot 'prepare_motion_commands_native.py')
        Check-Exit 'Prior verified recipe preparation'
        & $pythonExe (Join-Path $PSScriptRoot 'prepare_party_motion_native.py')
        Check-Exit 'Party/motion recipe preparation'
        & $pythonExe (Join-Path $PSScriptRoot 'prepare_scenario01_native.py')
        Check-Exit 'SCENA01 recipe preparation'
        & $pythonExe (Join-Path $PSScriptRoot 'prepare_scenario01_events_native.py')
        Check-Exit 'SCENA01 event recipe preparation'
        & $pythonExe (Join-Path $PSScriptRoot 'prepare_world_tiles_native.py')
        Check-Exit 'AREA033 animated tile recipe preparation'
        $captures = Join-Path $workspace 'BoF3 Research\startup-world-tiles-inputs.json'
        if (Test-Path -LiteralPath $captures) {
            & $pythonExe "$framework\tools\compile_overlays.py" --static --force --captures $captures --game-toml "$gameRoot\game.toml" --recompiler "$gameRoot\build-recompiler\psxrecomp-game.exe" --runtime-include "$framework\runtime\include" --out-dir "$gameRoot\generated-scenario01-events-overlays" --cps --flavor 2 --jobs 4
            Check-Exit 'Captured startup and card overlay generation'
        }
    }
    $pythonExe = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    & $pythonExe (Join-Path $PSScriptRoot 'fix_motion_command_breaks.py') --generated-dir "$gameRoot\generated-scenario01-events-overlays"
    Check-Exit 'Motion-command BREAK translation correction'
    & $pythonExe (Join-Path $PSScriptRoot 'fix_widescreen_menu_background.py') --generated-dir "$gameRoot\generated-scenario01-events-overlays"
    Check-Exit 'Widescreen tiled menu background adjustment'
    & $pythonExe (Join-Path $PSScriptRoot 'fix_skip_capcom_logo.py') --generated-dir "$gameRoot\generated-scenario01-events-overlays"
    Check-Exit 'Optional Capcom logo skip'
    & $pythonExe (Join-Path $PSScriptRoot 'import_title_footer.py')
    Check-Exit 'Title footer asset extraction'
    & $pythonExe (Join-Path $PSScriptRoot 'build_button_prompt_assets.py')
    Check-Exit 'Button prompt asset compilation'
    & $pythonExe (Join-Path $PSScriptRoot 'fix_widescreen_terrain.py')
    Check-Exit 'Widescreen terrain acceptance adjustment'
    & $pythonExe (Join-Path $PSScriptRoot 'fix_turbo_vsync.py')
    Check-Exit 'Bounded Turbo VSync cadence correction'
    cmake -S $gameRoot -B "$gameRoot\build-release" -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSX_DEBUG_TOOLS=ON
    Check-Exit 'Runtime configuration'
    cmake --build "$gameRoot\build-release" -j 6
    Check-Exit 'Runtime build'
} else {
    $gameRoot = Join-Path $workspace 'BoF3 Recomp1\BreathOfFireIII'
    $framework = Join-Path $workspace 'BoF3 Recomp1\RecompOne-master'
    if ($Regenerate) {
        dotnet build "$framework\RecompOne.Recompiler\RecompOne.Recompiler.csproj" -c Release
        Check-Exit 'RecompOne compiler build'
        & "$framework\RecompOne.Recompiler\bin\Release\net10.0\recompone.exe" "$gameRoot\config\boot-baseline.json"
        Check-Exit 'RecompOne boot generation'
    }
    dotnet build "$gameRoot\BreathOfFireIII.csproj" -c Release
    Check-Exit 'RecompOne game build'
}



