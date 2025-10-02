from flask import Flask, render_template, request, redirect, url_for, session, abort
import sqlite3, os 
from secrets import token_urlsafe
from flask_wtf.csrf import CSRFProtect
 
import bleach

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", token_urlsafe(32))

csrf = CSRFProtect(app)

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",  
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True)

DB_PATH = os.path.join(os.path.dirname(__file__), 'cars.db')

def sanitize_html(html:str) -> str:
    #clean disallowed tags/attrs/protocols
    cleaned = bleach.clean(
        html or "",
        tags=[],
        attributes={},
        protocols=[],
        strip=True
    )

    cleaned = " ".join(cleaned.split())[:2000]
    return cleaned

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT,
            model TEXT,
            year INTEGER,
            price INTEGER,
            description TEXT
        )
    """)
    c = cur.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
    if c == 0:
        seed = [
            ("Toyota", "Corolla", 2018, 14990, "Good condition, one owner."),
            ("Mazda", "CX-5", 2020, 32990, "Top spec, low kms."),
            ("Ford", "Mustang", 2016, 38990, "V8 power — test me!"),
            ("Hyundai", "i30", 2019, 17990, "Great commuter car."),
        ]
        cur.executemany("INSERT INTO cars(make,model,year,price,description) VALUES(?,?,?,?,?)", seed)
    conn.commit()
    conn.close()

if not os.path.exists(DB_PATH):
    init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form.get('user') or 'demo'
        return redirect(url_for('sell'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Buy (NO SQLi; parameterized LIKE) + keep reflected/stored XSS in templates
@app.route('/buy')
def buy():
    q = request.args.get('q', '')
    conn = get_db(); cur = conn.cursor()
    if q:
        like = f"%{q}%"
        rows = cur.execute(
            "SELECT id,make,model,year,price,description FROM cars "
            "WHERE make LIKE ? OR model LIKE ? OR CAST(year AS TEXT) LIKE ? "
            "OR CAST(price AS TEXT) LIKE ? OR description LIKE ?",
            (like, like, like, like, like)
        ).fetchall()
    else:
        rows = cur.execute("SELECT id,make,model,year,price,description FROM cars").fetchall()
    conn.close()
    return render_template('buy.html', rows=rows, q=q)

#  Sell (parameterized INSERT to avoid SQLi) + CSRF VULNERABILITY + XSS kept
@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if 'user' not in session:
        return redirect(url_for('login'))

    message = ''
    if request.method == 'POST':
        # VULN: No CSRF token verification on a state-changing POST
        # SAFE (commented) CSRF check example further below.

        make = request.form.get('make', '')
        model = request.form.get('model', '')
        year = request.form.get('year', '0')
        price = request.form.get('price', '0')
        description = request.form.get('description', '')

        conn = get_db(); cur = conn.cursor()
        
        desc = sanitize_html(description) #removing all tags

        # SAFE for SQLi (parameterized). We keep XSS in templates, not here.
        cur.execute(
            "INSERT INTO cars(make,model,year,price,description) VALUES(?,?,?,?,?)",
            (make, model, int(year or 0), int(price or 0), desc)
        )
        conn.commit()
        conn.close()

        # VULN: reflected XSS (the template uses |safe to render this)
        # message = f"Thanks! Listed <strong>{make} {model}</strong> ({year}) for ${price}. Description: {description}"

        # SAFE (commented) — CSRF token generation + check (see template notes):
        message = f"{make} {model} ({year}) for ${price} successfully listed"

    # SAFE (commented) — pass token to template:
    return render_template('sell.html', message=message)

@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "img-src 'self' data:; "
        "font-src 'self' data: https://fonts.gstatic.com; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'self'"
    )
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)