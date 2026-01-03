# Synkventory Auth Integration

## Files to Copy

Copy these files to your existing backend:

```
app/
├── core/
│   ├── tenant.py      # NEW - Tenant context management
│   ├── security.py    # NEW - JWT + password utilities  
│   └── deps.py        # NEW - Auth dependencies
├── middleware/
│   ├── __init__.py    # NEW
│   └── tenant.py      # NEW - Subdomain extraction middleware
├── api/v1/
│   ├── api.py         # REPLACE - Adds auth router
│   └── auth.py        # NEW - Login/logout/register endpoints
├── models/
│   └── user.py        # REPLACE - Adds tenant_id, password_hash, etc.
├── db/
│   └── session.py     # REPLACE - Adds RLS context setting
└── main.py            # REPLACE - Adds tenant middleware
```

## Requirements

Add to requirements.txt:
```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

## Environment Variables

Add to your .env:
```
# Auth settings
SECRET_KEY=your-super-secret-key-generate-with-openssl-rand-base64-32
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Tenant settings
BASE_DOMAIN=synkventory.com
ENVIRONMENT=development  # or production
```

## Database

The SQL migration (v3) you already ran adds:
- tenant_id, password_hash, is_locked, locked_until to users table
- tenant_id to all inventory tables
- RLS policies on all tenant-scoped tables
- synkventory_app role for RLS enforcement

## Testing Locally

With ENVIRONMENT=development, the middleware:
1. Allows localhost requests
2. Uses X-Tenant-Slug header OR defaults to "demo" tenant
3. Cookies use secure=True (may need adjustment for http://localhost)

Test login:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: demo" \
  -d '{"email": "admin@demo.com", "password": "changeme123"}'
```

## Protecting Routes

Add auth to existing routes:

```python
from app.core.deps import get_current_user
from app.models.user import User

@router.get("/inventory/")
def get_inventory(
    user: User = Depends(get_current_user),  # NEW: Requires auth
    db: Session = Depends(get_db),           # RLS auto-filters by tenant
):
    # ... existing code works unchanged
    # All queries automatically filtered by tenant
```

## Production Deployment

1. Set ENVIRONMENT=production
2. Configure Cloudflare:
   - CNAME *.synkventory.com → your-app-platform-url
   - Page rule: synkventory.com/* → redirect to coming soon
3. Generate secure SECRET_KEY:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

## Auth Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/auth/login | POST | Login, returns cookies |
| /api/v1/auth/logout | POST | Clear cookies |
| /api/v1/auth/refresh | POST | Refresh access token |
| /api/v1/auth/me | GET | Get current user |
| /api/v1/auth/register | POST | Register new user |
