# Manual installation of required components

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  MANUAL INSTALLATION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$downloads = "C:\GOST-Downloads"
New-Item -ItemType Directory -Path $downloads -Force | Out-Null

# Download Strawberry Perl
Write-Host "`n[1/3] Downloading Strawberry Perl..." -ForegroundColor Yellow
$perlUrl = "https://github.com/StrawberryPerl/Perl-Dist-Strawberry/releases/download/SP_53822_64bit/strawberry-perl-5.38.2.2-64bit.msi"
$perlInstaller = "$downloads\strawberry-perl.msi"
Invoke-WebRequest -Uri $perlUrl -OutFile $perlInstaller -UseBasicParsing
Write-Host "Installing Perl..." -ForegroundColor Gray
Start-Process msiexec.exe -ArgumentList "/i `"$perlInstaller`" /quiet /norestart" -Wait -NoNewWindow
Write-Host "Perl installed!" -ForegroundColor Green

# Download CMake
Write-Host "`n[2/3] Downloading CMake..." -ForegroundColor Yellow
$cmakeUrl = "https://github.com/Kitware/CMake/releases/download/v3.28.1/cmake-3.28.1-windows-x86_64.msi"
$cmakeInstaller = "$downloads\cmake.msi"
Invoke-WebRequest -Uri $cmakeUrl -OutFile $cmakeInstaller -UseBasicParsing
Write-Host "Installing CMake..." -ForegroundColor Gray
Start-Process msiexec.exe -ArgumentList "/i `"$cmakeInstaller`" ADD_CMAKE_TO_PATH=System /quiet /norestart" -Wait -NoNewWindow
Write-Host "CMake installed!" -ForegroundColor Green

# Download NASM
Write-Host "`n[3/3] Downloading NASM..." -ForegroundColor Yellow
$nasmUrl = "https://www.nasm.us/pub/nasm/releasebuilds/2.16.01/win64/nasm-2.16.01-installer-x64.exe"
$nasmInstaller = "$downloads\nasm-installer.exe"
Invoke-WebRequest -Uri $nasmUrl -OutFile $nasmInstaller -UseBasicParsing
Write-Host "Installing NASM..." -ForegroundColor Gray
Start-Process $nasmInstaller -ArgumentList "/S" -Wait -NoNewWindow
Write-Host "NASM installed!" -ForegroundColor Green

# Update PATH
Write-Host "`nUpdating PATH..." -ForegroundColor Yellow
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  VERIFYING INSTALLATIONS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`nPerl:" -ForegroundColor Yellow
if (Test-Path "C:\Strawberry\perl\bin\perl.exe") {
    & "C:\Strawberry\perl\bin\perl.exe" --version | Select-Object -First 2
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "NOT FOUND" -ForegroundColor Red
}

Write-Host "`nCMake:" -ForegroundColor Yellow
if (Get-Command cmake -ErrorAction SilentlyContinue) {
    cmake --version | Select-Object -First 1
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "NOT FOUND" -ForegroundColor Red
}

Write-Host "`nNASM:" -ForegroundColor Yellow
if (Get-Command nasm -ErrorAction SilentlyContinue) {
    nasm -v
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "NOT FOUND (optional)" -ForegroundColor Yellow
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nNext: Run compile_openssl_gost.ps1" -ForegroundColor Yellow

