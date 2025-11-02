# 🚀 Быстрая установка GOST (4 часа)

## ✅ Что уже готово
- [x] КриптоПРО CSP 5.0 установлен
- [x] Контейнер ключей `VTB_Test_Container` создан
- [x] GOST ключи сгенерированы

## 📋 Шаги установки

### Шаг 1: Получение тестового сертификата (30 мин)

1. **Установите КриптоПро ЭЦП Browser plug-in:**
   - Скачайте: https://www.cryptopro.ru/products/cades/plugin
   - Установите и перезапустите браузер

2. **Получите тестовый сертификат:**
   - Откройте: https://www.cryptopro.ru/certsrv/certrqxt.asp
   - Нажмите "Сформировать ключи и отправить запрос на сертификат"
   - Заполните форму:
     - Контейнер: `VTB_Test_Container`
     - Тип: "Сертификат проверки подлинности клиента"
     - Отметьте "Пометить ключ как экспортируемый"
   - Нажмите "Выдать тестовый сертификат"
   - Установите сертификат в хранилище

### Шаг 2: Установка OpenSSL с GOST (2 часа)

**Вариант A: Компиляция (рекомендуется)**

1. **Установите Visual Studio Build Tools:**
   - Скачайте: https://visualstudio.microsoft.com/downloads/
   - Выберите "Build Tools for Visual Studio"
   - Установите "Desktop development with C++"

2. **Установите ActivePerl:**
   - Скачайте: https://www.activestate.com/products/perl/downloads/
   - Установите (нужен для компиляции OpenSSL)

3. **Скачайте исходники:**
   ```powershell
   # OpenSSL 3.3.0
   git clone https://github.com/openssl/openssl.git
   cd openssl
   git checkout openssl-3.3.0
   
   # GOST engine
   git clone https://github.com/gost-engine/engine.git
   ```

4. **Скомпилируйте:**
   ```powershell
   # Откройте "x64 Native Tools Command Prompt for VS"
   cd openssl
   perl Configure VC-WIN64A --prefix=C:\OpenSSL-GOST
   nmake
   nmake install
   
   # Установите GOST engine
   cd ..\engine
   perl Configure --openssldir=C:\OpenSSL-GOST
   nmake
   nmake install
   ```

**Вариант B: Готовая сборка (быстрее, но сложнее найти)**
- Ищите готовые бинарники на GitHub или форумах

### Шаг 3: Установка curl с GOST (1 час)

```powershell
# Скачайте curl
git clone https://github.com/curl/curl.git
cd curl

# Настройте с OpenSSL GOST
./configure --with-openssl=C:\OpenSSL-GOST --prefix=C:\curl-GOST

# Скомпилируйте (в Visual Studio Command Prompt)
nmake
nmake install
```

### Шаг 4: Тестирование (30 мин)

```powershell
# 1. Получите access_token
curl.exe -v --data "grant_type=client_credentials&client_id=team075&client_secret=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di" `
  https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token

# 2. Вызовите GOST API
curl.exe -v --cert VTB_Test_Container `
  -H "Authorization: Bearer [ваш_токен]" `
  https://api.gost.bankingapi.ru:8443/api/rb/rewardsPay/hackathon/v1/cards
```

## 🔧 Альтернативное решение (для быстрого теста)

Если компиляция занимает слишком много времени, можно использовать готовый Docker образ с GOST или Python-обёртку, которая вызывает curl через subprocess (уже создана в `backend/app/integrations/gost_client.py`).

## ⚡ Проверка установки

Запустите тест:
```powershell
python backend/test_gost_real.py
```

Этот скрипт проверит:
- ✅ Наличие curl
- ✅ Поддержку GOST в curl
- ✅ Наличие сертификата
- ✅ Подключение к GOST API

