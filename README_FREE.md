# KryoClient.org — бесплатное размещение

Вариант без VPS: Render Free для Flask-приложения + Supabase Free для PostgreSQL.

## 1. GitHub
Создай репозиторий и загрузи содержимое этой папки. Файл `render.yaml` уже подготовлен.

## 2. Supabase
Создай бесплатный проект на Supabase. В Project Settings → Database возьми connection string PostgreSQL.
Добавь его в Render как переменную `DATABASE_URL`.

Не публикуй пароль базы в GitHub.

## 3. Render
В Render: New → Web Service → подключи GitHub-репозиторий.
Выбери Free. Build command: `pip install -r requirements.txt`. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`.
`render.yaml` содержит эти настройки.

## 4. Домен
В Render открой Settings → Custom Domains → Add Custom Domain → `kryoclient.org`.
Render покажет нужную DNS-запись. В панели регистратора домена добавь именно её. Render автоматически выдаёт TLS/HTTPS для custom domain.

## Важно про бесплатный режим
Render Free усыпляет сервис после 15 минут без запросов, поэтому первый заход после простоя может занимать около минуты. Локальный диск Render непостоянный, поэтому проект использует PostgreSQL вместо SQLite.
Supabase Free предоставляет PostgreSQL с лимитом 500 MB и может приостанавливать проекты после недели бездействия.
