import flask
from flask_cors import CORS
import sqlite3
import os
import csv
import io
from datetime import datetime, timedelta

app = flask.Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smart-library-multi-portal-secret-2026")
CORS(app, resources={r"/*": {"origins": "*"}})

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library.db')
FINE_PER_DAY = 5
LOAN_DAYS = 7


def calculate_fine(due_date_str):
    """Calculate overdue fine at Rs 5/day past the due date."""
    if not due_date_str:
        return 0
    try:
        due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        diff_days = (today - due).days
        return diff_days * FINE_PER_DAY if diff_days > 0 else 0
    except Exception:
        return 0


SEED_USERS = [
    # Multiple Admins
    ('admin', 'Chief Librarian Sharma', 'admin', 'admin123', 'chief.admin@university.edu', 'Library Administration', 'ADM-001'),
    ('librarian_head', 'Dr. Kavita Verma', 'admin', 'admin123', 'kavita.verma@university.edu', 'Central Cataloging', 'ADM-002'),
    ('dean_library', 'Prof. Rajesh Iyer', 'admin', 'admin123', 'dean.library@university.edu', 'Academic Council', 'ADM-003'),
    # Multiple Students
    ('Rahul', 'Rahul Sharma', 'student', 'user123', 'rahul.cs@student.edu', 'B.Tech CSE', 'STU-2026-101'),
    ('Priya', 'Priya Patel', 'student', 'user123', 'priya.ai@student.edu', 'B.Tech AI & DS', 'STU-2026-102'),
    ('Amit', 'Amit Kumar', 'student', 'user123', 'amit.cyber@student.edu', 'B.Tech Cyber Security', 'STU-2026-103'),
    ('Sneha', 'Sneha Gupta', 'student', 'user123', 'sneha.it@student.edu', 'B.Tech Information Tech', 'STU-2026-104'),
    ('Rohan', 'Rohan Deshmukh', 'student', 'user123', 'rohan.ece@student.edu', 'B.Tech Electronics', 'STU-2026-105'),
    ('Ananya', 'Ananya Singh', 'student', 'user123', 'ananya.mca@student.edu', 'MCA', 'STU-2026-106'),
    ('Vikram', 'Vikram Rathore', 'student', 'user123', 'vikram.cs@student.edu', 'B.Tech CSE', 'STU-2026-107'),
    ('Neha', 'Neha Reddy', 'student', 'user123', 'neha.ds@student.edu', 'M.Tech Data Science', 'STU-2026-108'),
]

