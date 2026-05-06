# TaskFlow - Team Task Manager

TaskFlow is a full-stack Django project for team-based project and task management.
It includes role-based access (Admin/Member), Kanban task board, dashboard analytics,
user profiles, and REST APIs built with Django REST Framework.

## Tech Stack

- Django
- Django REST Framework
- Bootstrap 5
- PostgreSQL (Railway) / SQLite (local)
- WhiteNoise + Gunicorn (production)

## Core Features

- Authentication: register, login, logout, profile, password reset
- Role-based permissions:
  - Admin: manage projects, members, tasks, and edits/deletes
  - Member: view assigned/member projects, update task status, comment
- Project management:
  - Project CRUD
  - Member add/remove
  - Progress tracking
- Task management:
  - Task CRUD
  - Priority, due date, assignee, status
  - Comments
  - Overdue highlighting
- Dashboard:
  - Total/completed/pending/overdue tasks
  - Project progress
  - Recent tasks and activity
  - Chart.js 7-day activity chart
- Kanban board:
  - To Do / In Progress / Completed
  - Drag-and-drop status updates
- REST API:
  - Projects, tasks, comments
  - Dashboard stats endpoint
  - JWT auth endpoints

## Project Structure

```text
webapp/
├── accounts/          # Custom user, auth forms/views/serializers
├── tasks/             # Domain models, HTML views, forms, permissions, services
├── api/               # DRF viewsets/serializers/permissions over tasks domain
├── core/              # Settings, root URLs, WSGI/ASGI
├── templates/         # Bootstrap templates
├── static/            # Static assets
├── media/             # Uploaded files (avatars)
├── manage.py
├── requirements.txt
├── Procfile
└── .env.example
```

## Local Setup

1. Open terminal in `webapp/`.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create environment file:

```bash
cp .env.example .env
```

4. Run migrations:

```bash
python manage.py migrate
```

5. Seed demo data:

```bash
python manage.py seed_demo --reset
```

6. Run server:

```bash
python manage.py runserver
```

## Demo Credentials

- Admin: `admin` / `Admin12345`
- Member: `john` / `Member12345` (also `sarah`, `mike`, `emily` with same password)

## API Endpoints

Base URL: `/api/`

- `GET/POST /api/projects/`
- `GET/PUT/PATCH/DELETE /api/projects/<id>/`
- `GET/POST /api/tasks/`
- `GET/PUT/PATCH/DELETE /api/tasks/<id>/`
- `GET/POST /api/comments/`
- `GET/PUT/PATCH/DELETE /api/comments/<id>/`
- `GET /api/dashboard/stats/`

Auth endpoints:

- `POST /accounts/api/register/`
- `POST /accounts/api/token/`
- `POST /accounts/api/token/refresh/`
- `GET /accounts/api/me/`

## Running Tests

```bash
python manage.py test
```

## Railway Deployment

1. Set Railway environment variables:
   - `SECRET_KEY`
   - `DEBUG=False`
   - `ALLOWED_HOSTS`
   - `CSRF_TRUSTED_ORIGINS`
   - `DATABASE_URL` (from Railway Postgres plugin)
2. Deploy with included `Procfile`:
   - `release: python manage.py migrate --noinput`
   - `web: gunicorn core.wsgi --log-file - --bind 0.0.0.0:$PORT`
3. Run `collectstatic` (already configured via WhiteNoise settings).

## Notes

- Keep `.env`, `db.sqlite3`, `media/`, and `staticfiles/` out of git.
- In production, always use a strong `SECRET_KEY` and `DEBUG=False`.
