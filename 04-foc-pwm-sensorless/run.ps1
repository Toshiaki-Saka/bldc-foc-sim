#Requires -Version 5.1
<#
.SYNOPSIS
    BrushlessDCMotor シミュレータの起動スクリプト
.PARAMETER Args
    実行ファイルに渡す追加引数
.EXAMPLE
    .\run.ps1
#>
param(
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$ExeArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
$Exe  = Join-Path $Root "BrushlessDCMotor.exe"

if (-not (Test-Path $Exe)) {
    Write-Error "Executable not found: $Exe`nRun .\build.ps1 first."
}

Write-Host "=== BrushlessDCMotor Run ===" -ForegroundColor Cyan
Write-Host "Executable : $Exe"
if ($ExeArgs) {
    Write-Host "Arguments  : $ExeArgs"
}
Write-Host ""

Push-Location $Root
try {
    if ($ExeArgs) {
        & $Exe @ExeArgs
    } else {
        & $Exe
    }
    $ExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

if ($ExitCode -eq 0) {
    Write-Host "`nFinished successfully." -ForegroundColor Green
} else {
    Write-Host "`nProcess exited with code $ExitCode." -ForegroundColor Red
    exit $ExitCode
}
