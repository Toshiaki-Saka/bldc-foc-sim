#Requires -Version 5.1
<#
.SYNOPSIS
    Runs the BrushlessDCMotor simulation.
.PARAMETER IqRef
    q-axis current reference [A] (default: 85.0)
.PARAMETER Tload
    Load torque [Nm] (default: 4.3)
.PARAMETER Vdc
    DC link voltage [V] (default: 48.0)
.PARAMETER Span
    Simulation time [s] (default: 5.0)
.PARAMETER CsvOut
    Output CSV path (default: data/sim_output.csv)
.PARAMETER NoCsv
    Skip CSV output.
.PARAMETER Quiet
    Suppress verbose output (print only the RESULT line).
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
    Write-Error "Executable not found: $Exe`nRun .\build.ps1 first."
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
    if ($LASTEXITCODE -ne 0) { throw "Simulation exit code: $LASTEXITCODE" }
} finally {
    Pop-Location
}
