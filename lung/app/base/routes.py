import os, sys, hashlib
sys.path.append("..")
sys.path.append('../DSB2017')
from DSB2017.main import inference, make_bb_image
import numpy as np

from app.users.utils import token_hex_ct_scan

from flask import flash, render_template, redirect, request, url_for, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.base import blueprint
from app.base.models import CTScan
from app.base.forms import AnonymousForm
from app.patients.forms import PatientsForm

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


@blueprint.route('/upload', methods=['GET', 'POST'])
def upload():
    form = AnonymousForm()

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
            md5 = hashlib.md5(open(mhd_path, 'rb').read()).hexdigest()
            print(md5)

            # check if the file exists in db by md5 code
            ct_scan = CTScan.query.filter_by(md5=md5).first()

            # if yes, load the ct_scan in the db
            if ct_scan:
                result_percent = ct_scan.result_percent
                base_name = os.path.basename(ct_scan.mhd_path).replace('.mhd', '')

                return redirect(url_for('base_blueprint.result', result_percent=result_percent, base_name=base_name))

            # if no, save the file and run the model
            else:
                base_name = os.path.basename(mhd_path).replace('.mhd', '')

                # run the model
                result_matrix = inference(mhd_path)
                result_percent = int(result_matrix*100)

                ct_scan = CTScan()
                ct_scan.filename = mhd_path
                ct_scan.md5 = md5
                ct_scan.result_percent = result_percent

                return redirect(url_for('base_blueprint.result', result_percent=result_percent, base_name=base_name))

    return render_template('homepage/upload.html', title="Upload", form=form)


@blueprint.route('/result/<path:base_name>/<int:result_percent>', methods=['GET', 'POST'])
def result(base_name, result_percent):
    clean_path = os.path.join(current_app.static_folder, f'uploaded_ct_scan/{base_name}_clean.npy')
    pbb_path = os.path.join(current_app.static_folder, f'uploaded_ct_scan/{base_name}_pbb.npy')

    bbox_basename = make_bb_image(clean_path, pbb_path)

    return render_template('homepage/result.html', title="Upload", bbox_basename=bbox_basename, result_percent=result_percent)
