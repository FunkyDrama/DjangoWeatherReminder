# DjangoWeatherReminder

A Django-based web application that provides personalized weather notifications and reminders. Get daily weather updates, set custom weather alerts, and never be caught off guard by weather changes again.

## 🌟 Features

- **RESTful API**: 
  - Complete REST API for all operations
  - JWT authentication
  - API versioning support
  - Rate limiting
  
- **Weather Forecasts**: 
  - Current weather conditions
  - 7-day weather forecast
  - Hourly weather updates
  - Multiple location support
  
- **Smart Notifications**:
  - Daily weather summary emails
  - Severe weather alerts
  - Custom temperature threshold notifications
  - Rain/snow alerts
  
- **User Management**:
  - User registration and authentication via API
  - Profile management endpoints
  - Personalized location settings
  - Notification preferences
  
- **Reminder System**:
  - Set weather-based reminders
  - Schedule notifications for specific conditions
  - Email notifications
  
- **API Documentation**:
  - Interactive Swagger UI
  - OpenAPI 3.0 specification
  - Try-it-out functionality
  - Auto-generated API client code

## 🛠️ Technologies Used

- **Backend**: Django 5.0+ with Django REST Framework
- **API Documentation**: Swagger/OpenAPI (drf-yasg)
- **Database**: PostgreSQL / SQLite
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Weather API**: OpenWeatherMap API
- **Task Queue**: Celery with Redis
- **Email Service**: SMTP (Gmail/SendGrid)
- **API Testing**: Postman / Swagger UI
- **CORS**: django-cors-headers

## 📋 Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Redis server (for Celery)
- PostgreSQL (optional, SQLite for development)
- OpenWeatherMap API key

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/FunkyDrama/DjangoWeatherReminder.git
cd DjangoWeatherReminder
```

### 2. Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DATABASE_URL=postgresql://username:password@localhost/weatherreminder

# OpenWeatherMap API
OPENWEATHER_API_KEY=your-openweathermap-api-key
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Time Zone
TIME_ZONE=UTC
```

### 5. Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 6. Load Initial Data (Optional)

```bash
python manage.py loaddata fixtures/cities.json
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 8. Start Redis Server

```bash
# On macOS
brew services start redis

# On Ubuntu/Debian
sudo service redis-server start

# On Windows (using WSL or Docker)
docker run -d -p 6379:6379 redis
```

### 9. Start Celery Worker

In a separate terminal:

```bash
celery -A weatherreminder worker -l info
```

### 10. Start Celery Beat (for scheduled tasks)

In another terminal:

```bash
celery -A weatherreminder beat -l info
```

### 11. Run Development Server

```bash
python manage.py runserver
```

Visit the API documentation:
- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`
- **API Root**: `http://localhost:8000/api/`

## 📂 Project Structure

```
DjangoWeatherReminder/
│
├── weatherreminder/        # Main project directory
│   ├── __init__.py
│   ├── settings.py        # Django settings
│   ├── urls.py           # URL configuration
│   ├── wsgi.py          # WSGI configuration
│   ├── asgi.py          # ASGI configuration
│   └── celery.py        # Celery configuration
│
├── apps/
│   ├── accounts/         # User authentication & profiles
│   │   ├── models.py    # User models
│   │   ├── views.py     # API views
│   │   ├── serializers.py # DRF serializers
│   │   └── urls.py      # API endpoints
│   │
│   ├── weather/         # Weather functionality
│   │   ├── models.py    # Weather data models
│   │   ├── views.py     # API views
│   │   ├── serializers.py # DRF serializers
│   │   ├── api.py       # Weather API integration
│   │   └── utils.py     # Helper functions
│   │
│   ├── reminders/       # Reminder system
│   │   ├── models.py    # Reminder models
│   │   ├── views.py     # API views
│   │   ├── serializers.py # DRF serializers
│   │   └── tasks.py     # Celery tasks
│   │
│   └── notifications/   # Notification system
│       ├── models.py    # Notification models
│       ├── views.py     # API views
│       ├── serializers.py # DRF serializers
│       └── emails.py    # Email templates
│
├── static/              # Static files for Swagger UI
├── media/              # User uploads
├── fixtures/           # Initial data
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables example
└── README.md          # Project documentation
```

## 🔧 Configuration

### OpenWeatherMap API Setup

1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
2. Get your API key from the dashboard
3. Add the API key to your `.env` file

### Email Configuration

For Gmail:
1. Enable 2-factor authentication
2. Generate an app-specific password
3. Use the app password in your `.env` file

For production, consider using:
- SendGrid
- Mailgun
- Amazon SES

### Celery Schedule Configuration

