import secrets, os, json
import pdfkit, base64
from flask import render_template, redirect, request, url_for, flash, make_response
from flask_login import login_required, current_user

import app
from app import db, login_manager
from app.patients import blueprint

from app.users.utils import save_picture_patients
from app.patients.forms import PatientsForm

from app.base.models import User, Patient, CTScan, Upload

"""add patient"""


@blueprint.route("/create", methods=['GET', 'POST'])
@login_required
def create_patients():
    form = PatientsForm()

    # The user pressed the "Submit" button
    if 'submit' in request.form:
        if form.validate_on_submit():
            new_request = {k: v.capitalize() for k, v in request.form.items() if
                           k not in ['csrf_token', 'submit', 'cancel', 'ct_scan', 'picture']}

            patient = Patient(**new_request, doctor=current_user)
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

    return render_template('edit_info.html', title='Create', heading='Create', form=form, picture_file=picture_file)


"""edit patient"""


@blueprint.route("/<int:patient_id>/edit", methods=['GET', 'POST'])
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

            for field in form:
                if field.name not in ['csrf_token', 'submit', 'cancel', 'ct_scan', 'picture']:
                    setattr(patient, field.name, field.data)

            db.session.commit()
            flash('Your patient info has been updated!', 'success')
            return redirect(url_for('patients_blueprint.patients_profile', patient_id=patient.id))

    elif request.method == 'GET':
        for field in form:
            if field.name not in ['csrf_token', 'submit', 'cancel', 'ct_scan', 'picture']:
                field.data = getattr(patient, field.name)

    if patient.picture == '':
        picture_file = url_for('static', filename='patients_pics/default.png')
    else:
        picture_file = url_for('static', filename='patients_pics/' + patient.picture)

    return render_template('edit_info.html', title='Edit', heading='Edit', form=form, picture_file=picture_file)


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
                           picture_file=picture_file, upload_list=upload_list)


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


@blueprint.route("/<upload_id>/")
@login_required
def pdf_template(upload_id):
    upload = Upload.query.filter_by(id=upload_id).first()

    upload_list = upload.patient.upload.order_by(Upload.date_uploaded.desc()).all()
    if len(upload_list) > 1:
        upload_index = upload_list.index(upload) + 1
        previous_upload_list = upload_list[upload_index:]

    else:
        previous_upload_list = []

    ct_scan = upload.ct_scan
    result_percent = round(ct_scan.binary_prediction, 2)

    with open(f'app/base/static/uploaded_ct_scan/{ct_scan.bbox_basename}', 'rb') as image_file:
        bbox = base64.b64encode(image_file.read()).decode()

    rendered = render_template('pdf_template.html', upload=upload, ct_scan=ct_scan, result_percent=result_percent, bbox=bbox, previous_upload_list=previous_upload_list)

    # pdf template
    css = ['app/base/static/vendors/bootstrap/dist/css/bootstrap.min.css',
           'app/base/static/css/pdf.css']
    pdf = pdfkit.from_string(rendered, False, css=css)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=output.pdf'

    return response