SEED_50_BOOKS = [
    # 1-10: Programming & Software Engineering
    ('978-8177229967', 'Core Python Programming', 'R. Nageswara Rao', 'Programming', 'Available', '', '', '', ''),
    ('978-0132350884', 'Clean Code: A Handbook of Agile Software Craftsmanship', 'Robert C. Martin', 'Software Engineering', 'Available', '', '', '', ''),
    ('978-0134685991', 'Effective Java (3rd Edition)', 'Joshua Bloch', 'Programming', 'Available', '', '', '', ''),
    ('978-0131103627', 'The C Programming Language', 'Brian W. Kernighan & Dennis Ritchie', 'Programming', 'Available', '', '', '', ''),
    ('978-0321563842', 'The C++ Programming Language', 'Bjarne Stroustrup', 'Programming', 'Available', '', '', '', ''),
    ('978-1491952023', 'JavaScript: The Definitive Guide', 'David Flanagan', 'Web Development', 'Available', '', '', '', ''),
    ('978-1492056355', 'Fluent Python: Clear, Concise, and Effective Programming', 'Luciano Ramalho', 'Programming', 'Available', '', '', '', ''),
    ('978-0201616224', 'The Pragmatic Programmer', 'Andrew Hunt & David Thomas', 'Software Engineering', 'Available', '', '', '', ''),
    ('978-0201633610', 'Design Patterns: Elements of Reusable OO Software', 'Erich Gamma (GoF)', 'Software Engineering', 'Available', '', '', '', ''),
    ('978-0134494166', 'Clean Architecture', 'Robert C. Martin', 'Software Engineering', 'Available', '', '', '', ''),

    # 11-18: Data Structures & Algorithms
    ('978-0070144750', 'Data Structures With C (Schaum Series)', 'Seymour Lipschutz', 'Data Structures', 'Available', '', '', '', ''),
    ('978-0262033848', 'Introduction to Algorithms (CLRS)', 'Thomas H. Cormen', 'Algorithms', 'Available', '', '', '', ''),
    ('978-8193245279', 'Data Structures and Algorithms Made Easy', 'Narasimha Karumanchi', 'Data Structures', 'Issued', 'Amit', '2026-09-25', '2026-10-02', ''),
    ('978-1617292231', 'Grokking Algorithms', 'Aditya Bhargava', 'Algorithms', 'Available', '', '', '', ''),
    ('978-0321573513', 'Algorithms (4th Edition)', 'Robert Sedgewick & Kevin Wayne', 'Algorithms', 'Available', '', '', '', ''),
    ('978-0984782857', 'Cracking the Coding Interview', 'Gayle Laakmann McDowell', 'Interview Prep', 'Available', '', '', '', ''),
    ('978-1848000698', 'The Algorithm Design Manual', 'Steven S. Skiena', 'Algorithms', 'Available', '', '', '', ''),
    ('978-3319725468', 'Guide to Competitive Programming', 'Antti Laaksonen', 'Algorithms', 'Available', '', '', '', ''),

    # 19-26: Operating Systems, Computer Networks & Architecture
    ('978-1119800361', 'Operating System Concepts (10th Edition)', 'Abraham Silberschatz', 'Operating Systems', 'Issued', 'Rahul', '2026-08-15', '2026-08-22', ''),
    ('978-0133591620', 'Modern Operating Systems', 'Andrew S. Tanenbaum', 'Operating Systems', 'Available', '', '', '', ''),
    ('978-0132126953', 'Computer Networks (5th Edition)', 'Andrew S. Tanenbaum', 'Computer Networks', 'Available', '', '', '', ''),
    ('978-0133594140', 'Computer Networking: A Top-Down Approach', 'James F. Kurose & Keith W. Ross', 'Computer Networks', 'Available', '', '', '', ''),
    ('978-0073380681', 'Data Communications and Networking', 'Behrouz A. Forouzan', 'Computer Networks', 'Available', '', '', '', ''),
    ('978-0128122754', 'Computer Architecture: A Quantitative Approach', 'John L. Hennessy & David A. Patterson', 'Computer Architecture', 'Available', '', '', '', ''),
    ('978-9332585607', 'Computer System Architecture', 'M. Morris Mano', 'Computer Architecture', 'Available', '', '', '', ''),
    ('978-1593275679', 'How Linux Works: What Every Superuser Should Know', 'Brian Ward', 'Operating Systems', 'Available', '', '', '', ''),

    # 27-34: AI, Machine Learning & Data Science
    ('978-1492032649', 'Hands-On Machine Learning with Scikit-Learn & TensorFlow', 'Aurélien Géron', 'AI & Data Science', 'Issued', 'Priya', '2026-09-24', '2026-10-01', ''),
    ('978-0134610993', 'Artificial Intelligence: A Modern Approach', 'Stuart Russell & Peter Norvig', 'AI & Data Science', 'Available', '', '', '', ''),
    ('978-0262035613', 'Deep Learning', 'Ian Goodfellow & Yoshua Bengio', 'AI & Data Science', 'Available', '', '', '', ''),
    ('978-1492041139', 'Data Science from Scratch with Python', 'Joel Grus', 'AI & Data Science', 'Available', '', '', '', ''),
    ('978-1098104030', 'Python for Data Analysis (Pandas & NumPy)', 'Wes McKinney', 'AI & Data Science', 'Available', '', '', '', ''),
    ('978-0387848570', 'The Elements of Statistical Learning', 'Trevor Hastie & Robert Tibshirani', 'AI & Data Science', 'Available', '', '', '', ''),
    ('978-1617296864', 'Deep Learning with Python', 'François Chollet', 'AI & Data Science', 'Available', '', '', '', ''),
    ('978-1098113407', 'Natural Language Processing with Transformers', 'Lewis Tunstall', 'AI & Data Science', 'Available', '', '', '', ''),

    # 35-40: Databases, Cloud & DevOps
    ('978-0078022159', 'Database System Concepts (7th Edition)', 'Abraham Silberschatz & Henry F. Korth', 'Database Systems', 'Available', '', '', '', ''),
    ('978-0136086208', 'Fundamentals of Database Systems', 'Ramez Elmasri & Shamkant B. Navathe', 'Database Systems', 'Available', '', '', '', ''),
    ('978-1449373320', 'Designing Data-Intensive Applications', 'Martin Kleppmann', 'Database Systems', 'Available', '', '', '', ''),
    ('978-1492056812', 'Kubernetes: Up and Running', 'Kelsey Hightower & Brendan Burns', 'Cloud & DevOps', 'Available', '', '', '', ''),
    ('978-1617294761', 'Docker in Action', 'Jeff Nickoloff', 'Cloud & DevOps', 'Available', '', '', '', ''),
    ('978-1736049112', 'System Design Interview: An Insider Guide', 'Alex Xu', 'Software Engineering', 'Available', '', '', '', ''),

    # 41-45: Cybersecurity & Cryptography
    ('978-1118026472', 'The Web Application Hacker Handbook', 'Dafydd Stuttard & Marcus Pinto', 'Cybersecurity', 'Available', '', '', '', ''),
    ('978-0134444284', 'Cryptography and Network Security', 'William Stallings', 'Cybersecurity', 'Available', '', '', '', ''),
    ('978-1593271442', 'Hacking: The Art of Exploitation', 'Jon Erickson', 'Cybersecurity', 'Available', '', '', '', ''),
    ('978-1119795667', 'Blue Team Handbook: SOC, SIEM, and Threat Hunting', 'Don Murdoch', 'Cybersecurity', 'Available', '', '', '', ''),
    ('978-1593275907', 'Black Hat Python: Python Programming for Pentesters', 'Justin Seitz', 'Cybersecurity', 'Available', '', '', '', ''),

    # 46-50: Engineering Mathematics, Compiler Design & Aptitude
    ('978-8174091956', 'Higher Engineering Mathematics', 'B.S. Grewal', 'Mathematics & Aptitude', 'Available', '', '', '', ''),
    ('978-0073383095', 'Discrete Mathematics and Its Applications', 'Kenneth H. Rosen', 'Mathematics & Aptitude', 'Available', '', '', '', ''),
    ('978-8121924986', 'Quantitative Aptitude for Competitive Examinations', 'R.S. Aggarwal', 'Mathematics & Aptitude', 'Available', '', '', '', ''),
    ('978-0321486813', 'Compilers: Principles, Techniques, and Tools (Dragon Book)', 'Alfred V. Aho & Jeffrey D. Ullman', 'Computer Science', 'Available', '', '', '', ''),
    ('978-0393929720', 'Introduction to the Theory of Computation', 'Michael Sipser', 'Computer Science', 'Available', '', '', '', ''),
]


