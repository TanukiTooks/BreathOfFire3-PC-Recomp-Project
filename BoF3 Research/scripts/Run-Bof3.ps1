param(
    [Parameter(Mandatory)][ValidateSet('PSXRecomp', 'RecompOne')][string]$Tool,
    [switch]$Headless,
    [switch]$DisplaySettings,
    [ValidateRange(0, 65535)][int]$DebugPort = 0,
    [ValidateRange(0, 600)][int]$SmokeSeconds = 0
)
$ErrorActionPreference = 'Stop'
if ($DisplaySettings) {
    if ($Tool -ne 'PSXRecomp' -or $Headless -or $DebugPort -gt 0 -or $SmokeSeconds -gt 0) { throw 'DisplaySettings opens the interactive PSXRecomp settings window.' }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File (Join-Path $PSScriptRoot 'Show-Bof3DisplaySettings.ps1')
    return
}
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$cue = Join-Path $workspace 'iso\Breath of Fire III (USA)\Breath of Fire III (USA).cue'
if ($Tool -eq 'PSXRecomp') {
    if ($SmokeSeconds -gt 0) { throw 'SmokeSeconds is supported by the RecompOne diagnostic runner only.' }
    $gameRoot = Join-Path $workspace 'BoF3 PSXRecomp\BreathOfFireIII'
    $exe = Join-Path $gameRoot 'build-release\Breath_of_Fire_III___PSXRecomp.exe'
    $runRoot = Join-Path $gameRoot 'run-boot-baseline'
    $gameArgs = @('--game', "$gameRoot\game.toml", '--memcard-dir', "$runRoot\saves")
    if ($Headless) { $gameArgs += '--headless' }
    if ($DebugPort -gt 0) { $gameArgs += @('--debug-port', $DebugPort) }
} else {
    if ($Headless -or $DebugPort -gt 0) { throw 'These PSXRecomp options are unavailable in the RecompOne runner.' }
    $gameRoot = Join-Path $workspace 'BoF3 Recomp1\BreathOfFireIII'
    $exe = Join-Path $gameRoot 'bin\Release\net10.0\BreathOfFireIII-RecompOne.exe'
    $runRoot = Join-Path $gameRoot 'run-boot-baseline'
    $gameArgs = @($cue)
    New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
    $settingsPath = Join-Path $runRoot 'settings.json'
    if (-not (Test-Path -LiteralPath $settingsPath)) {
        @{ CdPath = $cue; Muted = $true } | ConvertTo-Json | Set-Content -LiteralPath $settingsPath
    }
}
if (-not (Test-Path -LiteralPath $exe)) { throw 'Build the selected game before running it.' }
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
$previousSmoke = $env:BOF3_SMOKE_SECONDS
$previousTurbo = $env:PSX_FAST_FORWARD_SPEED
$previousSkipLogo = $env:BOF3_SKIP_CAPCOM_LOGO
Push-Location $runRoot
try {
    if ($Tool -eq 'PSXRecomp') {
        $python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
        $prefsJson = & $python (Join-Path $PSScriptRoot 'bof3_display_settings.py') show
        if ($LASTEXITCODE -ne 0) { throw ($prefsJson -join "`n") }
        $launchPrefs = $prefsJson | ConvertFrom-Json
        $turboSpeed = [int]$launchPrefs.turbo_speed
        if ($launchPrefs.skip_capcom_logo -isnot [bool]) { throw 'Skip Capcom logo must be on or off in settings.' }
        $env:BOF3_SKIP_CAPCOM_LOGO = if ($launchPrefs.skip_capcom_logo) { '1' } else { '0' }
        if ($turboSpeed -notin @(2,4)) { throw 'Choose 2x or 4x Turbo in Display Settings.' }
        $env:PSX_FAST_FORWARD_SPEED = [string]$turboSpeed
        Write-Host "Turbo: ${turboSpeed}x available; F9 toggles on/off, Tab holds. Starts at normal speed."
    }
    if ($SmokeSeconds -gt 0) { $env:BOF3_SMOKE_SECONDS = [string]$SmokeSeconds }
    else { Remove-Item Env:\BOF3_SMOKE_SECONDS -ErrorAction SilentlyContinue }
    # GUI executables can leave LASTEXITCODE unset or stale in Windows PowerShell.
    # All arguments here are fixed flags, numbers or file paths (no embedded quotes).
    $quotedGameArgs = @($gameArgs | ForEach-Object { '"' + [string]$_ + '"' })
    $gameProcess = Start-Process -FilePath $exe -ArgumentList $quotedGameArgs -WorkingDirectory $runRoot -NoNewWindow -Wait -PassThru
    $gameExitCode = $gameProcess.ExitCode
    if ($null -eq $gameExitCode) { throw 'Could not read the runtime process exit code.' }
    if ($gameExitCode -ne 0) { throw "Runtime exited with code $gameExitCode" }
} finally {
    Pop-Location
    if ($null -ne $previousSkipLogo) { $env:BOF3_SKIP_CAPCOM_LOGO = $previousSkipLogo }
    else { Remove-Item Env:BOF3_SKIP_CAPCOM_LOGO -ErrorAction SilentlyContinue }
    if ($null -ne $previousTurbo) { $env:PSX_FAST_FORWARD_SPEED = $previousTurbo }
    else { Remove-Item Env:PSX_FAST_FORWARD_SPEED -ErrorAction SilentlyContinue }
    if ($null -ne $previousSmoke) { $env:BOF3_SMOKE_SECONDS = $previousSmoke }
    else { Remove-Item Env:\BOF3_SMOKE_SECONDS -ErrorAction SilentlyContinue }
}

