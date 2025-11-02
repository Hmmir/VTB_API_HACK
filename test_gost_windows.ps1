# Тест GOST подключения на Windows хосте

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  GOST CONNECTION CHECK" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Check curl
Write-Host "`n[1/3] Checking curl..." -ForegroundColor Yellow
$curlPaths = @(
    "curl",
    "C:\Windows\System32\curl.exe",
    "C:\curl-GOST\bin\curl.exe"
)

$curlFound = $false
foreach ($path in $curlPaths) {
    try {
        $result = & $path --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "OK: Found curl: $path" -ForegroundColor Green
            Write-Host $result[0] -ForegroundColor Gray
            $curlFound = $true
            break
        }
    } catch {
        continue
    }
}

if (-not $curlFound) {
    Write-Host "ERROR: curl not found" -ForegroundColor Red
    Write-Host "Install curl with GOST support (see QUICK_GOST_SETUP.md)" -ForegroundColor Yellow
}

# Check certificate
Write-Host "`n[2/3] Checking certificate..." -ForegroundColor Yellow
$csptest = "C:\Program Files\Crypto Pro\CSP\csptest.exe"
$container = "VTB_Test_Container"

if (Test-Path $csptest) {
    try {
        $result = & $csptest -keyset -enum_cont -fqcn -verifycontext 2>&1
        if ($result -match $container) {
            Write-Host "OK: Container $container found" -ForegroundColor Green
        } else {
            Write-Host "WARNING: Container $container not found" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "ERROR: Check failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "WARNING: csptest.exe not found" -ForegroundColor Yellow
}

# Test getting token
Write-Host "`n[3/3] Testing access_token..." -ForegroundColor Yellow
$teamId = "team075"
$teamSecret = "1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di"
$authUrl = "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token"

if ($curlFound) {
    try {
        $curlCmd = "curl -v --data 'grant_type=client_credentials&client_id=$teamId&client_secret=$teamSecret' $authUrl"
        Write-Host "Executing: $curlCmd" -ForegroundColor Gray
        
        $response = Invoke-Expression $curlCmd 2>&1
        
        if ($response -match "access_token") {
            Write-Host "OK: Access token received!" -ForegroundColor Green
        } else {
            Write-Host "WARNING: Response received but format unexpected" -ForegroundColor Yellow
            Write-Host $response -ForegroundColor Gray
        }
    } catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
    }
} else {
    Write-Host "SKIPPED: curl not found" -ForegroundColor Yellow
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
if ($curlFound) {
    Write-Host "curl: OK" -ForegroundColor Green
} else {
    Write-Host "curl: NOT FOUND" -ForegroundColor Red
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Get test certificate (see QUICK_GOST_SETUP.md)" -ForegroundColor White
Write-Host "2. Install OpenSSL with GOST" -ForegroundColor White
Write-Host "3. Install curl with GOST" -ForegroundColor White
Write-Host "4. Test GOST API connection" -ForegroundColor White
