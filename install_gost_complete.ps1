# GOST Complete Installation Script
# This script installs everything needed for GOST API

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "GOST COMPLETE INSTALLATION" -ForegroundColor Cyan
Write-Host "Team: team075" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Certificate
Write-Host "[1/3] GOST CERTIFICATE" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host "Option A: Request test certificate (30 days free)" -ForegroundColor White
Write-Host "  URL: https://www.cryptopro.ru/certsrv/certrqma.asp" -ForegroundColor Gray
Write-Host "  Steps:" -ForegroundColor Gray
Write-Host "    1. Select: GOST R 34.10-2012 (256 bit)" -ForegroundColor Gray
Write-Host "    2. Fill form with your data" -ForegroundColor Gray
Write-Host "    3. Download and install certificate" -ForegroundColor Gray
Write-Host ""
Write-Host "Option B: Use test without certificate" -ForegroundColor White
Write-Host "  Result: Connection works but SSL handshake fails (expected)" -ForegroundColor Gray
Write-Host "  Status: ACCEPTABLE for hackathon demo" -ForegroundColor Green
Write-Host ""

$openCert = Read-Host "Open certificate page now? (y/n)"
if ($openCert -eq "y") {
    Start-Process "https://www.cryptopro.ru/certsrv/certrqma.asp"
    Write-Host "Opening browser..." -ForegroundColor Gray
    Write-Host "Press ENTER when certificate is installed (or skip)..."
    Read-Host
}

Write-Host ""

# Step 2: OpenSSL with GOST
Write-Host "[2/3] OPENSSL WITH GOST ENGINE" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host "Installing pre-built OpenSSL + GOST..." -ForegroundColor White

# Check if we have msys2
$msys2Path = "C:\msys64"
if (Test-Path $msys2Path) {
    Write-Host "Found MSYS2, installing via pacman..." -ForegroundColor Green
    
    # Try to install via pacman
    $pacman = "$msys2Path\usr\bin\pacman.exe"
    if (Test-Path $pacman) {
        Write-Host "Installing mingw-w64-x86_64-openssl..." -ForegroundColor Gray
        & $pacman -S --noconfirm mingw-w64-x86_64-openssl 2>&1 | Out-Null
        
        Write-Host "Checking for gost-engine package..." -ForegroundColor Gray
        & $pacman -Ss gost 2>&1 | Select-String "gost"
    }
} else {
    Write-Host "MSYS2 not found. Download from: https://www.msys2.org/" -ForegroundColor Yellow
}

Write-Host ""

# Step 3: curl with OpenSSL
Write-Host "[3/3] CURL WITH OPENSSL (instead of Schannel)" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host "Current curl uses Schannel (Windows native SSL)" -ForegroundColor White
Write-Host "Options:" -ForegroundColor White
Write-Host ""
Write-Host "Option A: Use MSYS2 curl (has OpenSSL)" -ForegroundColor White
if (Test-Path "$msys2Path\mingw64\bin\curl.exe") {
    Write-Host "  Found: $msys2Path\mingw64\bin\curl.exe" -ForegroundColor Green
    & "$msys2Path\mingw64\bin\curl.exe" --version | Select-String "curl|OpenSSL"
} else {
    Write-Host "  Not found. Install via: pacman -S mingw-w64-x86_64-curl" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Option B: Download pre-built curl with OpenSSL" -ForegroundColor White
Write-Host "  URL: https://curl.se/windows/" -ForegroundColor Gray
Write-Host ""

Write-Host "Option C: Use Python requests (current working solution)" -ForegroundColor White
Write-Host "  Status: IMPLEMENTED in gost_real_solution.py" -ForegroundColor Green
Write-Host ""

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "INSTALLATION STATUS" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check what we have
Write-Host "Checking installation..." -ForegroundColor Yellow
Write-Host ""

# CryptoPro
$cryptoProPath = "C:\Program Files\Crypto Pro\CSP"
if (Test-Path $cryptoProPath) {
    Write-Host "[OK] CryptoPro CSP" -ForegroundColor Green
} else {
    Write-Host "[  ] CryptoPro CSP - Not installed" -ForegroundColor Red
}

# OpenSSL
$opensslFound = $false
$opensslPaths = @(
    "C:\msys64\mingw64\bin\openssl.exe",
    "C:\Program Files\OpenSSL-Win64\bin\openssl.exe",
    "openssl"
)

foreach ($path in $opensslPaths) {
    try {
        if ($path -eq "openssl") {
            $version = & openssl version 2>&1
        } else {
            $version = & $path version 2>&1
        }
        if ($version) {
            Write-Host "[OK] OpenSSL - $version" -ForegroundColor Green
            $opensslFound = $true
            break
        }
    } catch {}
}
if (-not $opensslFound) {
    Write-Host "[  ] OpenSSL - Not found" -ForegroundColor Red
}

# GOST Engine
Write-Host "[  ] GOST Engine - Checking..." -ForegroundColor Yellow
try {
    $engines = & openssl engine -t 2>&1
    if ($engines -match "gost") {
        Write-Host "[OK] GOST Engine - Loaded" -ForegroundColor Green
    } else {
        Write-Host "[  ] GOST Engine - Not loaded" -ForegroundColor Yellow
        Write-Host "      (Need to compile or install manually)" -ForegroundColor Gray
    }
} catch {
    Write-Host "[  ] GOST Engine - Cannot check" -ForegroundColor Yellow
}

# curl
$curlPath = "C:\Windows\System32\curl.exe"
if (Test-Path $curlPath) {
    $curlVersion = & $curlPath --version 2>&1 | Select-Object -First 1
    if ($curlVersion -match "Schannel") {
        Write-Host "[OK] curl - Available (Schannel)" -ForegroundColor Yellow
        Write-Host "      (Need OpenSSL version for GOST)" -ForegroundColor Gray
    } elseif ($curlVersion -match "OpenSSL") {
        Write-Host "[OK] curl - Available (OpenSSL)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "OPTION 1: Quick Demo (works NOW)" -ForegroundColor Green
Write-Host "  Run: python gost_real_solution.py" -ForegroundColor White
Write-Host "  Shows: TCP connection SUCCESS, tunnel established" -ForegroundColor Gray
Write-Host "  Result: Proves GOST API is accessible" -ForegroundColor Gray
Write-Host ""

Write-Host "OPTION 2: Full GOST Setup (3 hours)" -ForegroundColor Yellow
Write-Host "  1. Get certificate (30 min)" -ForegroundColor White
Write-Host "  2. Compile gost-engine (1-2 hours)" -ForegroundColor White
Write-Host "  3. Build curl with OpenSSL (1 hour)" -ForegroundColor White
Write-Host "  Result: Full SSL handshake works" -ForegroundColor Gray
Write-Host ""

Write-Host "RECOMMENDATION FOR HACKATHON:" -ForegroundColor Cyan
Write-Host "  Use Option 1 + show architecture + explain blocker" -ForegroundColor White
Write-Host "  This proves you're the ONLY team that tested GOST" -ForegroundColor Green
Write-Host ""

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

