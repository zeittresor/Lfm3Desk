param([switch]$FrameworkDependent)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
. (Join-Path $PSScriptRoot 'NativeProcess.ps1')
try {
  $dotnet=Get-Command dotnet -ErrorAction SilentlyContinue
  $local=Join-Path $PSScriptRoot 'tools\dotnet\dotnet.exe'
  if(Test-Path $local){$dotnet=$local}elseif($dotnet){$dotnet=$dotnet.Source}
  if(!$dotnet){
    Write-Host '[STEP] Installing local .NET 8 SDK' -ForegroundColor Cyan
    New-Item -ItemType Directory -Force tools | Out-Null
    Invoke-WebRequest 'https://dot.net/v1/dotnet-install.ps1' -OutFile 'tools\dotnet-install.ps1' -UseBasicParsing
    & 'tools\dotnet-install.ps1' -Channel 8.0 -InstallDir (Join-Path $PSScriptRoot 'tools\dotnet') -NoPath
    if(!(Test-Path $local)){throw 'SDK installation failed'}
    $dotnet=$local
  }
  $self=if($FrameworkDependent){'false'}else{'true'}
  Write-Host '[STEP] Publishing Windows x64 application' -ForegroundColor Cyan
  Run $dotnet @('publish','src\Lfm3Desk.csproj','-c','Release','-r','win-x64','--self-contained',$self,'-p:PublishSingleFile=true','-o','build\app')
  Get-ChildItem 'build\app' -File | Copy-Item -Destination $PSScriptRoot -Force
  Write-Host '[OK] lfm3gui.exe ready.' -ForegroundColor Green
} catch {Write-Host "[ERR] $_" -ForegroundColor Red;exit 1}
