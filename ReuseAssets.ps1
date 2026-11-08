# Bounded predecessor discovery: inspect release folders, never whole drives.
function Get-PreviousInstallations {
  param([string]$AppRoot,[string[]]$ReuseFrom=@(),[string]$AppName='Lfm3Desk')
  $self=[IO.Path]::GetFullPath($AppRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
  $seen=@{};$output=New-Object 'Collections.Generic.List[string]'
  $candidates=New-Object 'Collections.Generic.List[string]'
  foreach($entry in $ReuseFrom){if($entry){$candidates.Add($entry)}}
  $parent=Split-Path $self -Parent
  $bases=@($parent,(Split-Path $parent -Parent)) | Select-Object -Unique
  foreach($base in $bases){
    if(!$base -or !(Test-Path $base -PathType Container)){continue}
    # Only named application/release directories, bounded to 40 per level.
    foreach($folder in (Get-ChildItem $base -Directory -ErrorAction SilentlyContinue | Where-Object {$_.Name -like "$AppName*"} | Sort-Object LastWriteTime -Descending | Select-Object -First 40)){$candidates.Add($folder.FullName)}
  }
  foreach($candidate in $candidates){
    foreach($path in @($candidate,(Join-Path $candidate $AppName))){
      if(!(Test-Path $path -PathType Container)){continue}
      $full=[IO.Path]::GetFullPath($path).TrimEnd([IO.Path]::DirectorySeparatorChar)
      if($full -eq $self -or $seen.ContainsKey($full)){continue}
      if(!(Test-Path (Join-Path $full 'Setup.ps1')) -and !(Test-Path (Join-Path $full 'backend/engine.py'))){continue}
      if(!(Test-Path (Join-Path $full 'wheelhouse')) -and !(Test-Path (Join-Path $full 'models')) -and !(Test-Path (Join-Path $full 'tools'))){continue}
      $seen[$full]=$true;$output.Add($full)
    }
  }
  return $output.ToArray()
}
function Copy-ReuseTree {
  param([string]$Source,[string]$Destination,[string]$Filter='*')
  if(!(Test-Path $Source -PathType Container)){return}
  $sourceRoot=[IO.Path]::GetFullPath($Source).TrimEnd([IO.Path]::DirectorySeparatorChar)+[IO.Path]::DirectorySeparatorChar
  $count=0;$bytes=[long]0
  foreach($file in Get-ChildItem $Source -File -Recurse -Force -Filter $Filter -ErrorAction SilentlyContinue){
    if($file.Name -match '\.(part|incomplete|lock|reuse-part)$'){continue}
    # Ignore links/junction entries rather than escaping a known cache tree.
    if(($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){continue}
    $relative=$file.FullName.Substring($sourceRoot.Length)
    $target=Join-Path $Destination $relative
    if(Test-Path $target){continue}
    [void](New-Item -ItemType Directory -Force (Split-Path $target -Parent))
    try{
      $temporary=$target+'.reuse-part'
      Copy-Item -LiteralPath $file.FullName -Destination $temporary -ErrorAction Stop
      if((Get-Item $temporary).Length -ne $file.Length){throw 'File size changed while copying'}
      Move-Item -LiteralPath $temporary -Destination $target -ErrorAction Stop
      $count++;$bytes+=$file.Length
    }catch{Write-Host "[WARN] Reuse skipped: $($file.FullName) - $_" -ForegroundColor DarkYellow;if(Test-Path ($target+'.reuse-part')){Remove-Item -LiteralPath ($target+'.reuse-part') -Force -ErrorAction SilentlyContinue}}
  }
  if($count -gt 0){Write-Host "[REUSE] $count files / $bytes bytes from $Source" -ForegroundColor Green}
}
function Import-PreviousAssets {
  param([string]$AppRoot,[string[]]$Sources,[switch]$RuntimeOnly,[switch]$SkipWikipedia)
  if($RuntimeOnly){
    if(Test-Path (Join-Path $AppRoot 'tools/dotnet-runtime/dotnet.exe')){return}
    foreach($source in $Sources){
      if(Test-Path (Join-Path $source 'tools/dotnet-runtime/dotnet.exe')){
        Write-Host "[SOURCE] $source"
        Copy-ReuseTree (Join-Path $source 'tools/dotnet-runtime') (Join-Path $AppRoot 'tools/dotnet-runtime')
        break
      }
    }
    return
  }
  foreach($source in $Sources){
    Write-Host "[SOURCE] $source"
    Copy-ReuseTree (Join-Path $source 'wheelhouse') (Join-Path $AppRoot 'wheelhouse') '*.whl'
  }
  $wikiTarget=Join-Path $AppRoot 'data/wikipedia'
  if(!$SkipWikipedia -and !(Get-ChildItem $wikiTarget -Filter '*.zim' -File -ErrorAction SilentlyContinue)){
    $archives=@(foreach($source in $Sources){Get-ChildItem (Join-Path $source 'data/wikipedia') -Filter 'wikipedia_de*.zim' -File -ErrorAction SilentlyContinue})
    # Reuse just one archive; prefer Mini, then the latest filename. Never copy all snapshots.
    $selected=$archives | Sort-Object @{Expression={if($_.Name -match '_mini_'){0}else{1}}},@{Expression={$_.Name};Descending=$true} | Select-Object -First 1
    if($selected){Copy-ReuseTree $selected.Directory.FullName $wikiTarget $selected.Name}
  }
  # Weather reports are small, self-contained per-region caches. Preserve sources.
  $weatherFiles=@(foreach($source in $Sources){Get-ChildItem (Join-Path $source 'data/weather') -Filter '*.json' -File -ErrorAction SilentlyContinue})
  foreach($group in ($weatherFiles | Group-Object Name)){
    $recent=$group.Group | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    Copy-ReuseTree $recent.Directory.FullName (Join-Path $AppRoot 'data/weather') $recent.Name
  }
  # Select a single source per model/tool, rather than merging whole runtimes.
  foreach($name in @('LFM3-Omni-2B','Tiny-SD')){
    $target=Join-Path $AppRoot "models/$name"
    $sourcesWithModel=@($Sources | Where-Object {Test-Path (Join-Path $_ "models/$name") -PathType Container})
    if($name -eq 'LFM3-Omni-2B'){
      $complete=@()
      foreach($source in $sourcesWithModel){
        $manifest=Join-Path $source "models/$name/download-manifest.json"
        if(!(Test-Path $manifest)){continue}
        try{
          $record=Get-Content $manifest -Raw | ConvertFrom-Json
          $valid=$record.repo -eq 'LiquidAI/LFM3-Omni-2B' -and $record.files.PSObject.Properties.Count -gt 0
          foreach($file in $record.files.PSObject.Properties){
            $path=Join-Path $source ("models/$name/"+$file.Name)
            if(!(Test-Path $path -PathType Leaf) -or (Get-Item $path).Length -ne [long]$file.Value){$valid=$false;break}
          }
          if($valid){$complete+=$source}
        }catch{}
      }
      if($complete.Count){$sourcesWithModel=$complete}
    }
    foreach($source in $sourcesWithModel){
      $from=Join-Path $source "models/$name"
      if(!(Get-ChildItem $from -File -Recurse -ErrorAction SilentlyContinue | Where-Object {$_.Name -notmatch '\.(part|incomplete|lock|reuse-part)$'} | Select-Object -First 1)){continue}
      # A model already being downloaded without its final manifest is resumed
      # by the downloader, not combined with a different snapshot here.
      if($name -eq 'LFM3-Omni-2B' -and (Test-Path $target)){
        $currentManifest=Join-Path $target 'download-manifest.json'
        $sourceManifest=Join-Path $from 'download-manifest.json'
        $hasWeights=Get-ChildItem $target -File -Filter '*.safetensors' -ErrorAction SilentlyContinue | Select-Object -First 1
        if($hasWeights){
          if(!(Test-Path $currentManifest) -or !(Test-Path $sourceManifest)){break}
          try{
            $current=Get-Content $currentManifest -Raw | ConvertFrom-Json
            $old=Get-Content $sourceManifest -Raw | ConvertFrom-Json
            if($current.revision -ne $old.revision){continue}
          }catch{break}
        }
      }
      Copy-ReuseTree $from $target
      break
    }
  }
  foreach($name in @('python','ffmpeg')){
    $target=Join-Path $AppRoot "tools/$name"
    foreach($source in $Sources){
      $from=Join-Path $source "tools/$name"
      if(!(Test-Path $from -PathType Container)){continue}
      Copy-ReuseTree $from $target
      break
    }
  }
  foreach($name in @('python-3.12.10-amd64.exe','dotnet-install.ps1')){
    $to=Join-Path $AppRoot "tools/$name"
    if(Test-Path $to){continue}
    foreach($source in $Sources){
      $from=Join-Path $source "tools/$name"
      if(!(Test-Path $from -PathType Leaf)){continue}
      [void](New-Item -ItemType Directory -Force (Split-Path $to -Parent));Copy-Item -LiteralPath $from -Destination $to;Write-Host "[REUSE] $from" -ForegroundColor Green;break
    }
  }
}
