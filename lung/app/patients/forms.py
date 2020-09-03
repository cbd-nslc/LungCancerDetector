from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, TextAreaField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, ValidationError, NumberRange, Length


class PatientsForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=20)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=20)])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=1000)], render_kw={'type': 'number'})
    sex = SelectField('Sex', validators=[DataRequired()], choices=[('', 'Choose'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validate_choice=False)
    occupation = StringField('Occupation')
    address = StringField('Address')

    # health info
    weight = FloatField('Weight (kg)', render_kw={'type': 'number', 'step':'.01'})
    height = FloatField('Height (cm)', render_kw={'type': 'number', 'step':'.01'})
    blood_pressure = FloatField('Blood Pressure (mmHg)', render_kw={'type': 'number', 'step':'.01'})

    # General Biochemistry
    diabetes = SelectField('Diabetes', choices=[('N/A', 'Choose'), ('Yes', 'Yes'), ('No', 'No')], validate_choice=False)
    smoking = SelectField('Smoking', choices=[('N/A', 'Choose'), ('Yes', 'Yes'), ('No', 'No')], validate_choice=False,)
    hemolized_sample = SelectField('Hemolized sample', choices=[('N/A', 'Choose'), ('Yes', 'Yes'),  ('No', 'No')], validate_choice=False)

    # Comorbidities
    liver_disease = SelectField('Liver Disease', choices=[('N/A', 'Choose'), ('Yes', 'Yes'),  ('No', 'No')], validate_choice=False)
    pemphigus = SelectField('Pemphigus/ Psoriasis', choices=[('N/A', 'Choose'), ('Yes', 'Yes'),  ('No', 'No')], validate_choice=False)
    renal_failure = SelectField('Renal Failure', choices=[('N/A', 'Choose'), ('Yes', 'Yes'),  ('No', 'No')], validate_choice=False)

    # Serum Tumor Markers:
    ca = FloatField('CA 15.3(U/mL)', render_kw={'type': 'number', 'step':'.01'})
    cea = FloatField('CEA (ng/mL)', render_kw={'type': 'number', 'step':'.01'})
    cyfra = FloatField('CYFRA 21-1 (ng/mL)', render_kw={'type': 'number', 'step':'.01'})
    nse = FloatField('NSE (ng/mL)', render_kw={'type': 'number', 'step':'.01'})
    pro_grp = FloatField('ProGRP (pg/mL)', render_kw={'type': 'number', 'step':'.01'})
    scc = FloatField('SCC (ng/mL)', render_kw={'type': 'number', 'step':'.01'})

    # Biochemistry Realization
    blood_drawn_date = StringField('Blood drawn date',
                                   render_kw={'type': 'date', 'min': '2000-01-01', 'max': '2100-01-01'})

    # biopsy test
    egpr = SelectField('EGPR', choices=[('N/A', 'Choose'), ('Positve', 'Positve'), ('Negative', 'Negative')], validate_choice=False)
    alk = SelectField('ALK', choices=[('N/A', 'Choose'), ('Positve', 'Positve'), ('Negative', 'Negative')], validate_choice=False)
    ros1 = SelectField('ROS1', choices=[('N/A', 'Choose'), ('Positve', 'Positve'), ('Negative', 'Negative')], validate_choice=False)
    kras = SelectField('KRAS', choices=[('N/A', 'Choose'), ('Positve', 'Positve'), ('Negative', 'Negative')], validate_choice=False)

    ardenocarcinoma = SelectField('ARDENOCARCINOMA', choices=[('N/A', 'Choose'), ('Yes', 'Yes'), ('No', 'No')], validate_choice=False)
    angiolymphatic = SelectField('ANGIOLYMPHATIC', choices=[('N/A', 'Choose'), ('Yes', 'Yes'), ('No', 'No')], validate_choice=False)
    antypia = SelectField('ATYPIA', choices=[('N/A', 'Choose'), ('Yes', 'Yes'), ('No', 'No')], validate_choice=False)
    antibody = SelectField('ANTIBODY', choices=[('N/A', 'Choose'), ('Yes', 'Yes'), ('No', 'No')], validate_choice=False)
    squamous_cell_carcinoma = SelectField('Squamous cell carcinoma', choices=[('N/A', 'Choose'), ('Yes', 'Yes'), ('No', 'No')], validate_choice=False)
    large_cell_carcinoma = SelectField('Large cell carcinoma', choices=[('N/A', 'Choose'), ('Yes', 'Yes'), ('No', 'No')], validate_choice=False)

    lymph_node = SelectField('LYMPH NODE', choices=[('N/A', 'Choose'), ('Not spread', 'Not spread'), ('Spread nearby', 'Spread nearby'), ('Spread both chests', 'Spread both chests')], validate_choice=False)
    metastasis = SelectField('METASTASIS', choices=[('N/A', 'Choose'), ('Yes', 'Yes'), ('No', 'No')], validate_choice=False)

    # genetic test
    egfr = SelectField('EGFR', choices=[('N/A', 'Choose'), ('Positve', 'Positve'), ('Negative', 'Negative')],
                       validate_choice=False)
    egfr_t790m = SelectField('EGFR T790M', choices=[('N/A', 'Choose'), ('Positve', 'Positve'), ('Negative', 'Negative')],
                      validate_choice=False)
    eml4_alk = SelectField('EML4-ALK', choices=[('N/A', 'Choose'), ('Positve', 'Positve'), ('Negative', 'Negative')],
                       validate_choice=False)
    braf = SelectField('BRAF', choices=[('N/A', 'Choose'), ('Positve', 'Positve'), ('Negative', 'Negative')],
                       validate_choice=False)
    her2 = SelectField('HER2', choices=[('N/A', 'Choose'), ('Positve', 'Positve'), ('Negative', 'Negative')],
                       validate_choice=False)
    mek = SelectField('MEK', choices=[('N/A', 'Choose'), ('Positve', 'Positve'), ('Negative', 'Negative')],
                      validate_choice=False)
    met = SelectField('MET', choices=[('N/A', 'Choose'), ('Positve', 'Positve'), ('Negative', 'Negative')],
                       validate_choice=False)
    ret = SelectField('RET', choices=[('N/A', 'Choose'), ('Positve', 'Positve'), ('Negative', 'Negative')],
                       validate_choice=False)


    picture = FileField('Patient Picture')

    submit = SubmitField('Save')
    cancel = SubmitField('Cancel')

