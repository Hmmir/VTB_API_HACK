@echo off
REM Compilation of curl with OpenSSL GOST

echo ============================================================
echo CURL COMPILATION WITH OPENSSL GOST
echo ============================================================

set CURL_SRC=C:\curl-src
set OPENSSL_DIR=C:\OpenSSL-GOST-Shared
set CURL_INSTALL=C:\curl-gost

REM Step 1: Clone curl
echo.
echo [1/5] Cloning curl...
if not exist "%CURL_SRC%" (
    git clone --depth=1 https://github.com/curl/curl.git "%CURL_SRC%"
    echo OK: curl cloned
) else (
    echo OK: curl already exists
)

REM Step 2: Create build directory
echo.
echo [2/5] Preparing build...
cd /d "%CURL_SRC%"
if not exist build mkdir build
cd build

REM Step 3: CMake configuration
echo.
echo [3/5] CMake configuration...
cmake .. ^
    -G "Visual Studio 17 2022" ^
    -A x64 ^
    -DCMAKE_INSTALL_PREFIX="%CURL_INSTALL%" ^
    -DCURL_USE_OPENSSL=ON ^
    -DOPENSSL_ROOT_DIR="%OPENSSL_DIR%" ^
    -DOPENSSL_INCLUDE_DIR="%OPENSSL_DIR%\include" ^
    -DOPENSSL_CRYPTO_LIBRARY="%OPENSSL_DIR%\lib\libcrypto.lib" ^
    -DOPENSSL_SSL_LIBRARY="%OPENSSL_DIR%\lib\libssl.lib" ^
    -DBUILD_CURL_EXE=ON ^
    -DBUILD_SHARED_LIBS=OFF ^
    -DCURL_DISABLE_LDAP=ON ^
    -DCURL_USE_LIBPSL=OFF ^
    -DCURL_USE_LIBSSH2=OFF ^
    -DCURL_ZLIB=OFF ^
    -DUSE_NGHTTP2=OFF ^
    -DUSE_LIBIDN2=OFF

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: CMake configuration failed
    pause
    exit /b 1
)

echo OK: CMake configured

REM Step 4: Build
echo.
echo [4/5] Building curl...
echo This may take 5-10 minutes...
cmake --build . --config Release --target curl

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo OK: curl built

REM Step 5: Install
echo.
echo [5/5] Installing curl...
cmake --install . --config Release

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Install failed
    pause
    exit /b 1
)

echo.
echo ============================================================
echo SUCCESS!
echo ============================================================
echo.
echo curl installed to: %CURL_INSTALL%\bin\curl.exe
echo.
echo Testing version:
"%CURL_INSTALL%\bin\curl.exe" --version

echo.
echo Next step: Run test_gost_final.bat
pause