def init_db():
    """Initialize SQLite tables for Users (Multi-Student & Multi-Admin), Books (50+ Catalog), Requests, and Transactions."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 1. Users Table (Multi-Admin & Multi-Student)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT DEFAULT '',
                department TEXT DEFAULT '',
                roll_no TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. Books Inventory & Loan Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isbn TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available',
                student TEXT DEFAULT '',
                issue_date TEXT DEFAULT '',
                due_date TEXT DEFAULT '',
                renew_count INTEGER DEFAULT 0,
                reserved_by TEXT DEFAULT ''
            )
        ''')

        cursor.execute("PRAGMA table_info(books)")
        book_cols = [c[1] for c in cursor.fetchall()]
        if 'reserved_by' not in book_cols:
            cursor.execute("ALTER TABLE books ADD COLUMN reserved_by TEXT DEFAULT ''")

        # 3. Student Advance Bookings & Issue Requests Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER DEFAULT 0,
                student TEXT NOT NULL,
                book_title TEXT NOT NULL,
                request_type TEXT NOT NULL,
                preferred_date TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Pending',
                admin_by TEXT DEFAULT '',
                admin_note TEXT DEFAULT '',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute("PRAGMA table_info(book_requests)")
        req_cols = [c[1] for c in cursor.fetchall()]
        for col_name, col_def in [
            ('book_id', 'INTEGER DEFAULT 0'),
            ('preferred_date', "TEXT DEFAULT ''"),
            ('admin_by', "TEXT DEFAULT ''"),
            ('admin_note', "TEXT DEFAULT ''")
        ]:
            if col_name not in req_cols:
                cursor.execute(f"ALTER TABLE book_requests ADD COLUMN {col_name} {col_def}")

        # 4. Circulation Transactions & Fine Audit Log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                book_title TEXT NOT NULL,
                student TEXT NOT NULL,
                action TEXT NOT NULL,
                fine_paid INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Seed Multi-Admin & Multi-Student Users
        for u in SEED_USERS:
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, full_name, role, password, email, department, roll_no)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', u)

        # Seed 50 Academic Books
        cursor.execute('SELECT title FROM books')
        existing_titles = {row[0].lower() for row in cursor.fetchall()}

        for b in SEED_50_BOOKS:
            if b[1].lower() not in existing_titles:
                cursor.execute('''
                    INSERT INTO books (isbn, title, author, category, status, student, issue_date, due_date, reserved_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', b)

        # Seed initial sample advance booking requests if book_requests is empty
        cursor.execute('SELECT COUNT(*) FROM book_requests')
        if cursor.fetchone()[0] == 0:
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            next_week = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
            cursor.execute('''
                INSERT INTO book_requests (book_id, student, book_title, request_type, preferred_date, status, admin_by, admin_note)
                VALUES
                (2, 'Sneha', 'Clean Code: A Handbook of Agile Software Craftsmanship', 'Book Issue Request', ?, 'Pending', '', 'Needed for Software Engineering Lab'),
                (12, 'Rohan', 'Introduction to Algorithms (CLRS)', 'Advance Booking', ?, 'Pending', '', 'Advance booking for mid-term exam prep'),
                (19, 'Ananya', 'Operating System Concepts (10th Edition)', 'Advance Booking', ?, 'Pending', '', 'Queueing for next available copy')
            ''', (tomorrow, next_week, next_week))

        conn.commit()


# Initialize database on startup
init_db()


@app.route('/')
def index():
    return flask.render_template('portal.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    data = flask.request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    role = (data.get('role') or 'student').strip().lower()

    if not username or not password:
        return flask.jsonify({'status': 'error', 'message': 'Please enter both username and password.'}), 400

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE LOWER(username) = LOWER(?) AND role = ?', (username, role))
        user_row = cursor.fetchone()

        if user_row:
            if user_row['password'] == password:
                return flask.jsonify({
                    'status': 'success',
                    'user': {
                        'id': user_row['id'],
                        'username': user_row['username'],
                        'full_name': user_row['full_name'],
                        'role': user_row['role'],
                        'department': user_row['department'],
                        'roll_no': user_row['roll_no'],
                        'email': user_row['email']
                    }
                })
            return flask.jsonify({'status': 'error', 'message': f'Incorrect password for {role} account "{username}".'}), 401

        if role == 'student' and password == 'user123':
            roll_id = f"STU-2026-{datetime.now().strftime('%H%M%S')}"
            cursor.execute('''
                INSERT INTO users (username, full_name, role, password, email, department, roll_no)
                VALUES (?, ?, 'student', 'user123', ?, 'B.Tech General', ?)
            ''', (username, username, f"{username.lower()}@student.edu", roll_id))
            conn.commit()
            return flask.jsonify({
                'status': 'success',
                'user': {
                    'id': cursor.lastrowid,
                    'username': username,
                    'full_name': username,
                    'role': 'student',
                    'department': 'B.Tech General',
                    'roll_no': roll_id,
                    'email': f"{username.lower()}@student.edu"
                }
            })

    return flask.jsonify({'status': 'error', 'message': 'Account not found or invalid credentials.'}), 401


@app.route('/api/users/register', methods=['POST'])
def register_user():
    data = flask.request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    full_name = (data.get('full_name') or username).strip()
    role = (data.get('role') or 'student').strip().lower()
    password = (data.get('password') or ('admin123' if role == 'admin' else 'user123')).strip()
    department = (data.get('department') or ('Library Admin' if role == 'admin' else 'B.Tech CSE')).strip()
    email = (data.get('email') or f"{username.lower()}@university.edu").strip()
    roll_no = (data.get('roll_no') or f"{'ADM' if role == 'admin' else 'STU'}-{datetime.now().strftime('%M%S')}").strip()

    if not username or not password:
        return flask.jsonify({'status': 'error', 'message': 'Username and password are required.'}), 400

    if role not in ('admin', 'student'):
        role = 'student'

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, full_name, role, password, email, department, roll_no)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, full_name, role, password, email, department, roll_no))
            conn.commit()
        return flask.jsonify({
            'status': 'success',
            'message': f'New {role.upper()} account "{username}" ({full_name}) saved to database!'
        })
    except sqlite3.IntegrityError:
        return flask.jsonify({'status': 'error', 'message': f'Username "{username}" already exists in database.'}), 400


@app.route('/api/state', methods=['GET'])
def get_state():
    """Return all 50+ books, requests, transactions, multi-user directory, and KPI metrics."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM books ORDER BY id ASC')
        book_rows = cursor.fetchall()

        books = []
        total_active_fines = 0
        for r in book_rows:
            fine = calculate_fine(r['due_date']) if r['status'] == 'Issued' else 0
            total_active_fines += fine
            books.append({
                'id': r['id'],
                'isbn': r['isbn'],
                'title': r['title'],
                'author': r['author'],
                'category': r['category'],
                'status': r['status'],
                'student': r['student'] or '',
                'issueDate': r['issue_date'] or '',
                'dueDate': r['due_date'] or '',
                'renewCount': r['renew_count'] or 0,
                'reservedBy': r['reserved_by'] or '',
                'fine': fine
            })

        cursor.execute('SELECT * FROM book_requests ORDER BY id DESC LIMIT 100')
        requests_list = [dict(r) for r in cursor.fetchall()]

        cursor.execute('SELECT * FROM transactions ORDER BY id DESC LIMIT 60')
        transactions = [dict(r) for r in cursor.fetchall()]

        cursor.execute('SELECT COALESCE(SUM(fine_paid), 0) FROM transactions')
        total_collected_fines = cursor.fetchone()[0]

        cursor.execute('SELECT id, username, full_name, role, email, department, roll_no, created_at FROM users ORDER BY role ASC, id ASC')
        users_list = [dict(r) for r in cursor.fetchall()]

    return flask.jsonify({
        'status': 'success',
        'books': books,
        'requests': requests_list,
        'transactions': transactions,
        'users': users_list,
        'metrics': {
            'total_books': len(books),
            'total_active_fines': total_active_fines,
            'total_collected_fines': total_collected_fines,
            'total_students': sum(1 for u in users_list if u['role'] == 'student'),
            'total_admins': sum(1 for u in users_list if u['role'] == 'admin'),
            'pending_requests': sum(1 for req in requests_list if req['status'] == 'Pending')
        }
    })


