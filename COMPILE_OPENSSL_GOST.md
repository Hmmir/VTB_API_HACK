# 🔐 Компиляция OpenSSL с GOST engine

## ⏱️ Время: ~2 часа

## 📋 Предварительные требования

✅ Visual Studio Build Tools 2022 установлен
✅ Perl установлен
✅ Git установлен
✅ КриптоПРО CSP установлен

## 🚀 Шаг 1: Подготовка (5 мин)

```powershell
# Создайте рабочую директорию
mkdir C:\GOST-Build
cd C:\GOST-Build

# Откройте "x64 Native Tools Command Prompt for VS 2022"
# Или выполните:
& "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
```

## 🔧 Шаг 2: Скачивание исходников (10 мин)

```powershell
# OpenSSL 3.3.0
git clone https://github.com/openssl/openssl.git
cd openssl
git checkout openssl-3.3.0
cd ..

# GOST engine
git clone https://github.com/gost-engine/engine.git gost-engine
cd gost-engine
git checkout v3.0.3
cd ..
```

## 🏗️ Шаг 3: Компиляция OpenSSL (40-60 мин)

```powershell
cd C:\GOST-Build\openssl

# Настройка
perl Configure VC-WIN64A ^
  --prefix=C:\OpenSSL-GOST ^
  --openssldir=C:\OpenSSL-GOST\ssl ^
  no-shared

# ВАЖНО: no-shared = статическая сборка (проще для curl)

# Компиляция (займёт ~40 минут)
nmake

# Установка
nmake install

# Проверка
C:\OpenSSL-GOST\bin\openssl.exe version
# Должно показать: OpenSSL 3.3.0
```

**Что происходит:**
- `perl Configure` - настройка сборки
- `nmake` - компиляция (~40 мин, будет много файлов)
- `nmake install` - установка в C:\OpenSSL-GOST

## 🇷🇺 Шаг 4: Компиляция GOST engine (20-30 мин)

```powershell
cd C:\GOST-Build\gost-engine

# Создайте build директорию
mkdir build
cd build

# Настройка с CMake
cmake -G "NMake Makefiles" ^
  -DCMAKE_INSTALL_PREFIX=C:\OpenSSL-GOST ^
  -DOPENSSL_ROOT_DIR=C:\OpenSSL-GOST ^
  ..

# Компиляция
nmake

# Установка
nmake install
```

## ✅ Шаг 5: Настройка OpenSSL для GOST (5 мин)

Создайте файл конфигурации для GOST:

```powershell
# Создайте C:\OpenSSL-GOST\ssl\openssl_gost.cnf
@"
openssl_conf = openssl_init

[openssl_init]
engines = engine_section

[engine_section]
gost = gost_section

[gost_section]
engine_id = gost
dynamic_path = C:/OpenSSL-GOST/lib/engines-3/gost.dll
default_algorithms = ALL
CRYPT_PARAMS = id-Gost28147-89-CryptoPro-A-ParamSet
"@ | Out-File -FilePath "C:\OpenSSL-GOST\ssl\openssl_gost.cnf" -Encoding UTF8
```

## 🧪 Шаг 6: Тестирование (5 мин)

```powershell
# Проверка OpenSSL
C:\OpenSSL-GOST\bin\openssl.exe version
# OpenSSL 3.3.0 ...

# Проверка GOST engine
C:\OpenSSL-GOST\bin\openssl.exe engine gost -c
# Должно показать: (gost) GOST engine

# Список поддерживаемых шифров GOST
C:\OpenSSL-GOST\bin\openssl.exe ciphers -v | findstr GOST
# Должны быть GOST-шифры
```

## ✅ Результат

После успешной компиляции у вас будет:

```
C:\OpenSSL-GOST\
  ├── bin\
  │   └── openssl.exe          # OpenSSL с GOST
  ├── lib\
  │   ├── libssl.lib
  │   ├── libcrypto.lib
  │   └── engines-3\
  │       └── gost.dll         # GOST engine
  ├── include\                 # Заголовочные файлы
  └── ssl\
      └── openssl_gost.cnf     # Конфигурация GOST
```

## 🚀 Следующий шаг

Компиляция curl с OpenSSL GOST (см. `COMPILE_CURL_GOST.md`)

## ❓ Решение проблем

### "perl не найден"
```powershell
# Добавьте Perl в PATH
$env:Path += ";C:\Strawberry\perl\bin"
```

### "nmake не найден"
```powershell
# Откройте "x64 Native Tools Command Prompt for VS 2022"
# Или выполните:
& "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
```

### "CMake не найден"
```powershell
# Установите CMake
winget install Kitware.CMake
```

### Ошибки компиляции
```powershell
# Очистите и начните заново
nmake clean
perl Configure VC-WIN64A --prefix=C:\OpenSSL-GOST --openssldir=C:\OpenSSL-GOST\ssl no-shared
nmake
```

### Недостаточно места
- OpenSSL займёт ~1.5 ГБ во время компиляции
- Финальная установка: ~200 МБ
- Освободите минимум 2 ГБ

## 📊 Прогресс

- [x] Подготовка
- [x] Скачивание исходников
- [ ] Компиляция OpenSSL (текущий шаг, ~40 мин)
- [ ] Компиляция GOST engine (~20 мин)
- [ ] Настройка конфигурации
- [ ] Тестирование

