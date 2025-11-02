# Stunnel от КриптоПро - Выбор версии

## Доступные версии:

### 1. `stunnel msspi x86` (32-бит с MSSPI)
- ✅ Поддержка MSSPI (Microsoft SSPI)
- ✅ Работает с КриптоПро CSP через CAPI
- ⚠️ 32-битное приложение
- **MD5**: `e6074e618b6df66c3121b029fdde5e83`
- **Использование**: Если нужна MSSPI поддержка и не важна архитектура

### 2. `stunnel msspi cli x86` (32-бит CLI с MSSPI)
- ✅ Поддержка MSSPI
- ✅ Командная строка
- ⚠️ 32-битное приложение
- **MD5**: `27eb6c28b21d84adfb9c05bd7d883a75`
- **Использование**: Для автоматизации с MSSPI

### 3. `stunnel x86` (32-бит)
- ⚠️ Нет MSSPI
- ✅ Есть OpenSSL с GOST
- ⚠️ 32-битное приложение
- **MD5**: `5ca74c6fa2d8e93ca1006718ebabf192`

### 4. `stunnel x64` (64-бит) ⭐ РЕКОМЕНДУЕТСЯ
- ✅ 64-битное приложение (нативное для Windows 10 x64)
- ✅ Есть OpenSSL с GOST
- ⚠️ Нет MSSPI (но это НЕ критично)
- **MD5**: `a89ada95a0136f89405c9fea297742cd`
- **ГОСТ**: `1D8047302EB7E56FEB2459790745113AC81E6ACEDE962EC6B2E172E22B793AF3`

---

## ✅ Рекомендация для вашей системы (Windows 10 x64):

### Скачать: **`stunnel x64`**

**Почему:**
1. ✅ Нативная 64-битная версия для вашей ОС
2. ✅ Есть OpenSSL с GOST (самое важное!)
3. ✅ Будет работать с КриптоПро CSP
4. ⚠️ Нет MSSPI, но это не критично — GOST поддержка есть через OpenSSL

**MSSPI нужен только для:**
- Автоматического выбора сертификата из Windows Certificate Store
- Более глубокой интеграции с Windows

**Без MSSPI можно:**
- Явно указать сертификат в конфиге stunnel
- Использовать CAPI engine напрямую
- Работать с GOST через OpenSSL

---

## Конфигурация для `stunnel x64`:

### Файл: `C:\Program Files\stunnel\stunnel.conf`

```ini
; Конфигурация для GOST API с stunnel x64
debug = 7
output = stunnel.log

[gost-api]
client = yes
accept = 127.0.0.1:8444
connect = api.gost.bankingapi.ru:8443

; Используем CAPI engine для доступа к КриптоПро CSP
engineId = capi

; Указываем сертификат из контейнера КриптоПро
; (Опционально, stunnel может попробовать выбрать автоматически)
; cert = VTB_Test_Container

; GOST cipher suites
ciphers = GOST2012-GOST8912-GOST8912:GOST2001-GOST89-GOST89
```

---

## После установки:

### 1. Проверка версии:
```cmd
cd "C:\Program Files\stunnel"
stunnel.exe -version
```

Должно быть:
```
stunnel 5.72 on x86-pc-msvc-1929 platform
Compiled with OPENSSL 1.1.1 или выше  ✅
Threading:WIN32 Sockets:SELECT,IPv6 TLS:OCSP,SNI
```

**Ключевое:** `Compiled with OPENSSL` (не `without OPENSSL`)

### 2. Проверка GOST поддержки:
```cmd
stunnel.exe -options
```

Должны быть GOST cipher suites в списке.

### 3. Запуск:
```cmd
cd "C:\Program Files\stunnel"
stunnel.exe stunnel.conf
```

### 4. Тест подключения:
```cmd
curl -H "Authorization: Bearer YOUR_TOKEN" http://127.0.0.1:8444/api/rb/rewardsPay/hackathon/v1/cards/accounts
```

---

## Альтернатива (если `stunnel x64` не заработает):

Можно попробовать `stunnel msspi x86` — 32-битное приложение будет работать на 64-битной Windows благодаря WoW64.

---

## Итоговая рекомендация:

✅ **Скачать: `stunnel x64`**
- MD5: `a89ada95a0136f89405c9fea297742cd`
- Это правильная версия для Windows 10 x64
- Имеет OpenSSL с GOST
- Будет работать с КриптоПро CSP через CAPI engine

