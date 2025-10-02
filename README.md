# Cars4U Cybersecurity Lab

## Overview
Cars4U is a teaching aid for security testing that ships with two sibling Flask applications:
- `vulnerable/` keeps intentionally weak defaults so common web vulnerabilities are easy to demonstrate.
- `non-vulnerable/` applies hardening measures that close the same issues while preserving user flows.

Both variants share an SQLite catalogue of cars, Bootstrap-based templates, and a lightweight master-detail UI driven by `static/buy.js`.

## Requirements
- Python 3.9 or newer (tested with Python 3.11 on macOS)
- pip

Install the Python packages that the apps rely on:
```bash
pip install flask flask-wtf bleach
```

## Quick Start
Each app can be run on its own. The vulnerable build binds to port 5000; the hardened build uses 5001 so both can run side-by-side.

### macOS setup
1. Ensure the system Python is 3.9+. macOS ships with `python3`; install Xcode CLT if it is missing.
2. From the repository root:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install flask flask-wtf bleach
   ```
3. Run the vulnerable lab:
   ```bash
   cd vulnerable
   python3 app.py
   ```
   Visit http://localhost:5000.
4. In a second terminal keep the virtual environment active, then start the patched lab:
   ```bash
   cd non-vulnerable
   python3 app.py
   ```
   Visit http://localhost:5001.
5. Both variants create `cars.db` on first launch; delete it if you want a clean slate.

### General (Linux/Windows)
The same commands apply, substituting `source .venv/bin/activate` with `.venv\Scripts\activate` on Windows PowerShell.

## Detecting the vulnerabilities
- **Missing CSRF protection**: Inspect the `/sell` form response headers and payload. The vulnerable app sends cookies without `SameSite` or `Secure`, and the form lacks a hidden token. Intercepted POSTs replay cleanly.
- **Stored XSS**: Submitting HTML in the description field (e.g., `<img src=x onerror=alert('stored')>`) persists to SQLite. Reload `/buy` and the description block renders with `|safe`, triggering script execution.
- **Reflected XSS**: The confirmation flash returned after a successful sale request reflects raw user values into the success banner.

## Exploiting the vulnerabilities
1. Log in through `/login` on the vulnerable server.
2. Use `/sell` to add a listing with script payloads in `description` and observe script execution on `/buy` and in the success alert.
3. With the victim logged in, open `attacker.html` in a separate tab or host it with `python3 -m http.server`. The auto-submitting form posts cross-site to `http://localhost:5000/sell`, proving CSRF is achievable when `SESSION_COOKIE_SAMESITE=None`.

## Patching strategy
The non-vulnerable implementation illustrates the fixes:
- `flask_wtf.CSRFProtect` enforces per-request tokens, and cookie settings tighten to `SameSite=Lax`, `Secure=True`, and `HttpOnly=True`.
- User-generated content passes through `sanitize_html` (Bleach) before reaching SQLite, stripping tags and bounding length.
- The success banner in `/sell` now formats plain text instead of raw HTML.
- A strict Content Security Policy is applied after every response to reduce script injection impact.
- Front-end scripting relies on text setters (`textContent`) only.

Compare `vulnerable/app.py` with `non-vulnerable/app.py` to see each change in context.

## Notes to markers
- Verify both servers start cleanly, auto-creating `cars.db` in their respective folders.
- Demonstrate CSRF from `attacker.html` while the vulnerable server runs on port 5000; the hardened server should reject the same flow with a 400.
- Validate that stored scripts execute on `/buy` in the vulnerable build but render harmlessly in the secure build.
- Confirm that the README steps were followed when assessing automation scripts or grading execution traces.
- Please note any environment-specific tweaks (alternate ports, Python versions) directly in the marking sheet for reproducibility.
