# KAAF University Smart Chatbot System

A production-ready AI-powered university assistant built with Django, WebSockets, NLP, and Tailwind CSS.

## Features

- Role-based auth (Student / Staff / Admin)
- AI chatbot with NLP intent recognition
- Real-time WebSocket chat
- GPA tracking & trend charts
- Timetable management
- Smart planner with Pomodoro timer
- Document upload & AI summarization
- Notifications & events system
- Gamification (points, streaks, leaderboard)
- Dark mode support
- REST API with JWT

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Node.js (optional, for Tailwind CLI)

## Setup Instructions

### 1. Install Python
Download from https://python.org and install. Make sure to check "Add to PATH".

### 2. Clone / Navigate to project
```bash
cd kaaf_chatbot
```

### 3. Create virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Install spaCy model (optional but recommended)
```bash
python -m spacy download en_core_web_sm
```

### 6. Setup PostgreSQL
Create a database:
```sql
CREATE DATABASE kaaf_db;
CREATE USER kaaf_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE kaaf_db TO kaaf_user;
```

### 7. Configure environment
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 8. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 9. Seed sample data
```bash
python manage.py seed_data
```

### 10. Start Redis (required for WebSockets & Celery)
```bash
# Windows (using WSL or Docker):
docker run -d -p 6379:6379 redis:alpine
# Or install Redis for Windows from https://github.com/microsoftarchive/redis
```

### 11. Start Celery worker (optional, for background tasks)
```bash
# In a separate terminal:
celery -A kaaf worker -l info
celery -A kaaf beat -l info
```

### 12. Run the development server
```bash
python manage.py runserver
```

Visit: http://localhost:8000

## Demo Credentials

| Role    | ID              | Password    |
|---------|-----------------|-------------|
| Student | STU/2021/001    | password123 |
| Staff   | STF/2020/001    | password123 |
| Admin   | ADM/001         | admin123    |

## Project Structure

```
kaaf_chatbot/
├── kaaf/                   # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py             # WebSocket support
│   └── celery.py           # Background tasks
├── apps/
│   ├── accounts/           # Auth, users, gamification
│   ├── students/           # GPA, results, timetable, documents
│   ├── staff/              # Staff profiles, workplans
│   ├── chatbot/            # NLP engine, WebSocket consumer
│   ├── notifications/      # Alerts, events, announcements
│   ├── planner/            # Tasks, study timer
│   └── analytics/          # Dashboard, reports
├── templates/              # HTML templates (Tailwind CSS)
├── static/                 # CSS, JS assets
├── media/                  # User uploads
└── manage.py
```

## API Endpoints

| Method | Endpoint                    | Description          |
|--------|-----------------------------|----------------------|
| POST   | /api/accounts/token/        | Get JWT token        |
| POST   | /api/accounts/token/refresh/| Refresh JWT          |
| GET    | /api/students/results/      | Student results      |
| GET    | /api/students/timetable/    | Timetable            |
| GET    | /api/students/gpa/          | GPA history          |
| POST   | /api/chatbot/send/          | Send chat message    |
| GET    | /api/notifications/         | Notifications        |
| GET    | /api/planner/tasks/         | Tasks list           |

## WebSocket

Connect to: `ws://localhost:8000/ws/chat/`

Send: `{"message": "What is my GPA?", "session_id": 1}`

## Chatbot Commands

- "What is my GPA?" — Current GPA
- "Show my results" — Semester results
- "Show my timetable" — Today's schedule
- "Motivate me" — Inspirational quote
- "I'm stressed" — Meditation tips
- "Study tips" — Study techniques
- "My tasks" — Planner tasks
- "Upcoming events" — School events
- "help" — Full command list

## Adding OpenAI Integration

Set `OPENAI_API_KEY` in `.env` and the chatbot will use GPT as a fallback for unrecognized queries.

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Set a strong `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Run `python manage.py collectstatic`
5. Use Gunicorn: `gunicorn kaaf.wsgi:application`
6. Use Daphne for ASGI: `daphne kaaf.asgi:application`
7. Configure Nginx as reverse proxy