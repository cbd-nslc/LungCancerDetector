import secrets, os, json
from PIL import Image
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_required, current_user

import app
from app import db, login_manager
from app.patients import blueprint
from app.patients.forms import PatientsForm

from app.base.models import User, Patient

"""Save picture"""
def save_CT_scan(CT_scan):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(CT_scan.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/CT_scan', picture_fn)

    # resize picture
    output_size = (125, 125)
    resized_picture = Image.open(CT_scan)
    resized_picture.thumbnail(output_size)

    # save picture
    resized_picture.save(picture_path)
    return picture_fn


"""add patient"""
@blueprint.route("/create", methods=['GET', 'POST'])
@login_required
def create_patients():
    form = PatientsForm(request.form)

    # The user pressed the "Submit" button
    if 'submit' in request.form:
        if form.validate_on_submit():
            new_request = {k: v for k, v in request.form.items() if
                           k not in ['csrf_token', 'submit', 'cancel', 'ct_scan']}
            patient = Patient(**new_request, doctor=current_user)
            db.session.add(patient)
            db.session.commit()
            flash('Your patient has been added!', 'success')
            return redirect(url_for('home_blueprint.index'))

    # The user pressed the "Cancel" button
    if 'cancel' in request.form:
        return redirect(url_for('home_blueprint.index'))

    return render_template('edit_info.html', title='Create', heading='Create', form=form, request_form=request.form)

"""edit patient"""
@blueprint.route("/<int:patient_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_info(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PatientsForm(request.form)

    # The user pressed the "Submit" button
    if form.validate_on_submit():
        if form.submit.data:
            for field in form:
                if field.name not in ['csrf_token', 'submit', 'cancel', 'ct_scan']:
                    setattr(patient, field.name, field.data)

            db.session.commit()
            flash('Your patient info has been updated!', 'success')
            return redirect(url_for('patients_blueprint.patients_profile', patient_id=patient.id))

    elif request.method == 'GET':
        for field in form:
            if field.name not in ['csrf_token', 'submit', 'cancel', 'ct_scan']:
                field.data = getattr(patient, field.name)

    # The user pressed the "Cancel" button
    if form.cancel.data:
        return redirect(url_for('home_blueprint.index'))

    return render_template('edit_info.html', title='Edit', heading='Edit', form=form)

"""view patients"""
@blueprint.route("/<int:patient_id>/profile", methods=['GET', 'POST'])
@login_required
def patients_profile(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template('patients_profile.html', title='Profile', patient=patient, form=PatientsForm())

"""delete patient"""
@blueprint.route("/<int:patient_id>/delete", methods=['POST'])
@login_required
def delete_patients(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    flash(f"Your patient '{patient.first_name}' has been deleted!", 'success')

    return redirect(url_for('home_blueprint.index'))


@blueprint.route("/upload", methods=['GET', 'POST'])
@login_required
def upload_ct_scan():
    form = PatientsForm()

    return render_template('upload_ct_scan.html', title='Upload CT Scan', form=form)
