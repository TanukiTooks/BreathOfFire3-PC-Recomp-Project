param([string]$PreviewPath,[string]$SettingsPath,[switch]$VerifyUI)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$python=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$backend=Join-Path $PSScriptRoot 'bof3_display_settings.py'
$pathArgs=@();if($SettingsPath){$pathArgs=@('--path',$SettingsPath)}
$initial=& $python $backend @pathArgs show
if($LASTEXITCODE -ne 0){[System.Windows.Forms.MessageBox]::Show(($initial -join "`n"),'Display settings');exit 1}
$script:prefs=$initial|ConvertFrom-Json
$form=New-Object System.Windows.Forms.Form
$form.Text='Breath of Fire III - Display settings';$form.ClientSize=New-Object Drawing.Size(610,750);$form.StartPosition='CenterScreen';$form.FormBorderStyle='FixedDialog';$form.MaximizeBox=$false
$form.BackColor=[Drawing.Color]::FromArgb(24,28,34);$form.ForeColor=[Drawing.Color]::FromArgb(238,239,242);$form.Font=New-Object Drawing.Font('Segoe UI',10)
function LabelAt($text,$x,$y,$width,$height){$c=New-Object Windows.Forms.Label;$c.Text=$text;$c.Location=New-Object Drawing.Point($x,$y);$c.Size=New-Object Drawing.Size($width,$height);$form.Controls.Add($c);return $c}
$title=LabelAt 'BREATH OF FIRE III' 28 23 550 35;$title.Font=New-Object Drawing.Font('Segoe UI Semibold',19)
$sub=LabelAt 'Display settings' 30 65 540 30;$sub.ForeColor=[Drawing.Color]::FromArgb(171,190,208)
function Choice($label,$y,$items){$null=LabelAt $label 30 ($y+5) 205 26;$c=New-Object Windows.Forms.ComboBox;$c.Location=New-Object Drawing.Point(252,$y);$c.Size=New-Object Drawing.Size(324,30);$c.DropDownStyle='DropDownList';$c.Items.AddRange([object[]]$items);$form.Controls.Add($c);return $c}
$mode=Choice 'Window mode' 121 @('Windowed','Borderless fullscreen')
$aspect=Choice 'Aspect ratio' 171 @('4:3 - Original (default)','16:9 - Experimental widescreen')
$size=Choice 'Window width' 221 @('640 x 480','960 x 720','1280 x 960','1600 x 1200','1920 x 1440')
$scale=Choice 'Internal resolution' 271 @('1x - Original','2x - Higher resolution','3x - Higher resolution','4x - Higher resolution')
$filter=Choice 'Texture filtering' 321 @('Nearest - Crisp (default)','Bilinear - Smooth')
$wobble=Choice 'PSX polygon wobble' 371 @('On - Original PSX','Off - Corrected 3D (experimental)')
$tip=New-Object Windows.Forms.ToolTip;$tip.SetToolTip($wobble,'Off reduces vertex jitter and texture warping. Use 2x or higher internal resolution. Applies to supported 3D geometry; keeps sprite filtering separate.')
$vsync=Choice 'VSync' 421 @('On','Off')
$turbo=Choice 'Turbo speed' 471 @('2x - Fast','4x - Target (performance limited)')
$skipLogo=New-Object Windows.Forms.CheckBox;$skipLogo.Text='Skip Capcom logo';$skipLogo.Location=New-Object Drawing.Point(30,508);$skipLogo.Size=New-Object Drawing.Size(548,28);$form.Controls.Add($skipLogo)
$note=LabelAt "Turbo: F9 toggles on/off; hold Tab for a temporary boost.`nController: Select + L3 toggles; hold Select + L1 for a boost.`nSettings apply next launch; Turbo starts at normal speed.`nTurbo speeds up music too. Logo skip keeps the remaining intro.`nExperimental 16:9 may show missing scenery or edge artifacts." 30 543 548 84;$note.Font=New-Object Drawing.Font('Segoe UI',9);$note.ForeColor=[Drawing.Color]::FromArgb(171,190,208)
$status=LabelAt 'Ready' 30 630 548 28;$status.ForeColor=[Drawing.Color]::FromArgb(139,200,157)
function ButtonAt($text,$x,$width){$b=New-Object Windows.Forms.Button;$b.Text=$text;$b.Location=New-Object Drawing.Point($x,680);$b.Size=New-Object Drawing.Size($width,40);$b.FlatStyle='Flat';$b.BackColor=[Drawing.Color]::FromArgb(44,53,65);$b.ForeColor=$form.ForeColor;$form.Controls.Add($b);return $b}
$reset=ButtonAt 'Crisp defaults' 30 145;$save=ButtonAt 'Save' 302 105;$play=ButtonAt 'Save and play' 424 152;$play.BackColor=[Drawing.Color]::FromArgb(47,103,125)
function Populate($p){if($null -eq $p.psx_wobble){if($wobble.Items.Count -eq 2){$null=$wobble.Items.Add('Custom - Keep current corrections')};$wobble.SelectedIndex=2}else{$wobble.SelectedIndex=[int](-not $p.psx_wobble)};$skipLogo.Checked=[bool]$p.skip_capcom_logo;$turbo.SelectedIndex=[int]($p.turbo_speed -eq 4);$aspect.SelectedIndex=[int]($p.aspect -eq '16:9');$mode.SelectedIndex=[int]($p.window_mode -eq 'borderless');$widths=@(640,960,1280,1600,1920);$size.SelectedIndex=[Math]::Max(0,[Array]::IndexOf($widths,[int]$p.width));$scale.SelectedIndex=[Math]::Min(3,[Math]::Max(0,([int]$p.scale-1)));$filter.SelectedIndex=[int]($p.filter -eq 'bilinear');$vsync.SelectedIndex=[int]($p.vsync -eq 'off');$size.Enabled=($mode.SelectedIndex -eq 0)}
# Windows PowerShell uses .NET Framework, which lacks Math.Clamp.
$mode.Add_SelectedIndexChanged({$size.Enabled=($mode.SelectedIndex -eq 0)})
$aspect.Add_SelectedIndexChanged({
 $index=$size.SelectedIndex;$size.Items.Clear()
 $den=3;$num=4;if($aspect.SelectedIndex -eq 1){$den=9;$num=16}
 foreach($w in @(640,960,1280,1600,1920)){$null=$size.Items.Add(('{0} x {1}' -f $w,[int]($w*$den/$num)))}
 $size.SelectedIndex=[Math]::Max(0,$index)
})
function SavePreferences {
 $widths=@(640,960,1280,1600,1920)
 $argsToSave=@('save','--window-mode',@('windowed','borderless')[$mode.SelectedIndex],'--width',[string]$widths[$size.SelectedIndex],'--scale',[string]($scale.SelectedIndex+1),'--filter',@('nearest','bilinear')[$filter.SelectedIndex],'--vsync',@('on','off')[$vsync.SelectedIndex],'--expected-sha',$script:prefs.source_sha,'--aspect',@('4:3','16:9')[$aspect.SelectedIndex],'--turbo-speed',@('2','4')[$turbo.SelectedIndex],'--skip-capcom-logo',@('off','on')[[int]$skipLogo.Checked])
 if($wobble.SelectedIndex -lt 2){$argsToSave+=@('--psx-wobble',@('on','off')[$wobble.SelectedIndex])}
 $result=& $python $backend @pathArgs @argsToSave
 if($LASTEXITCODE -ne 0){[Windows.Forms.MessageBox]::Show(($result -join "`n"),'Could not save');return $false}
 $script:prefs=$result|ConvertFrom-Json;$status.Text='Saved. Applies at next launch.';return $true
}
$reset.Add_Click({Populate ([pscustomobject]@{psx_wobble=$true;skip_capcom_logo=$skipLogo.Checked;turbo_speed=2;aspect='4:3';window_mode='windowed';width=960;scale=1;filter='nearest';vsync='on'});$status.Text='Crisp defaults selected. Click Save to apply.'})
$save.Add_Click({$null=SavePreferences})
$play.Add_Click({if(SavePreferences){$runner=Join-Path $PSScriptRoot 'Run-Bof3.ps1';Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$runner+'"'),'-Tool','PSXRecomp');$form.Close()}})
Populate $script:prefs
if($VerifyUI){
 if(-not $SettingsPath){throw 'VerifyUI requires an isolated SettingsPath.'}
 $form.Show();$wobble.SelectedIndex=1;$skipLogo.Checked=$true;$turbo.SelectedIndex=1;$aspect.SelectedIndex=1;$mode.SelectedIndex=1;$size.SelectedIndex=2;$scale.SelectedIndex=1;$filter.SelectedIndex=1;$vsync.SelectedIndex=1
 if($size.Enabled){throw 'Borderless must disable window size.'}
 $save.PerformClick()
 $readback=(& $python $backend @pathArgs show)|ConvertFrom-Json
 if($readback.psx_wobble -ne $false -or -not $readback.skip_capcom_logo -or $readback.turbo_speed -ne 4 -or $readback.aspect -ne '16:9' -or $readback.window_mode -ne 'borderless' -or $readback.width -ne 1280 -or $readback.scale -ne 2 -or $readback.filter -ne 'bilinear' -or $readback.vsync -ne 'off'){throw 'UI Save did not persist selected values.'}
 $reset.PerformClick();$save.PerformClick()
 $readback=(& $python $backend @pathArgs show)|ConvertFrom-Json
 if($readback.psx_wobble -ne $true -or -not $readback.skip_capcom_logo -or $readback.turbo_speed -ne 2 -or $readback.aspect -ne '4:3' -or $readback.window_mode -ne 'windowed' -or $readback.width -ne 960 -or $readback.scale -ne 1 -or $readback.filter -ne 'nearest' -or $readback.vsync -ne 'on'){throw 'Crisp defaults did not persist.'}
 $skipLogo.Checked=$false;$save.PerformClick()
 $readback=(& $python $backend @pathArgs show)|ConvertFrom-Json
 if($readback.skip_capcom_logo){throw 'Skip-logo toggle did not turn off.'}
 Write-Output 'PASS: PSX wobble off and restored by crisp defaults; logo skip on/off and preserved through visual defaults; UI Save with 16:9, crisp defaults restore 4:3, and fullscreen size disable.'
 $form.Close();$form.Dispose();return
}
if($PreviewPath){$form.Show();$form.Refresh();$bitmap=New-Object Drawing.Bitmap($form.Width,$form.Height);$form.DrawToBitmap($bitmap,(New-Object Drawing.Rectangle(0,0,$form.Width,$form.Height)));$bitmap.Save($PreviewPath,[Drawing.Imaging.ImageFormat]::Png);$bitmap.Dispose();$form.Close()}else{[void]$form.ShowDialog()}
$form.Dispose()
