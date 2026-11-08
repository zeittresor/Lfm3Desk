param([switch]$Offline)
$ErrorActionPreference='Stop'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
Set-Location $PSScriptRoot
try {
  if(Test-Path 'tools\dotnet-runtime\dotnet.exe'){
    $runtimes=& 'tools\dotnet-runtime\dotnet.exe' --list-runtimes
    if(($runtimes -match 'Microsoft.WindowsDesktop.App 8\.') -and ($runtimes -match 'Microsoft.NETCore.App 8\.')){exit 0}
  }
  $system=Get-Command dotnet -ErrorAction SilentlyContinue
  if($system){$runtimes=& $system.Source --list-runtimes;if($runtimes -match 'Microsoft.WindowsDesktop.App 8\.'){exit 0}}
  . (Join-Path $PSScriptRoot 'ReuseAssets.ps1')
  $previous=@(Get-PreviousInstallations -AppRoot $PSScriptRoot)
  if($previous.Count){
    Import-PreviousAssets -AppRoot $PSScriptRoot -Sources $previous -RuntimeOnly
    if(Test-Path 'tools\dotnet-runtime\dotnet.exe'){
      $runtimes=& 'tools\dotnet-runtime\dotnet.exe' --list-runtimes
      if(($runtimes -match 'Microsoft.WindowsDesktop.App 8\.') -and ($runtimes -match 'Microsoft.NETCore.App 8\.')){exit 0}
    }
  }
  if($Offline){throw '.NET 8 Desktop runtime missing for offline setup.'}
  Write-Host '[STEP] Installing local .NET 8 Desktop runtime (no administrator required)' -ForegroundColor Cyan
  New-Item -ItemType Directory -Force 'tools' | Out-Null
  if(!(Test-Path 'tools\dotnet-install.ps1')){Invoke-WebRequest 'https://dot.net/v1/dotnet-install.ps1' -OutFile 'tools\dotnet-install.ps1' -UseBasicParsing}
  foreach($runtime in @('dotnet','windowsdesktop')){
    & 'tools\dotnet-install.ps1' -Channel 8.0 -Runtime $runtime -Architecture x64 -InstallDir "$PSScriptRoot\tools\dotnet-runtime" -NoPath
    if(!(Test-Path 'tools\dotnet-runtime\dotnet.exe')){throw 'Runtime installation failed'}
  }
  $runtimes=& 'tools\dotnet-runtime\dotnet.exe' --list-runtimes
  if(!($runtimes -match 'Microsoft.WindowsDesktop.App 8\.')){throw 'Desktop runtime missing after installation'}
} catch {Write-Host "[ERR] $_" -ForegroundColor Red;exit 1}
