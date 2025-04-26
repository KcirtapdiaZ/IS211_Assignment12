import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key


# Dynamically get the directory where the app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(os.path.dirname(__file__), 'hw13.db')


def get_db_connection():
    """Create a new SQLite database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enable named access for columns
    return conn


def init_db():
    """Initialize the SQLite database using schema.sql."""
    try:
        # Check if schema.sql file exists
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if not os.path.exists(schema_path):
            print("schema.sql file not found!")
            return
        
        # Connect to the SQLite database (it will create the file if it doesn't exist)
        with sqlite3.connect(DATABASE) as conn:
            # Execute schema.sql to initialize tables
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
                
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

@app.route('/')
def index():
    """Redirect to the login page when visiting the root URL."""
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'password':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    students = conn.execute('SELECT * FROM student').fetchall()
    quizzes = conn.execute('SELECT * FROM quiz').fetchall()
    conn.close()
    return render_template('dashboard.html', students=students, quizzes=quizzes)


@app.route('/student/add', methods=['GET', 'POST'])
def add_student():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        conn = get_db_connection()
        conn.execute('INSERT INTO student (first_name, last_name) VALUES (?, ?)', (first_name, last_name))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    return render_template('add_student.html')


@app.route('/quiz/add', methods=['GET', 'POST'])
def add_quiz():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        subject = request.form['subject']
        num_questions = request.form['num_questions']
        quiz_date = request.form['quiz_date']
        conn = get_db_connection()
        conn.execute('INSERT INTO quiz (subject, num_questions, quiz_date) VALUES (?, ?, ?)',
                     (subject, num_questions, quiz_date))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    return render_template('add_quiz.html')


@app.route('/student/<int:student_id>')
def view_results(student_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    results = conn.execute('''
        SELECT quiz.id AS quiz_id, quiz.subject, result.score 
        FROM result 
        JOIN quiz ON result.quiz_id = quiz.id 
        WHERE result.student_id = ?
    ''', (student_id,)).fetchall()
    conn.close()
    return render_template('view_results.html', results=results)


@app.route('/results/add', methods=['GET', 'POST'])
def add_result():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    students = conn.execute('SELECT * FROM student').fetchall()
    quizzes = conn.execute('SELECT * FROM quiz').fetchall()
    conn.close()

    if request.method == 'POST':
        student_id = request.form['student_id']
        quiz_id = request.form['quiz_id']
        score = request.form['score']
        conn = get_db_connection()
        conn.execute('INSERT INTO result (student_id, quiz_id, score) VALUES (?, ?, ?)',
                     (student_id, quiz_id, score))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    return render_template('add_result.html', students=students, quizzes=quizzes)


if __name__ == '__main__':
    # Initialize the database before starting the app
    init_db()
    app.run(debug=True)
