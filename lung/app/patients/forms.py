from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, ValidationError, NumberRange, Length


class PatientsForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=20)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=20)])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=1000)])
    sex = SelectField('Sex', choices=['Male', 'Female', 'Other'], validate_choice=False)
    occupation = StringField('Occupation')
    address = StringField('Address')

    # weight = FloatField('Weight (kg)')
    # height = FloatField('Height (cm)')
    # health_condition = TextAreaField('Health Condition')
    # diabetes = StringField('Diabetes')
    # blood_pressure = FloatField('Blood Pressure (mmHg)')
    # cancer_report = TextAreaField('Cancer Report')
    # other_problems = TextAreaField('Other Problems')

    # CT_scan = FileField('CT Scan', validators=[FileAllowed(['jpg', 'png', 'raw', 'mhd'])])

    submit = SubmitField('Save')
    cancel = SubmitField('Cancel')

