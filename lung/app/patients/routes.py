

from app.patients import blueprint
from app.patients.forms import PatientsForm

import secrets, os
from PIL import Image
from flask import render_template
from flask_login import login_required

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


@blueprint.route("/profile", methods=['GET', 'POST'])
@login_required
def patients_profile():
    form = PatientsForm()


    return render_template('patients_profile.html', title='Profile', form=form)


@blueprint.route("/info", methods=['GET', 'POST'])
@login_required
def edit_info():
    form = PatientsForm()

    return render_template('edit_info.html', title='Info', form=form)


@blueprint.route("/upload", methods=['GET', 'POST'])
@login_required
def upload_ct_scan():
    form = PatientsForm()

    return render_template('upload_ct_scan.html', title='Upload CT Scan', form=form)
