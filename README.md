# Weather Reminder

A full-stack weather notification service with a Django REST API backend and React frontend. Subscribe to weather updates for any city and receive notifications via email or webhook.

**Live:** [weather.danielkravchenko.dev](https://weather.danielkravchenko.dev)

## Features

- **React SPA** with Tailwind CSS, responsive design (mobile + desktop)
- **Weather search** with city autocomplete via OpenWeatherMap Geocoding API
- **Subscriptions** — choose city, notification interval, and delivery method (email/webhook)
- **Notification logs** — track every sent notification with status and response
- **JWT authentication** — register, login, token refresh
- **Webhook support** — receive weather updates at your own URL
- **Swagger UI** — interactive API documentation at `/api/v1/docs/`
- **Background tasks** — Celery + RabbitMQ for scheduled weather notifications

## Tech Stack

| Layer      | Technology                                           |
|------------|------------------------------------------------------|
| Frontend   | React 19, Vite, Tailwind CSS v4, React Router, Axios |
| Backend    | Django 5, Django REST Framework, drf-spectacular     |
| Auth       | JWT (djangorestframework-simplejwt)                  |
| Database   | PostgreSQL 16                                        |
| Task Queue | Celery + RabbitMQ                                    |
| Proxy      | Nginx (serves React SPA + proxies API)               |
| Deploy     | Docker Compose, GitHub Actions, Cloudflare Tunnel    |

## Project Structure

```
djangoweatherreminder/
├── backend/
│   ├── Dockerfile
│   ├── manage.py
│   ├── pyproject.toml
│   ├── poetry.lock
│   ├── djangoweatherreminder/   # settings, urls, wsgi, celery
│   ├── users/                   # auth, registration, profile
│   ├── weather/                 # weather API, city autocomplete
│   ├── subscriptions/           # subscription CRUD, city model
│   ├── notifications/           # notification logs, send tasks
│   └── templates/               # email templates
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── api/client.js        # axios + JWT interceptors
│       ├── context/AuthContext.jsx
│       ├── components/          # Layout, WeatherCard, SubscriptionForm, etc.
│       └── pages/               # Login, Register, Dashboard, Logs, Profile
├── docker-compose.yml
├── nginx.conf
├── .env
└── .github/workflows/deploy.yml
```

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/FunkyDrama/DjangoWeatherReminder.git
cd DjangoWeatherReminder
cp .env.example .env   # edit with your values
docker compose up --build
```

App available at `http://localhost:3005`:
- `/` — React SPA
- `/api/v1/docs/` — Swagger UI
- `/admin/` — Django admin

### Local Development

**Backend:**
```bash
cd backend
poetry install
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Vite dev server proxies `/api` requests to `localhost:8000`.

## Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-secret-key

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=weather_reminder
POSTGRES_HOST=db
POSTGRES_PORT=5432

# OpenWeatherMap
OPEN_WEATHER_API_KEY=your-openweathermap-api-key

# Email (Gmail SMTP)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Celery / RabbitMQ
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
```

## API Endpoints

All endpoints are prefixed with `/api/v1/`.

### Authentication
| Method | Endpoint               | Description                          |
|--------|------------------------|--------------------------------------|
| POST   | `/auth/register/`      | Register (username, email, password) |
| POST   | `/auth/login/`         | Login, returns JWT tokens            |
| POST   | `/auth/token/refresh/` | Refresh access token                 |
| GET    | `/auth/me/`            | Get current user                     |
| PATCH  | `/auth/me/`            | Update profile (webhook_url)         |

### Weather
| Method | Endpoint                       | Description                     |
|--------|--------------------------------|---------------------------------|
| GET    | `/weather/?city=London`        | Current weather by city name    |
| GET    | `/weather/?lat=51.5&lon=-0.12` | Current weather by coordinates  |
| GET    | `/weather/cities/?q=Lon`       | City autocomplete (min 2 chars) |

### Subscriptions
| Method | Endpoint               | Description               |
|--------|------------------------|---------------------------|
| GET    | `/subscriptions/`      | List user's subscriptions |
| POST   | `/subscriptions/`      | Create subscription       |
| PUT    | `/subscriptions/{id}/` | Update subscription       |
| DELETE | `/subscriptions/{id}/` | Delete subscription       |

### Notifications
| Method | Endpoint               | Description            |
|--------|------------------------|------------------------|
| GET    | `/notifications/logs/` | List notification logs |

## License

MIT License — see [LICENSE.txt](LICENSE.txt) for details.
