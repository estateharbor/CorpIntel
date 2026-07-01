# Auth-Gated App Testing Playbook (CorpIntel India)

This app supports Email/Password (JWT) auth. For automated testing, prefer the
**test-bypass demo login** in non-production environments.

## Test-bypass demo login (development)
When `ALLOW_TEST_BYPASS=true` the backend exposes
`POST /api/v1/auth/demo-login` which returns a valid JWT for a seeded demo user
(`demo@corpintel.in`, plan=pro). The frontend shows a "Demo Login" button.
The backend refuses to start with this flag enabled in production.

```bash
curl -X POST "$REACT_APP_BACKEND_URL/api/v1/auth/demo-login"
# -> { access_token, token_type, user: {...} }
```

## Email/Password
```bash
curl -X POST "$REACT_APP_BACKEND_URL/api/v1/auth/register" -H 'Content-Type: application/json' \
  -d '{"email":"qa@example.com","password":"Test@1234","name":"QA"}'
curl -X POST "$REACT_APP_BACKEND_URL/api/v1/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"qa@example.com","password":"Test@1234"}'
# Use: Authorization: Bearer <access_token>
```

## Checklist
- /api/v1/auth/me returns user data for a bearer token
- Protected pages load without redirect to login
- Plan-gated features (exports, contact data) enforce limits
