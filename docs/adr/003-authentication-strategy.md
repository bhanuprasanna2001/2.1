# ADR-003: Authentication Strategy

## Status
Accepted

## Context
The API needs to authenticate users and protect resources. Users should only access their own bookmarks, collections, and tags. The authentication mechanism should be stateless, scalable, and suitable for API consumers (web apps, mobile apps, CLI tools).

## Decision Drivers
- **Stateless**: No server-side session storage for horizontal scaling
- **Security**: Modern standards for password storage and token handling
- **Mobile-friendly**: Works well with mobile apps and SPAs
- **Simplicity**: Not over-engineered for the scope
- **Revocability**: Ability to invalidate sessions when needed

## Considered Options

### 1. JWT (Access + Refresh Tokens)
- Stateless, self-contained tokens
- Short-lived access tokens (15 min)
- Long-lived refresh tokens (7 days)
- Requires refresh logic on client
- Revocation needs token blacklist

### 2. Session-based Authentication
- Server stores session state
- Requires shared session store (Redis) for scaling
- Simpler revocation (delete session)
- Cookie-based, CSRF concerns

### 3. API Keys
- Simple for server-to-server
- No built-in expiration
- Not suitable for user authentication
- Hard to revoke per-device

### 4. OAuth2 with External Provider
- Delegates auth to Google/GitHub
- Complex setup
- Dependency on external services
- Good UX for end users

## Decision
**JWT with Access + Refresh Tokens**, using:
- **Password hashing**: argon2-cffi (2026 standard, OWASP recommended)
- **JWT library**: PyJWT (lightweight, actively maintained)
- **Token storage**: Refresh tokens stored in database for revocation

### Token Strategy
```
┌─────────────────────────────────────────────────────────────────┐
│                        Authentication Flow                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Login: POST /auth/login                                     │
│     └─> Returns: access_token (15min) + refresh_token (7days)   │
│                                                                 │
│  2. API Call: GET /bookmarks                                    │
│     └─> Header: Authorization: Bearer <access_token>            │
│                                                                 │
│  3. Token Expired: 401 Unauthorized                             │
│     └─> Client calls: POST /auth/refresh                        │
│         └─> Returns: new access_token                           │
│                                                                 │
│  4. Logout: POST /auth/logout                                   │
│     └─> Invalidates refresh_token in database                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Rationale
1. **Argon2 over bcrypt**: Memory-hard algorithm resists GPU/ASIC attacks, OWASP 2024+ recommendation
2. **Short access tokens**: Limits exposure window if token leaked
3. **Refresh tokens in DB**: Enables logout/revocation without Redis
4. **PyJWT simplicity**: Lightweight, does one thing well, actively maintained

## Consequences

### Positive
- Stateless API servers (horizontal scaling)
- No shared session store needed
- Works with any client (web, mobile, CLI)
- Modern security with Argon2
- Revocation via database (refresh tokens)

### Negative
- Access token revocation requires short expiry (15 min window)
- Client must handle token refresh logic
- Slightly more complex than sessions

### Risks
- JWT secret key exposure (mitigated: environment variable, rotation plan)
- Refresh token theft (mitigated: stored securely, HTTPS only)

## Security Parameters

```python
# Argon2 parameters (OWASP recommendations)
ARGON2_TIME_COST = 3          # iterations
ARGON2_MEMORY_COST = 65536    # 64 MB
ARGON2_PARALLELISM = 4        # threads

# JWT parameters
ACCESS_TOKEN_EXPIRE = 15      # minutes
REFRESH_TOKEN_EXPIRE = 7      # days
ALGORITHM = "HS256"           # HMAC-SHA256
```

## References
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [argon2-cffi](https://argon2-cffi.readthedocs.io/)
- [PyJWT](https://pyjwt.readthedocs.io/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
