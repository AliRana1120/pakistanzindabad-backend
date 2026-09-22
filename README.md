# 🇵🇰 Pakistan Zindabad — Backend

> **Production-oriented REST API backend for Pakistan Zindabad digital news platform.**

The **Pakistan Zindabad Backend** is a Django-based REST API powering the Pakistan Zindabad digital news platform. It provides APIs for news article management, authentication, e-paper publishing, comments, RSS aggregation, search, filtering, and automated background processing.

The backend is designed to support a modern news platform with a React/Vite frontend and can be deployed using Docker and Gunicorn.

---

## 🚀 Features

### 📰 News & Article Management

* Create, update, delete and retrieve articles
* Public users can access published articles
* Admin users can manage article content
* SEO-friendly article slugs
* Featured article support
* Article categories and tags
* Article search
* Related articles
* Latest-news ticker
* Pagination
* Ordering and filtering

### 🔐 Authentication & Authorization

* Custom Django user model
* User registration
* JWT-based authentication
* Access and refresh tokens
* Token rotation
* Authenticated user profile endpoint
* Role-based administrative permissions
* Admin-only content management

The project uses Django REST Framework Simple JWT with 6-hour access tokens and 30-day refresh tokens.

### 📰 RSS News Aggregation

The backend can import and process news from RSS feeds.

Supported sources configured in the application include:

* BBC Urdu
* Dawn
* The News International
* Business Recorder
* Express Tribune
* Associated Press of Pakistan (APP)
* Reuters
* Al Jazeera

RSS feeds can be processed asynchronously through Celery and Redis, with synchronous fallback processing when the task queue is unavailable.

### ⚡ Background Processing

* Celery task queue
* Redis broker/cache
* Celery Beat scheduled tasks
* Automated RSS refresh
* Category-based feed processing
* Redis caching for RSS responses

RSS categories are scheduled for automatic refresh every 5 minutes.

### 📄 E-Paper Management

The API supports:

* E-paper creation
* E-paper updates
* E-paper publishing
* E-paper retrieval
* Media/file handling
* Admin-controlled publication

### 💬 Comments

* Users can submit comments
* Comments require approval before publication
* Admins can approve or delete comments
* Public users can retrieve approved comments

### 🔎 Search & Filtering

The API supports:

* Keyword search
* Category filtering
* Featured article filtering
* Published/unpublished filtering
* Tag filtering
* Ordering by creation/update date
* Related article retrieval

### 🐳 Deployment Ready

The project includes:

* Dockerfile
* Gunicorn
* WhiteNoise
* Static file collection
* Environment-variable configuration
* PostgreSQL support
* SQLite fallback for local development

The included Docker configuration runs the Django application with Gunicorn on port `8000`.

---

# 🛠️ Tech Stack

| Technology                | Purpose                      |
| ------------------------- | ---------------------------- |
| **Python**                | Backend programming language |
| **Django 5.1**            | Web framework                |
| **Django REST Framework** | REST API development         |
| **Simple JWT**            | JWT authentication           |
| **PostgreSQL**            | Production database          |
| **SQLite**                | Local development database   |
| **Redis**                 | Caching & Celery broker      |
| **Celery**                | Background task processing   |
| **Celery Beat**           | Scheduled tasks              |
| **django-filter**         | API filtering                |
| **WhiteNoise**            | Static file serving          |
| **Gunicorn**              | Production WSGI server       |
| **Docker**                | Containerization             |
| **BeautifulSoup**         | Web/feed processing          |
| **feedparser**            | Feed processing              |
| **Python Decouple**       | Environment configuration    |

The current dependency set includes Django, DRF, Simple JWT, PostgreSQL support, Redis, Celery, django-filter, Gunicorn, feedparser and related packages.

---

# 📁 Project Structure

```text
pakistanzindabad-backend/
│
├── accounts/
│   ├── migrations/
│   ├── admin.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
│
├── articles/
│   ├── migrations/
│   ├── admin.py
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── tasks.py
│   ├── urls.py
│   └── views.py
│
├── pzn_news/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   ├── wsgi.py
│   └── ...
│
├── media/
├── Dockerfile
├── build.sh
├── manage.py
├── requirements.txt
├── .dockerignore
└── .gitignore
```

