#Requires -Version 5.1
<#
.SYNOPSIS
    Run BrushlessDCMotor or EpsGearboxSim simulation and optionally launch the viewer.

.PARAMETER Sim
    Which simulation to run: Motor or Eps (default: Motor)
      Motor ... BrushlessDCMotor.exe  -> data/motor_log.csv
      Eps   ... EpsGearboxSim.exe     -> data/eps_output.csv

.PARAMETER Viewer
    Launch the Python viewer after the simulation completes.

.PARAMETER Config
    Executable configuration to look up when the binary is not in the project root
    (only used as a fallback; the CMakeLists.txt places binaries in the root).

.EXAMPLE
    .\run.ps1
    .\run.ps1 -Sim Eps
    .\run.ps1 -Sim Motor -Viewer
    .\run.ps1 -Sim Eps -Viewer
#>
param(
    [ValidateSet('Motor', 'Eps')]
    [string]$Sim = 'Motor',

    [switch]$Viewer,

    [ValidateSet('Debug', 'Release', 'RelWithDebInfo', 'MinSizeRel')]
    [string]$Config = 'Release'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = $PSScriptRoot

# --- Resolve executable ---
$ExeMap = @{
    Motor = @{ Exe = 'BrushlessDCMotor.exe'; Viewer = 'scripts\sim_viewer.py'  }
    Eps   = @{ Exe = 'EpsGearboxSim.exe';    Viewer = 'scripts\eps_viewer.py'  }
}

$entry   = $ExeMap[$Sim]
$ExePath = Join-Path $ProjectRoot $entry.Exe

# Fallback: build/<Config>/
if (-not (Test-Path $ExePath)) {
    $fallback = Join-Path $ProjectRoot "build\$Config\$($entry.Exe)"
    if (Test-Path $fallback) {
        $ExePath = $fallback
    } else {
        Write-Host "Executable not found: $ExePath" -ForegroundColor Red
        Write-Host "Run .\build.ps1 first to compile the project." -ForegroundColor Yellow
        exit 1
    }
}

# --- Run simulation ---
Write-Host "`n==> Running $($entry.Exe) ..." -ForegroundColor Cyan
Set-Location $ProjectRoot
& $ExePath
$simExit = $LASTEXITCODE

if ($simExit -ne 0) {
    Write-Host "Simulation exited with code $simExit." -ForegroundColor Red
    exit $simExit
}

Write-Host "Simulation finished." -ForegroundColor Green

# --- Optional viewer ---
if ($Viewer) {
    $ViewerScript = Join-Path $ProjectRoot $entry.Viewer

    if (-not (Test-Path $ViewerScript)) {
        Write-Host "Viewer script not found: $ViewerScript" -ForegroundColor Yellow
        exit 0
    }

    Write-Host "`n==> Launching viewer: $($entry.Viewer)" -ForegroundColor Cyan

    $python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
    if (-not $python) {
        $python = (Get-Command python3 -ErrorAction SilentlyContinue)?.Source
    }
    if (-not $python) {
        Write-Host "Python not found in PATH. Install Python 3 to use the viewer." -ForegroundColor Red
        exit 1
    }

    & $python $ViewerScript
}
