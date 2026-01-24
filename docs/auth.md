# Auth, OAuth, and RBAC (Phase 1)

Goals: secure access, low-friction onboarding (Google/Microsoft), least-privilege roles, auditability. Target: web app + desktop agent using the same backend.

## Decisions
- Identity store: users table with optional password_hash (bcrypt/argon2) for email/password; SSO-first onboarding via Google/Microsoft OAuth.
- Session model: server-issued, HttpOnly secure cookies for web; short-lived access tokens + refresh for desktop agent/API. Keep rotation and revocation.
- Token format: signed JWT access tokens (15m) + opaque refresh tokens stored in sessions table (revocable).
- RBAC: coarse roles initially (admin, member, viewer). Admin can manage team, billing rules, invoices; member can log time, view own invoices; viewer is read-only.
- Audit: log auth events (login, logout, password reset, SSO link) into audit_logs.

## OAuth (Google/Microsoft)
- Flow: Authorization Code with PKCE.
- Scopes: profile, email; calendar.readonly (optional consent for time-capture signals).
- Account linking: user_oauth_accounts stores provider + provider_account_id; uniqueness enforced; on login, map to user.
- Token storage: store refresh_token encrypted; access_token only if needed for background sync; track expires_at.
- Revocation: allow unlink; keep audit entry.

## Endpoints (sketch)
- POST /auth/register {email, password?, name}
- POST /auth/login {email, password}
- POST /auth/refresh {refresh_token}
- POST /auth/logout
- GET /auth/me -> user profile + roles
- GET /auth/oauth/:provider/start (redirect)
- GET /auth/oauth/:provider/callback

Responses: set-cookie for session/refresh tokens with Secure, HttpOnly, SameSite=Lax; CSRF token header for state-changing requests (double-submit or SameSite + custom header).

## Session & Token Handling
- Access token: JWT with sub, role, exp, iat; signed with rotating key; 15m TTL.
- Refresh: opaque random token, stored hashed in sessions table with user_id, expires_at; TTL 30d; rotate on use.
- Logout: delete session row, clear cookies.
- Idle timeout: configurable; renew access on activity via refresh.

## RBAC Model (initial)
- Roles: admin | member | viewer (future: billing-admin, integrator).
- Policy examples:
  - admin: manage users, clients, projects, billing rules, invoices, payments, integrations.
  - member: CRUD time entries, view own entries, view assigned projects, create invoices if granted per-project flag.
  - viewer: read-only dashboards and reports.
- Enforcement: middleware checks role against route permissions; per-entity ownership checks for client/project/time entry access.

## Password & Security Hygiene
- Passwords: argon2id (preferred) or bcrypt with strong cost; never log raw input.
- Rate limiting: login/refresh/register endpoints (IP + user tuple); captcha optional after threshold.
- MFA (future): TOTP/WebAuthn; design schema extensible (add mfa_factors table).
- Email flows: password reset tokens (short TTL, single-use); email verification tokens.

## Desktop Agent Authentication
- Device login: OAuth device code or browser-based SSO to issue agent-specific refresh token; scope limited to time ingest.
- Token storage: OS keychain/secure store; never persist long-lived tokens in plain text.
- Agent headers: Authorization: Bearer <access>; include device_id for traceability; user agent string identifies app version.

## Audit & Observability
- Record auth events in audit_logs with actor_email, action, meta (ip, ua, provider).
- Emit security metrics: login_success/failure, refresh_success/failure, token_rotation, oauth_link/unlink.

## Open Questions
- Do we support organization-level admins distinct from global admins? If yes, add orgs + memberships.
- Do we need SAML/SCIM later? Keep user schema extensible.
- Do we require enforced email verification before time capture?
