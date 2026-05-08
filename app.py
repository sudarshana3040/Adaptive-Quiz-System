import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
import random
# --- App Initialization & Configuration ---

app = Flask(__name__)
app.secret_key = 'a_very_secret_and_secure_key_for_this_app'
basedir = os.path.abspath(os.path.dirname(__file__))

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'quiz_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database and Login Manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Constants
QUIZ_LENGTH = 5

# --- Database Models ---

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    max_questions = db.Column(db.Integer, nullable=False, default=30)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='quizzes')
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    op1 = db.Column(db.String(100), nullable=False)
    op2 = db.Column(db.String(100), nullable=False)
    op3 = db.Column(db.String(100), nullable=False)
    op4 = db.Column(db.String(100), nullable=False)
    ans = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    topic_id = db.Column(db.Integer, nullable=True)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    user = db.relationship('User', backref='results')
    # Correctly defines the relationship and cascade rule from the "child" side
    quiz = db.relationship('Quiz', backref=db.backref('results', cascade="all, delete-orphan"))

# --- Flask-Login User Loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Authentication Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'warning')
            return redirect(url_for('register'))
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Core Application Routes ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'teacher':
        quizzes = Quiz.query.filter_by(author_id=current_user.id).all()
        return render_template('dashboard_teacher.html', quizzes=quizzes)
    else: # Student
        quizzes = Quiz.query.all()
        return render_template('dashboard_student.html', quizzes=quizzes)

