# OpenSSL GOST Compilation Script
# Run this from Administrator PowerShell after installing Perl, CMake, and NASM

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  COMPILING OPENSSL WITH GOST ENGINE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Update PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Step 1: Create build directory
Write-Host "`n[1/6] Creating build directory..." -ForegroundColor Yellow
$buildDir = "C:\GOST-Build"
if (Test-Path $buildDir) {
    Write-Host "Build directory exists, cleaning..." -ForegroundColor Gray
    Remove-Item -Path $buildDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
Set-Location $buildDir
Write-Host "Build directory created: $buildDir" -ForegroundColor Green

# Step 2: Clone OpenSSL
Write-Host "`n[2/6] Cloning OpenSSL 3.3.0..." -ForegroundColor Yellow
if (!(Test-Path "$buildDir\openssl")) {
    git clone --depth 1 --branch openssl-3.3.0 https://github.com/openssl/openssl.git
    Write-Host "OpenSSL cloned!" -ForegroundColor Green
} else {
    Write-Host "OpenSSL already cloned" -ForegroundColor Green
}

# Step 3: Clone GOST engine
Write-Host "`n[3/6] Cloning GOST engine..." -ForegroundColor Yellow
if (!(Test-Path "$buildDir\gost-engine")) {
    git clone --depth 1 --branch v3.0.3 https://github.com/gost-engine/engine.git gost-engine
    Write-Host "GOST engine cloned!" -ForegroundColor Green
} else {
    Write-Host "GOST engine already cloned" -ForegroundColor Green
}

# Step 4: Find Visual Studio
Write-Host "`n[4/6] Finding Visual Studio..." -ForegroundColor Yellow
$vcvarsPath = $null
$possiblePaths = @(
    "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $vcvarsPath = $path
        Write-Host "Found Visual Studio: $vcvarsPath" -ForegroundColor Green
        break
    }
}

if (!$vcvarsPath) {
    Write-Host "ERROR: Visual Studio not found!" -ForegroundColor Red
    Write-Host "Please install Visual Studio 2019 or 2022 with C++ tools" -ForegroundColor Yellow
    Write-Host "Download: https://visualstudio.microsoft.com/downloads/" -ForegroundColor Yellow
    exit 1
}

# Step 5: Compile OpenSSL
Write-Host "`n[5/6] Compiling OpenSSL (this will take ~40 minutes)..." -ForegroundColor Yellow
Set-Location "$buildDir\openssl"

# Create compilation script
$compileScript = @"
@echo off
call "$vcvarsPath"
perl Configure VC-WIN64A --prefix=C:\OpenSSL-GOST --openssldir=C:\OpenSSL-GOST\ssl no-shared
nmake
nmake install
"@

$compileScript | Out-File -FilePath "$buildDir\compile_openssl.bat" -Encoding ASCII
Write-Host "Starting OpenSSL compilation..." -ForegroundColor Gray
Write-Host "This will take 30-60 minutes. Please be patient..." -ForegroundColor Yellow

& cmd /c "$buildDir\compile_openssl.bat"

if (Test-Path "C:\OpenSSL-GOST\bin\openssl.exe") {
    Write-Host "OpenSSL compiled successfully!" -ForegroundColor Green
    & "C:\OpenSSL-GOST\bin\openssl.exe" version
} else {
    Write-Host "ERROR: OpenSSL compilation failed!" -ForegroundColor Red
    exit 1
}

# Step 6: Compile GOST engine
Write-Host "`n[6/6] Compiling GOST engine (this will take ~20 minutes)..." -ForegroundColor Yellow
Set-Location "$buildDir\gost-engine"
New-Item -ItemType Directory -Path "build" -Force | Out-Null
Set-Location "build"

$compileGostScript = @"
@echo off
call "$vcvarsPath"
cmake -G "NMake Makefiles" -DCMAKE_INSTALL_PREFIX=C:\OpenSSL-GOST -DOPENSSL_ROOT_DIR=C:\OpenSSL-GOST ..
nmake
nmake install
"@

$compileGostScript | Out-File -FilePath "$buildDir\compile_gost.bat" -Encoding ASCII
Write-Host "Starting GOST engine compilation..." -ForegroundColor Gray

& cmd /c "$buildDir\compile_gost.bat"

if (Test-Path "C:\OpenSSL-GOST\lib\engines-3\gost.dll") {
    Write-Host "GOST engine compiled successfully!" -ForegroundColor Green
} else {
    Write-Host "ERROR: GOST engine compilation failed!" -ForegroundColor Red
    exit 1
}

# Verify installation
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  VERIFICATION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`nOpenSSL version:" -ForegroundColor Yellow
& "C:\OpenSSL-GOST\bin\openssl.exe" version

Write-Host "`nGOST engine:" -ForegroundColor Yellow
& "C:\OpenSSL-GOST\bin\openssl.exe" engine gost -c

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  COMPILATION COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nOpenSSL with GOST installed to: C:\OpenSSL-GOST" -ForegroundColor Green
Write-Host "`nNext step: Compile curl with OpenSSL GOST" -ForegroundColor Yellow
Write-Host "Run: powershell -ExecutionPolicy Bypass -File compile_curl_gost.ps1" -ForegroundColor Yellow

