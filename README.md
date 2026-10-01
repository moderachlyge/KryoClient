# KryoClient.org — production-ready deployment package

Проект подготовлен для размещения на `https://kryoclient.org`.

## Что внутри

- Flask-приложение с реальной регистрацией/авторизацией.
- SQLite для текущей версии.
- Gunicorn как production WSGI-сервер.
- Nginx reverse proxy.
- systemd unit для автозапуска и перезапуска.
- HTTPS через Let's Encrypt / Certbot.
- `.env` для секретного `SECRET_KEY`.
- `/healthz` для проверки состояния сервера.
- Безопасные cookie-сессии и `ProxyFix` для работы за Nginx.

## Развёртывание на Ubuntu VPS

1. Купи/подключи домен `kryoclient.org` и VPS с публичным IPv4.
2. В DNS создай:
   - `A` → `kryoclient.org` → IP VPS
   - `A` → `www.kryoclient.org` → IP VPS (необязательно, но конфиг поддерживает)
3. Скопируй проект на сервер в `/var/www/kryoclient`.
4. Запусти:

```bash
cd /var/www/kryoclient
auto=false
sudo ./deploy/setup_ubuntu.sh
```

Строка `auto=false` не нужна для запуска; её можно просто не вводить. Правильная последовательность:

```bash
cd /var/www/kryoclient
sudo ./deploy/setup_ubuntu.sh
```

5. После того как DNS начал указывать на VPS, выпусти сертификат:

```bash
sudo certbot --nginx -d kryoclient.org -d www.kryoclient.org
```

6. Открой `https://kryoclient.org`.

## Ручная установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

В `.env` обязательно задай длинный случайный `SECRET_KEY`.

Запуск приложения:

```bash
gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
```

## Важно

- Сам файл проекта не может зарегистрировать домен и не может изменить DNS без доступа к регистратору.
- HTTPS появляется после настройки сертификата на сервере.
- SQLite подходит для небольшой нагрузки. При росте проекта лучше перейти на PostgreSQL.
- Для публичной регистрации рекомендуется добавить подтверждение email, rate limiting, CSRF-защиту для state-changing форм и восстановление пароля.
- Не коммить `.env` в Git.
