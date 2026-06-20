#Requires -Version 5.1
<#
.SYNOPSIS
    BrushlessDCMotor シミュレーションを実行します。
.PARAMETER IqRef
    q 軸電流指令 [A]（デフォルト: 85.0）
.PARAMETER Tload
    負荷トルク [Nm]（デフォルト: 4.3）
.PARAMETER Vdc
    DC リンク電圧 [V]（デフォルト: 48.0）
.PARAMETER Span
    シミュレーション時間 [s]（デフォルト: 5.0）
.PARAMETER CsvOut
    出力 CSV パス（デフォルト: data/sim_output.csv）
.PARAMETER NoCsv
    CSV 出力をスキップします。
.PARAMETER Quiet
    詳細表示を抑制します（RESULT 行のみ出力）。
.EXAMPLE
    .\run.ps1
    .\run.ps1 -IqRef 5.0 -Tload 0.3 -Vdc 48.0
    .\run.ps1 -Quiet -NoCsv
    .\run.ps1 -CsvOut "data/my_output.csv"
#>
param(
    [double]$IqRef  = 85.0,
    [double]$Tload  = 4.3,
    [double]$Vdc    = 48.0,
    [double]$Span   = 5.0,
    [string]$CsvOut = "",
    [switch]$NoCsv,
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$Exe = Join-Path $ProjectRoot "BrushlessDCMotor.exe"

if (-not (Test-Path $Exe)) {
    Write-Error "実行ファイルが見つかりません: $Exe`nまず .\build.ps1 を実行してください。"
    exit 1
}

$exeArgs = @(
    "--iq_ref", $IqRef,
    "--tload",  $Tload,
    "--vdc",    $Vdc,
    "--span",   $Span
)

if ($CsvOut -ne "") {
    $exeArgs += @("--csv_out", $CsvOut)
}
if ($NoCsv)  { $exeArgs += "--no_csv" }
if ($Quiet)  { $exeArgs += "--quiet"  }

Write-Host "=== BrushlessDCMotor Run ===" -ForegroundColor Cyan
Write-Host "iq_ref : $IqRef A"
Write-Host "tload  : $Tload Nm"
Write-Host "vdc    : $Vdc V"
Write-Host "span   : $Span s"
if ($NoCsv)  { Write-Host "csv    : skip" }
elseif ($CsvOut -ne "") { Write-Host "csv    : $CsvOut" }
else         { Write-Host "csv    : data/sim_output.csv" }
Write-Host ""

Push-Location $ProjectRoot
try {
    & $Exe @exeArgs
    if ($LASTEXITCODE -ne 0) { throw "シミュレーション終了コード: $LASTEXITCODE" }
} finally {
    Pop-Location
}