# --- Teacher Routes ---
@app.route('/quiz/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if current_user.role != 'teacher': return redirect(url_for('dashboard'))
    if request.method == 'POST':
        title, file = request.form['title'], request.files['file']
        max_questions = int(request.form['max_questions'])
        if not title or not file or not file.filename.endswith('.csv'):
            flash('Please provide a title and a valid CSV file.', 'warning')
            return redirect(request.url)
        try:
            df = pd.read_csv(file.stream)
            if len(df.columns) != 7:
                flash(f"Error: Your CSV must have 7 columns, but it has {len(df.columns)}. Please check the file.", "danger")
                return redirect(request.url)
            df.columns = ['question', 'op1', 'op2', 'op3', 'op4', 'ans', 'difficulty']

            # this for checking emt columns or rows in csv file
            for index, row in df.iterrows():
                if row.isnull().any():
                    empty_column = row[row.isnull()].index[0]
                    error_message = f"Error on spreadsheet Row {index + 2}: The column '{empty_column}' cannot be empty. Please fix your file and re-upload."
                    flash(error_message, 'danger')
                    return redirect(request.url)
            
            # --- NEW CLUSTERING LOGIC ---
            question_texts = df['question'].tolist()
            
            # 1. Vectorize: Convert question text into numerical vectors
            vectorizer = TfidfVectorizer(stop_words='english')
            X = vectorizer.fit_transform(question_texts)

            # 2. Cluster: Group the questions into topics
            # We'll aim for about 5 topics, but no more than the number of questions.
            num_clusters = min(5, len(question_texts))
            
            if num_clusters > 0:
                kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
                kmeans.fit(X)
                # Add the cluster labels (topic_id) back to our dataframe
                df['topic_id'] = kmeans.labels_
            else:
                df['topic_id'] = 0 # Default topic if there are no questions

            new_quiz = Quiz(title=title, max_questions=max_questions, author_id=current_user.id)
            db.session.add(new_quiz); db.session.commit()
            for _, row in df.iterrows():
                question = Question(
                                question_text=row['question'], op1=row['op1'], op2=row['op2'], op3=row['op3'],
                                op4=row['op4'], ans=row['ans'], difficulty=row['difficulty'],
                                quiz_id=new_quiz.id, topic_id=int(row['topic_id'])
                            )
                db.session.add(question)

            db.session.commit()
            flash('Quiz created successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')
            return redirect(request.url)
    return render_template('create_quiz.html')

@app.route('/quiz/<int:quiz_id>/delete', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.author_id != current_user.id: return redirect(url_for('dashboard'))
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/quiz/<int:quiz_id>/results')
@login_required
def view_quiz_results(quiz_id):
    if current_user.role != 'teacher': return redirect(url_for('dashboard'))
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.author_id != current_user.id:
        flash("You are not authorized to view these results.", "danger")
        return redirect(url_for('dashboard'))
    results = Result.query.filter_by(quiz_id=quiz.id).order_by(Result.score.desc()).all()
    return render_template('teacher_results.html', quiz=quiz, results=results)

# --- Student Routes ---
@app.route('/quiz/<int:quiz_id>')
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    session['quiz_id'] = quiz.id
    session['quiz_length'] = min(quiz.max_questions, len(quiz.questions))
    session['seen_indices'] = []
    session['user_score'] = 0
    session['current_difficulty'] = 2 
    session['user_answers'] = {}
    session['current_topic_id'] = None 
    session['seen_topics'] = []      
    return redirect(url_for('quiz_question'))

@app.route('/quiz/question')
@login_required
def quiz_question():
    if 'quiz_id' not in session: 
        return redirect(url_for('dashboard'))

    quiz_id, seen_indices = session['quiz_id'], session.get('seen_indices', [])

    if len(seen_indices) >= session['quiz_length']: 
        return redirect(url_for('submit_quiz'))
    
    all_questions = Question.query.filter_by(quiz_id=quiz_id).all()
    current_topic = session.get('current_topic_id')

    if current_topic is None:
        all_topics = sorted(list(set([q.topic_id for q in all_questions])))
        seen_topics = session.get('seen_topics', [])
        available_topics = [t for t in all_topics if t not in seen_topics]
        
        # If we've run out of new topics, just allow any topic
        if not available_topics:
            available_topics = all_topics
            
        current_topic = random.choice(available_topics)
        session['current_topic_id'] = current_topic

    # 2. Select a question from the chosen topic, applying difficulty logic
    topic_questions = [q for q in all_questions if q.topic_id == current_topic and q.id not in seen_indices]
    
    # If there are no more questions in this topic, switch to another topic
    if not topic_questions:
        session.pop('current_topic_id', None) # Clear the current topic
        return redirect(url_for('quiz_question')) # Re-run the selection logic

    # Apply the simple Easy/Medium/Hard difficulty logic WITHIN the topic
    def get_difficulty_name(num): return {1: 'Easy', 2: 'Medium', 3: 'Hard'}.get(num)
    current_difficulty_num = session['current_difficulty']
    target_difficulty = get_difficulty_name(current_difficulty_num)
    
    target_questions = [q for q in topic_questions if q.difficulty == target_difficulty]
    if not target_questions: # Fallback if no questions at current difficulty
        target_questions = topic_questions

    next_question = random.choice(target_questions)

    return render_template('quiz.html', 
                           question=next_question, 
                           question_num=len(seen_indices) + 1, 
                           total_questions=session['quiz_length'])

@app.route('/quiz/answer', methods=['POST'])
@login_required
def quiz_answer():
    if 'quiz_id' not in session: 
        return redirect(url_for('dashboard'))

    user_answer = request.form.get('answer')
    question_id = int(request.form.get('question_id'))
    question = Question.query.get(question_id)
    
    user_answers = session.get('user_answers', {}); user_answers[str(question_id)] = user_answer; session['user_answers'] = user_answers
    seen = session.get('seen_indices', []); seen.append(question_id); session['seen_indices'] = seen
    
    if str(user_answer) == str(question.ans):
        session['user_score'] = session.get('user_score', 0) + 1
        session['current_difficulty'] = min(3, session['current_difficulty'] + 1)
    else:
        session['current_difficulty'] = max(1, session['current_difficulty'] - 1)
        seen_topics = session.get('seen_topics', [])
        if question.topic_id not in seen_topics:
            seen_topics.append(question.topic_id)
        session['seen_topics'] = seen_topics
        # Clear the current topic to force selection of a new one
        session.pop('current_topic_id', None)
    return redirect(url_for('quiz_question'))
    
@app.route('/quiz/submit')
@login_required
def submit_quiz():
    if 'quiz_id' not in session: return redirect(url_for('dashboard'))
    new_result = Result(user_id=current_user.id, quiz_id=session['quiz_id'], score=session['user_score'], total=session['quiz_length'])
    db.session.add(new_result); db.session.commit()
    
    questions_for_review = []
    for q_id in session.get('seen_indices', []):
        question = Question.query.get(q_id)
        if question:
            questions_for_review.append({'question_text': question.question_text, 'op1': question.op1, 'op2': question.op2, 'op3': question.op3, 'op4': question.op4, 'ans': question.ans, 'user_answer': session.get('user_answers', {}).get(str(q_id), "Not Answered")})
    
    for key in ['quiz_id', 'quiz_length', 'seen_indices', 'user_score', 'current_difficulty', 'user_answers']: session.pop(key, None)
    return render_template('results.html', score=new_result.score, total=new_result.total, questions=questions_for_review)

# --- Main Execution ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)

