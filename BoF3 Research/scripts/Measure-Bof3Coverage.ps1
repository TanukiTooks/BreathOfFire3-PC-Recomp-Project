param([ValidateRange(1,600)][int]$Seconds = 35, [ValidateRange(1024,65535)][int]$Port = 4385)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$gameRoot = Join-Path $workspace 'BoF3 PSXRecomp\BreathOfFireIII'
$exe = Join-Path $gameRoot 'build-release\Breath_of_Fire_III___PSXRecomp.exe'
$python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$portProbe = New-Object Net.Sockets.TcpClient
try {
    try { $portProbe.Connect('127.0.0.1',$Port) } catch {}
    if ($portProbe.Connected) { throw "Port $Port is already in use; select another port." }
} finally { $portProbe.Dispose() }
$runRoot = Join-Path $workspace ('BoF3 Research\coverage\runs\' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path "$runRoot\saves" -Force | Out-Null
foreach ($card in @('card1.mcd','card2.mcd')) {
    $source = Join-Path $gameRoot "run-boot-baseline\saves\$card"
    if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination "$runRoot\saves\$card" }
}
$config = Get-Content -Raw -LiteralPath "$gameRoot\game.toml"
if ($config -notmatch '(?m)^overlay_cache\s*=') { $config = $config.Replace('[runtime]', "[runtime]`noverlay_cache = true") }
else { $config = $config -replace '(?m)^overlay_cache\s*=.*$', 'overlay_cache = true' }
Set-Content -LiteralPath "$runRoot\game.toml" -Value $config
$previousCaptures = $env:PSX_OVERLAY_CAPTURES
$process = $null
try {
    $env:PSX_OVERLAY_CAPTURES = "$runRoot\overlay_captures.json"
    $argsForGame = @('--headless','--game',"$runRoot\game.toml",'--debug-port',[string]$Port,'--memcard-dir',"$runRoot\saves") | ForEach-Object { '"' + $_ + '"' }
    $process = Start-Process -FilePath $exe -ArgumentList $argsForGame -WorkingDirectory $runRoot -WindowStyle Hidden -RedirectStandardOutput "$runRoot\runtime.stdout.log" -RedirectStandardError "$runRoot\runtime.stderr.log" -PassThru
    $process.Id | Set-Content -LiteralPath "$runRoot\process-id.txt"
    & $python "$PSScriptRoot\record_runtime_coverage.py" --port $Port --seconds $Seconds --out $runRoot
    if ($LASTEXITCODE -ne 0) { throw "Coverage recording failed; partial evidence is in $runRoot" }
} finally {
    if ($process -and -not $process.HasExited) { Stop-Process -Id $process.Id -ErrorAction SilentlyContinue }
    if ($null -eq $previousCaptures) { Remove-Item Env:\PSX_OVERLAY_CAPTURES -ErrorAction SilentlyContinue }
    else { $env:PSX_OVERLAY_CAPTURES = $previousCaptures }
}
Write-Output "Coverage run: $runRoot"