Edit `weatherreminder/celery.py` to configure periodic tasks:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'send-daily-weather': {
        'task': 'reminders.tasks.send_daily_weather',
        'schedule': crontab(hour=7, minute=0),  # 7:00 AM daily
    },
    'check-weather-alerts': {
        'task': 'reminders.tasks.check_weather_alerts',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.weather
python manage.py test apps.reminders

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

## 📊 API Usage

### Authentication

The API uses JWT (JSON Web Tokens) for authentication:

```bash
# Register a new user
POST /api/auth/register/
{
  "username": "user@example.com",
  "password": "securepassword",
  "email": "user@example.com"
}

# Login to get tokens
POST /api/auth/login/
{
  "username": "user@example.com",
  "password": "securepassword"
}

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# Use the access token in headers
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### API Endpoints

#### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login user
- `POST /api/auth/logout/` - Logout user
- `POST /api/auth/refresh/` - Refresh JWT token
- `POST /api/auth/password/reset/` - Request password reset
- `POST /api/auth/password/reset/confirm/` - Confirm password reset

#### Weather
- `GET /api/weather/current/` - Get current weather for user's location
- `GET /api/weather/current/{city}/` - Get current weather for specific city
- `GET /api/weather/forecast/` - Get 7-day forecast
- `GET /api/weather/forecast/{city}/` - Get 7-day forecast for specific city
- `GET /api/weather/hourly/` - Get hourly forecast
- `GET /api/weather/history/` - Get weather history

#### Reminders
- `GET /api/reminders/` - List user's reminders
- `POST /api/reminders/` - Create new reminder
- `GET /api/reminders/{id}/` - Get reminder details
- `PUT /api/reminders/{id}/` - Update reminder
- `PATCH /api/reminders/{id}/` - Partially update reminder
- `DELETE /api/reminders/{id}/` - Delete reminder
- `POST /api/reminders/{id}/activate/` - Activate reminder
- `POST /api/reminders/{id}/deactivate/` - Deactivate reminder

#### User Profile
- `GET /api/users/profile/` - Get user profile
- `PUT /api/users/profile/` - Update user profile
- `POST /api/users/locations/` - Add location
- `DELETE /api/users/locations/{id}/` - Remove location
- `GET /api/users/preferences/` - Get notification preferences
- `PUT /api/users/preferences/` - Update notification preferences

#### Notifications
- `GET /api/notifications/` - List user notifications
- `GET /api/notifications/{id}/` - Get notification details
- `POST /api/notifications/{id}/mark-read/` - Mark as read
- `DELETE /api/notifications/{id}/` - Delete notification
- `POST /api/notifications/mark-all-read/` - Mark all as read

### Swagger Documentation

Access the interactive API documentation:

1. **Swagger UI**: `http://localhost:8000/swagger/`
   - Interactive API explorer
   - Try out endpoints directly
   - View request/response schemas
   - Download OpenAPI specification

2. **ReDoc**: `http://localhost:8000/redoc/`
   - Clean, responsive documentation
   - Better for reading and understanding

### Example API Calls

Using cURL:

```bash
# Get current weather (authenticated)
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     http://localhost:8000/api/weather/current/

# Create a reminder
curl -X POST \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Umbrella reminder",
       "condition": "rain",
       "threshold": 50,
       "notification_time": "08:00",
       "is_active": true
     }' \
     http://localhost:8000/api/reminders/
```

Using Python requests:

```python
import requests

# Login and get token
response = requests.post('http://localhost:8000/api/auth/login/', 
                         json={'username': 'user', 'password': 'pass'})
token = response.json()['access']

# Make authenticated request
headers = {'Authorization': f'Bearer {token}'}
weather = requests.get('http://localhost:8000/api/weather/current/', 
                       headers=headers)
print(weather.json())
```

### Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour
- Weather API endpoints: 60 requests/minute

### Pagination

List endpoints support pagination:

```bash
GET /api/reminders/?page=1&page_size=20
```

Response includes:
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/reminders/?page=2",
  "previous": null,
  "results": [...]
}
```

### Filtering and Ordering

```bash
# Filter reminders by status
GET /api/reminders/?is_active=true

# Order by creation date
GET /api/reminders/?ordering=-created_at

# Search
GET /api/reminders/?search=rain
``` in the dashboard

### API Endpoints (if applicable)

- `GET /api/weather/current/` - Get current weather
- `GET /api/weather/forecast/` - Get weather forecast
- `POST /api/reminders/` - Create a reminder
- `GET /api/notifications/` - Get user notifications

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Heroku Deployment

```bash
# Login to Heroku
heroku login

# Create app
heroku create djangoweatherreminder

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set OPENWEATHER_API_KEY=your-api-key

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis
heroku addons:create heroku-redis:hobby-dev

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation as needed
- Keep commits atomic and descriptive

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenWeatherMap](https://openweathermap.org/) for weather data API
- Django community for the excellent framework
- Bootstrap for responsive UI components
- Chart.js for weather data visualization

## 📧 Contact

Project Creator: [FunkyDrama](https://github.com/FunkyDrama)

Project Link: [https://github.com/FunkyDrama/DjangoWeatherReminder](https://github.com/FunkyDrama/DjangoWeatherReminder)

## 🐛 Bug Reports & Feature Requests

Please use the [GitHub Issues](https://github.com/FunkyDrama/DjangoWeatherReminder/issues) page to report bugs or request features.

**Stay prepared for any weather!** 🌤️🌧️❄️
