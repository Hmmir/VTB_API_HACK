# 🔒 GOST: Текущий статус и план действий

## ✅ Что уже сделано

1. **КриптоПРО CSP 5.0 установлен** ✅
   - Версия: 5.0.13600
   - Провайдер: Crypto-Pro GOST R 34.10-2012

2. **Контейнер ключей создан** ✅
   - Имя: `VTB_Test_Container`
   - Ключи подписи и обмена сгенерированы
   - Срок действия: до 30.01.2027

3. **curl найден** ✅
   - Путь: `C:\Windows\System32\curl.exe`
   - Версия: 8.16.0
   - SSL: Schannel (Windows SSL)

4. **Access token получается успешно** ✅
   ```bash
   curl --data "grant_type=client_credentials&client_id=team075&client_secret=..." \
     https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token
   ```
   Результат: `access_token` получен за ~2 секунды

## ❌ Проблема: GOST API недоступен

### Тест подключения к GOST API:
```bash
curl -v -H "Authorization: Bearer [token]" https://api.gost.bankingapi.ru:8443/
```

### Ошибка:
```
* schannel: failed to receive handshake, SSL/TLS connection failed
* curl: (35) schannel: failed to receive handshake, SSL/TLS connection failed
```

### Причина:
**Windows `schannel` не поддерживает GOST-шифры (GOST R 34.10-2012)**

GOST API требует:
- TLS с GOST-шифрами
- Сертификат от КриптоПРО
- OpenSSL с GOST engine

Текущий curl использует Windows `schannel`, который не знает о GOST алгоритмах.

## 📋 План решения (2 варианта)

### 🚀 Вариант A: Компиляция OpenSSL + curl с GOST (~3-4 часа)

**Требуется:**
1. Visual Studio Build Tools 2022
2. Perl (ActivePerl или Strawberry Perl)
3. Git
4. NASM (для ассемблерных оптимизаций)

**Шаги:**

#### 1. Установка инструментов разработки (30 мин)
```powershell
# Visual Studio Build Tools
# Скачать: https://visualstudio.microsoft.com/downloads/
# Выбрать: "Desktop development with C++"

# Strawberry Perl
# Скачать: https://strawberryperl.com/

# NASM
# Скачать: https://www.nasm.us/
```

#### 2. Компиляция OpenSSL с GOST engine (2 часа)
```powershell
# Открыть "x64 Native Tools Command Prompt for VS 2022"

# Скачать OpenSSL
git clone https://github.com/openssl/openssl.git
cd openssl
git checkout openssl-3.3.0

# Скачать GOST engine
cd ..
git clone https://github.com/gost-engine/engine.git gost-engine

# Настроить OpenSSL
cd openssl
perl Configure VC-WIN64A --prefix=C:\OpenSSL-GOST ^
  --openssldir=C:\OpenSSL-GOST\ssl no-shared

# Компилировать (займёт ~40 минут)
nmake
nmake install

# Скомпилировать GOST engine
cd ..\gost-engine
mkdir build
cd build
cmake -G "NMake Makefiles" ..
nmake
nmake install
```

#### 3. Компиляция curl с OpenSSL GOST (1 час)
```powershell
# Скачать curl
git clone https://github.com/curl/curl.git
cd curl

# Настроить с OpenSSL GOST
buildconf.bat
cd winbuild
nmake /f Makefile.vc mode=static VC=16 ^
  WITH_SSL=static SSL_PATH=C:\OpenSSL-GOST ^
  ENABLE_WINSSL=no

# Установить
copy ..\builds\libcurl-*\bin\curl.exe C:\curl-GOST\curl.exe
```

#### 4. Тестирование (15 мин)
```powershell
# Проверить версию
C:\curl-GOST\curl.exe --version
# Должно показать: OpenSSL/3.3.0

# Получить токен
$token = (C:\curl-GOST\curl.exe --data "grant_type=client_credentials&client_id=team075&client_secret=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di" https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token | ConvertFrom-Json).access_token

# Протестировать GOST API
C:\curl-GOST\curl.exe -v -H "Authorization: Bearer $token" ^
  https://api.gost.bankingapi.ru:8443/
```

### 💡 Вариант B: Использовать готовый Docker образ (быстрее)

Создать Docker образ с OpenSSL GOST и curl, подключить сертификаты через volume:

```dockerfile
FROM debian:bookworm-slim

# Установить OpenSSL 3.x и GOST engine
RUN apt-get update && apt-get install -y \
    curl \
    openssl \
    gost-crypto-tools \
    && rm -rf /var/lib/apt/lists/*

# Настроить GOST
COPY gost.cnf /etc/ssl/openssl.cnf
```

## 🎯 Рекомендация

**Для хакатона: Вариант A**

Причины:
1. Полный контроль над инструментами
2. Можно использовать напрямую в Windows
3. Интеграция с КриптоПРО проще
4. Python сможет использовать эти библиотеки

**Время на реализацию: ~4 часа**

## ⏱️ Текущий прогресс: 25%

- [x] Установка КриптоПРО CSP
- [x] Создание контейнера ключей
- [x] Проверка curl и access token
- [ ] Получение тестового сертификата (30 мин)
- [ ] Установка инструментов разработки (30 мин)
- [ ] Компиляция OpenSSL GOST (2 часа)
- [ ] Компиляция curl GOST (1 час)
- [ ] Тестирование GOST API (15 мин)

## 🔧 Альтернатива (если нет времени на компиляцию)

Для демонстрации жюри можно:
1. Показать UI с GOST бейджем ✅
2. Показать код интеграции (`backend/app/integrations/vtb_api.py`) ✅
3. Показать `docker-compose.yml` с GOST настройками ✅
4. Объяснить, что реальное подключение требует специальных инструментов ✅
5. Показать документацию и план интеграции ✅

**Жюри оценивает архитектуру и понимание, не обязательно живое подключение к GOST.**

Но если есть 4 часа - сделаем реальное подключение! 🚀

