# СЖ Саратов

Рабочее пространство церкви «Слово Жизни». Реализованы интерфейсы основных макетов, совместная работа в задачах и недельный цикл офиса со сводкой пастора.

Реализованы вход по коду на почту, сессии, приглашения, управление командой, пространства, календарь, богослужения и фоновые задания. Локальная демонстрация остаётся включаемым режимом с синтетическими данными. Перед реальными пользователями нужны SMTP, HTTPS, утверждение прав и проверка развёртывания; подробности ниже.

Полный перечень реализованного, прототипов и открытых вопросов: [docs/requirements.md](docs/requirements.md). Правила для разработчиков и агентов: [AGENTS.md](AGENTS.md).

## Docker

Нужен запущенный Docker Desktop с Linux-контейнерами. Для frontend используется Node.js 22 (локально поддерживается 20.19+). Из корня:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Открыть http://localhost:8080. PostgreSQL хранится в именованном томе. Backend сначала применяет миграции, затем запускает API. Порт PostgreSQL не выставлен наружу; интерфейс доступен только на локальном компьютере. Удаление тома удалит демо-данные.

## Локальный запуск без Docker (Windows)

Из корня проекта:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend/requirements-dev.lock
cd backend
$env:DEMO_MODE="true"
$env:DATABASE_URL="sqlite+aiosqlite:///./office.db"
..\.venv\Scripts\python -m alembic upgrade head
..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

В другом терминале из frontend:

```powershell
npm ci
npm run dev
```

Открыть http://localhost:5173. Vite пересылает `/api` на порт 8000. Описание API: http://localhost:8000/docs. Переключатель пользователя в шапке — инструмент локальной демонстрации.

## Проверки

Backend (из backend, с активированным окружением):

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy app
```

Frontend (из frontend):

```powershell
npm run lint
npm run typecheck
npm test
npm run build
```

GitHub Actions запускает эти проверки для push и pull request. Сборка и запуск Docker дополнительно проверяются локально при доступном Docker Engine.

PWA-оболочка включается в production-сборке. Для установки вне localhost нужен HTTPS. Данные API не кэшируются; без связи работа с личными данными недоступна. Push пока не подключён.

Результаты проверки и ограничения окружения: [docs/verification.md](docs/verification.md). Временные бизнес-правила: [docs/decisions.md](docs/decisions.md).

## Структура

```text
backend/app/domain          бизнес-правила и роли
backend/app/application     сценарии задач и интерфейс репозитория
backend/app/infrastructure  SQLAlchemy, настройки, демо-данные
backend/app/api             HTTP-маршруты и схемы
backend/migrations         версионирование базы
backend/tests              тесты правил и HTTP-сценариев
frontend/src               React, Ant Design, SCSS
docs                       требования, решения и состояние реализации
```

Сценарии находятся в application, их DTO — в application/models. HTTP-схемы лежат в api/schemas, а ORM-модели и преобразования записей — в infrastructure/models и infrastructure/mappers. Общие константы и утилиты сгруппированы по назначению в app/constants и app/utils. Исключения и их преобразование в HTTP-ответы находятся в domain/exceptions.py и api/exceptions.py соответственно. Расширенные карточка задачи, редактор, недельный план и сводка вынесены в frontend/src/features. Типы frontend описаны вручную по текущим схемам; генерация из OpenAPI ещё не настроена. `docs/requirements.md` не является отчётом о полной готовности проекта.

Миграция 0002 сохраняет прежние задачи, пункты и итоги недель, добавляя участников, комментарии, чек-листы и состояние недели. Перед обновлением рабочей среды сохраняйте резервную копию. Пример локальной копии перед текущим обновлением находится в .local-backups и исключён из Git.


## Вход и фоновые задания · 5 ноября 2026

Для проверки локального входа задайте `LOCAL_AUTH_CODES=true`, `PUBLIC_ORIGIN=http://127.0.0.1:5173` и перезапустите backend. Код будет показан прямо в форме: только для локальной разработки. Демо-адреса: admin@example.test, office@example.test, leader@example.test, volunteer@example.test. Вход создаёт HttpOnly-сессию на 7 дней; небезопасные методы требуют CSRF. Страница «Сеансы» позволяет отозвать устройства. Восстановление через почту завершает старые сеансы; смена утраченной почты выполняется другим администратором с новым приглашением. Ссылку приглашения администратор передаёт отдельно, автоматической отправки приглашений нет.

Без демо сначала примените миграции, затем из backend выполните `python -m app.manage admin@your-domain.ru "Имя администратора"`. Публичной регистрации нет. Настройки берутся из окружения или .env в текущем каталоге; корневой .env автоматически используется Compose, для запуска Python из backend передайте переменные явно.

Для SMTP задайте `OTP_DELIVERY=smtp`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, при необходимости `SMTP_USER`/`SMTP_PASSWORD`. По умолчанию используется STARTTLS. Для production обязательны `APP_ENV=production`, `DEMO_MODE=false`, `LOCAL_AUTH_CODES=false`, `COOKIE_SECURE=true`, HTTPS в `PUBLIC_ORIGIN`, постоянный случайный `APP_SECRET` минимум 32 символа и SMTP. Пример секретов из .env.example запрещён в production. SMS не реализован. При нескольких процессах используйте одинаковый APP_SECRET.

В отдельном терминале с теми же переменными запустите `python -m app.worker`: повторения, напоминания и push обрабатываются раз в минуту. Compose запускает worker после готовности backend. Без worker автоматические действия не происходят. Для Web Push задайте VAPID-ключи `PUSH_PRIVATE_KEY` (PEM или путь к PEM внутри контейнера), `PUSH_PUBLIC_KEY` (base64url), `PUSH_CONTACT` (mailto:контакт). Путь к приватному ключу должен быть доступен worker; секреты не добавляйте в Git. Затем пользователь самостоятельно разрешает уведомления в браузере на странице уведомлений. Без ключей остаются уведомления внутри приложения. Реальная доставка писем и push пока не проверена.

Файлы хранятся вне публичной статики в `STORAGE_PATH`; Compose сохраняет их в томе uploads. Лимит одного файла — 10 МБ. Доступ проверяется при скачивании. Удаление мягкое с восстановлением; физической очистки и антивирусного сервиса пока нет. База и файлы должны резервироваться согласованно.

Nginx перезаписывает IP-заголовок, backend доверяет прокси внутри закрытой сети Compose. Не выставляйте порт backend наружу с этой настройкой. При отдельном прокси настройте доверенные адреса и HTTPS под свою схему. Текущий Compose публикует интерфейс только на loopback. Docker/PostgreSQL ещё требуют проверки на работающем Docker Engine.
