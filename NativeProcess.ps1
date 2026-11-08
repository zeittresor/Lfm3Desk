# PowerShell 5.1-compatible native argument handling and independent stderr capture.
function ConvertTo-NativeArgument {
  param([AllowEmptyString()][string]$Value)
  if($Value.Length -gt 0 -and $Value -notmatch '[\s"]'){return $Value}
  $builder=New-Object Text.StringBuilder
  [void]$builder.Append([char]34)
  $slashes=0
  foreach($ch in $Value.ToCharArray()){
    if($ch -eq [char]92){$slashes++;continue}
    if($ch -eq [char]34){[void]$builder.Append([char]92,2*$slashes+1)}
    elseif($slashes -gt 0){[void]$builder.Append([char]92,$slashes)}
    [void]$builder.Append($ch)
    $slashes=0
  }
  if($slashes -gt 0){[void]$builder.Append([char]92,2*$slashes)}
  [void]$builder.Append([char]34)
  return $builder.ToString()
}
function Invoke-NativeProcess {
  param([string]$FilePath,[string[]]$Arguments=@(),[AllowNull()][string]$InputText=$null,[bool]$Echo=$true)
  $info=New-Object Diagnostics.ProcessStartInfo
  $info.FileName=$FilePath
  $info.Arguments=($Arguments | ForEach-Object {ConvertTo-NativeArgument $_}) -join ' '
  $info.WorkingDirectory=(Get-Location).ProviderPath
  $info.UseShellExecute=$false
  $info.CreateNoWindow=$true
  $info.RedirectStandardOutput=$true
  $info.RedirectStandardError=$true
  $info.RedirectStandardInput=$true
  $info.StandardOutputEncoding=New-Object Text.UTF8Encoding($false)
  $info.StandardErrorEncoding=New-Object Text.UTF8Encoding($false)
  $info.EnvironmentVariables['PYTHONIOENCODING']='utf-8'
  $info.EnvironmentVariables['PYTHONUTF8']='1'
  $process=New-Object Diagnostics.Process
  $process.StartInfo=$info
  $stdout=New-Object Text.StringBuilder
  $stderr=New-Object Text.StringBuilder
  try {
    [void]$process.Start()
    if($null -ne $InputText){$process.StandardInput.WriteLine($InputText)}
    $process.StandardInput.Close()
    $outTask=$process.StandardOutput.ReadLineAsync()
    $errTask=$process.StandardError.ReadLineAsync()
    while($null -ne $outTask -or $null -ne $errTask){
      $activity=$false
      if($null -ne $outTask -and $outTask.IsCompleted){
        $line=$outTask.GetAwaiter().GetResult()
        if($null -eq $line){$outTask=$null}else{
          [void]$stdout.AppendLine($line)
          if($Echo){Write-Host $line}
          $outTask=$process.StandardOutput.ReadLineAsync()
        }
        $activity=$true
      }
      if($null -ne $errTask -and $errTask.IsCompleted){
        $line=$errTask.GetAwaiter().GetResult()
        if($null -eq $line){$errTask=$null}else{
          [void]$stderr.AppendLine($line)
          if($Echo){Write-Host $line}
          $errTask=$process.StandardError.ReadLineAsync()
        }
        $activity=$true
      }
      if(!$activity){Start-Sleep -Milliseconds 25}
    }
    $process.WaitForExit()
    return [pscustomobject]@{ExitCode=$process.ExitCode;Output=$stdout.ToString();Error=$stderr.ToString()}
  } finally {$process.Dispose()}
}
function Run {
  param([string]$FilePath,[string[]]$Arguments,[int[]]$AllowedExitCodes=@(0))
  $result=Invoke-NativeProcess -FilePath $FilePath -Arguments $Arguments
  if($result.ExitCode -notin $AllowedExitCodes){
    $detail=($result.Error.Trim() -split '\r?\n' | Select-Object -Last 8) -join [Environment]::NewLine
    throw "Command failed (exit $($result.ExitCode)): $FilePath$([Environment]::NewLine)$detail"
  }
}
