#Requires -Version 7
<#
.SYNOPSIS
    Builds the BrushlessDCMotor project.

.PARAMETER Config
    Build configuration (Release / Debug). Default: Release

.PARAMETER ToolchainFile
    Path to the vcpkg toolchain file.
    When omitted, C:\vcpkg\scripts\buildsystems\vcpkg.cmake is used.

.PARAMETER Eigen3Dir
    Eigen3 CMake directory to use when not using vcpkg.
    When specified, it takes precedence over ToolchainFile.

.PARAMETER Clean
    When specified, deletes the build directory before building.

.EXAMPLE
    .\build.ps1
    .\build.ps1 -Config Debug
    .\build.ps1 -Clean
    .\build.ps1 -Eigen3Dir "C:\eigen3\cmake"
#>
param(
    [ValidateSet("Release", "Debug")]
    [string]$Config = "Release",

    [string]$ToolchainFile = "C:\vcpkg\scripts\buildsystems\vcpkg.cmake",

    [string]$Eigen3Dir = "",

    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$BuildDir    = Join-Path $ProjectRoot "build"

if ($Clean -and (Test-Path $BuildDir)) {
    Write-Host ">> Deleting build directory: $BuildDir"
    Remove-Item -Recurse -Force $BuildDir
}

if (-not (Test-Path $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir | Out-Null
}

Push-Location $BuildDir
try {
    Write-Host ">> CMake configure ($Config) ..."

    if ($Eigen3Dir -ne "") {
        cmake .. "-DEigen3_DIR=$Eigen3Dir" "-DVCPKG_APPLOCAL_DEPS=OFF"
    } elseif (Test-Path $ToolchainFile) {
        cmake .. "-DCMAKE_TOOLCHAIN_FILE=$ToolchainFile" "-DVCPKG_APPLOCAL_DEPS=OFF"
    } else {
        Write-Warning "vcpkg toolchain not found: $ToolchainFile"
        Write-Warning "Specify the Eigen3 path with the -Eigen3Dir option."
        cmake ..
    }

    if ($LASTEXITCODE -ne 0) { throw "CMake configure failed." }

    Write-Host ">> Building ($Config) ..."
    cmake --build . --config $Config

    if ($LASTEXITCODE -ne 0) { throw "Build failed." }

    $ExePath = Join-Path $ProjectRoot "BrushlessDCMotor.exe"
    if (Test-Path $ExePath) {
        Write-Host ""
        Write-Host "Build succeeded: $ExePath" -ForegroundColor Green
    } else {
        Write-Warning "Executable not found: $ExePath"
    }
} finally {
    Pop-Location
}
