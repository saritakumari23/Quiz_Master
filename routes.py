from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user,LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Subject, Chapter, Quiz, Question, Score
from form import LoginForm, RegistrationForm
from flask_restful import Resource, Api
from datetime import datetime
from collections import defaultdict


main = Blueprint("main", __name__)
login_manager = LoginManager()
login_manager.login_view = "main.login"


api = Api(main)

class SubjectAPI(Resource):
    def get(self):
        subjects = Subject.query.all()
        return jsonify([{"id": sub.id, "name": sub.name} for sub in subjects])

class ChapterAPI(Resource):
    def get(self, subject_id):
        chapters = Chapter.query.filter_by(subject_id=subject_id).all()
        return jsonify([{"id": chap.id, "name": chap.name} for chap in chapters])

class QuizAPI(Resource):
    def get(self, chapter_id):
        quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
        return jsonify([{"id": quiz.id, "title": quiz.title} for quiz in quizzes])

api.add_resource(SubjectAPI, '/api/subjects')
api.add_resource(ChapterAPI, '/api/subjects/<int:subject_id>/chapters')
api.add_resource(QuizAPI, '/api/chapters/<int:chapter_id>/quizzes')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already registered. Please log in or use a different email.", "warning")
            return redirect(url_for("main.register"))

        hashed_password = generate_password_hash(form.password.data, method="pbkdf2:sha256")

        # Fix: Use `form.email.data` for correct comparison
        role = "admin" if form.email.data == "admin@gmail.com" else "user"

        new_user = User(
            email=form.email.data,
            password=hashed_password,
            full_name=form.full_name.data,
            qualification=form.qualification.data,
            dob=form.dob.data,
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for("main.login"))

    return render_template("register.html", form=form)


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            
            # Redirect based on role
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            else:
                return redirect(url_for("main.user_home"))

                  
    
    
    return render_template("login.html", form=form)

@main.route("/logout")
@login_required
def logout():
    logout_user()
    
    return render_template("index.html")

@main.route("/dashboard")
@login_required
def dashboard():
    quizzes = Quiz.query.order_by(Quiz.date_of_quiz.desc()).all()  # Sorting in descending order
    attempted_quiz_ids = {score.quiz_id for score in Score.query.filter_by(user_id=current_user.id).all()}

    return render_template("dashboard.html", user=current_user, quizzes=quizzes, attempted_quiz_ids=attempted_quiz_ids)


@main.route("/quiz/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def attempt_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    if request.method == "POST":
        total_score = 0
        for question in questions:
            selected_option = request.form.get(f"question-{question.id}")
            if selected_option and int(selected_option) == question.correct_option:
                total_score += 1

        score_entry = Score(quiz_id=quiz_id, user_id=current_user.id, total_scored=total_score)
        db.session.add(score_entry)
        db.session.commit()
        
        return redirect(url_for("main.dashboard"))

    return render_template("quiz_attempt.html", quiz=quiz, questions=questions)




from collections import defaultdict

@main.route('/summary')
@login_required
def summary():
    latest_attempt = Score.query.filter_by(user_id=current_user.id).order_by(Score.timestamp.desc()).first()

    if not latest_attempt:
        return render_template("summary.html", latest_attempt=None, previous_attempts=[], subject_attempts=[], monthly_attempts=[])

    previous_attempts = Score.query.filter(Score.user_id == current_user.id).order_by(Score.timestamp.desc()).all()

   
    subject_attempts = defaultdict(int)
    for attempt in previous_attempts:
        if attempt.quiz and attempt.quiz.subject:
            subject_attempts[attempt.quiz.subject.name] += 1

    subject_attempts_data = [{"subject": sub, "count": count} for sub, count in subject_attempts.items()]

    #
    monthly_attempts = defaultdict(int)
    for attempt in previous_attempts:
        if attempt.timestamp:
            month_year = attempt.timestamp.strftime("%b %Y")  
            monthly_attempts[month_year] += 1

    monthly_attempts_data = [{"month": month, "count": count} for month, count in monthly_attempts.items()]

    return render_template(
        "summary.html", 
        latest_attempt=latest_attempt, 
        previous_attempts=previous_attempts, 
        subject_attempts=subject_attempts_data or [],  
        monthly_attempts=monthly_attempts_data or []  
    )



@main.route("/user_home")
@login_required
def user_home():
    return render_template("user_home.html")

@main.route("/quiz")
@login_required
def quiz():
    
    return render_template("quiz.html")




@main.route("/quiz/<int:quiz_id>/view")
@login_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template("quiz.html", quiz=quiz)

@main.route("/quiz/<int:quiz_id>/start")
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    questions = quiz.questions  
    if len(questions) == 0:
       flash("This quiz has no questions. You cannot attempt it.", "danger")
       return redirect(url_for("main.dashboard"))
    return render_template("start_quiz.html", quiz=quiz, questions=questions)


from datetime import datetime

@main.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

   
    score = 0
    for question in quiz.questions:
        selected = request.form.get(f'question_{question.id}')
        if selected and selected.strip().isdigit():
            selected = int(selected)

        if selected == question.correct_option:
            score += 1

   
    new_attempt = Score(user_id=current_user.id, quiz_id=quiz.id, total_scored=score, timestamp=datetime.now())
    db.session.add(new_attempt)
    db.session.commit()

    
    return redirect(url_for('main.scores'))


@main.route('/score_summary/<int:score_id>')
@login_required
def score_summary(score_id):
    user_score = Score.query.get_or_404(score_id)

    # Ensure the score belongs to current user
    if user_score.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('main.dashboard'))

    return render_template('score.html', score=user_score)

@main.route('/scores')
@login_required
def scores():
    user_scores = Score.query.filter_by(user_id=current_user.id).order_by(Score.timestamp.desc()).all()
    user_score = Score.query.filter_by(user_id=current_user.id).all()

    score_trend = [
        {"date": score.timestamp.strftime('%Y-%m-%d'), "score": score.total_scored}
        for score in user_score
    ]

    return render_template("score.html", scores=user_scores, score_trend=score_trend)



####################################################################################
####################################################################################
####################################################################################


