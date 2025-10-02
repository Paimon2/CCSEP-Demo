from flask import Flask, render_template, request, redirect, url_for, session, abort
import sqlite3, os

app = Flask(__name__)  
app.secret_key = "dev-secret"  # needed for sessions

# CSRFProtect(app) # fixes CSRF

# VULN: Make the session cookie cross-site so CSRF is easy to demonstrate
app.config.update(
    SESSION_COOKIE_SAMESITE=None,  # VULN: allow cross-site POSTs to carry session cookie
    SESSION_COOKIE_SECURE=False,    # VULN (ok for localhost demo). SAFE later: True (with HTTPS)
)
# SAFE (commented):
# app.config.update(SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=True)

DB_PATH = os.path.join(os.path.dirname(__file__), 'cars.db')

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
            ("Ford", "Mustang", 2016, 38990, "V8 power. Test me!"),
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
        # SAFE for SQLi (parameterized).
        cur.execute(
            "INSERT INTO cars(make,model,year,price,description) VALUES(?,?,?,?,?)",
            (make, model, int(year or 0), int(price or 0), description)
        )
        conn.commit(); conn.close()

        # VULN: reflected XSS (the template uses |safe to render this)
        message = f"Thanks! Listed <strong>{make} {model}</strong> ({year}) for ${price}. Description: {description}"

        # SAFE (commented) — CSRF token generation + check (see template notes):
        # from secrets import token_urlsafe
        # if 'csrf' not in session: session['csrf'] = token_urlsafe(32)
        # sent = request.form.get('csrf_token')
        # if not sent or sent != session['csrf']: abort(403)

    # SAFE (commented) — pass token to template:
    # token = session.get('csrf', None)
    # return render_template('sell.html', message=message, csrf_token=token)

    return render_template('sell.html', message=message)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
