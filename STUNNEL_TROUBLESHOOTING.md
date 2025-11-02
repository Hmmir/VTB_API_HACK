# Решение проблемы: stunnel сразу закрывается

## Проблема:
При запуске `stunnel.exe` окно мгновенно закрывается.

## Причины:

### 1. Нормальное поведение (служба)
stunnel по умолчанию запускается как **фоновая служба** (daemon/service), поэтому окно сразу закрывается.
- ✅ Это **нормально** если stunnel работает правильно
- ✅ Он продолжает работать в фоне

### 2. Ошибка в конфигурации
Если в конфигурации есть ошибка, stunnel завершается с ошибкой, но вы не видите сообщение.

### 3. Отсутствие конфигурации
Если stunnel не находит файл конфигурации, он завершается.

---

## Решение 1: Запуск в режиме foreground (РЕКОМЕНДУЕТСЯ)

### Используйте готовый скрипт:

```cmd
test_stunnel.bat
```

Этот скрипт:
1. ✅ Проверит установку stunnel
2. ✅ Создаст тестовый конфиг
3. ✅ Запустит stunnel **в текущем окне**
4. ✅ Покажет все ошибки и предупреждения
5. ✅ Создаст подробный лог

---

## Решение 2: Просмотр логов

### Используйте скрипт для просмотра логов:

```cmd
check_stunnel_logs.bat
```

Этот скрипт покажет все логи stunnel, даже если он уже завершился.

---

## Решение 3: Ручной запуск с foreground

### Создайте конфиг с параметром `foreground`:

```ini
; stunnel.conf
debug = 7
output = C:\Program Files\stunnel\stunnel.log
foreground = yes  ; ← КЛЮЧЕВОЙ ПАРАМЕТР

[gost-api]
client = yes
accept = 127.0.0.1:8444
connect = api.gost.bankingapi.ru:8443
engineId = capi
```

### Запустите:
```cmd
cd "C:\Program Files\stunnel"
stunnel.exe stunnel.conf
```

---

## Решение 4: Установка как службы Windows

Если stunnel работает правильно, но вы хотите, чтобы он запускался автоматически:

```cmd
cd "C:\Program Files\stunnel"
stunnel.exe -install -quiet
stunnel.exe -start
```

Проверка статуса службы:
```cmd
sc query stunnel
```

---

## Типичные ошибки и решения:

### Ошибка 1: "Cannot open configuration file"
**Причина:** Файл конфигурации не найден

**Решение:**
```cmd
REM Проверьте путь к конфигу
dir "C:\Program Files\stunnel\stunnel.conf"

REM Создайте конфиг, если его нет
copy stunnel_cryptopro.conf "C:\Program Files\stunnel\stunnel.conf"
```

### Ошибка 2: "Compiled without OPENSSL"
**Причина:** Скачали stunnel с stunnel.org вместо КриптоПро

**Решение:** Скачать `stunnel x64` с сайта КриптоПро

### Ошибка 3: "engineId = capi: engine initialization failed"
**Причина:** CAPI engine не найден или КриптоПро CSP не установлен

**Решение:**
```cmd
REM Проверить установку КриптоПро CSP
dir "C:\Program Files\Crypto Pro\CSP"

REM Проверить контейнер с сертификатом
csptest -keyset -enum_cont -fqcn -verifycontext
```

### Ошибка 4: "No limit detected for the number of clients"
**Причина:** Это предупреждение, не ошибка

**Решение:** Игнорировать, это нормально для Windows

---

## Диагностика:

### Шаг 1: Проверка установки
```cmd
"C:\Program Files\stunnel\stunnel.exe" -version
```

Должно показать:
```
stunnel 5.72 on x86-pc-msvc-1929 platform
Compiled with OPENSSL 1.1.1 или выше  ✅
```

### Шаг 2: Проверка конфигурации
```cmd
type "C:\Program Files\stunnel\stunnel.conf"
```

### Шаг 3: Проверка логов
```cmd
type "C:\Program Files\stunnel\stunnel.log"
```

### Шаг 4: Проверка процесса
```cmd
tasklist | findstr stunnel
```

Если stunnel работает, вы увидите:
```
stunnel.exe          1234 Console     1      5,000 K
```

### Шаг 5: Проверка порта
```cmd
netstat -an | findstr 8444
```

Должно показать:
```
TCP    127.0.0.1:8444    0.0.0.0:0    LISTENING
```

---

## Пошаговая инструкция для диагностики:

1. **Запустите:** `test_stunnel.bat`
2. **Дождитесь:** Окно должно остаться открытым
3. **Скопируйте:** Весь вывод из окна
4. **Отправьте:** Мне для анализа

Если увидите ошибки, я смогу точно сказать что не так!

---

## Ожидаемый успешный вывод:

```
============================================================
STUNNEL DIAGNOSTIC AND TEST SCRIPT
============================================================

[1/6] Checking stunnel installation...
OK: stunnel found at "C:\Program Files\stunnel\stunnel.exe"

[2/6] Checking stunnel version...
stunnel 5.72 on x86-pc-msvc-1929 platform
Compiled with OPENSSL 1.1.1
Threading:WIN32 Sockets:SELECT,IPv6 TLS:OCSP,SNI

[3/6] Creating stunnel configuration...
OK: Configuration created

[4/6] Checking configuration syntax...
OK: Configuration syntax is valid

[5/6] Configuration content:
============================================================
[конфиг]
============================================================

[6/6] Starting stunnel in foreground mode...
2025.10.31 12:00:00 LOG5[main]: stunnel 5.72 on x86-pc-msvc-1929 platform
2025.10.31 12:00:00 LOG5[main]: Compiled with OPENSSL 1.1.1
2025.10.31 12:00:00 LOG5[main]: Configuration successful
```

Если увидите это - stunnel работает! ✅

