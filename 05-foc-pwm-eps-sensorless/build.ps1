#Requires -Version 5.1
<#
.SYNOPSIS
    CMake configure + build script for BrushlessDCMotor / EpsGearboxSim

.PARAMETER Config
    Build configuration: Debug or Release (default: Release)

.PARAMETER Clean
    Clean the build directory before configuring

.PARAMETER Target
    CMake target to build: BrushlessDCMotor, EpsGearboxSim, or ALL_BUILD (default: ALL_BUILD)

.EXAMPLE
    .\build.ps1
    .\build.ps1 -Config Debug
    .\build.ps1 -Clean
    .\build.ps1 -Target EpsGearboxSim
#>
param(
    [ValidateSet('Debug', 'Release', 'RelWithDebInfo', 'MinSizeRel')]
    [string]$Config = 'Release',

    [switch]$Clean,

    [ValidateSet('BrushlessDCMotor', 'EpsGearboxSim', 'ALL_BUILD')]
    [string]$Target = 'ALL_BUILD'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = $PSScriptRoot
$BuildDir    = Join-Path $ProjectRoot 'build'

function Write-Step([string]$msg) {
    Write-Host "`n==> $msg" -ForegroundColor Cyan
}

function Invoke-Checked([string]$desc, [scriptblock]$block) {
    Write-Step $desc
    & $block
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAILED: $desc (exit $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# --- Clean ---
if ($Clean -and (Test-Path $BuildDir)) {
    Write-Step "Cleaning build directory"
    Remove-Item -Recurse -Force $BuildDir
    Write-Host "Removed: $BuildDir" -ForegroundColor Yellow
}

# --- CMake configure ---
$NeedsConfigure = -not (Test-Path (Join-Path $BuildDir 'CMakeCache.txt'))

if ($NeedsConfigure) {
    Invoke-Checked "CMake configure" {
        cmake -S $ProjectRoot -B $BuildDir "-DVCPKG_APPLOCAL_DEPS=OFF"
    }
} else {
    Write-Step "CMakeCache.txt exists — skipping configure (use -Clean to reconfigure)"
}

# --- Build ---
Invoke-Checked "CMake build  [config=$Config, target=$Target]" {
    cmake --build $BuildDir --config $Config --target $Target
}

Write-Host "`nBuild succeeded." -ForegroundColor Green
