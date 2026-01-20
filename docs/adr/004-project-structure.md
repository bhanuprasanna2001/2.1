# ADR-004: Project Structure

## Status
Accepted

## Context
We need to decide how to organize the codebase. A well-structured project improves maintainability, testability, and onboarding. The structure should support the layered architecture (API → Service → Repository → Model) while remaining navigable.

## Decision Drivers
- **Separation of concerns**: Each layer has clear responsibility
- **Testability**: Easy to mock dependencies
- **Navigability**: New developers can find things quickly
- **Scalability**: Structure should work as codebase grows
- **Convention**: Follow patterns recognizable to Python developers

## Considered Options

### 1. Layer-based Structure
```
app/
├── models/      # All database models
├── schemas/     # All Pydantic schemas
├── routes/      # All endpoints
├── services/    # All business logic
└── repositories/# All data access
```
- Easy to see all models, all routes at once
- Good for smaller projects
- Can become cluttered as features grow

### 2. Feature-based Structure (Domain-Driven)
```
app/
├── bookmarks/
│   ├── models.py
│   ├── schemas.py
│   ├── router.py
│   └── service.py
├── users/
│   └── ...
└── core/
```
- Groups related code together
- Better for larger projects
- Harder to see all models at once

### 3. Hybrid Structure
```
app/
├── api/v1/          # Routes by version
├── models/          # All models (shared)
├── schemas/         # All schemas (shared)
├── services/        # Business logic
├── repositories/    # Data access
└── core/            # Cross-cutting
```
- Models/schemas visible together
- Routes organized by version
- Clear layer separation

## Decision
**Hybrid structure** with layer-based organization and API versioning.

### Rationale
1. **Learning clarity**: Seeing all models together helps understand the domain
2. **API versioning built-in**: `/api/v1/` allows future versions
3. **Clear boundaries**: Each folder has one responsibility
4. **Repository pattern**: Abstracts data access for testability
5. **Phase 1 consistency**: Similar to patterns in Task Manager/API Client projects

### Final Structure
```
app/
├── __init__.py
├── __main__.py          # Entry point for `python -m app`
├── main.py              # FastAPI app configuration
├── config.py            # Settings via pydantic-settings
├── database.py          # Async engine and session
│
├── api/                 # HTTP layer
│   ├── __init__.py
│   ├── deps.py          # Dependency injection (get_db, get_current_user)
│   └── v1/
│       ├── __init__.py
│       ├── router.py    # Aggregates all v1 routes
│       ├── bookmarks.py
│       ├── collections.py
│       ├── tags.py
│       └── health.py
│
├── core/                # Cross-cutting concerns
│   ├── __init__.py
│   ├── exceptions.py    # Custom exception classes
│   └── middleware.py    # Request logging, error handling
│
├── models/              # SQLAlchemy models
│   ├── __init__.py      # Exports all models
│   ├── base.py          # Base class, mixins
│   ├── user.py
│   ├── bookmark.py
│   ├── collection.py
│   └── tag.py
│
├── schemas/             # Pydantic schemas
│   ├── __init__.py
│   ├── base.py          # Shared schemas (pagination, errors)
│   ├── bookmark.py
│   ├── collection.py
│   └── tag.py
│
├── repositories/        # Data access layer
│   ├── __init__.py
│   ├── base.py          # Generic CRUD repository
│   ├── bookmark.py
│   ├── collection.py
│   └── tag.py
│
└── services/            # Business logic
    ├── __init__.py
    ├── bookmark.py
    ├── collection.py
    └── tag.py
```

## Layer Responsibilities

| Layer | Responsibility | Depends On |
|-------|---------------|------------|
| **API** | HTTP handling, request/response, auth guards | Services, Schemas |
| **Service** | Business logic, orchestration, validation | Repositories, Models |
| **Repository** | Database queries, CRUD operations | Models, Database |
| **Model** | Database schema, relationships | SQLAlchemy |
| **Schema** | Request/response validation | Pydantic |
| **Core** | Exceptions, middleware, security | - |

## Consequences

### Positive
- Clear mental model of data flow
- Easy to test each layer in isolation
- Consistent with industry patterns
- Room to grow without major refactoring

### Negative
- More files than a minimal structure
- Some boilerplate in repository pattern
- Need to maintain imports in `__init__.py`

### Risks
- Over-engineering for small features (mitigated: keep services thin initially)

## References
- [FastAPI Project Structure](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
