# Adaptive-Quiz-System
📌 Overview

Adaptive Quiz System is an AI-powered web application developed using Flask, Python, SQLite, and Machine Learning concepts to create personalized quizzes based on user performance and difficulty levels. The system dynamically adjusts quiz questions according to the student's answers and learning progress.

The project is designed to improve learning efficiency by providing intelligent question selection, performance tracking, and role-based quiz management for students and teachers.

🎯 Features
👨‍🎓 Student Features
User Registration & Login
Attempt Adaptive Quizzes
Dynamic Question Difficulty Adjustment
View Quiz Results & Scores
Performance Tracking Dashboard

👨‍🏫 Teacher Features
Create and Manage Quizzes
Add Questions with Difficulty Levels
Monitor Student Performance
View Quiz Reports & Results
Manage Quiz Content

🤖 AI & Adaptive Learning Features
Intelligent Question Selection
Difficulty-Based Quiz Generation
Topic-Based Clustering
Personalized Learning Experience
Performance-Based Adaptation

🛠 Technologies Used

💻 Programming Language
Python

🌐 Web Framework
Flask

🗄 Database
SQLite

📚 Machine Learning & Data Processing
Scikit-learn
Pandas
NumPy

🔐 Authentication & Security
Flask-Login
Werkzeug Security

🎨 Frontend
HTML
CSS
Jinja Templates

📂 Project Structure
Adaptive-Quiz-System/
│
├── app.py
├── test.py
├── quiz_app.db
├── data.csv
├── requirements.txt
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── create_quiz.html
│   ├── dashboard_student.html
│   ├── dashboard_teacher.html
│   ├── quiz.html
│   ├── results.html
│   └── teacher_results.html
│
└── static/

⚙️ System Workflow

1️⃣ User Authentication
Users can register and log in securely.
Role-based access is implemented for students and teachers.
2️⃣ Quiz Creation
Teachers create quizzes with multiple questions.
Questions are categorized by difficulty levels.
3️⃣ Adaptive Quiz Logic
The system adjusts question difficulty based on user responses.
Performance tracking helps personalize the learning experience.
4️⃣ Machine Learning Integration
TF-IDF Vectorization is used for text processing.
KMeans clustering is used for topic-based grouping and quiz adaptation.
5️⃣ Result Analysis
Student scores and quiz performance are stored in the database.
Teachers can monitor quiz statistics and student progress.

📊 Key Functionalities
Adaptive Learning System
Difficulty-Based Question Selection
Quiz Performance Analysis
Student & Teacher Dashboards
Secure Authentication System
Database Management
Machine Learning-Based Topic Clustering

🚀 Installation & Setup
Clone the Repository
git clone <repository-url>
cd Adaptive-Quiz-System
Install Dependencies
pip install -r requirements.txt
Run the Application
python app.py
Open in Browser
http://127.0.0.1:5000

📈 Future Improvements
Real-Time Quiz Analytics
AI-Based Recommendation System
Leaderboard System
Online Multiplayer Quizzes
Advanced Machine Learning Models
Cloud Deployment
Mobile Responsive UI

✅ Conclusion
The Adaptive Quiz System demonstrates practical implementation of web development, database management, authentication, machine learning concepts, and adaptive learning techniques. The project highlights skills in Python, Flask, SQLite, AI-based quiz generation, and intelligent educational systems suitable for Software Development and Data Analytics roles.
