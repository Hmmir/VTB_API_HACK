# 5-WHY ROOT CAUSE ANALYSIS: GOST API TLS HANDSHAKE FAILURE

## Problem
TLS handshake to GOST API fails with "unexpected eof while reading" and "Cipher is (NONE)" despite TCP connection succeeding.

## Context Snapshot
- Environment: Windows 10 (26100), OpenSSL 3.3.0 (static build), CryptoPRO CSP 5.0
- Repro Summary: 100% reproducible on any connection attempt
- Facts:
  * OpenSSL compiled with "no-shared" flag (static linking)
  * gostprov.dll fails to load with error: "could not bind to the requested symbol name:...symname(OSSL_provider_init)"
  * Error: "provider has no provider init function"
  * `openssl list -providers` shows only "default", NOT "gostprov"
  * `openssl ciphers -v 'GOST'` returns "no cipher match"
  * OpenSSL compilation options include: "no-shared no-dynamic-engine"
- Assumptions:
  * gostprov.dll was compiled against static OpenSSL libraries
  * GOST API requires GOST cipher suites for TLS
- Unknowns (NOW RESOLVED):
  * ✅ Why gostprov.dll doesn't load: symbol binding failure
  * ✅ OpenSSL compilation: static build (no-shared)

## 5-Why Analysis

**Why #1: Why does TLS handshake fail?**
- **Cause**: No GOST cipher suites are available for TLS negotiation
- **Evidence**: `openssl ciphers -v 'GOST'` returns "Error in cipher list" and "no cipher match"; TLS output shows "Cipher is (NONE)"

**Why #2: Why are no GOST cipher suites available?**
- **Cause**: GOST provider (gostprov.dll) fails to load into OpenSSL
- **Evidence**: `openssl list -providers` shows only "default" provider; explicit load with `-provider gostprov` gives "unable to load provider gostprov"

**Why #3: Why does gostprov.dll fail to load?**
- **Cause**: OpenSSL cannot bind to the OSSL_provider_init symbol in gostprov.dll
- **Evidence**: Error message "A8510000:error:1280006A:DSO support routines:win32_bind_func:could not bind to the requested symbol name:crypto\dso\dso_win32.c:182:symname(OSSL_provider_init)"

**Why #4: Why can't OpenSSL bind to OSSL_provider_init in gostprov.dll?**
- **Cause**: Static OpenSSL build (libcrypto.lib) cannot dynamically load provider DLLs because the provider was compiled expecting to link against shared OpenSSL DLLs (libcrypto-3-x64.dll), but our OpenSSL was compiled with "no-shared" flag
- **Evidence**: 
  * configdata.pm shows: `"no-shared"` in options
  * Compiler flags show static linking: `/MT /Zl`
  * gostprov.dll expects dynamic OpenSSL libraries but static libs don't export symbols for dynamic loading

**Why #5 (ROOT CAUSE): Why was OpenSSL compiled with static linking incompatible with dynamic providers?**
- **Cause**: OpenSSL compilation used `./Configure VC-WIN64A no-shared` which creates static libraries (libcrypto.lib, libssl.lib) instead of DLLs. Dynamic providers (gostprov.dll) require shared OpenSSL libraries (libcrypto-3-x64.dll, libssl-3-x64.dll) to dynamically link against at runtime. The fundamental mismatch is: **static OpenSSL cannot load dynamic providers**.
- **Evidence**: 
  * configdata.pm: `"no-shared"` explicitly set
  * Build artifacts: no libcrypto-3-x64.dll or libssl-3-x64.dll in C:\OpenSSL-GOST\bin
  * GOST engine compilation succeeded but provider failed because providers MUST link to shared OpenSSL libs

## Root Cause Summary
- **Category**: Configuration / Build Process
- **One-liner**: OpenSSL was compiled with static linking (no-shared), which is incompatible with loading dynamic GOST provider DLLs that require shared OpenSSL libraries
- **Evidence Anchor(s)**: 
  * configdata.pm line showing `"no-shared"` option
  * Error "could not bind to the requested symbol name:...symname(OSSL_provider_init)"
  * Absence of libcrypto-3-x64.dll and libssl-3-x64.dll
- **Blast Radius**: All GOST API connections fail; affects hackathon demonstration
- **Confidence**: 99% (direct evidence from build config and symbol binding errors)

## Fix Recommendation

### Immediate Fix
**Recompile OpenSSL 3.3.0 with shared library support:**

1. Clean previous build:
   ```powershell
   cd C:\GOST-Build\openssl
   nmake clean
   ```

2. Reconfigure with shared libraries:
   ```powershell
   perl Configure VC-WIN64A shared --prefix="C:\OpenSSL-GOST-Shared"
   ```

3. Rebuild:
   ```powershell
   nmake
   nmake install
   ```

4. Recompile GOST engine/provider against shared OpenSSL:
   ```powershell
   cd C:\GOST-Build\gost-engine\build
   cmake .. -DOPENSSL_ROOT_DIR="C:\OpenSSL-GOST-Shared"
   cmake --build . --target install
   ```

5. Test provider loading:
   ```powershell
   C:\OpenSSL-GOST-Shared\bin\openssl.exe list -providers
   ```

### Alternative Immediate Fix (Faster - Use Precompiled)
**Copy MSYS2 OpenSSL shared libraries (already compiled with GOST support):**

```powershell
# MSYS2 already has OpenSSL with shared libs
$msys2OpenSSL = "C:\msys64\mingw64\bin"
$targetDir = "C:\OpenSSL-GOST\bin"

Copy-Item "$msys2OpenSSL\libcrypto-3-x64.dll" -Destination $targetDir -Force
Copy-Item "$msys2OpenSSL\libssl-3-x64.dll" -Destination $targetDir -Force

# Update PATH
$env:Path = "C:\OpenSSL-GOST\bin;$env:Path"

# Test
C:\OpenSSL-GOST\bin\openssl.exe list -providers
```

### Validation Plan
1. **Provider load test**:
   ```powershell
   openssl list -providers
   # Expected: default AND gostprov listed
   ```

2. **Cipher test**:
   ```powershell
   openssl ciphers -v | findstr GOST
   # Expected: List of GOST cipher suites
   ```

3. **TLS connection test**:
   ```powershell
   echo "GET / HTTP/1.1" | openssl s_client -connect api.gost.bankingapi.ru:8443
   # Expected: Cipher negotiated (not NONE)
   ```

4. **Full API test**: Run test_gost_jury_final.py and verify HTTP response

### Prevention
- **Build documentation**: Document that OpenSSL MUST be compiled with `shared` flag for provider support
- **CI/CD check**: Add automated test that verifies `openssl list -providers` shows gostprov before deployment
- **Dockerfile**: If containerizing, ensure shared OpenSSL libs are installed
- **README update**: Add troubleshooting section for "provider has no provider init function" error

## Implementation Priority
**CRITICAL - Execute Alternative Fix immediately** (5 minutes vs 2 hours for recompilation)

