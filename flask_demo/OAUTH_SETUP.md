# Implementing OAuth (Google) in the Flask Demo

This document describes how to add real user authentication to the Flask demo using
**Google as the identity provider** via OpenID Connect (OAuth 2.0).

## Why this is a small change

The app already has a single, clean seam for identity: `get_current_user_id()` in
[`app.py`](app.py) (lines 48–53). Today it returns a hardcoded `'demo-user'`:

```python
def get_current_user_id():
    """Get current user ID from session (demo uses session, not real auth)."""
    if 'user_id' not in session:
        session['user_id'] = 'demo-user'
    return session['user_id']
```

Every route (`/upload`, `/results`, `/dashboard`, `/abnormal`, `/changes`, `/reset`, …)
derives its `user_id` from this one function, and that `user_id` is used directly as the
`patient_id` foreign key in the `bloodwork` package (see the repository/ORM layer). So the
entire OAuth task reduces to:

1. Authenticate the user against Google.
2. On success, store a **stable, unique** Google identifier in `session['user_id']`.
3. Make `get_current_user_id()` return that value (and reject requests when it's absent).

No changes are needed in the `bloodwork` package — it already treats `patient_id` as an
opaque string supplied by the host app.

> ⚠️ **Data-scoping note:** Once real users log in, their `user_id` changes from
> `'demo-user'` to something like `google-oauth2|1179087...`. Existing rows in
> `bloodwork_demo.db` are keyed to `'demo-user'` and will no longer be visible to any
> logged-in user. This is expected. See [Migrating existing data](#migrating-existing-demo-data).

---

## Step 0 — Choose a library

Use **[Authlib](https://docs.authlib.org/en/latest/client/flask.html)**. It has
first-class Flask integration, does OpenID Connect discovery automatically (no
hand-wiring of Google's endpoints), and validates the ID token for you.

```bash
pip install "Authlib>=1.3" requests
```

Add to `requirements.txt`:

```
Authlib==1.3.2
requests==2.32.3
```

(`cryptography` is already pinned in `requirements.txt`, which Authlib needs for JWT
signature verification.)

---

## Step 1 — Create Google OAuth credentials

In the [Google Cloud Console](https://console.cloud.google.com/):

1. Create (or select) a project.
2. **APIs & Services → OAuth consent screen**
   - User type: **External**.
   - Fill in app name, support email, developer contact.
   - Scopes: add `openid`, `.../auth/userinfo.email`, `.../auth/userinfo.profile`.
   - While in "Testing" mode, add your Google account under **Test users** (only listed
     users can log in until you publish).
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Web application**.
   - **Authorized redirect URIs** — add every origin the app is served from:
     - Local dev: `http://localhost:5000/auth/callback`
     - Public (Cloudflare tunnel): `https://reports.example.com/auth/callback`
   - Copy the **Client ID** and **Client Secret**.

> The redirect URI must match **exactly** (scheme, host, port, path). A mismatch is the
> #1 cause of `redirect_uri_mismatch` errors. Because this app is fronted by a Cloudflare
> tunnel (see repo memory: `cloudflare-tunnel-setup`), the browser sees
> `https://reports.example.com` even though Flask listens on plain HTTP internally — the
> registered redirect URI must be the **public HTTPS** one, and Flask must generate that
> URL correctly (Step 4).

---

## Step 2 — Provide configuration via environment variables

Never hardcode the client secret. Add these to your shell / `.env` / systemd unit /
`cloudflared` host environment:

```bash
export GOOGLE_CLIENT_ID="xxxxxxxx.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="GOCSPX-xxxxxxxx"
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

`SECRET_KEY` is already read in `app.py` (line 22) but currently defaults to a random value
per process — **that logs everyone out on every restart / breaks multi-worker gunicorn.**
Set it to a stable, secret value in any real deployment.

---

## Step 3 — Register the OAuth client

Near the top of `app.py`, after the Flask app is created:

```python
from authlib.integrations.flask_client import OAuth

oauth = OAuth(app)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    client_kwargs={"scope": "openid email profile"},
)
```

The `server_metadata_url` lets Authlib discover Google's authorization, token, and JWKS
endpoints automatically — you don't maintain those URLs yourself.

---

## Step 4 — Fix HTTPS URL generation (Cloudflare tunnel)

`url_for(..., _external=True)` must produce `https://reports.example.com/auth/callback`,
not `http://...`, or Google will reject the callback. Two things:

1. There's an existing **typo** in `app.py` line 23: `PREFFERED_URL_SCHEME` should be
   `PREFERRED_URL_SCHEME`. Fix it:

   ```python
   app.config['PREFERRED_URL_SCHEME'] = 'https'
   ```

2. `PREFERRED_URL_SCHEME` alone is not always honored for `url_for` during a request.
   The robust fix behind a reverse proxy / tunnel is `ProxyFix`, which trusts the
   `X-Forwarded-Proto` header Cloudflare sends:

   ```python
   from werkzeug.middleware.proxy_fix import ProxyFix
   app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
   ```

Also harden the session cookie for production:

```python
app.config.update(
    SESSION_COOKIE_SECURE=True,      # only send cookie over HTTPS
    SESSION_COOKIE_HTTPONLY=True,    # not readable by JS
    SESSION_COOKIE_SAMESITE="Lax",   # needed so the cookie survives the OAuth redirect
)
```

(Use `SESSION_COOKIE_SECURE=True` only when served over HTTPS — for pure `http://localhost`
dev, leave it `False` or the cookie won't be set.)

---

## Step 5 — Add login / callback / logout routes

```python
from functools import wraps
from flask import abort

@app.route("/login")
def login():
    redirect_uri = url_for("auth_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/auth/callback")
def auth_callback():
    token = oauth.google.authorize_access_token()  # validates state + ID token
    userinfo = token["userinfo"]                   # dict from the verified ID token

    # 'sub' is Google's stable, unique, non-reassigned user id — use it as the key.
    session["user_id"] = f"google:{userinfo['sub']}"
    session["email"] = userinfo.get("email")
    session["name"] = userinfo.get("name")
    session.permanent = True
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
```

**Use `sub`, not `email`, as the identity key.** Emails can change or be reassigned;
`sub` is Google's permanent per-user identifier. Prefixing with `google:` namespaces it so
you can add other providers later without collisions.

---

## Step 6 — Enforce authentication

Replace the demo `get_current_user_id()` so it no longer invents a user, and add a
decorator to protect routes:

```python
def get_current_user_id():
    """Return the authenticated user's id, or None if not logged in."""
    return session.get("user_id")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            # Remember where they were headed, then send to login.
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped
```

Then decorate every route that reads or writes user data:

```python
@app.route("/dashboard")
@login_required
def dashboard():
    ...
```

Apply `@login_required` to: `/upload`, `/results`, `/api/results`, `/abnormal`,
`/dashboard`, `/api/visualize/<test_name>`, `/test/<test_name>`, `/changes`, `/reset`.
Leave `/`, `/about`, `/login`, `/auth/callback`, and `/logout` public.

> For the JSON API routes (`/api/...`), you may prefer returning
> `jsonify({'success': False, 'error': 'auth required'}), 401` instead of a redirect, so
> programmatic callers get a clean status code.

---

## Step 7 — Update the UI

In [`templates/base.html`](templates/base.html), show login state in the nav:

```jinja
{% if session.get('user_id') %}
  <span>{{ session.get('name') or session.get('email') }}</span>
  <a href="{{ url_for('logout') }}">Log out</a>
{% else %}
  <a href="{{ url_for('login') }}">Log in with Google</a>
{% endif %}
```

`session` is available in Jinja templates by default — no need to pass it explicitly.

---

## Step 8 — Test the flow

1. `python app.py`, visit `http://localhost:5000`.
2. Click **Log in with Google** → Google consent screen → back to `/dashboard`.
3. Confirm `session['user_id']` is now `google:...` (upload a report; the data is scoped
   to your account).
4. Log out, confirm protected routes redirect to `/login`.
5. Repeat against the public URL `https://reports.example.com` to validate the tunnel /
   HTTPS redirect-URI path.

---

## Migrating existing demo data

Existing rows are owned by `'demo-user'`. To hand them to your real account after first
login, repoint the `patient_id` in the SQLite DB (one-time, do it while logged in and
knowing your new id):

```sql
-- Replace with your actual google:sub value from the session
UPDATE patient_info      SET patient_id = 'google:1179087...' WHERE patient_id = 'demo-user';
UPDATE blood_test_results SET patient_id = 'google:1179087...' WHERE patient_id = 'demo-user';
```

(Confirm the exact table/column names against `bloodwork/repositories/models.py` before
running — they are `PatientInfoORM` / `BloodTestResultORM`.) Or just re-upload the PDFs
while logged in.

---

## Security checklist

- [ ] `GOOGLE_CLIENT_SECRET` and `SECRET_KEY` come from the environment, never committed.
- [ ] `SECRET_KEY` is **stable** across restarts and workers (otherwise sessions break).
- [ ] `SESSION_COOKIE_SECURE`, `HTTPONLY`, and `SAMESITE=Lax` set in production.
- [ ] Redirect URIs in Google Console match the served origins exactly (localhost + tunnel).
- [ ] Authlib validates `state` (CSRF) and the ID-token signature automatically — don't
      bypass `authorize_access_token()` by parsing the token yourself.
- [ ] All data routes are behind `@login_required`; identity keyed on `sub`, not email.
- [ ] Recall this app handles PHI: real auth is what makes per-user isolation real. Keep
      `BLOODWORK_REDACT_PHI=true` and serve only over HTTPS.

---

## Beyond the demo (optional hardening)

- **Restrict to a domain/allowlist:** after callback, reject `userinfo['email']` outside an
  allowed set / Google Workspace `hd` claim if this shouldn't be open to any Google account.
- **Persist users:** the demo keeps everything in the session cookie. For audit trails or
  roles, add a `users` table and store `sub`, email, and last-login.
- **Token refresh:** this design only uses Google for *login* (authentication), so you don't
  need to store or refresh access tokens. Only add refresh handling if you later call Google
  APIs on the user's behalf.
- **Multiple providers:** the `google:` prefix on `user_id` leaves room to register more
  Authlib providers (GitHub, Microsoft) without key collisions.
```