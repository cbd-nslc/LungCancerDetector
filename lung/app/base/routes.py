import itertools
import os
import sys
from datetime import datetime
from pathlib import Path

from werkzeug.utils import secure_filename

from app import db
from app.base.upload_file_utils import handle_file_list, UploadType, md5_checksum

sys.path.append("..")
sys.path.append('../DSB2017')

from DSB2017.main import inference, make_bb_image
from DSB2017.utils import get_binary_prediction, directory_padding

from flask import render_template, redirect, url_for, current_app
from flask_login import current_user, login_required

from app.base import blueprint
from app.base.models import CTScan, Patient, Upload
from app.base.forms import CTScanFormUI

from app.users.utils import additional_specs
from app.patients.routes import health_info_dict


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


def commit_new_ct_scan(path, md5, patient):
    print('Not pre-computed, calling model')
    
    # run the model
    if os.path.isdir(path):
        path = directory_padding(path)
    new_prediction = inference(path)

    new_ct_scan = CTScan(path=path, md5=md5, prediction=new_prediction)
    if patient:
        upload = Upload(patient_id=patient.id, date_uploaded=datetime.utcnow())
        new_ct_scan.patient.append(patient)
        new_ct_scan.upload.append(upload)

    db.session.add(new_ct_scan)
    db.session.commit()

    return new_ct_scan


@blueprint.route('/upload', defaults={'patient_id': None}, methods=['GET', 'POST'])
@blueprint.route('/upload/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def upload(patient_id):
    form = CTScanFormUI()
    # if patient_id available, not show the patient list
    if patient_id:
        patient = Patient.query.filter_by(id=patient_id).first()
        patients_list = None
    else:
        patient = None
        patients_list = Patient.query.filter_by(doctor=current_user).all()

    if form.submit.data and form.validate_on_submit():
        files = form.file.data
        print(files)

        timestamp = int(datetime.now().timestamp())
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id), str(patient_id), str(timestamp))
        if not os.path.isdir(save_path):
            os.makedirs(save_path)
        file_paths = [os.path.join(save_path, secure_filename(file.filename)) for file in files]
        for file in files:
            file_path = os.path.join(save_path, secure_filename(file.filename))
            file_paths.append(file_path)
            file.save(file_path)

        print(file_paths)
        upload_type, valid_upload_result = handle_file_list(file_paths)
        print(upload_type)
        print(valid_upload_result)

        if upload_type == UploadType.MHD_RAW:
            new_ct_scan_path = valid_upload_result
            # new_ct_scan_name = os.path.basename(new_ct_scan_path)
            new_ct_scan_md5 = md5_checksum(new_ct_scan_path)

        elif upload_type == UploadType.DICOM:
            new_ct_scan_path = valid_upload_result
            dicom_files = [os.path.join(p) for p in os.listdir(new_ct_scan_path)]
            new_ct_scan_md5 = md5_checksum(dicom_files)
            # new_ct_scan_name = Path(new_ct_scan_path).name

        else:
            raise NotImplementedError()

        # check if the file exists in db by md5 code
        ct_scan = CTScan.query.filter_by(md5=new_ct_scan_md5).first()

        # if ct_scan exists, create pdf report (upload)
        if ct_scan:
            upload = Upload(patient_id=patient_id, ct_scan_id=ct_scan.id, date_uploaded=datetime.utcnow())
            if ct_scan not in patient.ct_scan.all():
                patient.ct_scan.append(ct_scan)
            db.session.add(upload)
            db.session.commit()
        else:
            pass

        # if yes, load the ct_scan in the db
        if ct_scan:
            print('Pre-computed')

            old_ct_scan_path = ct_scan.path
            if os.path.isfile(old_ct_scan_path):
                # With MHD & RAW files, old_ct_scan_path is the path to the MHD file, we need the parent dir
                base_name = os.path.basename(old_ct_scan_path)
                old_ct_scan_path = Path(old_ct_scan_path).parent

            else:
                base_name = Path(old_ct_scan_path).name

            clean_path = os.path.join(old_ct_scan_path, f'{base_name}_clean.npy')
            pbb_path = os.path.join(old_ct_scan_path, f'{base_name}_pbb.npy')

            # check if file is not saved due to some error
            if os.path.exists(clean_path) and os.path.exists(pbb_path):
                return redirect(
                    url_for('base_blueprint.result', ct_scan_md5=new_ct_scan_md5, patient_id=patient_id, upload_id=upload.id))

            else:
                new_ct_scan = commit_new_ct_scan(path=new_ct_scan_path, md5=new_ct_scan_md5, patient=patient)
                return redirect(
                    url_for('base_blueprint.result', ct_scan_md5=new_ct_scan.md5, patient_id=patient_id,
                            upload_id=upload.id))

        # if no, save the file and run the model
        else:
            new_ct_scan = commit_new_ct_scan(path=new_ct_scan_path, md5=new_ct_scan_md5, patient=patient)
            return redirect(url_for('base_blueprint.result', ct_scan_md5=new_ct_scan.md5, patient_id=patient_id,
                                    upload_id=upload.id))

    return render_template('homepage/upload.html', title="upload", form=form, patients_list=patients_list,
                           patient=patient)


