# ADR-005: Error Handling Strategy

## Status
Accepted

## Context
APIs must communicate errors clearly to clients. A consistent error format enables clients to handle errors programmatically, aids debugging, and improves user experience. We need to decide on error response format, exception hierarchy, and error codes.

## Decision Drivers
- **Consistency**: All errors follow the same format
- **Debuggability**: Errors include enough context for troubleshooting
- **Client-friendly**: Programmatic error handling possible
- **Security**: Don't leak internal details in production
- **Standards**: Follow REST/HTTP conventions

## Considered Options

### 1. Minimal (HTTP status only)
```json
{"detail": "Not found"}
```
- FastAPI default
- Simple but not enough for complex errors

### 2. RFC 7807 Problem Details
```json
{
  "type": "https://api.example.com/errors/not-found",
  "title": "Resource not found",
  "status": 404,
  "detail": "Bookmark with ID 123 not found",
  "instance": "/bookmarks/123"
}
```
- Industry standard
- Verbose, requires URI management

### 3. Custom Structured Format
```json
{
  "error": {
    "code": "BOOKMARK_NOT_FOUND",
    "message": "Bookmark not found",
    "details": {...},
    "request_id": "uuid"
  }
}
```
- Flexible, tailored to needs
- Not a formal standard

## Decision
**Custom structured format** inspired by RFC 7807 but simplified.

### Error Response Schema
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable error message",
    "details": [
      {
        "field": "url",
        "message": "Invalid URL format"
      }
    ],
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Rationale
1. **Consistent envelope**: All errors wrapped in `error` object
2. **Error codes**: Machine-readable codes for client logic
3. **Request ID**: Links to logs for debugging
4. **Details array**: Supports multiple validation errors
5. **No stack traces**: Security in production

### Error Codes
```python
# Resource errors
BOOKMARK_NOT_FOUND = "BOOKMARK_NOT_FOUND"
COLLECTION_NOT_FOUND = "COLLECTION_NOT_FOUND"
TAG_NOT_FOUND = "TAG_NOT_FOUND"
USER_NOT_FOUND = "USER_NOT_FOUND"

# Validation errors
VALIDATION_ERROR = "VALIDATION_ERROR"
DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
INVALID_URL = "INVALID_URL"

# Authentication errors
INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
TOKEN_EXPIRED = "TOKEN_EXPIRED"
TOKEN_INVALID = "TOKEN_INVALID"
UNAUTHORIZED = "UNAUTHORIZED"

# Server errors
INTERNAL_ERROR = "INTERNAL_ERROR"
DATABASE_ERROR = "DATABASE_ERROR"
```

### HTTP Status Code Mapping
| Code | Status | When |
|------|--------|------|
| `*_NOT_FOUND` | 404 | Resource doesn't exist |
| `VALIDATION_ERROR` | 422 | Invalid request body |
| `DUPLICATE_RESOURCE` | 409 | Unique constraint violation |
| `INVALID_CREDENTIALS` | 401 | Wrong email/password |
| `TOKEN_*` | 401 | JWT issues |
| `UNAUTHORIZED` | 403 | Missing permissions |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

### Exception Hierarchy
```python
class AppException(Exception):
    """Base exception for all application errors"""
    code: str
    message: str
    status_code: int

class NotFoundError(AppException):
    status_code = 404

class ValidationError(AppException):
    status_code = 422

class AuthenticationError(AppException):
    status_code = 401

class AuthorizationError(AppException):
    status_code = 403
```

## Consequences

### Positive
- Clients can switch on `error.code` for handling
- Request ID enables log correlation
- Validation errors are granular (per-field)
- Consistent format across all endpoints

### Negative
- Custom format, not RFC 7807
- Need to maintain error code enum

### Risks
- Inconsistent error codes (mitigated: centralized enum)
- Leaking sensitive info (mitigated: exception handler sanitizes in production)

## Implementation Notes

1. **Global exception handler** catches all `AppException` subclasses
2. **Request ID middleware** generates UUID for each request
3. **Logging** includes request ID for correlation
4. **Validation errors** from Pydantic are transformed to our format

## References
- [RFC 7807: Problem Details for HTTP APIs](https://datatracker.ietf.org/doc/html/rfc7807)
- [Google Cloud API Error Model](https://cloud.google.com/apis/design/errors)
- [Stripe API Errors](https://stripe.com/docs/api/errors)
