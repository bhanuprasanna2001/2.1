# ADR-001: Web Framework Selection

## Status
Accepted

## Context
We need to select a Python web framework for building a REST API that will handle bookmark management. The framework should support modern Python practices, provide good developer experience, and be suitable for production use.

## Decision Drivers
- **Learning value**: Should teach modern patterns applicable to industry work
- **Type safety**: Strong typing support for maintainability
- **Performance**: Ability to handle concurrent requests efficiently
- **Documentation**: Auto-generated API documentation for consumers
- **Ecosystem**: Good library support and community
- **Async support**: Native async/await for I/O-bound operations

## Considered Options

### 1. FastAPI
- Modern, async-first framework
- Native Pydantic integration for validation
- Automatic OpenAPI documentation
- Type hints drive behavior
- Rapidly growing adoption

### 2. Flask
- Mature, battle-tested
- Large ecosystem
- Sync by default (async requires extensions)
- Manual documentation setup
- Flexible but more boilerplate

### 3. Django REST Framework
- Batteries included
- Excellent for rapid development
- Tightly coupled to Django ORM
- Opinionated structure
- Heavier learning curve for customization

## Decision
**FastAPI** is selected as the web framework.

### Rationale
1. **Type-driven development**: Pydantic models define both validation and documentation, reducing duplication
2. **Async native**: Built on Starlette, handles async database operations naturally
3. **Modern Python**: Uses type hints as first-class citizens, aligning with Python 3.12+ best practices
4. **Auto documentation**: OpenAPI/Swagger generated automatically from code
5. **Performance**: One of the fastest Python frameworks, comparable to Node.js
6. **Industry momentum**: Rapidly becoming the standard for Python APIs (2024-2026 trend)

## Consequences

### Positive
- Clean, type-safe code with Pydantic validation
- Excellent developer experience with IDE support
- Auto-generated, always-up-to-date API docs
- Easy testing with built-in test client
- Good performance characteristics

### Negative
- Smaller ecosystem than Flask/Django (though growing)
- Fewer "batteries included" features
- Team members unfamiliar with async may need ramp-up

### Risks
- Pydantic v2 migration issues (mitigated: starting with v2)
- Async complexity in debugging (mitigated: structured logging)

## References
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Starlette](https://www.starlette.io/)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [TechEmpower Benchmarks](https://www.techempower.com/benchmarks/)
