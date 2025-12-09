import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'sms.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            branch TEXT NOT NULL,
            year_of_joining INTEGER NOT NULL,
            dob TEXT NOT NULL,
            polycet_rank TEXT,
            admission_based_on TEXT NOT NULL,
            aadhar_student TEXT,
            aadhar_parent TEXT,
            mobile_student TEXT,
            mobile_parent TEXT,
            status TEXT NOT NULL DEFAULT 'Active',
            photo_path TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            location TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            exam_date TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            exam_id INTEGER NOT NULL,
            internal INTEGER NOT NULL DEFAULT 0,
            external INTEGER NOT NULL DEFAULT 0,
            total INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(exam_id) REFERENCES exams(id) ON DELETE CASCADE,
            UNIQUE(student_id, exam_id)
        )
        """
    )

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM inventory")
    if cur.fetchone()[0] == 0:
        seed = [
            ("Branches", 3, "Academic"),
            ("Chairs", 240, "All Classrooms"),
            ("CCTV Cameras", 28, "Campus"),
            ("Fans", 120, "All Classrooms"),
            ("AC Units", 12, "Labs & Offices"),
            ("Desktops", 85, "Computer Labs"),
            ("CPU Towers", 60, "Computer Labs"),
            ("Keyboards", 90, "Computer Labs"),
            ("Mice", 90, "Computer Labs"),
            ("Boards", 18, "Classrooms"),
        ]
        cur.executemany(
            "INSERT INTO inventory(item_name, quantity, location) VALUES (?,?,?)",
            seed
        )
        conn.commit()

    conn.close()