@app.route('/api/books/add', methods=['POST'])
def add_book():
    data = flask.request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    author = (data.get('author') or '').strip()
    category = (data.get('category') or 'General').strip() or 'General'
    isbn = (data.get('isbn') or '').strip() or f"978-{datetime.now().strftime('%H%M%S%f')[:10]}"

    if not title or not author:
        return flask.jsonify({'status': 'error', 'message': 'Title and author are required.'}), 400

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO books (isbn, title, author, category, status)
            VALUES (?, ?, ?, ?, 'Available')
        ''', (isbn, title, author, category))
        book_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO transactions (book_id, book_title, student, action, fine_paid)
            VALUES (?, ?, 'Admin', 'CATALOG_ADDED', 0)
        ''', (book_id, title))
        conn.commit()

    return flask.jsonify({'status': 'success', 'message': f'Book "{title}" added to SQLite database.'})


@app.route('/api/books/issue', methods=['POST'])
def issue_book():
    data = flask.request.get_json(silent=True) or {}
    book_id = data.get('book_id')
    student = (data.get('student') or '').strip()
    loan_days = int(data.get('loan_days') or LOAN_DAYS)

    if not book_id or not student:
        return flask.jsonify({'status': 'error', 'message': 'Book ID and student name are required.'}), 400

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
        book = cursor.fetchone()

        if not book:
            return flask.jsonify({'status': 'error', 'message': 'Book not found.'}), 404
        if book['status'] == 'Issued':
            return flask.jsonify({'status': 'error', 'message': 'This book is already issued.'}), 400

        issue_date = datetime.now().strftime("%Y-%m-%d")
        due_date = (datetime.now() + timedelta(days=loan_days)).strftime("%Y-%m-%d")

        cursor.execute('''
            UPDATE books
            SET status = 'Issued', student = ?, issue_date = ?, due_date = ?, renew_count = 0, reserved_by = ''
            WHERE id = ?
        ''', (student, issue_date, due_date, book_id))

        cursor.execute('''
            INSERT INTO transactions (book_id, book_title, student, action, fine_paid)
            VALUES (?, ?, ?, 'ISSUED', 0)
        ''', (book_id, book['title'], student))
        conn.commit()

    return flask.jsonify({
        'status': 'success',
        'message': f'Book "{book["title"]}" issued to {student}. Due Date: {due_date}'
    })


