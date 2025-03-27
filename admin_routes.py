from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Subject, Quiz, User, Chapter, Question, Score # Import models
from form import SubjectForm, QuizForm, ChapterForm, QuestionForm 
from datetime import datetime
from sqlalchemy.exc import IntegrityError

admin = Blueprint("admin", __name__, url_prefix="/admin")

# ======================== Dashboard ========================
@admin.route('/dashboard')
@login_required
def dashboard():
    quizzes = Quiz.query.all()
    subjects = Subject.query.all()
    Users = User.query.all()
    form = SubjectForm() 
    return render_template("admin/dashboard.html", subjects=subjects, form=form, quizzes=quizzes, Users=Users)

# ======================== Manage Subjects ========================
@admin.route('/subjects', methods=['GET', 'POST'])
@login_required
def manage_subjects():
    form = SubjectForm()
    subjects = Subject.query.all()

    if form.validate_on_submit():
        existing_subject = Subject.query.filter_by(name=form.name.data, description=form.description.data).first()
        
        if existing_subject:
            flash("Subject already exists!", "warning")
        else:
            try:
                new_subject = Subject(name=form.name.data, description=form.description.data)
                db.session.add(new_subject)
                db.session.commit()
                
                return redirect(url_for('admin.manage_subjects'))
            except IntegrityError:
                db.session.rollback()
                flash("Error adding subject!", "danger")

    return render_template('admin/manage_subjects.html', subjects=subjects, form=form)

@admin.route('/subject/<int:subject_id>/delete', methods=['POST'])
@login_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    
    return redirect(url_for('admin.manage_subjects'))

