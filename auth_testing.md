# Auth-Gated App Testing Playbook (CorpIntel India)

This app supports BOTH Email/Password (JWT) auth AND Emergent managed Google
Auth (session-token cookie). For automated testing prefer the **test-bypass
demo login** or a seeded session token.

## Test-bypass demo login (development)
When `ALLOW_TEST_BYPASS=true` (default in this environment) the backend exposes
`POST /api/auth/demo-login` which returns a valid JWT for a seeded demo user
(`demo@corpintel.in`, plan=pro). The frontend shows a "Demo Login" button.

```bash
curl -X POST "$REACT_APP_BACKEND_URL/api/auth/demo-login"
# -> { access_token, token_type, user: {...} }
```

## Email/Password
```bash
curl -X POST "$REACT_APP_BACKEND_URL/api/auth/register" -H 'Content-Type: application/json' \
  -d '{"email":"qa@example.com","password":"Test@1234","name":"QA"}'
curl -X POST "$REACT_APP_BACKEND_URL/api/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"qa@example.com","password":"Test@1234"}'
# Use: Authorization: Bearer <access_token>
```

## Emergent Google session (seed a session token)
```bash
mongosh "$MONGO_URL" --eval '
const dbn = "test_database"; const d = db.getSiblingDB(dbn);
const uid = "user_" + Date.now();
const tok = "test_session_" + Date.now();
d.users.insertOne({user_id: uid, email: "google.qa@example.com", name: "Google QA", plan: "pro", created_at: new Date()});
d.user_sessions.insertOne({user_id: uid, session_token: tok, expires_at: new Date(Date.now()+7*24*3600*1000), created_at: new Date()});
print(tok);'
```
Then set cookie `session_token=<tok>` (httpOnly, secure, sameSite=None) OR send
`Authorization: Bearer <tok>`.

## Checklist
- /api/auth/me returns user data (cookie OR bearer)
- Protected pages load without redirect to login
- Plan-gated features (exports, contact data) enforce limits
