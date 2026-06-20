#Requires -Version 5.1
<#
.SYNOPSIS
    Launch script for BrushlessDCMotor or EpsGearboxSim simulations.

.PARAMETER Sim
    Which simulation to run: Motor, EPS, or Both. Default: Both (Motor + EPS in parallel)

.PARAMETER Viewer
    After the simulation, open the corresponding Python GUI viewer.

.PARAMETER Sweep
    Run the characteristic-sweep script instead of the simulation + viewer.
      Motor -> scripts/tn_sweep.py
      EPS   -> scripts/eps_vcurve_sweep.py

--- BrushlessDCMotor options ---
.PARAMETER IqRef    q-axis current reference [A]   (default: 85.0)
.PARAMETER Tload    Load torque [Nm]                (default: 4.3)
.PARAMETER Span     Simulation duration [s]         (default: 5.0)
.PARAMETER Vdc      DC link voltage [V]             (default: 48.0)
.PARAMETER CsvOut   Output CSV path                 (default: data/sim_output.csv)
.PARAMETER NoCsv    Disable CSV output
.PARAMETER Quiet    Suppress console output

--- EpsGearboxSim options ---
.PARAMETER Tmax     Peak driver steering torque [Nm] (default: 5.0)
.PARAMETER EpsSpan  Simulation duration [s]          (default: 5.0)
.PARAMETER Ramp     Torque ramp duration [s]          (default: 2.0)

.EXAMPLE
    .\run.ps1                                  # Both simulations in parallel (default)
    .\run.ps1 -Sim Both -Viewer                # Both + open viewers
    .\run.ps1 -Sim EPS -Viewer
    .\run.ps1 -Sim Motor -IqRef 60 -Tload 3.0 -Viewer
    .\run.ps1 -Sim EPS -Sweep
    .\run.ps1 -Sim Both -Sweep                 # Both sweep scripts sequentially
#>
param(
    [ValidateSet("Motor", "EPS", "Both")]
    [string]$Sim = "Both",
    [switch]$Viewer,
    [switch]$Sweep,

    # BrushlessDCMotor options
    [double]$IqRef   = 85.0,
    [double]$Tload   = 4.3,
    [double]$Span    = 5.0,
    [double]$Vdc     = 48.0,
    [string]$CsvOut  = "",
    [switch]$NoCsv,
    [switch]$Quiet,

    # EpsGearboxSim options
    [double]$Tmax    = 5.0,
    [double]$EpsSpan = 5.0,
    [double]$Ramp    = 2.0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot

function Invoke-Sim {
    param([string]$ExePath, [string[]]$Args)

    if (-not (Test-Path $ExePath)) {
        Write-Error "Executable not found: $ExePath`nRun .\build.ps1 first."
    }

    Write-Host "[run] $ExePath $Args" -ForegroundColor Green
    & $ExePath @Args
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Simulation exited with code $LASTEXITCODE."
    }
}

function Invoke-Python {
    param([string]$Script)

    $ScriptPath = Join-Path $ProjectRoot $Script
    if (-not (Test-Path $ScriptPath)) {
        Write-Error "Script not found: $ScriptPath"
    }

    Write-Host "[python] $ScriptPath" -ForegroundColor Green
    python $ScriptPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python script exited with code $LASTEXITCODE."
    }
}

Write-Host "=== $Sim Simulation ===" -ForegroundColor Cyan

# --- Both (Motor + EPS in parallel) ---
if ($Sim -eq "Both") {
    if ($Sweep) {
        # Run both sweep scripts sequentially (each produces its own output)
        Invoke-Python "scripts/tn_sweep.py"
        Invoke-Python "scripts/eps_vcurve_sweep.py"
    } else {
        $MotorExe = Join-Path $ProjectRoot "BrushlessDCMotor.exe"
        $EpsExe   = Join-Path $ProjectRoot "EpsGearboxSim.exe"

        foreach ($exe in @($MotorExe, $EpsExe)) {
            if (-not (Test-Path $exe)) {
                Write-Error "Executable not found: $exe`nRun .\build.ps1 first."
            }
        }

        $MotorArgs = @("--iq_ref", $IqRef, "--tload", $Tload, "--span", $Span, "--vdc", $Vdc)
        if ($CsvOut) { $MotorArgs += @("--csv_out", $CsvOut) }
        if ($NoCsv)  { $MotorArgs += "--no_csv" }
        if ($Quiet)  { $MotorArgs += "--quiet" }

        $EpsArgs = @("--tmax", $Tmax, "--span", $EpsSpan, "--ramp", $Ramp)
        if ($NoCsv)  { $EpsArgs += "--no_csv" }
        if ($Quiet)  { $EpsArgs += "--quiet" }

        Write-Host "[run] Starting Motor and EPS simulations in parallel..." -ForegroundColor Green

        $jobMotor = Start-Job -ScriptBlock {
            param($exe, $args)
            & $exe @args 2>&1
        } -ArgumentList $MotorExe, $MotorArgs

        $jobEps = Start-Job -ScriptBlock {
            param($exe, $args)
            & $exe @args 2>&1
        } -ArgumentList $EpsExe, $EpsArgs

        # Wait for both jobs and stream their output
        $null = Wait-Job $jobMotor, $jobEps

        Write-Host "`n--- Motor result ---" -ForegroundColor Yellow
        Receive-Job $jobMotor
        Remove-Job  $jobMotor

        Write-Host "`n--- EPS result ---" -ForegroundColor Yellow
        Receive-Job $jobEps
        Remove-Job  $jobEps

        if ($Viewer) {
            Invoke-Python "scripts/sim_viewer_updated.py"
            Invoke-Python "scripts/eps_viewer.py"
        }
    }
}

# --- Motor ---
if ($Sim -eq "Motor") {
    if ($Sweep) {
        Invoke-Python "scripts/tn_sweep.py"
    } else {
        $ExePath = Join-Path $ProjectRoot "BrushlessDCMotor.exe"
        $SimArgs = @(
            "--iq_ref", $IqRef,
            "--tload",  $Tload,
            "--span",   $Span,
            "--vdc",    $Vdc
        )
        if ($CsvOut)  { $SimArgs += @("--csv_out", $CsvOut) }
        if ($NoCsv)   { $SimArgs += "--no_csv" }
        if ($Quiet)   { $SimArgs += "--quiet" }

        Invoke-Sim -ExePath $ExePath -Args $SimArgs

        if ($Viewer) { Invoke-Python "scripts/sim_viewer.py" }
    }
}

# --- EPS ---
if ($Sim -eq "EPS") {
    if ($Sweep) {
        Invoke-Python "scripts/eps_vcurve_sweep.py"
    } else {
        $ExePath = Join-Path $ProjectRoot "EpsGearboxSim.exe"
        $SimArgs = @(
            "--tmax",  $Tmax,
            "--span",  $EpsSpan,
            "--ramp",  $Ramp
        )
        if ($NoCsv) { $SimArgs += "--no_csv" }
        if ($Quiet) { $SimArgs += "--quiet" }

        Invoke-Sim -ExePath $ExePath -Args $SimArgs

        if ($Viewer) { Invoke-Python "scripts/eps_viewer.py" }
    }
}

Write-Host ""
Write-Host "[done]" -ForegroundColor Cyan
