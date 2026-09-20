param([ValidateSet('baseline','native')][string]$Variant='baseline',[switch]$LoadSave,[string]$EvidenceRoot,[string]$BaselineExe)
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$gameRoot=Join-Path $workspace 'BoF3 PSXRecomp\BreathOfFireIII'
$runRoot=if($EvidenceRoot){Join-Path $EvidenceRoot $Variant}else{Join-Path $workspace "BoF3 Research\coverage\card-native\$Variant"}
New-Item -ItemType Directory -Force -Path "$runRoot\saves"|Out-Null
$exe=if($Variant -eq 'baseline'){"$gameRoot\build-release\Breath_of_Fire_III___PSXRecomp.before-card-native.exe"}else{"$gameRoot\build-release\Breath_of_Fire_III___PSXRecomp.exe"}
Copy-Item -LiteralPath "$gameRoot\run-boot-baseline\saves\card1.mcd","$gameRoot\run-boot-baseline\saves\card2.mcd" -Destination "$runRoot\saves"
$portProbe=New-Object Net.Sockets.TcpClient
try {
 try {$portProbe.Connect('127.0.0.1',4387)}catch{}
 if($portProbe.Connected){throw 'Debug port 4387 is already in use; close the previous diagnostic session first.'}
}finally{$portProbe.Dispose()}
if($Variant -eq 'baseline' -and $BaselineExe){$exe=$BaselineExe}
$previousTrace=$env:BOF3_TRACE_NATIVE_CARD
$env:BOF3_TRACE_NATIVE_CARD='1'
$runtimeArgs=@('--headless','--game',"$gameRoot\game.toml",'--debug-port','4387','--memcard-dir',"$runRoot\saves")|ForEach-Object{'"'+$_+'"'}
$runtimeProcess=$null
try {
 $runtimeProcess=Start-Process -FilePath $exe -ArgumentList $runtimeArgs -WorkingDirectory $runRoot -WindowStyle Hidden -RedirectStandardOutput "$runRoot\stdout.log" -RedirectStandardError "$runRoot\stderr.log" -PassThru
 $probeArgs=@('--out',$runRoot)
 if($LoadSave){$probeArgs+='--load-save'}
 & "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "$PSScriptRoot\probe_card_selection.py" @probeArgs *> "$runRoot\probe.log"
 if($LASTEXITCODE -ne 0){throw "Card probe failed: see $runRoot\probe.log"}
 Get-Content -LiteralPath "$runRoot\probe.log"
} finally {
 if($runtimeProcess -and -not $runtimeProcess.HasExited){Stop-Process -Id $runtimeProcess.Id}
 if($null -eq $previousTrace){Remove-Item Env:\BOF3_TRACE_NATIVE_CARD -ErrorAction SilentlyContinue}else{$env:BOF3_TRACE_NATIVE_CARD=$previousTrace}
}
