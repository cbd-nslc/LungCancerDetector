import os
from flask import render_template, redirect, request, url_for, flash, session, current_app, send_from_directory
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.base import blueprint
from app.base.forms import AnonymousForm


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'raw', 'mhd'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        file = form.ct_scan.data
        if file and allowed_file(file.filename):
            file_name = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file_name))

        return render_template('homepage/upload.html', title="Upload", form=form, loading=True)

    else:
        return render_template('homepage/upload.html', title="Upload", form=form, loading=False)


@blueprint.route('/result/<path:ct_scan_name>', methods=['GET', 'POST'])
def result(ct_scan_name):
    return render_template('homepage/result.html', title="Upload", ct_scan_file=url_for('static', filename=f'uploaded_ct_scan/{ct_scan_name}'))






