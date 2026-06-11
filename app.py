from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__, template_folder="templates")
app.secret_key = "secret123"
app.config["SESSION_PERMANENT"] = False


def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        hint_question TEXT,
        hint_answer TEXT
    )
    """)

    try:
        cur.execute("ALTER TABLE users ADD COLUMN hint_question TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE users ADD COLUMN hint_answer TEXT")
    except:
        pass

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    if "user" in session:
        return render_template("index.html", user=session["user"])
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hint_question = request.form["hint_question"]
        hint_answer = request.form["hint_answer"]

        try:
            conn = sqlite3.connect("users.db")
            cur = conn.cursor()

            cur.execute("""
            INSERT INTO users(username, password, hint_question, hint_answer)
            VALUES(?, ?, ?, ?)
            """, (username, password, hint_question, hint_answer))

            conn.commit()
            conn.close()

            return redirect("/login")

        except sqlite3.IntegrityError:
            error = "이미 존재하는 아이디입니다."

        except Exception as e:
            error = "회원가입 중 오류가 발생했습니다: " + str(e)

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT password FROM users WHERE username=?",
            (username,)
        )

        user = cur.fetchone()
        conn.close()

        if user is None:
            error = "존재하지 않는 회원 정보입니다."

        elif user[0] != password:
            error = "비밀번호가 틀렸습니다."

        else:
            session["user"] = username
            return redirect("/")

    return render_template("login.html", error=error)


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    error = None
    success = None
    hint_question = None
    username = None

    if request.method == "POST":
        step = request.form["step"]

        if step == "check_id":
            username = request.form["username"]

            conn = sqlite3.connect("users.db")
            cur = conn.cursor()

            cur.execute(
                "SELECT hint_question FROM users WHERE username=?",
                (username,)
            )

            user = cur.fetchone()
            conn.close()

            if user is None:
                error = "존재하지 않는 회원 정보입니다."
            else:
                hint_question = user[0]

        elif step == "reset_password":
            username = request.form["username"]
            hint_answer = request.form["hint_answer"]
            new_password = request.form["new_password"]

            conn = sqlite3.connect("users.db")
            cur = conn.cursor()

            cur.execute(
                "SELECT hint_answer, hint_question FROM users WHERE username=?",
                (username,)
            )

            user = cur.fetchone()

            if user is None:
                error = "존재하지 않는 회원 정보입니다."

            elif user[0] != hint_answer:
                error = "답변이 일치하지 않습니다."
                hint_question = user[1]

            else:
                cur.execute(
                    "UPDATE users SET password=? WHERE username=?",
                    (new_password, username)
                )

                conn.commit()
                success = "비밀번호가 변경되었습니다. 다시 로그인해주세요."

            conn.close()

    return render_template(
        "forgot_password.html",
        error=error,
        success=success,
        hint_question=hint_question,
        username=username
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/mypage")
def mypage():
    if "user" not in session:
        return redirect("/login")

    return render_template("mypage.html", user=session["user"])


@app.route("/update_user", methods=["POST"])
def update_user():
    if "user" not in session:
        return redirect("/login")

    current_user = session["user"]
    new_username = request.form["new_username"]
    new_password = request.form["new_password"]

    try:
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        cur.execute("""
        UPDATE users
        SET username=?, password=?
        WHERE username=?
        """, (new_username, new_password, current_user))

        conn.commit()
        conn.close()

        session["user"] = new_username

        return redirect("/mypage")

    except sqlite3.IntegrityError:
        return "이미 존재하는 아이디입니다. 뒤로 가서 다른 아이디를 입력하세요."

    except Exception as e:
        return "회원정보 수정 중 오류가 발생했습니다: " + str(e)


@app.route("/delete_user", methods=["POST"])
def delete_user():
    if "user" not in session:
        return redirect("/login")

    current_user = session["user"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM users WHERE username=?",
        (current_user,)
    )

    conn.commit()
    conn.close()

    session.clear()

    return redirect("/register")


if __name__ == "__main__":
    app.run(debug=True, port=5500)