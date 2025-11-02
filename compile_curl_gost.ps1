# Compile curl with OpenSSL GOST

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  COMPILING CURL WITH OPENSSL" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: Clone curl
Write-Host "`n[1/4] Cloning curl..." -ForegroundColor Yellow
cd C:\GOST-Build
if (!(Test-Path "curl")) {
    git clone --depth 1 https://github.com/curl/curl.git
    Write-Host "curl cloned!" -ForegroundColor Green
} else {
    Write-Host "curl already exists" -ForegroundColor Green
}

# Step 2: Build curl
Write-Host "`n[2/4] Building curl with OpenSSL..." -ForegroundColor Yellow
cd curl\winbuild

$buildScript = @"
@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
nmake /f Makefile.vc mode=static VC=17 WITH_SSL=static SSL_PATH=C:\OpenSSL-GOST ENABLE_WINSSL=no ENABLE_SSPI=no DEBUG=no MACHINE=x64
"@

$buildScript | Out-File -FilePath "C:\GOST-Build\build_curl.bat" -Encoding ASCII
cmd /c "C:\GOST-Build\build_curl.bat"

# Step 3: Find and copy curl.exe
Write-Host "`n[3/4] Installing curl..." -ForegroundColor Yellow
$curlExe = Get-ChildItem "C:\GOST-Build\curl\builds" -Recurse -Filter "curl.exe" -ErrorAction SilentlyContinue | Select-Object -First 1

if ($curlExe) {
    New-Item -ItemType Directory -Path "C:\curl-GOST" -Force | Out-Null
    Copy-Item $curlExe.FullName -Destination "C:\curl-GOST\curl.exe" -Force
    Write-Host "curl installed to C:\curl-GOST\curl.exe" -ForegroundColor Green
} else {
    Write-Host "ERROR: curl.exe not found after build!" -ForegroundColor Red
    exit 1
}

# Step 4: Test curl
Write-Host "`n[4/4] Testing curl..." -ForegroundColor Yellow
& "C:\curl-GOST\curl.exe" --version

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  CURL COMPILATION COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`ncurl with OpenSSL installed to: C:\curl-GOST\curl.exe" -ForegroundColor Green
Write-Host "`nNext: Test GOST API connection" -ForegroundColor Yellow
Write-Host "Run: powershell -ExecutionPolicy Bypass -File test_gost_final.ps1" -ForegroundColor Yellow