@app.route('/api/books/return', methods=['POST'])
def return_book():
    data = flask.request.get_json(silent=True) or {}
    book_id = data.get('book_id')

    if not book_id:
        return flask.jsonify({'status': 'error', 'message': 'Select a book to return.'}), 400

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
        book = cursor.fetchone()

        if not book:
            return flask.jsonify({'status': 'error', 'message': 'Book not found.'}), 404
        if book['status'] == 'Available':
            return flask.jsonify({'status': 'error', 'message': 'This book is already available.'}), 400

        fine = calculate_fine(book['due_date'])
        student_name = book['student']

        cursor.execute('''
            UPDATE books
            SET status = 'Available', student = '', issue_date = '', due_date = '', renew_count = 0
            WHERE id = ?
        ''', (book_id,))

        cursor.execute('''
            INSERT INTO transactions (book_id, book_title, student, action, fine_paid)
            VALUES (?, ?, ?, 'RETURNED', ?)
        ''', (book_id, book['title'], student_name, fine))
        conn.commit()

    msg = (
        f'Book returned late by {student_name}! Overdue fine collected: ₹{fine} (₹{FINE_PER_DAY}/day).'
        if fine > 0 else f'Book "{book["title"]}" returned on time by {student_name}! No fine.'
    )
    return flask.jsonify({'status': 'success', 'message': msg, 'fine': fine})


