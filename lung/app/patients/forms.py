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

    # health info

    weight = FloatField('Weight (kg)', render_kw={'type': 'number', 'step':'.01'})
    height = FloatField('Height (cm)', render_kw={'type': 'number', 'step':'.01'})
    blood_pressure = FloatField('Blood Pressure (mmHg)', render_kw={'type': 'number', 'step':'.01'})

    health_condition = TextAreaField('Health Condition', render_kw={'type': 'text-area'})
    cancer_report = TextAreaField('Cancer Report', render_kw={'type': 'text-area'})

    diabetes = SelectField('Diabetes', choices=['Yes', 'No'], validate_choice=False)
    smoking = SelectField('Smoking', choices=['Yes', 'No'], validate_choice=False)
    hemolized_sample = SelectField('Hemolized sample', choices=['Yes', 'No'], validate_choice=False)

    blood_drawn_date = StringField('Blood drawn date', render_kw={'type': 'date', 'min': '2000-01-01', 'max': '2100-01-01'})

    # Comorbidities
    liver_disease = SelectField('Liver Disease', choices=['Yes', 'No'], validate_choice=False)
    pemphigus = SelectField('Pemphigus/Psoriasis', choices=['Yes', 'No'], validate_choice=False)
    renal_failure = SelectField('Renal Failure', choices=['Yes', 'No'], validate_choice=False)

    # Serum Tumor Markers:
    ca = FloatField('CA 15.3(U/mL)', render_kw={'type': 'number', 'step':'.01'})
    cea = FloatField('CEA (ng/mL)', render_kw={'type': 'number', 'step':'.01'})
    cyfra = FloatField('CYFRA 21-1 (ng/mL)', render_kw={'type': 'number', 'step':'.01'})
    nse = FloatField('NSE (ng/mL)', render_kw={'type': 'number', 'step':'.01'})
    pro_grp = FloatField('ProGRP (pg/mL)', render_kw={'type': 'number', 'step':'.01'})
    scc = FloatField('SCC (ng/mL)', render_kw={'type': 'number', 'step':'.01'})

    other_problems = TextAreaField('Other Problems', render_kw={'type': 'text-area'})

    picture = FileField('Patient Picture')

    submit = SubmitField('Save')
    cancel = SubmitField('Cancel')

