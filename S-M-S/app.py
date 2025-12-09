from __future__ import annotations
import os
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, send_from_directory, flash
)
from werkzeug.utils import secure_filename
from PIL import Image

from db import get_db, init_db
from utils.pdf_utils import generate_tc_pdf

ADMIN_USER = "admin@gptplpt"
ADMIN_PASS = "gpt155"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
TC_DIR = os.path.join(BASE_DIR, "static", "tc")

# Ensure folders
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TC_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "change-this-in-production"

# Initialize database on startup
init_db()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def save_photo(file_storage) -> str | None:
    if not file_storage:
        return None
    filename = secure_filename(file_storage.filename)
    if not filename:
        return None
    try:
        img = Image.open(file_storage.stream)
        img = img.convert("RGB")
        max_side = 600
        ratio = min(max_side / img.width, max_side / img.height, 1)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))
        path = os.path.join(UPLOAD_DIR, filename)
        img.save(path, format="JPEG", quality=90)
        rel = os.path.relpath(path, BASE_DIR).replace("\\", "/")
        return rel
    except Exception:
        return None


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


# --------------------- Students ---------------------
@app.route('/students')
@login_required
def students():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students ORDER BY id DESC")
    students = cur.fetchall()
    conn.close()
    return render_template('students.html', students=students)


@app.route('/students/add', methods=['POST'])
@login_required
def add_student():
    f = request.form
    photo_rel = save_photo(request.files.get('photo'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO students(
            full_name, branch, year_of_joining, dob, polycet_rank,
            admission_based_on, aadhar_student, aadhar_parent,
            mobile_student, mobile_parent, status, photo_path
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            f.get('full_name'), f.get('branch'), int(f.get('year_of_joining')),
            f.get('dob'), f.get('polycet_rank'), f.get('admission_based_on'),
            f.get('aadhar_student'), f.get('aadhar_parent'),
            f.get('mobile_student'), f.get('mobile_parent'),
            f.get('status') or 'Active', photo_rel
        )
    )
    conn.commit()
    conn.close()
    flash('Student added.')
    return redirect(url_for('students'))


@app.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'POST':
        f = request.form
        photo_rel = save_photo(request.files.get('photo'))
        cur.execute("SELECT photo_path FROM students WHERE id=?", (student_id,))
        old = cur.fetchone()
        photo_final = photo_rel or (old[0] if old else None)

        cur.execute(
            """
            UPDATE students SET
                full_name=?, branch=?, year_of_joining=?, dob=?, polycet_rank=?,
                admission_based_on=?, aadhar_student=?, aadhar_parent=?,
                mobile_student=?, mobile_parent=?, status=?, photo_path=?
            WHERE id=?
            """,
            (
                f.get('full_name'), f.get('branch'), int(f.get('year_of_joining')),
                f.get('dob'), f.get('polycet_rank'), f.get('admission_based_on'),
                f.get('aadhar_student'), f.get('aadhar_parent'),
                f.get('mobile_student'), f.get('mobile_parent'),
                f.get('status') or 'Active', photo_final, student_id
            )
        )
        conn.commit()
        conn.close()
        flash('Student updated.')
        return redirect(url_for('students'))

    cur.execute("SELECT * FROM students WHERE id=?", (student_id,))
    s = cur.fetchone()
    conn.close()
    return render_template('edit_student.html', s=s)


@app.route('/tc/<int:student_id>')
@login_required
def tc_form(student_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE id=?", (student_id,))
    s = cur.fetchone()
    conn.close()
    return render_template('tc_form.html', s=s)


@app.route('/tc/<int:student_id>/generate', methods=['POST'])
@login_required
def tc_generate(student_id):
    completion_date = request.form.get('completion_date')
    if not completion_date:
        flash('Completion date is required.')
        return redirect(url_for('tc_form', student_id=student_id))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE id=?", (student_id,))
    s = cur.fetchone()
    conn.close()

    pdf_rel = generate_tc_pdf(s, completion_date, base_dir=BASE_DIR)
    flash('TC generated.')
    return redirect(url_for('serve_tc', filename=os.path.basename(pdf_rel)))


@app.route('/tc/files/<path:filename>')
@login_required
def serve_tc(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static', 'tc'), filename, as_attachment=False)


# --------------------- Inventory ---------------------
@app.route('/inventory')
@login_required
def inventory():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory ORDER BY id DESC")
    items = cur.fetchall()
    conn.close()
    return render_template('inventory.html', items=items)


@app.route('/inventory/add', methods=['POST'])
@login_required
def add_inventory():
    f = request.form
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO inventory(item_name, quantity, location) VALUES (?,?,?)",
        (f.get('item_name'), int(f.get('quantity', 0)), f.get('location'))
    )
    conn.commit()
    conn.close()
    flash('Item added.')
    return redirect(url_for('inventory'))


@app.route('/inventory/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_inventory(item_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'POST':
        f = request.form
        cur.execute(
            "UPDATE inventory SET item_name=?, quantity=?, location=? WHERE id=?",
            (f.get('item_name'), int(f.get('quantity', 0)), f.get('location'), item_id)
        )
        conn.commit()
        conn.close()
        flash('Item updated.')
        return redirect(url_for('inventory'))

    cur.execute("SELECT * FROM inventory WHERE id=?", (item_id,))
    i = cur.fetchone()
    conn.close()
    return render_template('edit_inventory.html', i=i)


# --------------------- Exams & Marks ---------------------
@app.route('/exams')
@login_required
def exams_index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM exams ORDER BY id DESC")
    exams = cur.fetchall()
    conn.close()
    return render_template('exams/index.html', exams=exams)


@app.route('/exams/add', methods=['POST'])
@login_required
def add_exam():
    f = request.form
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO exams(title, exam_date) VALUES (?,?)",
        (f.get('title'), f.get('exam_date'))
    )
    conn.commit()
    conn.close()
    flash('Exam created.')
    return redirect(url_for('exams_index'))


@app.route('/exams/<int:exam_id>/marks', methods=['GET', 'POST'])
@login_required
def enter_marks(exam_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM exams WHERE id=?", (exam_id,))
    exam = cur.fetchone()
    if not exam:
        conn.close()
        flash('Exam not found.')
        return redirect(url_for('exams_index'))

    if request.method == 'POST':
        cur.execute("SELECT id FROM students")
        for row in cur.fetchall():
            sid = row['id']
            internal = int(request.form.get(f'internal_{sid}', 0) or 0)
            external = int(request.form.get(f'external_{sid}', 0) or 0)
            total = internal + external
            cur.execute(
                """
                INSERT INTO marks(student_id, exam_id, internal, external, total)
                VALUES (?,?,?,?,?)
                ON CONFLICT(student_id, exam_id) DO UPDATE SET
                  internal=excluded.internal,
                  external=excluded.external,
                  total=excluded.total
                """,
                (sid, exam_id, internal, external, total)
            )
        conn.commit()
        conn.close()
        flash('Marks saved.')
        return redirect(url_for('exams_index'))

    cur.execute("SELECT * FROM students ORDER BY id")
    students = [dict(row) for row in cur.fetchall()]
    for s in students:
        cur.execute(
            "SELECT internal, external, total FROM marks WHERE student_id=? AND exam_id=?",
            (s['id'], exam_id)
        )
        m = cur.fetchone()
        if m:
            s.update({"internal": m['internal'], "external": m['external'], "total": m['total']})

    conn.close()
    return render_template('exams/enter_marks.html', exam=exam, students=students)


if __name__ == '__main__':
    app.run(debug=True)
