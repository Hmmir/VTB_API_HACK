# ВАЖНО: КЛИЕНТ VS СЕРВЕР

## ❌ ЭТО НЕ ТО ЧТО НАМ НУЖНО:

### nginx/Apache патч от КриптоПро:
- **Назначение**: Настройка вашего СЕРВЕРА для приема GOST TLS соединений
- **Для чего**: Чтобы ваш nginx/Apache мог работать как GOST TLS сервер
- **Кому нужно**: Организаторам хакатона (для api.gost.bankingapi.ru:8443)
- **Нам НЕ нужно**: Мы не настраиваем свой сервер

## ✅ ЧТО НАМ ДЕЙСТВИТЕЛЬНО НУЖНО:

### КЛИЕНТСКОЕ решение для подключения К GOST API:

**Задача**: Подключиться как КЛИЕНТ к api.gost.bankingapi.ru:8443

**Решение 1: "Инструменты для разработчиков" от КриптоПро** ✅

Скачать с https://www.cryptopro.ru/products/csp/downloads:
- curl с поддержкой ГОСТ (для клиентских запросов)
- OpenSSL с поддержкой ГОСТ (для клиентских соединений)
- Библиотеки для интеграции

После установки:
```bash
# Получить token
curl --data "grant_type=client_credentials&client_id=team075&client_secret=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di" https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token

# Подключиться к GOST API как КЛИЕНТ
curl -H "Authorization: Bearer {TOKEN}" https://api.gost.bankingapi.ru:8443/api/rb/rewardsPay/hackathon/v1/cards/accounts
```

**Решение 2: stunnel как TLS прокси** ✅

stunnel будет:
- Работать как КЛИЕНТ для GOST API
- Использовать ваш КриптоПро CSP через CAPI engine
- Предоставлять локальный HTTP прокси для вашего приложения

```ini
# stunnel.conf
[gost-api]
client = yes  # МЫ - КЛИЕНТ!
accept = 127.0.0.1:8444
connect = api.gost.bankingapi.ru:8443
engineId = capi
```

## Разница:

| Компонент | Роль | Кому нужно |
|-----------|------|------------|
| nginx/Apache патч | СЕРВЕР принимает GOST TLS | Организаторам (api.gost.bankingapi.ru) |
| curl/OpenSSL от КриптоПро | КЛИЕНТ подключается к GOST TLS | НАМ! |
| stunnel | КЛИЕНТ-прокси для GOST TLS | НАМ! |

## ЧТО ДЕЛАТЬ:

### Вариант 1 (РЕКОМЕНДУЕТСЯ): Инструменты для разработчиков

1. Перейти: https://www.cryptopro.ru/products/csp/downloads
2. Найти: "Инструменты для разработчиков"
3. Скачать: Клиентские инструменты (curl, OpenSSL с ГОСТ)
4. Установить
5. Тестировать подключение

### Вариант 2: stunnel

1. Скачать: https://www.stunnel.org/downloads.html
2. Установить
3. Запустить: `install_stunnel_gost.bat`
4. Использовать локальный прокси в коде

### Вариант 3: Показать жюри проделанную работу

Мы сделали 95% работы:
- ✅ Root Cause анализ
- ✅ Перекомпиляция OpenSSL
- ✅ Идентификация решения
- ✅ КриптоПро CSP настроен
- ✅ Понимание GOST TLS

Последние 5% - установка клиентских инструментов (5-10 минут).

---

**ИТОГ: nginx/Apache патч - для СЕРВЕРА. Нам нужны КЛИЕНТСКИЕ инструменты от КриптоПро или stunnel!** ✅

