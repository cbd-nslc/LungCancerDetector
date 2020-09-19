from datetime import datetime

from bcrypt import gensalt, hashpw
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import backref

from app import db, login_manager


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))


# @login_manager.request_loader
# def request_loader(request):
#     username = request.form.get('username')
#     user = User.query.filter_by(username=username).first()
#     return user if user else None


class User(db.Model, UserMixin):
    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    picture = Column(String(20), nullable=False, default='default.jpg')

    patients = db.relationship('Patient', backref='doctor', lazy=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]
            if property == 'password':
                value = hashpw(value.encode('utf8'), gensalt())
            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)


patient_ct_scan = db.Table('patient_ct_scan',
                           db.Column('patient_id', db.Integer, db.ForeignKey('patient.id')),
                           db.Column('ct_scan_id', db.Integer, db.ForeignKey('ct_scan.id')))


class Patient(db.Model):
    # id of patient
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String, nullable=False)
    occupation = db.Column(db.String)
    address = db.Column(db.String)

    # health info
    weight = db.Column(db.Integer)
    height = db.Column(db.Integer)
    blood_pressure = db.Column(db.Float)

    # General Biochemistry
    diabetes = db.Column(db.String)
    smoking = db.Column(db.String)
    hemolized_sample = db.Column(db.String)

    # Comorbidities
    liver_disease = db.Column(db.String)
    pemphigus = db.Column(db.String)
    renal_failure = db.Column(db.String)

    # biopsy test
    alk = db.Column(db.String)
    ros1 = db.Column(db.String)
    kras = db.Column(db.String)
    ardenocarcinoma = db.Column(db.String)
    angiolymphatic = db.Column(db.String)
    atypia = db.Column(db.String)
    antibody = db.Column(db.String)
    squamous_cell_carcinoma = db.Column(db.String)
    large_cell_carcinoma = db.Column(db.String)
    lymph_node = db.Column(db.String)
    metastasis = db.Column(db.String)

    # genetic test
    egfr = db.Column(db.String)
    egfr_t790m = db.Column(db.String)
    eml4_alk = db.Column(db.String)
    braf = db.Column(db.String)
    her2 = db.Column(db.String)
    mek = db.Column(db.String)
    met = db.Column(db.String)
    ret = db.Column(db.String)


    # Serum Tumor Markers:
    ca = db.Column(db.Float)
    cea = db.Column(db.Float)
    cyfra = db.Column(db.Float)
    nse = db.Column(db.Float)
    pro_grp = db.Column(db.Float)
    scc = db.Column(db.Float)

    # Biochemistry Realization
    blood_drawn_date = db.Column(db.String)


    picture = Column(String(20), nullable=False, default='default.png')
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # id of user
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)

    # ct_scan
    ct_scan = db.relationship('CTScan', secondary=patient_ct_scan, lazy='dynamic',
                              backref=db.backref('patient', lazy='dynamic'))

    # upload
    upload = db.relationship('Upload', back_populates='patient', lazy='dynamic')

    def __repr__(self):
        return f"Patients('{self.first_name}', '{self.last_name}')"


class CTScan(db.Model):
    id = db.Column(Integer, primary_key=True)
    mhd_name = db.Column(db.String, nullable=False)
    mhd_md5 = db.Column(db.String, nullable=False)
    prediction = db.Column(db.Float, nullable=False)
    binary_prediction = db.Column(db.Float)
    bbox_basename = db.Column(db.String)
    diameter = db.Column(db.Float)

    upload = db.relationship('Upload', back_populates='ct_scan', lazy='dynamic')


class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    ct_scan_id = db.Column(db.Integer, db.ForeignKey('ct_scan.id'))
    result_text = db.Column(db.String)
    treatment = db.Column(db.String)
    medicine = db.Column(db.String)

    patient = db.relationship('Patient', back_populates='upload')
    ct_scan = db.relationship('CTScan', back_populates='upload')