The repository currently contains the `accounts`, `articles`, and `pzn_news` Django components together with Docker/build and dependency configuration.

---

# 🔌 API Structure

The main API is organized under:

```text
/api/v1/
```

## Authentication

```text
/api/v1/auth/
```

Typical authentication functionality includes:

```text
Register
Login
Profile / Me
Token authentication
User management
```

## Articles

```text
/api/v1/articles/
```

The article API supports standard CRUD operations as well as additional actions such as:

```text
search
related
comments
ticker
import
```

The article endpoint uses slug-based lookup and supports category, featured, published, tag, search and ordering functionality.

## E-Papers

```text
/api/v1/epapers/
```

## RSS

```text
/api/v1/rss/
```

## RSS Ticker

```text
/api/v1/rss/ticker/
```

## Admin Comments

```text
/api/v1/admin/comments/
```

The URL configuration registers article, e-paper and admin-comment ViewSets and exposes RSS endpoints under `/api/v1/`.

---

# ⚙️ Environment Variables

Create a `.env` file in the project root.

```env
SECRET_KEY=your-secret-key
DEBUG=False

DATABASE_URL=postgresql://username:password@host:5432/database

REDIS_URL=redis://localhost:6379/0
```

### Local Development

If `DATABASE_URL` is not provided, the project falls back to SQLite:

```text
db.sqlite3
```

For production, PostgreSQL can be configured through `DATABASE_URL`.

---

# 💻 Local Installation

## 1. Clone the repository

```bash
git clone https://github.com/AliRana1120/pakistanzindabad-backend.git

cd pakistanzindabad-backend
```

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Create:

```text
.env
```

Example:

```env
SECRET_KEY=change-this-secret-key
DEBUG=True

# Optional for local development
DATABASE_URL=

REDIS_URL=redis://localhost:6379/0
```

## 5. Apply migrations

```bash
python manage.py migrate
```

## 6. Create an admin user

```bash
python manage.py createsuperuser
```

## 7. Collect static files

```bash
python manage.py collectstatic --noinput
```

## 8. Run the development server

```bash
python manage.py runserver
```

The API will then be available at:

```text
http://127.0.0.1:8000/
```

---

# 🔄 Running Celery

Redis is used as the Celery broker and result backend.

Start Redis:

```bash
redis-server
```

Then start the Celery worker:

```bash
celery -A pzn_news worker --loglevel=info
```

Start Celery Beat for scheduled RSS updates:

```bash
celery -A pzn_news beat --loglevel=info
```

The backend is configured to refresh RSS feeds for categories including:

```text
all
pakistan
politics
sports
business
technology
international
```

every 5 minutes.

---

# 🐳 Docker Deployment

Build the Docker image:

```bash
docker build -t pakistan-zindabad-backend .
```

Run the container:

```bash
docker run -p 8000:8000 pakistan-zindabad-backend
```

The included Dockerfile:

* Uses Python 3.13
* Installs PostgreSQL development dependencies
* Installs Python requirements
* Collects static files
* Runs Gunicorn
* Exposes port `8000`

---

# 🌐 Frontend Integration

The backend is designed to work with a separate frontend application.

The production frontend origin currently configured for CORS is:

```text
https://dailypakistanzindabad.vercel.app
```

Local development origins include:

```text
http://localhost:3000
http://127.0.0.1:3000
http://localhost:5173
http://127.0.0.1:5173
```

CORS and CSRF configuration are explicitly handled in Django settings.

---

# 🔐 Security

The project includes several security mechanisms:

* JWT authentication
* Authenticated API permissions
* Admin-only content modification
* Django password validation
* CORS configuration
* CSRF trusted origins
* Environment-based secret configuration
* PostgreSQL SSL configuration
* Restricted comment approval workflow

### Production Recommendations

