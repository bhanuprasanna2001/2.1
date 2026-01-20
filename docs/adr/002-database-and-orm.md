# ADR-002: Database and ORM Selection

## Status
Accepted

## Context
We need a database system and ORM for persisting bookmark data. The solution should support relational data (users, bookmarks, collections, tags with relationships), provide good developer experience, and be production-ready.

## Decision Drivers
- **Production readiness**: Must handle real-world workloads reliably
- **Async support**: Should work well with FastAPI's async nature
- **Migration tooling**: Database schema changes must be manageable
- **Learning transferability**: Skills should apply to industry jobs
- **Local development**: Easy to set up for development
- **Relationship modeling**: Complex many-to-many relationships required

## Considered Options

### 1. PostgreSQL + SQLAlchemy 2.0 + Alembic
- Industry-standard RDBMS
- SQLAlchemy is the de facto Python ORM
- Alembic provides explicit migration control
- Full async support in SQLAlchemy 2.0
- Requires Docker for local dev

### 2. SQLite + SQLAlchemy
- Zero setup, file-based
- Same ORM, different backend
- Limited concurrent write support
- No async driver
- Dev/prod parity issues

### 3. PostgreSQL + SQLModel
- Built on SQLAlchemy + Pydantic
- Less boilerplate
- Newer, smaller community
- Some edge cases not well documented

### 4. MongoDB + Motor
- Document-based, schema-flexible
- Good async support
- Not ideal for relational data
- Different paradigm from SQL

## Decision
**PostgreSQL 16 + SQLAlchemy 2.0 + Alembic** with async driver (asyncpg).

### Rationale
1. **Industry standard**: PostgreSQL + SQLAlchemy is used in majority of Python production systems
2. **Dev/prod parity**: Using PostgreSQL locally via Docker eliminates "works on my machine" issues
3. **Async native**: SQLAlchemy 2.0 + asyncpg provides true async database operations
4. **Explicit migrations**: Alembic allows reviewing migration SQL before running
5. **Rich features**: PostgreSQL provides JSON columns, full-text search, proper constraints
6. **Already learned SQLite**: Phase 1 covered SQLite; PostgreSQL expands skill set

## Consequences

### Positive
- Production-grade database from day one
- Transferable skills to any Python backend job
- Full async support aligns with FastAPI
- Proper foreign keys, constraints, indexes
- Migration files serve as schema documentation

### Negative
- Requires Docker for local development
- More setup complexity than SQLite
- SQLAlchemy has learning curve (repository pattern helps)

### Risks
- Docker not available on some systems (mitigated: documented in prerequisites)
- Async debugging complexity (mitigated: structured logging with request IDs)

## Database Schema Overview

```
┌──────────────┐       ┌────────────────────┐       ┌──────────────┐
│    users     │       │     bookmarks      │       │     tags     │
├──────────────┤       ├────────────────────┤       ├──────────────┤
│ id           │──────<│ user_id            │>──────│ id           │
│ email        │       │ id                 │       │ user_id      │
│ password     │       │ url                │       │ name         │
│ created_at   │       │ title              │       │ created_at   │
└──────────────┘       │ description        │       └──────────────┘
                       │ created_at         │              │
                       └────────────────────┘              │
                              │    │                       │
                              │    │   ┌───────────────────┘
                              │    │   │
                       ┌──────┴────┴───┴─────┐
                       │  bookmark_tags (M2M) │
                       └─────────────────────┘
                              │
                       ┌──────┴──────┐
                       │ collections │
                       ├─────────────┤
                       │ id          │
                       │ user_id     │
                       │ name        │
                       │ parent_id   │──┐ (self-referential)
                       │ created_at  │<─┘
                       └─────────────┘
                              │
                    ┌─────────┴─────────┐
                    │bookmark_collections│
                    │       (M2M)        │
                    └────────────────────┘
```

## References
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [asyncpg](https://github.com/MagicStack/asyncpg)
- [Alembic](https://alembic.sqlalchemy.org/)
- [PostgreSQL 16](https://www.postgresql.org/docs/16/)
- [12-Factor App: Dev/prod parity](https://12factor.net/dev-prod-parity)
