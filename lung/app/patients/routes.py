import secrets, os, json
from PIL import Image
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_required, current_user

import app
from app import db, login_manager
from app.patients import blueprint

from app.users.utils import save_picture_patients
from app.patients.forms import PatientsForm

from app.base.models import User, Patient


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

    return render_template('patients_profile.html', title='Profile', patient=patient, form=PatientsForm(), picture_file=picture_file)

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