@app.route('/api/books/renew', methods=['POST'])
def renew_book():
    data = flask.request.get_json(silent=True) or {}
    book_id = data.get('book_id')

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
        book = cursor.fetchone()

        if not book or book['status'] != 'Issued':
            return flask.jsonify({'status': 'error', 'message': 'Only issued books can be renewed.'}), 400

        if (book['renew_count'] or 0) >= 2:
            return flask.jsonify({'status': 'error', 'message': 'Maximum renewal limit (2 renewals) reached.'}), 400

        try:
            current_due = datetime.strptime(book['due_date'], "%Y-%m-%d")
        except Exception:
            current_due = datetime.now()

        new_due = (max(current_due, datetime.now()) + timedelta(days=LOAN_DAYS)).strftime("%Y-%m-%d")
        new_count = (book['renew_count'] or 0) + 1

        cursor.execute('''
            UPDATE books
            SET due_date = ?, renew_count = ?
            WHERE id = ?
        ''', (new_due, new_count, book_id))

        cursor.execute('''
            INSERT INTO transactions (book_id, book_title, student, action, fine_paid)
            VALUES (?, ?, ?, 'RENEWED (+7d)', 0)
        ''', (book_id, book['title'], book['student']))
        conn.commit()

    return flask.jsonify({
        'status': 'success',
        'message': f'Loan renewed for "{book["title"]}". New Due Date: {new_due} (Renewal {new_count}/2)'
    })


