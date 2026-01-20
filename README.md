# Bookmark Manager REST API

A REST API for managing bookmarks with collections and tags, built with FastAPI, SQLAlchemy 2.0, and PostgreSQL.

## Features

- **Bookmark Management**: Create, read, update, delete bookmarks with automatic metadata fetching
- **Collections**: Organize bookmarks into hierarchical collections (folders)
- **Tags**: Flexible tagging system for cross-cutting organization
- **PostgreSQL**: Database with proper migrations
- **Docker**: Containerized development and deployment
- **Type Safety**: Full type hints with Pydantic v2 validation

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.115+ |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Validation | Pydantic 2.10+ |
| Containerization | Docker + Docker Compose |
| Testing | pytest + httpx |
| Linting | Ruff |
| Type Checking | mypy |

## Quick Start

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Make (optional, for convenience commands)

### Setup

1. **Clone and navigate to project**
   ```bash
   cd "Phase - 2/2.1 - REST API"
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

3. **Start PostgreSQL**
   ```bash
   make db-up
   # or: docker compose up -d db
   ```

4. **Install dependencies**
   ```bash
   make dev-install
   # or: pip install -e ".[dev]"
   ```

5. **Run migrations**
   ```bash
   make migrate
   # or: alembic upgrade head
   ```

6. **Start the server**
   ```bash
   make dev
   # or: uvicorn app.main:app --reload
   ```

7. **Open API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Project Structure

```
├── app/
│   ├── api/                 # API routes/endpoints
│   │   ├── deps.py          # Dependency injection
│   │   └── v1/              # API version 1
│   │       ├── router.py    # Route aggregator
│   │       ├── bookmarks.py
│   │       ├── collections.py
│   │       ├── tags.py
│   │       └── health.py
│   ├── core/                # Cross-cutting concerns
│   │   ├── exceptions.py    # Custom exceptions
│   │   └── middleware.py    # Request middleware
│   ├── models/              # SQLAlchemy models
│   │   ├── base.py          # Base model class
│   │   ├── bookmark.py
│   │   ├── collection.py
│   │   └── tag.py
│   ├── repositories/        # Data access layer
│   │   ├── base.py          # Generic repository
│   │   ├── bookmark.py
│   │   ├── collection.py
│   │   └── tag.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── base.py          # Shared schemas
│   │   ├── bookmark.py
│   │   ├── collection.py
│   │   └── tag.py
│   ├── services/            # Business logic
│   │   ├── bookmark.py
│   │   ├── collection.py
│   │   └── tag.py
│   ├── config.py            # Application settings
│   ├── database.py          # Database connection
│   └── main.py              # FastAPI application
├── migrations/              # Alembic migrations
├── tests/                   # Test suite
├── docs/                    # Documentation
│   └── adr/                 # Architecture Decision Records
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## API Endpoints

### Bookmarks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/bookmarks` | List bookmarks (paginated) |
| POST | `/api/v1/bookmarks` | Create bookmark |
| GET | `/api/v1/bookmarks/{id}` | Get bookmark |
| PATCH | `/api/v1/bookmarks/{id}` | Update bookmark |
| DELETE | `/api/v1/bookmarks/{id}` | Delete bookmark |

### Collections
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/collections` | List collections |
| POST | `/api/v1/collections` | Create collection |
| GET | `/api/v1/collections/{id}` | Get collection |
| PATCH | `/api/v1/collections/{id}` | Update collection |
| DELETE | `/api/v1/collections/{id}` | Delete collection |

### Tags
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tags` | List tags |
| POST | `/api/v1/tags` | Create tag |
| PATCH | `/api/v1/tags/{id}` | Update tag |
| DELETE | `/api/v1/tags/{id}` | Delete tag |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

## Development

### Commands

```bash
# Start database
make db-up

# Run development server
make dev

# Run tests
make test

# Run linter
make lint

# Format code
make format

# Type check
make typecheck

# Create migration
make migrate-create MSG="add_new_field"

# Apply migrations
make migrate
```

### Architecture

This project follows a layered architecture:

1. **API Layer** (`app/api/`): HTTP handling, request/response
2. **Service Layer** (`app/services/`): Business logic
3. **Repository Layer** (`app/repositories/`): Data access
4. **Model Layer** (`app/models/`): Database entities

See [Architecture Decision Records](docs/adr/) for detailed design decisions.

## License

MIT
