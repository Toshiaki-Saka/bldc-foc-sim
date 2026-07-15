#Requires -Version 7
<#
.SYNOPSIS
    Runs the BrushlessDCMotor simulation.

.PARAMETER IqRef
    q-axis current reference [A] (--iq_ref)

.PARAMETER Tload
    Load torque [Nm] (--tload)

.PARAMETER Span
    Simulation time [s] (--span)

.PARAMETER CsvOut
    CSV output file path (--csv_out). When omitted, the default path is used.

.PARAMETER NoCsv
    Disables CSV output (--no_csv).

.PARAMETER Quiet
    Prints only the RESULT line (--quiet).

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
    Write-Error "Executable not found: $ExePath`nRun .\build.ps1 first."
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