@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT title FROM books WHERE id = ?', (book_id,))
        row = cursor.fetchone()
        if not row:
            return flask.jsonify({'status': 'error', 'message': 'Book not found.'}), 404

        cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
        cursor.execute('''
            INSERT INTO transactions (book_id, book_title, student, action, fine_paid)
            VALUES (?, ?, 'Admin', 'REMOVED', 0)
        ''', (book_id, row['title']))
        conn.commit()

    return flask.jsonify({'status': 'success', 'message': f'Book "{row["title"]}" deleted from database.'})


@app.route('/api/requests', methods=['POST'])
def create_request():
    """Student creates an Advance Booking or Book Issue Request."""
    data = flask.request.get_json(silent=True) or {}
    book_id = int(data.get('book_id') or 0)
    student = (data.get('student') or '').strip()
    book_title = (data.get('book_title') or '').strip()
    request_type = (data.get('request_type') or 'Advance Booking').strip()
    preferred_date = (data.get('preferred_date') or datetime.now().strftime("%Y-%m-%d")).strip()
    note = (data.get('note') or '').strip()

    if not student or not book_title:
        return flask.jsonify({'status': 'error', 'message': 'Student name and book title are required.'}), 400

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if not book_id:
            cursor.execute('SELECT id FROM books WHERE LOWER(title) = LOWER(?) LIMIT 1', (book_title,))
            match = cursor.fetchone()
            if match:
                book_id = match[0]

        cursor.execute('''
            INSERT INTO book_requests (book_id, student, book_title, request_type, preferred_date, status, admin_note)
            VALUES (?, ?, ?, ?, ?, 'Pending', ?)
        ''', (book_id, student, book_title, request_type, preferred_date, note))

        cursor.execute('''
            INSERT INTO transactions (book_id, book_title, student, action, fine_paid)
            VALUES (?, ?, ?, ?, 0)
        ''', (book_id, book_title, student, f'REQUEST: {request_type.upper()}'))
        conn.commit()

    return flask.jsonify({
        'status': 'success',
        'message': f'{request_type} for "{book_title}" sent to Admin Portal for approval!'
    })


