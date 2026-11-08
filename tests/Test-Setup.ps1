param([Parameter(Mandatory=$true)][string]$Python)
$ErrorActionPreference='Stop'
. (Join-Path (Split-Path $PSScriptRoot) 'NativeProcess.ps1')
$temporary=Join-Path ([IO.Path]::GetTempPath()) ('Lfm3 probe spaces '+[Guid]::NewGuid().ToString('N'))
[void](New-Item -ItemType Directory $temporary)
try {
  $probe=Join-Path $temporary 'argument probe.py'
  $code=@'
import json,sys
print(json.dumps(sys.argv[1:]))
print('stderr warning, not a failure',file=sys.stderr)
'@
  [IO.File]::WriteAllText($probe,$code,(New-Object Text.UTF8Encoding($false)))
  $values=@('two words','a"b','C:\folder with spaces\','',"Gr$([char]252)$([char]223)e")
  $result=Invoke-NativeProcess -FilePath $Python -Arguments (@($probe)+$values) -Echo $false
  if($result.ExitCode -ne 0){throw "Argument probe failed: $($result.Error)"}
  $received=@($result.Output | ConvertFrom-Json)
  if($received.Count -ne $values.Count){throw 'Wrong argument count'}
  for($i=0;$i -lt $values.Count;$i++){if($received[$i] -cne $values[$i]){throw "Argument $i changed"}}
  if($result.Error -notmatch 'stderr warning'){throw 'stderr was not captured'}
  [IO.File]::WriteAllText($probe,"import sys`nprint('expected failure',file=sys.stderr)`nsys.exit(7)`n")
  $result=Invoke-NativeProcess -FilePath $Python -Arguments @($probe) -Echo $false
  if($result.ExitCode -ne 7 -or $result.Error -notmatch 'expected failure'){throw 'Exit code/stderr capture failed'}
  $file=Join-Path (Split-Path $PSScriptRoot) 'backend\probe_python.py'
  $result=Invoke-NativeProcess -FilePath $Python -Arguments @($file) -Echo $false
  if($result.ExitCode -ne 0){throw 'File-based version probe failed'}
  $details=$result.Output | ConvertFrom-Json
  if(!$details.executable -or !$details.version -or !$details.bits){throw 'Incomplete interpreter metadata'}
  foreach($script in Get-ChildItem (Split-Path $PSScriptRoot) -Filter '*.ps1'){
    $tokens=$null;$errors=$null
    [void][Management.Automation.Language.Parser]::ParseFile($script.FullName,[ref]$tokens,[ref]$errors)
    if($errors.Count){throw ($errors | Out-String)}
  }
  Write-Host '[OK] Native arguments, whitespace, quotes, trailing slash, empty/Unicode values, stderr, exit code, Python file probe and PowerShell syntax.'
} finally {Remove-Item $temporary -Recurse -Force}
