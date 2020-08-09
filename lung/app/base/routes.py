import hashlib
import os
import sys
from datetime import datetime

from app import db

sys.path.append("..")
sys.path.append('../DSB2017')

from DSB2017.main import inference, make_bb_image
from DSB2017.utils import get_binary_prediction

from flask import render_template, redirect, url_for, current_app, flash
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.base import blueprint
from app.base.models import CTScan, Patient
from app.base.forms import CTScanForm


# default page
@blueprint.route('/')
def route_default():
    return redirect(url_for('base_blueprint.home'))


@blueprint.route('/home')
def home():
    return render_template('homepage/home.html', title='Home')


@blueprint.route('/about')
def about():
    return render_template('homepage/about.html', title='About')


@blueprint.route('/contact')
def contact():
    return render_template('homepage/contact.html', title='Contact')


def call_model(path, name, md5):
    print('Not pre-computed, calling model')

    # run the model
    new_prediction = inference(path)

    new_ct_scan = CTScan()
    new_ct_scan.mhd_name = name
    new_ct_scan.mhd_md5 = md5
    new_ct_scan.prediction = new_prediction
    db.session.add(new_ct_scan)
    db.session.commit()

    return new_ct_scan

@blueprint.route('/upload', defaults={'patient_id': None}, methods=['GET', 'POST'])
@blueprint.route('/upload/patient_id:<int:patient_id>', methods=['GET', 'POST'])
def upload(patient_id):
    form = CTScanForm()

    # if patient_id available, not show the patient list
    if patient_id:
        patients_list = None
        patient = Patient.query.filter_by(id=patient_id).first()
    else:
        if current_user.is_authenticated:
            patients_list = Patient.query.filter_by(doctor=current_user).all()
            patient = None
        else:
            patients_list = None
            patient = None

    if form.submit.data and form.validate_on_submit():
        raw_file = form.raw_file.data
        mhd_file = form.mhd_file.data

        if raw_file and mhd_file:
            raw_name = secure_filename(raw_file.filename)
            mhd_name = secure_filename(mhd_file.filename)

            # raw_name, mhd_name = token_hex_ct_scan(raw_name, mhd_name)

            raw_path = os.path.join(current_app.config['UPLOAD_FOLDER'], raw_name)
            mhd_path = os.path.join(current_app.config['UPLOAD_FOLDER'], mhd_name)

            raw_file.save(raw_path)
            mhd_file.save(mhd_path)

            mhd_md5 = hashlib.md5(open(mhd_path, 'rb').read()).hexdigest()

            # check if the file exists in db by md5 code
            ct_scan = CTScan.query.filter_by(mhd_md5=mhd_md5).first()

            # if yes, load the ct_scan in the db
            if ct_scan:
                print('Pre-computed')

                # Return 0 if negative, 1 if positive, and keep the probability if unsure
                base_name = ct_scan.mhd_name.replace('.mhd', '')

                clean_path = os.path.join(current_app.static_folder, f'uploaded_ct_scan/{base_name}_clean.npy')
                pbb_path = os.path.join(current_app.static_folder, f'uploaded_ct_scan/{base_name}_pbb.npy')

                # check if file is not saved due to some error
                if os.path.exists(clean_path) and os.path.exists(pbb_path):
                    return redirect(url_for('base_blueprint.result', mhd_md5=mhd_md5, patient_id=patient_id))

                else:
                    new_ct_scan = call_model(mhd_path, mhd_name, mhd_md5)
                    return redirect(url_for('base_blueprint.result', mhd_md5=new_ct_scan.mhd_md5, patient_id=patient_id))

            # if no, save the file and run the model
            else:
                new_ct_scan = call_model(mhd_path, mhd_name, mhd_md5)
                return redirect(url_for('base_blueprint.result', mhd_md5=new_ct_scan.mhd_md5, patient_id=patient_id))

    return render_template('homepage/upload.html', title="Upload", form=form, patients_list=patients_list, patient=patient)


@blueprint.route('/result/<mhd_md5>/', defaults={'patient_id': None}, methods=['GET', 'POST'])
@blueprint.route('/result/<mhd_md5>/patient_id:<int:patient_id>', methods=['GET', 'POST'])
def result(mhd_md5, patient_id):
    ct_scan = CTScan.query.filter_by(mhd_md5=mhd_md5).first()

    base_name = ct_scan.mhd_name.replace('.mhd', '')
    binary_prediction = get_binary_prediction(ct_scan.prediction)

    clean_path = os.path.join(current_app.static_folder, f'uploaded_ct_scan/{base_name}_clean.npy')
    pbb_path = os.path.join(current_app.static_folder, f'uploaded_ct_scan/{base_name}_pbb.npy')

    # diameter
    bbox_basename, diameter = make_bb_image(clean_path, pbb_path)
    ct_scan.diameter = diameter

    print(ct_scan.patient)
    print(patient_id)
    print(ct_scan.patient_id)

    if patient_id:
        ct_scan.patient_id = patient_id
        ct_scan.date_uploaded = datetime.utcnow()

    db.session.commit()

    return render_template('homepage/result.html', title="Upload", bbox_basename=bbox_basename,
                           result_percent=binary_prediction, diameter=diameter, ct_scan=ct_scan)
