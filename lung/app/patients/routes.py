import secrets, os, json
from datetime import datetime
from flask import render_template, redirect, request, url_for, flash, make_response
from flask_login import login_required, current_user
from flask_weasyprint import HTML, render_pdf, CSS

import app
from app import db, login_manager
from app.patients import blueprint

from app.users.utils import save_picture_patients
from app.patients.forms import PatientsForm

from app.base.models import User, Patient, CTScan, Upload

personal_info = ['first_name', 'last_name', 'age', 'sex', 'occupation', 'address']
health = ['weight', 'height', 'blood_pressure']
general_biochemistry = ['diabetes', 'smoking', 'hemolized_sample']
comorbidities = ['liver_disease', 'pemphigus', 'renal_failure']
serum_tumor_markers = ['ca', 'cea', 'cyfra', 'nse', 'pro_grp', 'scc']

biopsy_test = ['egpr', 'alk', 'ros1', 'kras', 'ardenocarcinoma', 'angiolymphatic', 'antypia', 'antibody', 'squamous_cell_carcinoma', 'large_cell_carcinoma', 'lymph_node', 'metastasis']
genetic_test = ['egfr', 'egfr_t790m', 'eml4_alk', 'braf', 'her2', 'mek', 'met', 'ret']

biochemistry_realization = ['blood_drawn_date']

health_info_dict = {'personal_info': personal_info, 'health': health, 'general_biochemistry': general_biochemistry,
                    'comorbidities': comorbidities, 'serum_tumor_markers': serum_tumor_markers, 'biopsy_test': biopsy_test,
                    'genetic_test': genetic_test, 'biochemistry_realization': biochemistry_realization}


"""add patient"""

@blueprint.route("/create", methods=['GET', 'POST'])
@login_required
def create_patients():
    form = PatientsForm()

    # The user pressed the "Submit" button
    if 'submit' in request.form:
        if form.validate_on_submit():
            new_request = {k: v.capitalize() for k, v in request.form.items() if
                           k not in ['csrf_token', 'submit', 'cancel', 'ct_scan', 'picture', 'blood_drawn_date']}

            patient = Patient(**new_request, doctor=current_user)
            if form.blood_drawn_date.data:
                patient.blood_drawn_date = datetime.strptime(form.blood_drawn_date.data, '%Y-%m-%d').strftime('%b %d, %Y')

            if form.picture.data:
                patient.picture = save_picture_patients(form.picture.data)

            db.session.add(patient)
            db.session.commit()
            flash('Your patient has been added!', 'success')
            return redirect(url_for('patients_blueprint.patients_profile', patient_id=patient.id))

    # The user pressed the "Cancel" button
    if 'cancel' in request.form:
        return redirect(url_for('home_blueprint.index'))

    picture_file = url_for('static', filename='patients_pics/default.png')

    return render_template('edit_info.html', title='Create', heading='Create', form=form, picture_file=picture_file, health_info_dict=health_info_dict)


"""edit patient"""

@blueprint.route("/patient_id:<int:patient_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_info(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PatientsForm()

    # The user pressed the "Cancel" button
    if form.cancel.data:
        return redirect(url_for('home_blueprint.index'))

    # The user pressed the "Submit" button
    if form.submit.data:
        if form.validate_on_submit():
            if form.picture.data:
                patient.picture = save_picture_patients(form.picture.data)

            if form.blood_drawn_date.data:
                patient.blood_drawn_date = datetime.strptime(form.blood_drawn_date.data, '%Y-%m-%d').strftime('%b %d, %Y')

            for field in form:
                if field.name not in ['csrf_token', 'submit', 'cancel', 'ct_scan', 'picture', 'blood_drawn_date']:
                    setattr(patient, field.name, field.data)

            db.session.commit()
            flash('Your patient info has been updated!', 'success')
            return redirect(url_for('patients_blueprint.patients_profile', patient_id=patient.id))

    elif request.method == 'GET':
        for field in form:
            if field.name not in ['csrf_token', 'submit', 'cancel', 'ct_scan', 'picture', 'blood_drawn_date']:
                field.data = getattr(patient, field.name)
            elif field.name == 'blood_drawn_date':
                if field.data:
                    field.data = datetime.strptime(patient.blood_drawn_date, '%b %d, %Y').strftime('%Y-%m-%d')


    if patient.picture == '':
        picture_file = url_for('static', filename='patients_pics/default.png')
    else:
        picture_file = url_for('static', filename='patients_pics/' + patient.picture)

    return render_template('edit_info.html', title='Edit', heading='Edit', form=form, picture_file=picture_file, health_info_dict=health_info_dict)


"""view patients"""

@blueprint.route("/patient_id:<int:patient_id>/profile", methods=['GET', 'POST'])
@login_required
def patients_profile(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if patient.picture == '':
        picture_file = url_for('static', filename='patients_pics/default.png')
    else:
        picture_file = url_for('static', filename='patients_pics/' + patient.picture)

    upload_list = patient.upload.order_by(Upload.date_uploaded.desc()).all()

    return render_template('patients_profile.html', title='Profile', patient=patient, form=PatientsForm(),
                           picture_file=picture_file, upload_list=upload_list, health_info_dict=health_info_dict)


"""delete patient"""

@blueprint.route("/<int:patient_id>/delete", methods=['POST'])
@login_required
def delete_patients(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    # delete patients uploads from db
    for upload in patient.upload.all():
        db.session.delete(upload)

    db.session.delete(patient)
    db.session.commit()
    flash(f"Your patient '{patient.first_name}' has been deleted!", 'success')

    return redirect(url_for('home_blueprint.index'))


"""pdf template"""

import logging
logging.getLogger('weasyprint').setLevel(100)

import warnings
warnings.filterwarnings("ignore", module="weasyprint")

@blueprint.route("/patient_id:<int:patient_id>/pdf/upload_id:<upload_id>")
@login_required
def pdf_template(patient_id, upload_id):
    form = PatientsForm()

    upload = Upload.query.filter_by(id=upload_id).first()

    upload_list = upload.patient.upload.order_by(Upload.date_uploaded.desc()).all()
    if len(upload_list) > 1:
        upload_index = upload_list.index(upload) + 1
        previous_upload_list = upload_list[upload_index:]
    else:
        previous_upload_list = []

    ct_scan = upload.ct_scan
    result_percent = round(ct_scan.binary_prediction, 2)

    rendered = render_template('pdf_template.html', form=form, upload=upload, ct_scan=ct_scan, result_percent=result_percent, previous_upload_list=previous_upload_list, health_info_dict=health_info_dict)

    return render_pdf(HTML(string=rendered))