@admin.route('/subject/<int:subject_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    form = SubjectForm(obj=subject)

    if form.validate_on_submit():
        subject.name = form.name.data
        subject.description = form.description.data
        db.session.commit()
        
        return redirect(url_for('admin.manage_subjects'))

    return render_template('admin/edit_subject.html', form=form, subject_id=subject_id)

# ======================== Manage Chapters ========================
@admin.route('/subject/<int:subject_id>/chapters', methods=['GET', 'POST'])
def manage_chapters(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    form = ChapterForm()
    
    # Set subject_id in the form
    form.subject_id.data = subject_id  

    if form.validate_on_submit():
        
        chapter = Chapter(
            subject_id=form.subject_id.data,
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(chapter)
        db.session.commit()
        
        return redirect(url_for('admin.manage_chapters', subject_id=subject_id))

    return render_template("admin/manage_chapters.html", subject=subject, form=form, chapters=subject.chapters)


@admin.route('/chapter/<int:chapter_id>/delete', methods=['POST'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    subject_id = chapter.subject_id
    db.session.delete(chapter)
    db.session.commit()
    
    return redirect(url_for('admin.manage_chapters', subject_id=subject_id))


@admin.route('/chapter/<int:chapter_id>/edit', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    form = ChapterForm(obj=chapter)
    if form.validate_on_submit():
        chapter.name = form.name.data
        chapter.description = form.description.data
        db.session.commit()
        
        return redirect(url_for('admin.manage_chapters', subject_id=chapter.subject_id))

    return render_template('admin/edit_chapter.html', form=form, chapter=chapter)

@admin.route('/get_chapters/<int:subject_id>')
@login_required
def get_chapters(subject_id):
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    chapters_data = [{"id": chapter.id, "name": chapter.name} for chapter in chapters]
    return jsonify({"chapters": chapters_data})

# ======================== Manage Quizzes ========================

@admin.route('/manage_quizzes', methods=['GET', 'POST'])
def manage_quizzes():
    form = QuizForm()

    # Fetch subjects and set dropdown choices
    subjects = Subject.query.all()
    quizzes= Quiz.query.all()
    form.subject_id.choices = [(s.id, s.name) for s in subjects]

    if form.subject_id.data:
        chapters = Chapter.query.filter_by(subject_id=form.subject_id.data).all()
        form.chapter_id.choices = [(c.id, c.name) for c in chapters]
    else:
        form.chapter_id.choices = []

    if form.validate_on_submit():
        try:
            new_quiz = Quiz(
                subject_id=form.subject_id.data,
                chapter_id=form.chapter_id.data,
                date_of_quiz=form.date_of_quiz.data,
                time_duration=form.time_duration.data
            )
            db.session.add(new_quiz)
            db.session.commit()
            
            return redirect(url_for('admin.manage_quizzes'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding quiz: {str(e)}", "danger")
            
   
        

    return render_template('admin/manage_quizzes.html', form=form, subjects=subjects, quizzes= quizzes)

@admin.route('/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuizForm(obj=quiz)
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
    form.chapter_id.choices = [(c.id, c.name) for c in Chapter.query.filter_by(subject_id=quiz.subject_id).all()]

    if form.validate_on_submit():
        quiz.subject_id = form.subject_id.data
        quiz.chapter_id = form.chapter_id.data
        quiz.date_of_quiz = form.date_of_quiz.data
        quiz.time_duration = form.time_duration.data
        db.session.commit()

        return redirect(url_for('admin.manage_quizzes'))

    return render_template('admin/edit_quiz.html', form=form, quiz=quiz)

@admin.route('/quiz/<int:quiz_id>/delete', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    
    return redirect(url_for('admin.manage_quizzes'))

# ======================== Manage Questions ========================
@admin.route('/quiz/<int:quiz_id>/view')
@login_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template('admin/view_quiz.html', quiz=quiz, questions=questions)

@admin.route('/quiz/<int:quiz_id>/add_question', methods=['GET', 'POST'])
@login_required
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == 'POST':

        statement = request.form['question_statement']
        option1 = request.form.get('option1', '').strip()
        option2 = request.form.get('option2', '').strip()
        option3 = request.form.get('option3', '').strip()
        option4 = request.form.get('option4', '').strip()
        correct_option = request.form.get('correct_option', '').strip()

        if not all([option1, option2, option3, option4, correct_option]):
            flash("All fields are required!", "danger")
            return redirect(url_for('admin.add_question', quiz_id=quiz.id))

        try:
            correct_option = int(correct_option)
            if correct_option not in [1, 2, 3, 4]:
                raise ValueError("Invalid correct option")
        except ValueError:
            flash("Correct option must be between 1 and 4.", "danger")
            return redirect(url_for('admin.add_question', quiz_id=quiz.id))
                # Save to database
        new_question = Question(
            quiz_id=quiz.id, 
            question_statement=statement,
            option1=option1, option2=option2,
            option3=option3, option4=option4,
            correct_option=correct_option
        )
        db.session.add(new_question)
        db.session.commit()
        

        
        return redirect(url_for('admin.view_quiz', quiz_id=quiz.id))

    return render_template('admin/questions.html', quiz=quiz)

@admin.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        question.question_statement = request.form['question_statement']
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form['option3']
        question.option4 = request.form['option4']
        question.correct_option = request.form['correct_option']

        db.session.commit()
       
        return redirect(url_for('admin.view_quiz', quiz_id=question.quiz_id))

    return render_template('admin/edit_question.html', question=question)

@admin.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    """Deletes a question from the database"""
    question = Question.query.get_or_404(question_id)  # Fetch the question

    try:
        db.session.delete(question)  # Delete the question
        db.session.commit()  # Commit the deletion
        
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        flash(f'Error deleting question: {str(e)}', 'danger')

    return redirect(url_for('admin.view_quiz', quiz_id=question.quiz_id))  




# ======================== Manage Users ========================
@admin.route('/users')
@login_required
def manage_users():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('main.home'))
    
    users = User.query.all()
    return render_template('admin/manage_user.html', users=users)


@admin.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")
    return redirect(url_for('admin.manage_users'))


# ======================== Summary ========================


@admin.route("/summary")
@login_required
def summary():
    total_subjects = Subject.query.count()
    total_chapters = Chapter.query.count()
    total_quizzes = Quiz.query.count()
    total_users = User.query.count()

    recent_subjects = Subject.query.order_by(Subject.id.desc()).limit(5).all()
    recent_quizzes = Quiz.query.order_by(Quiz.id.desc()).limit(5).all()

    # Fetch subject-wise top scores
    top_scores = (
        db.session.query(Subject.name, db.func.max(Score.total_scored))
        .join(Quiz, Quiz.subject_id == Subject.id)
        .join(Score, Score.quiz_id == Quiz.id)
        .group_by(Subject.name)
        .all()
    )
    subjects_top_scores = [row[0] for row in top_scores]
    top_scores_values = [row[1] if row[1] is not None else 0 for row in top_scores]  # Handle None values

    # Fetch subject-wise user attempts
    user_attempts = (
        db.session.query(Subject.name, db.func.count(Score.id))
        .join(Quiz, Quiz.subject_id == Subject.id)
        .join(Score, Score.quiz_id == Quiz.id)
        .group_by(Subject.name)
        .all()
    )
    subjects_attempts = [row[0] for row in user_attempts]
    attempts_values = [row[1] if row[1] is not None else 0 for row in user_attempts]  # Handle None values

    return render_template(
        "admin/summary.html",
        total_subjects=total_subjects,
        total_chapters=total_chapters,
        total_quizzes=total_quizzes,
        total_users=total_users,
        recent_subjects=recent_subjects,
        recent_quizzes=recent_quizzes,
        subjects_top_scores=subjects_top_scores,
        top_scores_values=top_scores_values,
        subjects_attempts=subjects_attempts,
        attempts_values=attempts_values,
    )
