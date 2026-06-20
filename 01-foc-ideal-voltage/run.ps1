#Requires -Version 7
<#
.SYNOPSIS
    BrushlessDCMotor シミュレーションを実行します。

.PARAMETER IqRef
    q 軸電流指令値 [A] (--iq_ref)

.PARAMETER Tload
    負荷トルク [Nm] (--tload)

.PARAMETER Span
    シミュレーション時間 [s] (--span)

.PARAMETER CsvOut
    CSV 出力ファイルパス (--csv_out)。省略時はデフォルトパスを使用します。

.PARAMETER NoCsv
    CSV 出力を無効にします (--no_csv)。

.PARAMETER Quiet
    RESULT 行のみ出力します (--quiet)。

.EXAMPLE
    .\run.ps1
    .\run.ps1 -IqRef 60.0 -Tload 2.0 -Span 3.0
    .\run.ps1 -CsvOut data\my_output.csv
    .\run.ps1 -NoCsv -Quiet
#>
param(
    [double]$IqRef   = [double]::NaN,
    [double]$Tload   = [double]::NaN,
    [double]$Span    = [double]::NaN,
    [string]$CsvOut  = "",
    [switch]$NoCsv,
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExePath = Join-Path $PSScriptRoot "BrushlessDCMotor.exe"

if (-not (Test-Path $ExePath)) {
    Write-Error "実行ファイルが見つかりません: $ExePath`nまず .\build.ps1 を実行してください。"
    exit 1
}

$Args = @()
if (-not [double]::IsNaN($IqRef))  { $Args += "--iq_ref"; $Args += $IqRef.ToString() }
if (-not [double]::IsNaN($Tload))  { $Args += "--tload";  $Args += $Tload.ToString() }
if (-not [double]::IsNaN($Span))   { $Args += "--span";   $Args += $Span.ToString() }
if ($CsvOut -ne "")                 { $Args += "--csv_out"; $Args += $CsvOut }
if ($NoCsv)                         { $Args += "--no_csv" }
if ($Quiet)                         { $Args += "--quiet" }

Write-Host ">> $ExePath $Args"
& $ExePath @Args
exit $LASTEXITCODE
