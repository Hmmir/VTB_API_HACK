# 🔧 Установка инструментов для компиляции GOST

## ⏱️ Время: ~1 час

## 📋 Что нужно установить

### 1. Visual Studio Build Tools 2022 (20 мин)

**Скачать:** https://visualstudio.microsoft.com/downloads/

1. Прокрутите вниз до раздела "Tools for Visual Studio"
2. Скачайте "Build Tools for Visual Studio 2022"
3. Запустите установщик
4. Выберите "Desktop development with C++"
5. Дождитесь установки (~10 ГБ)

**Проверка:**
```powershell
# Откройте новый PowerShell и запустите:
"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cl
# Должно показать: Microsoft (R) C/C++ Optimizing Compiler
```

### 2. Strawberry Perl (10 мин)

**Скачать:** https://strawberryperl.com/

1. Нажмите "Download" на главной странице
2. Скачайте "Recommended version" (64-bit)
3. Установите с настройками по умолчанию

**Проверка:**
```powershell
perl --version
# Должно показать: This is perl 5, version 38...
```

### 3. Git for Windows (если еще нет) (5 мин)

**Скачать:** https://git-scm.com/download/win

1. Скачайте 64-bit Git for Windows Setup
2. Установите с настройками по умолчанию

**Проверка:**
```powershell
git --version
# Должно показать: git version 2.x.x
```

### 4. NASM (опционально, для оптимизаций) (5 мин)

**Скачать:** https://www.nasm.us/pub/nasm/releasebuilds/

1. Скачайте последнюю версию (nasm-x.xx-win64.zip)
2. Распакуйте в `C:\nasm`
3. Добавьте в PATH:
```powershell
$env:Path += ";C:\nasm"
[Environment]::SetEnvironmentVariable("Path", $env:Path, [System.EnvironmentVariableTarget]::Machine)
```

**Проверка:**
```powershell
nasm -v
# Должно показать: NASM version x.xx.xx
```

## 🚀 После установки

1. **Перезапустите PowerShell** (чтобы обновился PATH)

2. **Проверьте все инструменты:**
```powershell
# Visual Studio
"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cl /?

# Perl
perl --version

# Git
git --version

# NASM (опционально)
nasm -v
```

3. **Готовы к компиляции!** 

Следующий шаг: Компиляция OpenSSL GOST (см. `COMPILE_OPENSSL_GOST.md`)

## ❓ Проблемы

### "cl не является командой"
- Убедитесь, что запустили `vcvars64.bat` перед использованием `cl`
- Или откройте "x64 Native Tools Command Prompt for VS 2022" из меню Пуск

### "perl не является командой"
- Перезапустите PowerShell после установки Perl
- Проверьте PATH: `$env:Path`

### Недостаточно места на диске
- Visual Studio Build Tools: ~10 ГБ
- OpenSSL компиляция: ~2 ГБ временно
- Освободите место перед установкой

