from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, TextAreaField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, ValidationError, NumberRange, Length


class PatientsForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=20)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=20)])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=1000)], render_kw={'type': 'number'})
    sex = SelectField('Sex', choices=['Male', 'Female', 'Other'], validate_choice=False)
    occupation = StringField('Occupation')
    address = StringField('Address')

    weight = FloatField('Weight (kg)', render_kw={'type': 'number'})
    height = FloatField('Height (cm)', render_kw={'type': 'number'})
    blood_pressure = FloatField('Blood Pressure (mmHg)', render_kw={'type': 'number'})

    diabetes = StringField('Diabetes')
    health_condition = TextAreaField('Health Condition', render_kw={'type': 'text-area'})
    cancer_report = TextAreaField('Cancer Report', render_kw={'type': 'text-area'})
    other_problems = TextAreaField('Other Problems', render_kw={'type': 'text-area'})

    picture = FileField('Patient Picture')
    # ct_scan = FileField('CT Scan')

    submit = SubmitField('Save')
    cancel = SubmitField('Cancel')

