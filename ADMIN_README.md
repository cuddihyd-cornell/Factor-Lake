# Admin Runbook

Audience: admins who manage Factor-Lake across Supabase, GitHub, and Streamlit Cloud.

## What you administer
- Supabase (data + org/project roles)
- GitHub (repo access and deploy source)
- Streamlit Cloud (app deployment, secrets, URL)

## Roles and scope
- **Supabase org (Factor Lake) admin/owner**: can add members, manage billing, rotate API keys, and create projects.
- **Supabase project admin (SYSEN 5900 - Software Systems Engineering in Quant Finance)**: can manage project settings, service keys, and table access. Project admins should also be org members.
- **Streamlit Cloud app admin**: can deploy/update the app, manage secrets, set custom URL, and restart.

## Prerequisites
- GitHub account (member of `cornell-sysen-5900/Factor-Lake`)
- Supabase account (sign in with GitHub)
- Streamlit Cloud account (sign in with GitHub)

## Supabase: add an admin
1. Sign in at https://app.supabase.com with GitHub.
2. Switch to the **Factor Lake** organization.
3. **Org-level**: Invite the admin (email) → assign **Owner** or equivalent admin role.
4. Open project **“SYSEN 5900 - Software Systems Engineering in Quant Finance”**.
5. **Project-level**: Project Settings → Members → invite the same admin → grant **Admin** (or Owner) so they can view service keys and manage tables.
6. Confirm they can see Project Settings → API (for URL and anon key).

## Streamlit Cloud: deploy/manage the app
1. Sign in at https://share.streamlit.io with GitHub.
2. Click **New app**:
   - Repository: `https://github.com/cornell-sysen-5900/Factor-Lake`
   - Branch: `main`
   - Main file: `app/streamlit_app.py`
   - App URL: choose a name (e.g., `cornell-factor-lake`).
3. Configure secrets (Settings → Secrets) and env vars (Settings → Environment variables). Set both, because the code reads `os.environ` for Supabase and `st.secrets` for the password:

```toml
# Secrets (used by Streamlit st.secrets)
password = "<app_password>"
```

Environment variables (set these in the env vars panel):
```
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_KEY=<your-anon-public-key>
ADMIN_PASSWORD=<app_password>
```

4. Save; the app restarts. Test by opening the app URL and entering the password.
5. To redeploy after code changes: merge/push to `main`; Streamlit auto-redeploys.

## GitHub: keep deploy source healthy
- Default deploy branch: `main` in `cornell-sysen-5900/Factor-Lake`.
- Protect `main` if desired; use PRs for changes. After merge, Streamlit redeploys automatically.
- Keep `.streamlit/secrets.toml` out of git (already in `.gitignore`).

## Ops checklist for a new admin
- [ ] Added to Supabase org (Factor Lake) with admin/owner role
- [ ] Added to Supabase project “SYSEN 5900 - Software Systems Engineering in Quant Finance” with admin role
- [ ] Has GitHub access to `cornell-sysen-5900/Factor-Lake`
- [ ] Can open Streamlit Cloud app settings, edit secrets, and trigger redeploy

## Maintenance tips
- Rotate Supabase anon key if leaked; update Streamlit env vars accordingly and restart.
- Change the app password periodically: update `password` secret (and `ADMIN_PASSWORD` env var), then reload the app.
- If the app shows “Admin password is not configured,” verify secrets/env vars are set in Streamlit Cloud.
- If Supabase errors, re-check `SUPABASE_URL` and `SUPABASE_KEY` in env vars.

## Need stronger access control later?
- Replace the simple password gate with Streamlit Authenticator (per-user logins).
- Move to a private Streamlit Cloud workspace or Cloud Run behind an identity-aware proxy.