@blueprint.route('/result/<ct_scan_md5>/', defaults={'patient_id': None}, methods=['GET', 'POST'])
@blueprint.route('/result/<ct_scan_md5>/<int:patient_id>/<upload_id>', methods=['GET', 'POST'])
def result(ct_scan_md5, patient_id, upload_id):
    ct_scan = CTScan.query.filter_by(md5=ct_scan_md5).first()
    patient = Patient.query.filter_by(id=patient_id).first()
    upload = Upload.query.filter_by(id=upload_id).first()

    base_name = ct_scan.mhd_name.replace('.mhd', '')
    binary_prediction = get_binary_prediction(ct_scan.prediction)

    clean_path = os.path.join(current_app.static_folder, f'uploaded_ct_scan/{base_name}_clean.npy')
    pbb_path = os.path.join(current_app.static_folder, f'uploaded_ct_scan/{base_name}_pbb.npy')

    # diameter
    bbox_basename, diameter = make_bb_image(clean_path, pbb_path)

    if not ct_scan.diameter:
        ct_scan.diameter = diameter

    if not ct_scan.binary_prediction:
        ct_scan.binary_prediction = binary_prediction

    if not ct_scan.bbox_basename:
        ct_scan.bbox_basename = bbox_basename

    specs_list = list(itertools.chain(*[health_info_dict['biopsy_test'], health_info_dict['genetic_test']]))
    specs_dict = dict(zip(specs_list, [getattr(patient, spec) for spec in specs_list]))

    if binary_prediction == 0:
        result_text = 'NOT having lung cancer'
        treatment = 'No treatment required'
        medicine = 'No medicine required'
    elif binary_prediction == 1:
        result = additional_specs(diameter, specs_dict)
        result_text = f"stage {result['stage']}, {result['cell_type']}, grade {result['grade']}, {result['invasive_type']}"
        treatment = result['treatment']
        medicine = result['medicine']
    else:
        result_text = f'{round(binary_prediction * 100, 2)}% chance of having lung cancer'
        treatment = 'No treatment required'
        medicine = 'No medicine required'

    for spec in ['ardenocarcinoma', 'squamous_cell_carcinoma', 'large_cell_carcinoma', 'atypia', 'angiolymphatic',
                 'lymph_node', 'metastasis', 'egfr', 'alk', 'ros1', 'kras', 'braf', 'mek', 'ret', 'met']:
        setattr(upload, spec, getattr(patient, spec))

    if not upload.result_text:
        upload.result_text = result_text

    if not upload.treatment:
        upload.treatment = treatment

    if not upload.medicine:
        upload.medicine = medicine

    db.session.commit()

    return render_template('homepage/result.html', title="Upload", bbox_basename=bbox_basename,
                           result_percent=binary_prediction, result_text=result_text, diameter=diameter,
                           ct_scan=ct_scan, patient=patient, upload=upload)
