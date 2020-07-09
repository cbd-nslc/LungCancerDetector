import os, sys
sys.path.append("..")
sys.path.append('../DSB2017')
from DSB2017.main import inference

from app.base import blueprint
from app.base.forms import AnonymousForm

from app.users.utils import token_hex_ct_scan

from flask import flash, render_template, redirect, request, url_for, current_app
from werkzeug.utils import secure_filename


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

    if form.cancel.data:
        return redirect(request.url)

    if form.submit.data and form.validate_on_submit():
        raw_file = form.raw_file.data
        mhd_file = form.mhd_file.data

        if raw_file and mhd_file:
            raw_name = secure_filename(raw_file.filename)
            mhd_name = secure_filename(mhd_file.filename)

            raw_name, mhd_name = token_hex_ct_scan(raw_name, mhd_name)

            raw_path = os.path.join(current_app.config['UPLOAD_FOLDER'], raw_name)
            mhd_path = os.path.join(current_app.config['UPLOAD_FOLDER'], mhd_name)

            raw_file.save(raw_path)
            mhd_file.save(mhd_path)

            # import time
            # time.sleep(5)

            print(mhd_path)
            print(raw_path)
            result_percent = inference(mhd_path)

            return redirect(url_for('base_blueprint.result', result_percent=result_percent))

    return render_template('homepage/upload.html', title="Upload", form=form)


@blueprint.route('/result/<int:result_percent>', methods=['GET', 'POST'])
def result(result_percent):

    return render_template('homepage/result.html', title="Upload", result_percent=result_percent)
