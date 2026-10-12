import os
from functools import wraps

import bcrypt
import pymysql
import pymysql.cursors
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "change-me")

def get_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "registration"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def query(sql, params=()):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def execute(sql, params=()):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.lastrowid
    finally:
        conn.close()


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return view(*args, **kwargs)
    return wrapper


def check_title(raw):
    title = (raw or "").strip()
    if not title:
        return title, "Title is required"
    if len(title) > 200:
        return title, "Title is too long (200 characters at most)"
    return title, None


def hash_password(password):
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt(12)).decode()


def verify_password(password, stored_hash):
    try:
        return bcrypt.checkpw(password.encode()[:72], stored_hash.encode())
    except ValueError:
        return False


def start_session(user_id, name):
    session.clear()
    session["user_id"] = user_id
    session["name"] = name


@app.route("/")
def index():
    return redirect("/todos" if "user_id" in session else "/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect("/todos")
    if request.method == "GET":
        return render_template("register.html", errors={}, values={})

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    errors = {}
    if not name:
        errors["name"] = "Name is required"
    elif len(name) > 100:
        errors["name"] = "Name is too long (100 characters at most)"
    if not email:
        errors["email"] = "Email is required"
    elif len(email) > 255:
        errors["email"] = "Email is too long (255 characters at most)"
    if not password:
        errors["password"] = "Password is required"
    if not confirm:
        errors["confirm_password"] = "Confirm password is required"
    elif password and password != confirm:
        errors["confirm_password"] = "Passwords do not match"

    values = {"name": name, "email": email}
    if errors:
        return render_template("register.html", errors=errors, values=values)

    try:
        user_id = execute(
            "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
            (email, name, hash_password(password)),
        )
    except pymysql.err.IntegrityError as e:
        if e.args and e.args[0] == 1062:
            return render_template(
                "register.html", errors={"email": "Email Already Exists"}, values=values
            )
        raise

    start_session(user_id, name)
    return redirect("/todos")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect("/todos")
    if request.method == "GET":
        return render_template("login.html", errors={}, values={}, form_error=None)

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    errors = {}
    if not email:
        errors["email"] = "Email is required"
    if not password:
        errors["password"] = "Password is required"
    if errors:
        return render_template("login.html", errors=errors, values={"email": email}, form_error=None)

    rows = query("SELECT user_id, name, password_hash FROM users WHERE email = %s", (email,))
    user = rows[0] if rows else None
    if not user or not verify_password(password, user["password_hash"]):
        return render_template(
            "login.html", errors={}, values={"email": email}, form_error="Invalid email or password"
        )

    start_session(user["user_id"], user["name"])
    return redirect("/todos")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/login")


def render_todos(add_error=None, add_value="", edit_err=None):
    todos = query(
        "SELECT todo_id, title, is_done, created_at FROM todos "
        "WHERE user_id = %s ORDER BY todo_id DESC",
        (session["user_id"],),
    )
    return render_template(
        "todos.html",
        name=session["name"],
        todos=todos,
        add_error=add_error,
        add_value=add_value,
        edit_err=edit_err,
    )


@app.route("/todos")
@login_required
def todos():
    return render_todos()


@app.route("/todos/add", methods=["POST"])
@login_required
def add_todo():
    raw = request.form.get("title", "")
    title, error = check_title(raw)
    if error:
        return render_todos(add_error=error, add_value=raw)
    execute("INSERT INTO todos (user_id, title) VALUES (%s, %s)", (session["user_id"], title))
    return redirect("/todos")


@app.route("/todos/<int:todo_id>/edit", methods=["POST"])
@login_required
def edit_todo(todo_id):
    raw = request.form.get("title", "")
    title, error = check_title(raw)
    if error:
        return render_todos(edit_err={"id": todo_id, "message": error, "value": raw})
    execute(
        "UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s",
        (title, todo_id, session["user_id"]),
    )
    return redirect("/todos")


@app.route("/todos/<int:todo_id>/done", methods=["POST"])
@login_required
def done_todo(todo_id):
    is_done = 1 if request.form.get("is_done") == "1" else 0
    execute(
        "UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s",
        (is_done, todo_id, session["user_id"]),
    )
    return redirect("/todos")


@app.route("/todos/<int:todo_id>/delete", methods=["POST"])
@login_required
def delete_todo(todo_id):
    execute("DELETE FROM todos WHERE todo_id = %s AND user_id = %s", (todo_id, session["user_id"]))
    return redirect("/todos")


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Page not found."), 404


@app.errorhandler(405)
def not_allowed(e):
    return render_template("error.html", message="Page not found."), 405


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", message="Something went wrong. Please try again."), 500


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", 3000)), debug=False)
