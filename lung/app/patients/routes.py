import itertools
import os
from datetime import datetime

from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_required, current_user
from flask_weasyprint import HTML, render_pdf

from DSB2017.main import make_bb_image
from DSB2017.utils import get_bbox_image_path, get_slice_bb_matrices
from app import db
from app.base.models import Patient, Upload
from app.base.routes import get_relative_path
from app.patients import blueprint
from app.patients.forms import PatientsForm
from app.users.utils import save_picture_patients, additional_specs

personal_info = ['first_name', 'last_name', 'age', 'sex', 'occupation', 'address']
health = ['weight', 'height', 'blood_pressure']
general_biochemistry = ['diabetes', 'smoking', 'hemolized_sample']
comorbidities = ['liver_disease', 'pemphigus', 'renal_failure']
serum_tumor_markers = ['ca', 'cea', 'cyfra', 'nse', 'pro_grp', 'scc']

biopsy_test = ['alk', 'ros1', 'kras', 'ardenocarcinoma', 'angiolymphatic', 'atypia', 'antibody',
               'squamous_cell_carcinoma', 'large_cell_carcinoma', 'lymph_node', 'metastasis']
genetic_test = ['egfr', 'egfr_t790m', 'eml4_alk', 'braf', 'her2', 'mek', 'met', 'ret']

biochemistry_realization = ['blood_drawn_date']

health_info_dict = {'personal_info': personal_info, 'health': health, 'general_biochemistry': general_biochemistry,
                    'comorbidities': comorbidities, 'serum_tumor_markers': serum_tumor_markers,
                    'biopsy_test': biopsy_test,
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
                patient.blood_drawn_date = datetime.strptime(form.blood_drawn_date.data, '%Y-%m-%d').strftime(
                    '%b %d, %Y')

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

    return render_template('edit_info.html', title='Create', heading='Create', form=form, picture_file=picture_file,
                           health_info_dict=health_info_dict)


"""edit patient"""


@blueprint.route("/<int:patient_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_info(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PatientsForm()

    # The user pressed the "Cancel" button
    if form.cancel.data:
        return redirect(url_for('patients_blueprint.patients_profile', patient_id=patient.id))

    # The user pressed the "Submit" button
    if form.submit.data:
        if form.validate_on_submit():
            if form.picture.data:
                patient.picture = save_picture_patients(form.picture.data)

            if form.blood_drawn_date.data:
                patient.blood_drawn_date = datetime.strptime(form.blood_drawn_date.data, '%Y-%m-%d').strftime(
                    '%b %d, %Y')

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

    return render_template('edit_info.html', title='Edit', heading='Edit', form=form, picture_file=picture_file,
                           health_info_dict=health_info_dict)


# test
@blueprint.route("/<int:patient_id>/test", methods=['GET', 'POST'])
@login_required
def test(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PatientsForm()

    # The user pressed the "Cancel" button
    if form.cancel.data:
        return redirect(url_for('patients_blueprint.patients_profile', patient_id=patient.id))

    # The user pressed the "Submit" button
    if form.submit.data:
        for field in ['ardenocarcinoma', 'squamous_cell_carcinoma', 'large_cell_carcinoma', 'atypia', 'angiolymphatic',
                      'lymph_node', 'metastasis', 'egfr', 'alk', 'ros1', 'kras', 'braf', 'mek', 'ret', 'met']:
            field_data = getattr(form, field).data
            setattr(patient, field, field_data)

        db.session.commit()
        flash('Your patient info has been updated!', 'success')
        return redirect(url_for('patients_blueprint.patients_profile', patient_id=patient.id, _anchor='tab_content2'))

    elif request.method == 'GET':
        for field in ['ardenocarcinoma', 'squamous_cell_carcinoma', 'large_cell_carcinoma', 'atypia', 'angiolymphatic',
                      'lymph_node', 'metastasis', 'egfr', 'alk', 'ros1', 'kras', 'braf', 'mek', 'ret', 'met']:
            field_data = getattr(form, field)
            field_data.data = getattr(patient, field)

    return render_template('test.html', title='Test', heading='Test', form=form)


"""view patients"""


@blueprint.route("/<int:patient_id>/profile", methods=['GET', 'POST'])
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


@blueprint.route("/<int:patient_id>/pdf/<upload_id>")
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
    patient = upload.patient

    specs_list = list(itertools.chain(*[health_info_dict['biopsy_test'], health_info_dict['genetic_test']]))
    specs_dict = dict(zip(specs_list, [getattr(patient, spec) for spec in specs_list]))

    if ct_scan.binary_prediction == 0:
        result_text = 'NOT having lung cancer'
        treatment = 'No treatment required'
        medicine = 'No medicine required'
    elif ct_scan.binary_prediction == 1:
        result = additional_specs(ct_scan.diameter, specs_dict)
        result_text = f"stage {result['stage']}, {result['cell_type']}, grade {result['grade']}, {result['invasive_type']}"
        treatment = result['treatment']
        medicine = result['medicine']
    else:
        result_text = f'{round(ct_scan.binary_prediction * 100, 2)}% chance of having lung cancer'
        treatment = 'No treatment required'
        medicine = 'No medicine required'

    # if not upload.result_text:
    #     upload.result_text = result_text
    #     db.session.commit()
    bbox_image_path = get_bbox_image_path(ct_scan.path)

    if not os.path.exists(bbox_image_path):
        clean_path, pbb_path = get_slice_bb_matrices(ct_scan.path)
        # diameter
        bbox_image_path, diameter = make_bb_image(clean_path, pbb_path)
    bbox_image_path = get_relative_path(bbox_image_path, current_app.config['UPLOAD_FOLDER'])

    rendered = render_template('pdf_template.html', form=form, upload=upload, ct_scan=ct_scan, result_text=result_text,
                               treatment=treatment, medicine=medicine, result_percent=ct_scan.binary_prediction,
                               previous_upload_list=previous_upload_list, health_info_dict=health_info_dict,
                               bbox_image_path=bbox_image_path)

    return render_pdf(HTML(string=rendered))
