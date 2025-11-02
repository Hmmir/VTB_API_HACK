# 🧪 ТЕСТИРОВАНИЕ GOST API

## ПРЕДВАРИТЕЛЬНЫЕ ТРЕБОВАНИЯ

✅ Все компоненты установлены и скомпилированы:
- OpenSSL 3.3.0 + GOST engine (`C:\OpenSSL-GOST\`)
- КриптоПРО CSP 5.0 (контейнер `VTB_Test_Container`)
- curl (MSYS2 или собранный с OpenSSL GOST)

## ШАГ 1: ПОЛУЧЕНИЕ ТЕСТОВОГО СЕРТИФИКАТА

1. Перейдите на https://www.cryptopro.ru/
2. Зарегистрируйтесь для получения тестового сертификата (1 месяц бесплатно)
3. Установите сертификат в контейнер `VTB_Test_Container`

## ШАГ 2: НАСТРОЙКА OPENSSL

### Конфигурация OpenSSL (`C:\OpenSSL-GOST\ssl\openssl.cnf`):

```ini
openssl_conf = openssl_init

[openssl_init]
providers = provider_sect

[provider_sect]
default = default_sect
gostprov = gostprov_sect

[default_sect]
activate = 1

[gostprov_sect]
activate = 1
module = C:/OpenSSL-GOST/lib/ossl-modules/gostprov.dll
```

### Проверка загрузки GOST provider:

```powershell
$env:OPENSSL_CONF = "C:\OpenSSL-GOST\ssl\openssl.cnf"
C:\OpenSSL-GOST\bin\openssl.exe list -providers
```

Должен появиться `gostprov` в списке providers.

## ШАГ 3: ПОЛУЧЕНИЕ ACCESS TOKEN

```powershell
$teamId = "team075"
$teamSecret = "1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di"
$authUrl = "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token"

$response = Invoke-WebRequest -Uri $authUrl `
    -Method POST `
    -Body @{
        grant_type = "client_credentials"
        client_id = $teamId
        client_secret = $teamSecret
    } `
    -UseBasicParsing

$token = ($response.Content | ConvertFrom-Json).access_token
Write-Host "Access Token: $($token.Substring(0,50))..."
```

## ШАГ 4: ТЕСТИРОВАНИЕ GOST API

### Вариант A: Через curl (если пересобран с OpenSSL GOST)

```bash
curl -v \
  --ciphers 'GOST2012-GOST8912-GOST8912:GOST2001-GOST89-GOST89' \
  --cert <certificate.pem> \
  --key <private.key> \
  -H "Authorization: Bearer $token" \
  https://api.gost.bankingapi.ru:8443/
```

### Вариант B: Через Python httpx (с настроенным OpenSSL)

```python
import httpx
import os

# Настройка OpenSSL для использования GOST
os.environ['OPENSSL_CONF'] = r'C:\OpenSSL-GOST\ssl\openssl.cnf'
os.environ['OPENSSL_MODULES'] = r'C:\OpenSSL-GOST\lib\ossl-modules'

client = httpx.Client(
    verify=False,  # Для тестирования
    cert=('<certificate.pem>', '<private.key>')
)

response = client.get(
    'https://api.gost.bankingapi.ru:8443/',
    headers={'Authorization': f'Bearer {token}'}
)

print(response.status_code)
print(response.text)
```

### Вариант C: Через наше приложение

1. Убедитесь что `USE_GOST=true` в `docker-compose.yml`
2. Войдите как `team075-demo@financehub.ru` / `gost2024`
3. UI покажет зеленый бейдж "🔒 GOST ЦБ РФ"
4. Backend автоматически использует GOST API

## ШАГ 5: ПРОВЕРКА РАБОТЫ

### Тест получения счетов через GOST API:

```bash
curl -v \
  --ciphers 'GOST2012-GOST8912-GOST8912' \
  --cert <certificate.pem> \
  --key <private.key> \
  -H "Authorization: Bearer $token" \
  https://api.gost.bankingapi.ru:8443/api/rb/rewardsPay/hackathon/v1/cards/accounts
```

## ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### Успешное подключение:
- HTTP 200 OK
- JSON ответ с данными счетов/транзакций
- TLS handshake с GOST шифрами

### Возможные ошибки:

1. **SSL handshake failed**
   - Проверьте что GOST provider загружен
   - Проверьте что сертификат установлен правильно
   - Проверьте что используются GOST cipher suites

2. **Certificate not found**
   - Убедитесь что сертификат установлен в КриптоПРО
   - Проверьте путь к сертификату в curl/Python

3. **Provider not loaded**
   - Проверьте `OPENSSL_CONF` переменную окружения
   - Проверьте что `gostprov.dll` находится в правильной директории

## ЛОГИ ДЛЯ ДИАГНОСТИКИ

### OpenSSL debug:
```bash
C:\OpenSSL-GOST\bin\openssl.exe s_client \
  -connect api.gost.bankingapi.ru:8443 \
  -cipher 'GOST2012-GOST8912-GOST8912' \
  -cert <certificate.pem> \
  -key <private.key> \
  -showcerts
```

### Проверка доступных cipher suites:
```bash
C:\OpenSSL-GOST\bin\openssl.exe ciphers -v | grep GOST
```

## ВАЖНЫЕ ЗАМЕЧАНИЯ

1. **GOST API требует TLS с GOST шифрами** - стандартные TLS не работают
2. **Сертификат должен быть ГОСТ** - обычные RSA сертификаты не подходят
3. **OpenSSL 3.x использует providers** - не engines (для совместимости)
4. **КриптоПРО CSP обязателен** - для работы с ГОСТ сертификатами

## СТАТИСТИКА ДЛЯ ЖЮРИ

При успешном подключении к GOST API, ваши запросы будут видны в статистике организаторов, что подтверждает реальное использование GOST шлюза.

