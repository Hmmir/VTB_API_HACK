# Automated GOST Setup Script

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AUTOMATED GOST INSTALLATION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: Install Chocolatey if not installed
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "`n[1/5] Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    Write-Host "Chocolatey installed!" -ForegroundColor Green
} else {
    Write-Host "`n[1/5] Chocolatey already installed" -ForegroundColor Green
}

# Refresh environment
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Step 2: Install Strawberry Perl
Write-Host "`n[2/5] Installing Strawberry Perl..." -ForegroundColor Yellow
choco install strawberryperl -y
Write-Host "Perl installed!" -ForegroundColor Green

# Step 3: Install CMake
Write-Host "`n[3/5] Installing CMake..." -ForegroundColor Yellow
choco install cmake --installargs 'ADD_CMAKE_TO_PATH=System' -y
Write-Host "CMake installed!" -ForegroundColor Green

# Step 4: Install NASM
Write-Host "`n[4/5] Installing NASM..." -ForegroundColor Yellow
choco install nasm -y
Write-Host "NASM installed!" -ForegroundColor Green

# Refresh PATH again
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Step 5: Verify installations
Write-Host "`n[5/5] Verifying installations..." -ForegroundColor Yellow

Write-Host "`nPerl:" -ForegroundColor Cyan
& "C:\Strawberry\perl\bin\perl.exe" --version

Write-Host "`nCMake:" -ForegroundColor Cyan
cmake --version

Write-Host "`nNASM:" -ForegroundColor Cyan
nasm -v

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nNext: Run compile_openssl_gost.ps1" -ForegroundColor Yellow