@app.route('/api/requests/<int:req_id>/decision', methods=['POST'])
@app.route('/api/requests/<int:req_id>/status', methods=['POST'])
def decide_request(req_id):
    """Admin accepts (approves/issues) or rejects a student's advance booking or issue request."""
    data = flask.request.get_json(silent=True) or {}
    decision = (data.get('decision') or data.get('status') or 'Accepted').strip()
    admin_by = (data.get('admin_by') or 'Admin').strip()
    admin_note = (data.get('admin_note') or '').strip()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM book_requests WHERE id = ?', (req_id,))
        req = cursor.fetchone()
        if not req:
            return flask.jsonify({'status': 'error', 'message': 'Request not found.'}), 404

        book_id = req['book_id']
        student = req['student']
        book_title = req['book_title']

        book = None
        if book_id:
            cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
            book = cursor.fetchone()
        if not book:
            cursor.execute('SELECT * FROM books WHERE LOWER(title) = LOWER(?) LIMIT 1', (book_title,))
            book = cursor.fetchone()
            if book:
                book_id = book['id']

        if decision.lower() in ('accepted', 'approved', 'accept'):
            if book and book['status'] == 'Available':
                issue_date = datetime.now().strftime("%Y-%m-%d")
                due_date = (datetime.now() + timedelta(days=LOAN_DAYS)).strftime("%Y-%m-%d")
                cursor.execute('''
                    UPDATE books
                    SET status = 'Issued', student = ?, issue_date = ?, due_date = ?, renew_count = 0, reserved_by = ''
                    WHERE id = ?
                ''', (student, issue_date, due_date, book['id']))
                final_status = 'Accepted & Issued'
                note_msg = admin_note or f'Book issued on {issue_date} (Due: {due_date})'
                tx_action = f'APPROVED & ISSUED (by {admin_by})'
            else:
                if book:
                    cursor.execute('UPDATE books SET reserved_by = ? WHERE id = ?', (student, book['id']))
                final_status = 'Advance Confirmed'
                note_msg = admin_note or f'Advance booking reserved for {student}'
                tx_action = f'ADVANCE CONFIRMED (by {admin_by})'

            cursor.execute('''
                UPDATE book_requests
                SET status = ?, admin_by = ?, admin_note = ?
                WHERE id = ?
            ''', (final_status, admin_by, note_msg, req_id))

            cursor.execute('''
                INSERT INTO transactions (book_id, book_title, student, action, fine_paid)
                VALUES (?, ?, ?, ?, 0)
            ''', (book_id or 0, book_title, student, tx_action))
            conn.commit()

            return flask.jsonify({
                'status': 'success',
                'message': f'Request #{req_id} Accepted! "{book_title}" -> {final_status} for {student}.'
            })

        else:
            final_status = 'Rejected'
            note_msg = admin_note or 'Request declined by Library Admin'
            cursor.execute('''
                UPDATE book_requests
                SET status = ?, admin_by = ?, admin_note = ?
                WHERE id = ?
            ''', (final_status, admin_by, note_msg, req_id))

            cursor.execute('''
                INSERT INTO transactions (book_id, book_title, student, action, fine_paid)
                VALUES (?, ?, ?, ?, 0)
            ''', (book_id or 0, book_title, student, f'REJECTED (by {admin_by})'))
            conn.commit()

            return flask.jsonify({
                'status': 'success',
                'message': f'Request #{req_id} for "{book_title}" has been Rejected.'
            })


@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM books ORDER BY id ASC')
        rows = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'ISBN', 'Title', 'Author', 'Category', 'Status', 'Issued To', 'Reserved By', 'Issue Date', 'Due Date', 'Current Fine (INR)'])
    for r in rows:
        fine = calculate_fine(r['due_date']) if r['status'] == 'Issued' else 0
        writer.writerow([r['id'], r['isbn'], r['title'], r['author'], r['category'], r['status'], r['student'], r['reserved_by'], r['issue_date'], r['due_date'], fine])

    response = flask.make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=library_50_books_report.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5050))
    app.run(host='0.0.0.0', port=port, debug=False)
