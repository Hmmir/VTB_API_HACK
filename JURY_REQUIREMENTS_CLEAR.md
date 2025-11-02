# ЧТО РЕАЛЬНО ТРЕБУЕТ ЖЮРИ ДЛЯ GOST

## ❌ ЧТО Я ДЕЛАЛ (НЕПРАВИЛЬНО):
Пытался настроить **stunnel** - это НЕ требование жюри!

## ✅ ЧТО РЕАЛЬНО НУЖНО (3 УСЛОВИЯ):

### 1. OpenSSL с GOST
**Статус:** ✅ **ЕСТЬ!**
- Путь: `C:\OpenSSL-GOST-Shared\bin\openssl.exe`
- Версия: OpenSSL 3.3.0
- Скомпилирован с `shared` библиотеками
- GOST provider в: `C:\OpenSSL-GOST-Shared\lib\ossl-modules\gostprov.dll`

### 2. curl с GOST
**Статус:** ❓ **ПРОВЕРИТЬ**
- Возможно уже есть через MSYS2
- Или скачать с КриптоПро

### 3. Сертификат КриптоПРО
**Статус:** ✅ **ЕСТЬ!**
- Контейнер: `VTB_Test_Container`
- Установлен и проверен

---

## ЧТО ЖЮРИ ХОЧЕТ ВИДЕТЬ:

### Простой curl запрос:

```bash
# 1. Получить токен
curl -v --data "grant_type=client_credentials&client_id=team075&client_secret=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di" \
  https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token

# 2. Вызвать GOST API
curl -v -H "Authorization: Bearer <TOKEN>" \
  https://api.gost.bankingapi.ru:8443/api/rb/rewardsPay/hackathon/v1/cards/accounts
```

**С использованием:**
- OpenSSL с GOST: `C:\OpenSSL-GOST-Shared\bin\openssl.exe`
- curl с GOST: Установить/проверить
- Сертификат КриптоПРО: `VTB_Test_Container`

---

## НИКАКОГО STUNNEL НЕ НУЖНО!

Жюри требует **простой curl запрос** с GOST-совместимыми инструментами.

---

## ПЛАН ДЕЙСТВИЙ:

### Шаг 1: Проверить curl
```bash
curl --version
```

### Шаг 2: Если curl не поддерживает GOST - скачать с КриптоПро или MSYS2

### Шаг 3: Настроить переменные окружения для использования нашего OpenSSL

### Шаг 4: Сделать curl запрос

---

## ЭТО НАМНОГО ПРОЩЕ!

Мы потратили время на stunnel, который вообще НЕ нужен!

Нужно просто:
1. ✅ OpenSSL с GOST - **ЕСТЬ**
2. ❓ curl с GOST - **ПРОВЕРИТЬ/УСТАНОВИТЬ**
3. ✅ Сертификат - **ЕСТЬ**

И делать прямые curl запросы!

