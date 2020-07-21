import hashlib
import os
import sys

from app import db

sys.path.append("..")
sys.path.append('../DSB2017')

from DSB2017.main import inference, make_bb_image
from DSB2017.utils import get_binary_prediction

from flask import render_template, redirect, url_for, current_app
from werkzeug.utils import secure_filename

from app.base import blueprint
from app.base.models import CTScan
from app.base.forms import AnonymousForm


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
    def call_model():
        print('Not pre-computed, calling model')
        base_name = os.path.basename(mhd_path).replace('.mhd', '')

        # run the model
        prediction_result = inference(mhd_path)
        binary_prediction1 = get_binary_prediction(prediction_result)

        ct_scan = CTScan()
        ct_scan.mhd_name = mhd_name
        ct_scan.mhd_md5 = md5
        ct_scan.prediction = prediction_result
        db.session.add(ct_scan)
        db.session.commit()

        return redirect(url_for('base_blueprint.result', result_percent=binary_prediction1, base_name=base_name))

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
            print('mhd_path:', mhd_path)
            md5 = hashlib.md5(open(mhd_path, 'rb').read()).hexdigest()
            print('mhd_md5:', md5)

            # check if the file exists in db by md5 code
            ct_scan = CTScan.query.filter_by(mhd_md5=md5).first()

            # if yes, load the ct_scan in the db
            if ct_scan:
                print('Pre-computed')
                result_percent = int(ct_scan.prediction * 100)

                # Return 0 if negative, 1 if positive, and keep the probability if unsure
                binary_prediction = get_binary_prediction(ct_scan.prediction)

                base_name = ct_scan.mhd_name.replace('.mhd', '')

                clean_path = os.path.join(current_app.static_folder, f'uploaded_ct_scan/{base_name}_clean.npy')
                pbb_path = os.path.join(current_app.static_folder, f'uploaded_ct_scan/{base_name}_pbb.npy')
                if os.path.exists(clean_path) and os.path.exists(pbb_path):
                    return redirect(
                        url_for('base_blueprint.result', result_percent=binary_prediction, base_name=base_name))
                else:
                    return call_model()
            # if no, save the file and run the model
            else:
                return call_model()

    return render_template('homepage/upload.html', title="Upload", form=form)


@blueprint.route('/result/<path:base_name>/<int:result_percent>', methods=['GET', 'POST'])
def result(base_name, result_percent):
    clean_path = os.path.join(current_app.static_folder, f'uploaded_ct_scan/{base_name}_clean.npy')
    pbb_path = os.path.join(current_app.static_folder, f'uploaded_ct_scan/{base_name}_pbb.npy')

    bbox_basename = make_bb_image(clean_path, pbb_path)

    return render_template('homepage/result.html', title="Upload", bbox_basename=bbox_basename,
                           result_percent=result_percent)
