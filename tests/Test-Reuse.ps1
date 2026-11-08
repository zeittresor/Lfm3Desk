$ErrorActionPreference='Stop'
. (Join-Path (Split-Path $PSScriptRoot) 'ReuseAssets.ps1')
$temp=Join-Path ([IO.Path]::GetTempPath()) ('Lfm3 reuse '+[Guid]::NewGuid().ToString('N'))
function WriteFixture($path,$text){[void](New-Item -ItemType Directory -Force (Split-Path $path -Parent));[IO.File]::WriteAllText($path,$text)}
try{
  $old=Join-Path $temp 'Debug_Enviroment/Lfm3Desk_v1.0.1_Windows_x64_Source_and_App/Lfm3Desk'
  $new=Join-Path $temp 'Debug_Enviroment/Lfm3Desk_v1.0.3_Windows_x64_Source_and_App/Lfm3Desk'
  foreach($root in @($old,$new)){WriteFixture (Join-Path $root 'Setup.ps1') '# fixture'}
  WriteFixture (Join-Path $old 'wheelhouse/package.whl') 'wheel-bytes'
  WriteFixture (Join-Path $old 'models/LFM3-Omni-2B/model.safetensors') 'model-bytes'
  WriteFixture (Join-Path $old 'models/Tiny-SD/unet/model.onnx') 'tiny-bytes'
  WriteFixture (Join-Path $old 'tools/ffmpeg/bin/ffmpeg.exe') 'ffmpeg-bytes'
  WriteFixture (Join-Path $old '.venv/Scripts/python.exe') 'must-not-copy'
  WriteFixture (Join-Path $old 'settings.json') 'must-not-copy'
  WriteFixture (Join-Path $old 'models/LFM3-Omni-2B/test.part') 'partial-must-not-copy'
  $found=@(Get-PreviousInstallations -AppRoot $new)
  if($found.Count -ne 1 -or $found[0] -ne $old){throw 'Nested sibling predecessor not found correctly'}
  $manifest=@{repo='LiquidAI/LFM3-Omni-2B';revision='complete-revision';files=@{'model.safetensors'=11}} | ConvertTo-Json -Depth 4
  WriteFixture (Join-Path $old 'models/LFM3-Omni-2B/download-manifest.json') $manifest
  $partial=Join-Path $temp 'Debug_Enviroment/Lfm3Desk_v1.0.2_Windows_x64_Source_and_App/Lfm3Desk'
  WriteFixture (Join-Path $partial 'Setup.ps1') '# partial fixture'
  WriteFixture (Join-Path $partial 'models/LFM3-Omni-2B/model.safetensors') 'wrong-bytes'
  $partialManifest=@{repo='LiquidAI/LFM3-Omni-2B';revision='partial-revision';files=@{'model.safetensors'=11;'missing.bin'=20}} | ConvertTo-Json -Depth 4
  WriteFixture (Join-Path $partial 'models/LFM3-Omni-2B/download-manifest.json') $partialManifest
  WriteFixture (Join-Path $old 'data/wikipedia/wikipedia_de_all_mini_2026-07.zim') 'old-mini'
  WriteFixture (Join-Path $old 'data/wikipedia/wikipedia_de_all_mini_2026-10.zim') 'latest-mini'
  WriteFixture (Join-Path $partial 'data/wikipedia/wikipedia_de_all_nopic_2026-10.zim') 'full-archive'
  WriteFixture (Join-Path $old 'data/weather/region.json') '{"reports":[],"aliases":[]}'
  $found=@(Get-PreviousInstallations -AppRoot $new)
  Import-PreviousAssets -AppRoot $new -Sources $found
  foreach($file in @('wheelhouse/package.whl','models/LFM3-Omni-2B/model.safetensors','models/Tiny-SD/unet/model.onnx','tools/ffmpeg/bin/ffmpeg.exe')){
    if(!(Test-Path (Join-Path $new $file))){throw "Missing reused file: $file"}
  }
  if([IO.File]::ReadAllText((Join-Path $new 'models/LFM3-Omni-2B/model.safetensors')) -ne 'model-bytes'){throw 'Complete source was not preferred over partial snapshot'}
  foreach($file in @('.venv/Scripts/python.exe','settings.json','models/LFM3-Omni-2B/test.part')){if(Test-Path (Join-Path $new $file)){throw "Unexpected copy: $file"}}
  if(!(Test-Path (Join-Path $new 'data/weather/region.json'))){throw 'Weather cache not reused'}
  if(!(Test-Path (Join-Path $old 'data/weather/region.json'))){throw 'Weather source cache changed'}
  $zimFiles=@(Get-ChildItem (Join-Path $new 'data/wikipedia') -Filter '*.zim')
  if($zimFiles.Count -ne 1 -or $zimFiles[0].Name -ne 'wikipedia_de_all_mini_2026-10.zim'){throw 'Wikipedia should reuse only one, preferring newest Mini'}
  WriteFixture (Join-Path $new 'wheelhouse/package.whl') 'keep-current'
  Import-PreviousAssets -AppRoot $new -Sources $found
  if([IO.File]::ReadAllText((Join-Path $new 'wheelhouse/package.whl')) -ne 'keep-current'){throw 'Existing destination overwritten'}
  $explicit=Join-Path $temp 'elsewhere/old-app'
  WriteFixture (Join-Path $explicit 'Setup.ps1') '# fixture'
  WriteFixture (Join-Path $explicit 'wheelhouse/other.whl') 'other'
  $found=@(Get-PreviousInstallations -AppRoot $new -ReuseFrom @($explicit))
  if($found -notcontains $explicit){throw 'Explicit source not included'}
  Write-Host '[OK] Nested release discovery, local assets, no .venv/settings copy, partial-file exclusion, destination preservation, explicit source.'
}finally{if(Test-Path $temp){Remove-Item $temp -Recurse -Force}}