Before production deployment:

1. Set a strong `SECRET_KEY`.
2. Set `DEBUG=False`.
3. Restrict `ALLOWED_HOSTS` instead of using `*`.
4. Restrict CORS origins to trusted frontend domains.
5. Use a managed PostgreSQL database.
6. Use a managed Redis instance.
7. Store secrets only in environment variables.
8. Configure HTTPS.
9. Configure persistent media storage.
10. Run database migrations during deployment.

---

# 📡 Example API Requests

### Health Check

```http
GET /api/test/
```

Response:

```json
{
  "ok": true,
  "service": "backend"
}
```

### Get Articles

```http
GET /api/v1/articles/
```

### Search Articles

```http
GET /api/v1/articles/search/?q=technology
```

### Get Latest Ticker

```http
GET /api/v1/articles/ticker/
```

### Get RSS Feed

```http
GET /api/v1/rss/
```

### Get RSS Ticker

```http
GET /api/v1/rss/ticker/
```

### Filter by Category

```http
GET /api/v1/articles/?category=technology
```

The actual route structure and test endpoints are defined in the Django URL configuration.

---

# 🧩 Architecture

```text
                    ┌─────────────────────────┐
                    │      React Frontend     │
                    │        Vercel           │
                    └────────────┬────────────┘
                                 │
                                 │ REST API
                                 ▼
                    ┌─────────────────────────┐
                    │    Django REST API      │
                    │                         │
                    │  Authentication         │
                    │  Articles               │
                    │  E-Papers               │
                    │  Comments               │
                    │  Search / Filtering     │
                    └───────┬─────────┬───────┘
                            │         │
                 ┌──────────┘         └──────────┐
                 ▼                               ▼
        ┌─────────────────┐             ┌─────────────────┐
        │   PostgreSQL    │             │      Redis      │
        │   Database      │             │ Cache / Broker  │
        └─────────────────┘             └────────┬────────┘
                                                 │
                                                 ▼
                                      ┌─────────────────────┐
                                      │ Celery + Celery Beat │
                                      │                     │
                                      │ RSS Processing      │
                                      │ Scheduled Tasks     │
                                      └──────────┬──────────┘
                                                 │
                                                 ▼
                                      ┌─────────────────────┐
                                      │     RSS Sources     │
                                      │ BBC / Dawn / APP /  │
                                      │ Reuters / etc.      │
                                      └─────────────────────┘
```

---

# 🎯 Project Purpose

Pakistan Zindabad is designed as a digital news platform that combines:

* News publishing
* Digital journalism infrastructure
* Automated RSS aggregation
* E-paper distribution
* User interaction
* Search and discovery
* Background task processing
* RESTful API architecture

The backend separates authentication, article management and project configuration into dedicated Django applications, making the codebase easier to extend as the platform grows.

---

# 🚧 Future Improvements

Potential improvements include:

* [ ] API documentation with Swagger / OpenAPI
* [ ] Automated API testing
* [ ] CI/CD pipeline with GitHub Actions
* [ ] Rate limiting
* [ ] Advanced role-based permissions
* [ ] Cloud object storage for media
* [ ] Database query optimization
* [ ] Structured logging
* [ ] Error monitoring
* [ ] Redis-based caching for frequently accessed endpoints
* [ ] Full Docker Compose development environment
* [ ] Automated deployment pipeline
* [ ] News recommendation system
* [ ] Advanced RSS deduplication
* [ ] Automated article categorization
* [ ] AI-assisted news summarization

---

# 📌 Repository

**GitHub:**
https://github.com/AliRana1120/pakistanzindabad-backend

---

# 👨‍💻 Author

**Ali Rana**

Software Engineering Student & Backend Developer

Focused on:

* Python
* Django
* Django REST Framework
* PostgreSQL
* REST APIs
* Backend Architecture
* Automation
* AI-integrated applications

---

## ⭐ Contributing

Contributions, issues and suggestions are welcome.

If you find a bug or have an improvement idea, open an issue or submit a pull request.

---

