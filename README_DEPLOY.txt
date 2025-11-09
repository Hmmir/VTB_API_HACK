========================================
🚀 ДЕПЛОЙ НА vtb.gistrec.cloud
========================================

СЕРВЕР:
  IP:       178.20.42.63
  Login:    Administrator
  Password: 2:5w35V-kJtYj+Bu45U9
  Domain:   vtb.gistrec.cloud

========================================
ШАГ 1: ПОДКЛЮЧИТЬСЯ К СЕРВЕРУ
========================================

1. Откройте Remote Desktop (Win+R → mstsc)
2. Введите: 178.20.42.63
3. Логин: Administrator
4. Пароль: 2:5w35V-kJtYj+Bu45U9

========================================
ШАГ 2: УСТАНОВИТЬ DOCKER (если еще нет)
========================================

На сервере откройте PowerShell и выполните:

# Установка Docker Desktop
Invoke-WebRequest -Uri "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" -OutFile "$env:TEMP\DockerInstaller.exe"
Start-Process "$env:TEMP\DockerInstaller.exe" -Wait -ArgumentList "install --quiet"

# Перезагрузите сервер после установки Docker
Restart-Computer

========================================
ШАГ 3: ЗАПУСТИТЬ ДЕПЛОЙ (1 КОМАНДА!)
========================================

После перезагрузки откройте PowerShell от Администратора:

# Скачиваем и запускаем скрипт деплоя
Set-ExecutionPolicy Bypass -Scope Process -Force
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Hmmir/VTB_API_HACK/main/БЫСТРЫЙ_ДЕПЛОЙ.ps1" -OutFile "$env:TEMP\deploy.ps1"
& "$env:TEMP\deploy.ps1"

ИЛИ если не работает скачивание, клонируйте репозиторий:

cd C:\
git clone https://github.com/Hmmir/VTB_API_HACK.git
cd VTB_API_HACK
docker-compose down
docker-compose up -d --build

========================================
ШАГ 4: ПРОВЕРКА
========================================

Откройте браузер на сервере:
  http://vtb.gistrec.cloud

Или проверьте с вашего компьютера:
  http://vtb.gistrec.cloud

Логин:
  Email: team075-6@test.com
  Password: password123

========================================
ЕСЛИ НЕ РАБОТАЕТ
========================================

1. Проверьте Docker:
   docker --version
   docker ps

2. Проверьте логи:
   cd C:\Projects\VTB_API_HACK
   docker-compose logs backend
   docker-compose logs frontend

3. Проверьте firewall:
   New-NetFirewallRule -DisplayName "Allow HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
   New-NetFirewallRule -DisplayName "Allow Backend" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

4. Перезапустите контейнеры:
   docker-compose restart

========================================
ГОТОВО! 🎉
========================================

Приложение готово к записи демо-видео!

