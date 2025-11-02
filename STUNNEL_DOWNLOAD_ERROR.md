# ❌ ОШИБКА: Скачан неправильный stunnel

## Проблема:
```
[.] Compiled without OPENSSL
```
Это означает, что stunnel **НЕ поддерживает TLS** вообще!

---

## Что случилось:

Вы скачали обычный stunnel с **stunnel.org**, но нам нужен **специальный stunnel от КриптоПро** с поддержкой:
- ✅ OpenSSL с GOST
- ✅ CAPI engine (для работы с КриптоПро CSP)
- ✅ GOST TLS cipher suites

---

## ✅ ГДЕ СКАЧАТЬ ПРАВИЛЬНЫЙ:

### Сайт: https://www.cryptopro.ru/products/csp/downloads

**Вы уже авторизованы как:** `alien001predator@gmail.com`

### Как найти:

**Способ 1: Поиск (CTRL+F)**
```
stunnel msspi
```

**Способ 2: Прокрутить до раздела**
1. **КриптоПро CSP 5.0 R4 для Windows**
2. Найти подзаголовок: **"Приложение для создания TLS-туннеля"**
3. Скачать: **`stunnel msspi x64`** (для 64-битной Windows)

---

## Что скачать точно:

| Файл | Размер | Для чего |
|------|--------|----------|
| **stunnel msspi x64** | ~3 МБ | ✅ **ЭТОТ!** (64-бит, с MSSPI) |
| stunnel msspi cli x86 | ~2 МБ | Командная строка, 32-бит |
| stunnel x86 | ~2 МБ | 32-бит без MSSPI |
| stunnel x64 | ~3 МБ | 64-бит без MSSPI |

**Контрольная сумма ГОСТ для `stunnel msspi x64`:**
```
1D8047302EB7E56FEB2459790745113AC81E6ACEDE962EC6B2E172E22B793AF3
```

---

## Отличия от обычного stunnel:

| Параметр | stunnel.org | КриптоПро stunnel |
|----------|-------------|-------------------|
| OpenSSL | ❌ Нет | ✅ Есть (с GOST) |
| CAPI engine | ❌ Нет | ✅ Есть |
| GOST TLS | ❌ Нет | ✅ Есть |
| Работа с КриптоПро CSP | ❌ Нет | ✅ Есть |

---

## После скачивания:

1. **Установить** stunnel от КриптоПро
2. **Создать** файл `stunnel.conf` в папке `C:\Program Files\stunnel\`
3. **Содержимое** `stunnel.conf`:
   ```ini
   ; Конфигурация для GOST API
   debug = 7
   output = stunnel.log
   
   [gost-api]
   client = yes
   accept = 127.0.0.1:8444
   connect = api.gost.bankingapi.ru:8443
   engineId = capi
   ```
4. **Запустить**: 
   ```cmd
   cd "C:\Program Files\stunnel"
   stunnel.exe stunnel.conf
   ```

---

## Проверка версии:

После установки правильного stunnel:
```cmd
stunnel.exe -version
```

Должно быть:
```
stunnel 5.72 on x86-pc-msvc-1929 platform
Compiled with OPENSSL 1.1.1 или выше  ✅
Threading:WIN32 Sockets:SELECT,IPv6 TLS:OCSP,SNI
```

**Ключевое отличие:** `Compiled with OPENSSL` (а не `without OPENSSL`)

---

## ⚠️ ВАЖНО:

- ❌ НЕ используйте stunnel с stunnel.org
- ✅ Используйте ТОЛЬКО stunnel от КриптоПро
- ✅ Обязательно версию `stunnel msspi` (с MSSPI поддержкой)

