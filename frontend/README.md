# FinanceHub Frontend

React + TypeScript frontend для FinanceHub.

## Быстрый старт

### С Docker (рекомендуется)

```bash
# Из корня проекта
docker-compose up -d
```

### Без Docker

```bash
cd frontend

# Установить зависимости
npm install

# Настроить .env
cp .env.example .env

# Запустить dev server
npm run dev
```

Приложение откроется на http://localhost:3000

## Scripts

```bash
npm run dev          # Development server
npm run build        # Production build
npm run preview      # Preview production build
npm test             # Run tests
npm run lint         # Lint code
npm run format       # Format code
```

## Структура

```
src/
├── components/  # React components
├── pages/       # Page components
├── services/    # API clients
├── contexts/    # React contexts
├── hooks/       # Custom hooks
├── types/       # TypeScript types
└── utils/       # Utility functions
```

## Технологии

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Recharts** - Charts
- **React Router** - Routing
- **Axios** - HTTP client

