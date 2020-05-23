from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, ValidationError, NumberRange


class PatientsForm(FlaskForm):
    first_name = StringField('First Name')
    last_name = StringField('Last Name', validators=[DataRequired()])
    age = IntegerField('Age', [DataRequired(), NumberRange(min=0, max=1000)])
    sex = SelectField('Sex', validators=[DataRequired()], choices=['Male', 'Female', 'Other'])

    occupation = StringField('Occupation', validators=[DataRequired()])

    address = StringField('Address')

    health_condition = TextAreaField('Health Condition', validators=[DataRequired()])

    weight = FloatField('Weight (kg)')
    height = FloatField('Height (cm)')

    diabetes = StringField('Diabetes', validators=[DataRequired()])
    blood_pressure = StringField('Blood Pressure', validators=[DataRequired()])

    cancer_reports = TextAreaField('Cancer Reports', validators=[DataRequired()])

    CT_scan = FileField('CT Scan', validators=[FileAllowed(['jpg', 'png'])])

    other_problems = TextAreaField('Other Problems')

    submit = SubmitField('Save')
