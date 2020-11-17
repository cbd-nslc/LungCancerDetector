import itertools
import os
import sys
from datetime import datetime

from werkzeug.utils import secure_filename

from app import db
from app.base.upload_file_utils import handle_file_list, UploadType, md5_checksum, get_relative_path, get_full_path, \
    move_files

sys.path.append("..")
sys.path.append('../DSB2017')

from DSB2017.main import inference, make_bb_image
from DSB2017.utils import get_binary_prediction, directory_padding, get_slice_bb_matrices

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

        # Uploaded files will be saved into temp_path, then moved to save_path
        timestamp = int(datetime.now().timestamp())
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id), str(patient_id),
                                 str(timestamp))

        if not os.path.isdir(temp_path):
            os.makedirs(temp_path)

        file_paths = []
        for file in files:
            file_path = os.path.join(temp_path, secure_filename(file.filename))
            file_paths.append(file_path)
            file.save(file_path)

        combined_md5 = md5_checksum(file_paths)
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], combined_md5)
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        file_paths = move_files(save_path, file_paths)

        upload_type, valid_upload_result = handle_file_list(file_paths)

        if upload_type == UploadType.MHD_RAW:
            new_ct_scan_path = valid_upload_result
            # new_ct_scan_name = os.path.basename(new_ct_scan_path)
            # new_ct_scan_md5 = md5_checksum(new_ct_scan_path)
            new_ct_scan_md5 = combined_md5
        elif upload_type == UploadType.DICOM:
            new_ct_scan_path = valid_upload_result
            import glob
            dicom_files = glob.glob(new_ct_scan_path + '/*/*.dcm')
            # new_ct_scan_md5 = md5_checksum(dicom_files)
            # new_ct_scan_name = Path(new_ct_scan_path).name
            new_ct_scan_md5 = combined_md5

        else:
            raise NotImplementedError()

        # check if the file exists in db by md5 code
        ct_scan = CTScan.query.filter_by(md5=new_ct_scan_md5).first()

        # if yes, load the ct_scan in the db
        if ct_scan:
            print('\nPre-computed')
            # if ct_scan exists, create pdf report (upload)
            upload = Upload(patient_id=patient_id, ct_scan_id=ct_scan.id, date_uploaded=datetime.utcnow())
            if ct_scan not in patient.ct_scan.all():
                patient.ct_scan.append(ct_scan)
            db.session.add(upload)

            old_ct_scan_path = ct_scan.path
            if old_ct_scan_path is None or len(str(old_ct_scan_path)) == 0:
                ct_scan.path = get_relative_path(new_ct_scan_path, current_app.config['UPLOAD_FOLDER'])
            db.session.commit()

            clean_path, pbb_path = get_slice_bb_matrices(
                get_full_path(ct_scan.path, current_app.config['UPLOAD_FOLDER']))

            # check if file is not saved due to some error
            if os.path.exists(clean_path) and os.path.exists(pbb_path):
                return redirect(
                    url_for('base_blueprint.result', ct_scan_md5=new_ct_scan_md5, patient_id=patient_id,
                            upload_id=upload.id))

            else:
                print("\nPre-computed files not found")
                print(f"Old_pbb_path: {pbb_path}")
                # new_ct_scan = commit_new_ct_scan(path=new_ct_scan_path, md5=new_ct_scan_md5, patient=patient)
                call_model(new_ct_scan_path)
                ct_scan.path = get_relative_path(new_ct_scan_path, current_app.config['UPLOAD_FOLDER'])
                db.session.commit()
                print("CT_scan path changed to:", ct_scan.path)
                return redirect(
                    url_for('base_blueprint.result', ct_scan_md5=ct_scan.md5, patient_id=patient_id,
                            upload_id=upload.id))

        # if no, save the file and run the model
        else:
            print('\nCalling model due to computed results not found')
            new_ct_scan = commit_new_ct_scan(path=new_ct_scan_path, md5=new_ct_scan_md5, patient=patient)

            new_ct_scan.patient.append(patient)
            patient.ct_scan.append(new_ct_scan)

            # if ct_scan not exists, create pdf report (upload)
            upload = Upload(patient_id=patient_id, ct_scan_id=new_ct_scan.id, date_uploaded=datetime.utcnow())

            db.session.add(upload)
            db.session.commit()

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
    print("\nVisualizing result")
    binary_prediction = get_binary_prediction(ct_scan.prediction)
    clean_path, pbb_path = get_slice_bb_matrices(get_full_path(ct_scan.path, current_app.config['UPLOAD_FOLDER']))
    print("CT_Scan_path:", ct_scan.path)
    # diameter
    bbox_image_path, diameter = make_bb_image(clean_path, pbb_path)
    bbox_image_path = get_relative_path(bbox_image_path, current_app.config['UPLOAD_FOLDER'])
    print("BB image path:", bbox_image_path)

    if not ct_scan.diameter:
        ct_scan.diameter = diameter

    if not ct_scan.binary_prediction:
        ct_scan.binary_prediction = binary_prediction

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

    return render_template('homepage/result.html', title="Upload", bbox_image_path=bbox_image_path,
                           result_percent=binary_prediction, result_text=result_text, diameter=diameter,
                           ct_scan=ct_scan, patient=patient, upload=upload)


def call_model(path):
    print(f"\nCalling model for path: {path}")
    if os.path.isdir(path):
        path = directory_padding(path)
    prediction = inference(path)
    assert isinstance(path, str)
    print(f'Calling model for the input: {path}')
    return prediction


def commit_new_ct_scan(path, md5, patient):
    # run the model
    new_prediction = call_model(path)
    new_ct_scan = CTScan(path=get_relative_path(path, current_app.config['UPLOAD_FOLDER']),
                         md5=md5, prediction=new_prediction)
    new_ct_scan.patient.append(patient)

    db.session.add(new_ct_scan)
    db.session.commit()

    return new_ct_scan
