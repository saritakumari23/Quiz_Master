from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, IntegerField, TextAreaField, SelectField, HiddenField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from models import Subject, Chapter

class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    full_name = StringField("Full Name", validators=[DataRequired()])
    qualification = StringField("Qualification")
    dob = DateField("Date of Birth", format='%Y-%m-%d')
    role = SelectField("Role", choices=[("user", "User"), ("admin", "Admin")], validators=[DataRequired()])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")



class SubjectForm(FlaskForm):
    name = StringField("Subject Name", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    submit = SubmitField("Add Subject")


class ChapterForm(FlaskForm):
    name = StringField("Chapter Name", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    subject_id = HiddenField("Subject ID", validators=[DataRequired()])  # Ensures subject ID is passed
    submit = SubmitField("Add Chapter")

class QuizForm(FlaskForm):
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    chapter_id = SelectField('Chapter', coerce=int, validators=[DataRequired()])
    date_of_quiz = DateField('Date of Quiz', format='%Y-%m-%d', validators=[DataRequired()])
    time_duration = StringField('Time Duration', validators=[DataRequired()])

    submit = SubmitField('Save Changes')

    def __init__(self, *args, **kwargs):
        super(QuizForm, self).__init__(*args, **kwargs)
        self.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
        self.chapter_id.choices = []


class QuestionForm(FlaskForm):
    quiz_id = SelectField("Quiz", coerce=int)
    question_statement = TextAreaField("Question", )
    option1 = StringField("Option 1", )
    option2 = StringField("Option 2", )
    option3 = StringField("Option 3", )
    option4 = StringField("Option 4", )
    correct_option = IntegerField("Correct Option (1-4)",)
    submit = SubmitField("Add Question")