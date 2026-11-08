param([ValidateSet('auto','cuda','cpu')][string]$Device='auto',[switch]$NoLaunch,[switch]$Offline,[string]$TinySdPath,[string[]]$ReuseFrom=@(),[switch]$SkipWikipedia,[ValidateSet('nopic','mini')][string]$WikipediaFlavour='mini',[string]$WikipediaPath,[switch]$WikipediaOnly,[switch]$ImageGpuOnly)
$ErrorActionPreference='Stop'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force 'output\logs','wheelhouse','tools' | Out-Null
Start-Transcript -Path 'output\logs\setup.log' -Append | Out-Null
function Step($s){Write-Host "[STEP] $s" -ForegroundColor Cyan}
. (Join-Path $PSScriptRoot 'NativeProcess.ps1')
. (Join-Path $PSScriptRoot 'ReuseAssets.ps1')
try {
  Write-Host 'LFM3 Desk Setup v1.5.1' -ForegroundColor Magenta
  Write-Host "[DIR] $PSScriptRoot"
  if($ImageGpuOnly){
    $venv=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if(!(Test-Path $venv)){throw 'Run core setup first.'}
    Step 'Reusing previous wheelhouse files for optional image GPU runtime'
    $previous=@(Get-PreviousInstallations -AppRoot $PSScriptRoot -ReuseFrom $ReuseFrom)
    foreach($source in $previous){Copy-ReuseTree (Join-Path $source 'wheelhouse') (Join-Path $PSScriptRoot 'wheelhouse') '*.whl'}
    $gpuArgs=@('backend\image_setup.py');if($Offline){$gpuArgs+='--offline'}
    Run $venv $gpuArgs
    Stop-Transcript | Out-Null
    exit 0
  }
  if($WikipediaOnly){
    $venv=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if(!(Test-Path $venv)){throw 'Run runtime setup first.'}
    Run $venv @('backend\wiki_setup.py','--flavour',$WikipediaFlavour,'--select-flavour','--optional')
    Stop-Transcript | Out-Null
    exit 0
  }
  Step 'Finding previous releases and reusing local assets before downloads'
  $previous=@(Get-PreviousInstallations -AppRoot $PSScriptRoot -ReuseFrom $ReuseFrom)
  if($previous.Count){Import-PreviousAssets -AppRoot $PSScriptRoot -Sources $previous -SkipWikipedia:([bool]($SkipWikipedia -or $WikipediaPath))}else{Write-Host '[INFO] No matching previous release found in the bounded search.'}
  $runtimeArgs=@("-NoProfile","-ExecutionPolicy","Bypass","-File","$PSScriptRoot\EnsureRuntime.ps1")
  if($Offline){$runtimeArgs+="-Offline"}
  Run 'powershell.exe' $runtimeArgs
  $probe=Join-Path $PSScriptRoot 'backend\probe_python.py'
  $venvCandidate=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
  $venvValid=$false
  if(Test-Path $venvCandidate){
    try{
      $check=Invoke-NativeProcess -FilePath $venvCandidate -Arguments @($probe) -Echo $false
      if($check.ExitCode -eq 0){$details=$check.Output | ConvertFrom-Json;$venvValid=$details.version -eq '3.12' -and $details.bits -eq 64 -and $details.is_venv -and ([IO.Path]::GetFullPath($details.prefix).TrimEnd('\') -eq (Join-Path $PSScriptRoot '.venv'))}
    }catch{Write-Host "[WARN] Existing virtual environment could not start: $_" -ForegroundColor DarkYellow}
    if(!$venvValid){throw 'The existing .venv is not a working Python 3.12 x64 environment. Rename .venv and run Setup.cmd again; models and wheelhouse can remain.'}
  }
  if(!$venvValid){
    Step 'Finding Python 3.12 x64 (file-based probe; PowerShell 5.1 compatible)'
    $python=$null
    $candidates=@("$PSScriptRoot\tools\python\python.exe","$env:LOCALAPPDATA\Programs\Python\Python312\python.exe","$env:ProgramFiles\Python312\python.exe")
    foreach($old in $previous){
      $configuration=Join-Path $old '.venv/pyvenv.cfg'
      if(Test-Path $configuration){
        $homeLine=Get-Content $configuration | Where-Object {$_ -match '^home\s*='} | Select-Object -First 1
        if($homeLine){$base=($homeLine -split '=',2)[1].Trim();$candidates+=(Join-Path $base 'python.exe')}
      }
    }
    foreach($name in @('python','python3')){
      $cmd=Get-Command $name -ErrorAction SilentlyContinue
      if($cmd -and $cmd.Source -notmatch '\\WindowsApps\\'){$candidates+=$cmd.Source}
    }
    $launcher=Get-Command py -ErrorAction SilentlyContinue
    if($launcher){
      try{
        $check=Invoke-NativeProcess -FilePath $launcher.Source -Arguments @('-3.12',$probe) -Echo $false
        if($check.ExitCode -eq 0){$details=$check.Output | ConvertFrom-Json;if($details.version -eq '3.12' -and $details.bits -eq 64){$candidates+=$details.executable}}
      }catch{Write-Host "[WARN] Windows launcher probe skipped: $_" -ForegroundColor DarkYellow}
    }
    foreach($candidate in ($candidates | Select-Object -Unique)){
      if(!(Test-Path $candidate -PathType Leaf)){continue}
      try{
        $check=Invoke-NativeProcess -FilePath $candidate -Arguments @($probe) -Echo $false
        if($check.ExitCode -ne 0){Write-Host "[WARN] Python probe rejected: $candidate (exit $($check.ExitCode))" -ForegroundColor DarkYellow;continue}
        $details=$check.Output | ConvertFrom-Json
        if($details.version -eq '3.12' -and $details.bits -eq 64){$python=$details.executable;break}
        Write-Host "[INFO] Skipping Python $($details.version) / $($details.bits)-bit: $candidate"
      }catch{Write-Host "[WARN] Python probe skipped: $candidate - $_" -ForegroundColor DarkYellow}
    }
    if(!$python){
      if($Offline){throw 'Python 3.12 x64 missing; offline setup requires it already installed.'}
      Step 'Downloading official Python 3.12.10 installer (per user, no PATH changes)'
      $installer=Join-Path $PSScriptRoot 'tools\python-3.12.10-amd64.exe'
      if(!(Test-Path $installer)){Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile ($installer+'.part') -UseBasicParsing;Move-Item ($installer+'.part') $installer -Force}
      $sig=Get-AuthenticodeSignature $installer
      if($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'Python Software Foundation'){throw 'Invalid Python installer signature'}
      Run $installer @('/quiet','InstallAllUsers=0','PrependPath=0','Include_test=0','Include_launcher=0',('TargetDir='+$PSScriptRoot+'\tools\python')) @(0,3010)
      $python="$PSScriptRoot\tools\python\python.exe"
    }
    Write-Host "[OK] Selected Python: $python" -ForegroundColor Green
    Run $python @('-m','venv','.venv')
  }
  $venv="$PSScriptRoot\.venv\Scripts\python.exe"
  if($Device -eq 'auto'){$Device='cpu';if(Get-Command nvidia-smi -ErrorAction SilentlyContinue){$Device='cuda'}}
  $torchSpec=if($Device -eq 'cuda'){'torch==2.11.0+cu128'}else{'torch==2.11.0+cpu'}
  $visionSpec=if($Device -eq 'cuda'){'torchvision==0.26.0+cu128'}else{'torchvision==0.26.0+cpu'}
  $marker=".venv\lfm-runtime-$Device.ready"
  $requirementsHash=(Get-FileHash 'backend\requirements.txt' -Algorithm SHA256).Hash
  $runtimeCurrent=(Test-Path $marker) -and ((Get-Content $marker -Raw) -eq $requirementsHash)
  if(!$runtimeCurrent){
    Step 'Resolving packages from reused wheels; downloading missing requirements only'
    $index=if($Device -eq 'cuda'){'https://download.pytorch.org/whl/cu128'}else{'https://download.pytorch.org/whl/cpu'}
    $collect=@('backend\prepare_wheels.py','--torch',$torchSpec,'--vision',$visionSpec,'--index',$index)
    if($Offline){$collect+='--offline'}
    Run $venv $collect
    Step 'Installing from local wheelhouse'
    Run $venv @('-m','pip','--disable-pip-version-check','--no-cache-dir','install','--no-index','--find-links','wheelhouse','-r','backend\requirements.txt',$torchSpec,$visionSpec)
  } else {Write-Host '[OK] Existing runtime reused.' -ForegroundColor Green}
  Step 'Preparing FFmpeg for audio/video decoding'
  $ffdir=Join-Path $PSScriptRoot 'tools\ffmpeg\bin'
  New-Item -ItemType Directory -Force $ffdir | Out-Null
  if(!(Get-ChildItem $ffdir -Filter 'avcodec-*.dll')){
    $found=$null
    $ff=Get-Command ffmpeg -ErrorAction SilentlyContinue
    $search=@()
    if($ff){$search+=Split-Path $ff.Source}
    $search+=@("$env:LOCALAPPDATA\Microsoft\WinGet\Links","$PSScriptRoot\..\tools\ffmpeg\bin","$PSScriptRoot\..\ffmpeg\bin")
    foreach($candidate in $search){if((Test-Path $candidate) -and (Get-ChildItem $candidate -Filter 'avcodec-*.dll')){$found=$candidate;break}}
    if($found){Copy-Item "$found\*" $ffdir -Force}else{
      if($Offline){throw 'Shared FFmpeg missing; put ffmpeg.exe and shared DLLs in tools\ffmpeg\bin.'}
      $archive='tools\ffmpeg-shared.zip'
      if(!(Test-Path $archive)){Invoke-WebRequest 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n8.1-latest-win64-lgpl-shared-8.1.zip' -OutFile ($archive+'.part') -UseBasicParsing;Move-Item ($archive+'.part') $archive -Force}
      Expand-Archive $archive 'tools\ffmpeg-unpack' -Force
      $bin=Get-ChildItem 'tools\ffmpeg-unpack' -Filter ffmpeg.exe -Recurse | Select-Object -First 1
      if(!$bin){throw 'Shared FFmpeg archive has no ffmpeg.exe'}
      Copy-Item "$($bin.Directory.FullName)\*" $ffdir -Force
      Get-ChildItem $bin.Directory.Parent.FullName -File | Copy-Item -Destination (Split-Path $ffdir) -Force
      Remove-Item 'tools\ffmpeg-unpack' -Recurse -Force
      Remove-Item $archive -Force
    }
  }
  $env:PATH="$ffdir;$env:PATH"
  Step 'Checking runtime imports and shared FFmpeg DLL loading'
  Run $venv @('backend\doctor.py')
  Get-ChildItem '.venv' -Filter 'lfm-runtime-*.ready' | Where-Object { $_.Name -ne (Split-Path $marker -Leaf) } | Remove-Item -Force
  [IO.File]::WriteAllText((Join-Path $PSScriptRoot $marker),$requirementsHash)
  $freeze=Invoke-NativeProcess -FilePath $venv -Arguments @('-m','pip','freeze') -Echo $false
  if($freeze.ExitCode -ne 0){throw 'Could not record installed packages'}
  $versionHeader="# LFM3 Desk 1.5.1 | runtime-versions | $(Get-Date -Format o)"
  $environmentHeader="# Environment: $venv"
  @($versionHeader,$environmentHeader,$freeze.Output) | Set-Content 'output\logs\runtime-versions.txt' -Encoding UTF8
  if($Offline){$env:HF_HUB_OFFLINE='1';$env:TRANSFORMERS_OFFLINE='1'}
  if($TinySdPath){$env:TINYSD_MODELS=(Resolve-Path $TinySdPath).Path}
  Step 'Checking/downloading official model directly into models\LFM3-Omni-2B'
  $download=Invoke-NativeProcess -FilePath $venv -Arguments @('-u','backend\engine.py') -InputText '{"command":"download"}'
  if($download.ExitCode -ne 0){throw ('Model preparation failed: '+$download.Error)}
  if(!(Test-Path 'models\LFM3-Omni-2B\download-manifest.json')){throw 'Model incomplete; inspect log'}
  if(!$SkipWikipedia){
    Step 'Preparing offline German Wikipedia (mini default: article introductions, about 4.4 GB)'
    $wiki=@('backend\wiki_setup.py','--flavour',$WikipediaFlavour,'--optional')
    if($WikipediaPath){$wiki+=@('--path',$WikipediaPath)}
    if($Offline){$wiki+='--offline'}
    Run $venv $wiki
  }else{Write-Host '[INFO] Wikipedia download skipped; select a local ZIM or run setup again later.'}
  Write-Host '[OK] Setup complete.' -ForegroundColor Green
  Stop-Transcript | Out-Null
  if(!$NoLaunch){
    Write-Host '[INFO] Starting in 10 seconds. Press any key to cancel.' -ForegroundColor DarkYellow
    for($i=0;$i -lt 100;$i++){if([Console]::KeyAvailable){[void][Console]::ReadKey($true);exit 0};Start-Sleep -Milliseconds 100}
    & "$PSScriptRoot\Start.cmd"
  }
} catch {Write-Host "[ERR] $_" -ForegroundColor Red;Stop-Transcript | Out-Null;exit 1}
