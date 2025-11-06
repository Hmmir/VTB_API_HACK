# 🚀 Быстрый старт - FinanceHub

## Для тех, кто хочет запустить проект за 5 минут

### 1️⃣ Установите Docker

**Windows:**
- Скачайте [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Установите и запустите

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**Mac:**
- Скачайте [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)

---

### 2️⃣ Клонируйте репозиторий

```bash
git clone https://github.com/Hmmir/VTB_API_HACK.git
cd VTB_API_HACK
```

---

### 3️⃣ Запустите проект

```bash
docker-compose up -d
```

**Подождите 30-60 секунд** пока все контейнеры запустятся.

---

### 4️⃣ Создайте тестовых пользователей

```bash
docker-compose exec backend python scripts/create_demo_user.py
docker-compose exec backend python scripts/create_gost_demo_user.py
docker-compose exec backend python scripts/seed_demo_data.py
```

---

### 5️⃣ Откройте приложение

🌐 **Frontend**: http://localhost:3000

**Войдите как:**
- **Email**: `demo`
- **Password**: `demo123`

---

## ✅ Готово!

Теперь вы можете:
- ✨ Просматривать счета из разных банков
- 💸 Совершать переводы
- 📊 Анализировать расходы
- 🎯 Ставить финансовые цели
- 🏦 Открывать банковские продукты

---

## 🆘 Проблемы?

### Порты заняты?

Измените порты в `docker-compose.yml`:

```yaml
frontend:
  ports:
    - "3001:3000"  # Вместо 3000

backend:
  ports:
    - "8001:8000"  # Вместо 8000
```

### Контейнеры не запускаются?

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Frontend не загружается?

Очистите кэш браузера: `Ctrl+Shift+Delete` или откройте в режиме инкогнито: `Ctrl+Shift+N`

---

## 📚 Подробная документация

См. [README.md](README.md) для полной документации.

---

## 🎉 Приятного использования!

**Team 075** | VTB API Hackathon 2025

