import os
import secrets

from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from collections import namedtuple

from app import mail


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'base/static/profile_pics', picture_fn)

    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def save_picture_patients(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'base/static/patients_pics', picture_fn)

    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def token_hex_ct_scan(raw, mhd):
    random_hex = secrets.token_hex(8)

    _, raw_f_ext = os.path.splitext(raw)
    _, mhd_f_ext = os.path.splitext(mhd)

    raw_hex_name = random_hex + raw_f_ext
    mhd_hex_name = random_hex + mhd_f_ext

    return raw_hex_name, mhd_hex_name


lymph_node = ['not spread', 'spread nearby', 'spread both chests']

STAGE = dict(zip(['I', 'II', 'III', 'IV'], ['I', 'II', 'III', 'IV']))
GRADE = dict(zip(['1', '2', '3', '4'], ['1', '2', '3', '4']))
CELL_TYPE = dict(zip(['NSCLC', 'SCLC'], ['non-small cell type (NSCLC)', 'small-cell type (SCLC)']))
INVASIVE_TYPE = dict(zip(['non-invasive', 'invasive'], ['non-invasive', 'invasive']))


def additional_specs(diameter, specs):
    for key, value in specs.items():
        if value:
            specs[key] = value.lower()
        else:
            specs[key] = 'n/a'


    ardenocarcinoma, squamous_cell_carcinoma, large_cell_carcinoma, atypia, angiolymphatic, lymph_node, metastasis = \
        specs['ardenocarcinoma'], specs['squamous_cell_carcinoma'], specs['large_cell_carcinoma'], specs['atypia'], \
        specs['angiolymphatic'], specs['lymph_node'], specs['metastasis']

    egfr, alk, ros1, kras, braf, mek, ret, met = specs['egfr'], specs['alk'], specs['ros1'], specs['kras'], specs[
        'braf'], specs['mek'], specs['ret'], specs['met']

    if 'yes' in {ardenocarcinoma, squamous_cell_carcinoma, large_cell_carcinoma}:
        cell_type = CELL_TYPE['NSCLC']
        if atypia in {'no', 'n/a'}:  # 1,4,7,10,13, 16,19,22,25,28
            grade = GRADE['1']
            invasive_type = INVASIVE_TYPE['non-invasive']
        else:
            invasive_type = INVASIVE_TYPE['invasive']
            if angiolymphatic in {'no', 'n/a'}:  # 2,5,8,11,14, 17,20,23,26,29
                grade = GRADE['2']
            else:
                grade = f"{GRADE['3']} & {GRADE['4']}"  # 3,6,9,12,15, 18,21,24,27,30

    else:
        cell_type = CELL_TYPE['SCLC']
        invasive_type = INVASIVE_TYPE['invasive']
        if atypia in {'no', 'n/a'}:  # 1,4,7,10,13, 16,19,22,25,28
            grade = GRADE['1']
        else:
            if angiolymphatic in {'no', 'n/a'}:  # 2,5,8,11,14, 17,20,23,26,29
                grade = GRADE['2']
            else:
                grade = f"{GRADE['3']} & {GRADE['4']}"  # 3,6,9,12,15, 18,21,24,27,30

    if diameter <= 20:
        if lymph_node == 'not spread':
            stage = STAGE['I']
        elif lymph_node == 'spread nearby':
            stage = STAGE['II']
        else:
            stage = STAGE['III']

    else:
        if lymph_node == 'spread nearby':
            stage = STAGE['II']
        elif lymph_node == 'spread both chests':
            if metastasis == 'yes':
                stage = STAGE['IV']
            else:
                stage = STAGE['III']
        else:
            stage = STAGE['II']

    # treatment & medicine

    if cell_type == CELL_TYPE['NSCLC']:
        if stage == STAGE['I']:     #1-3
            treatment = 'Lobectomy, sleeve resection, segmentectomy, wedge resection, lobectomy preferred. Chemotherapy after surgery'
            medicine = 'No medicine needed'
        elif stage == STAGE['II']:  #4-9
            treatment = 'Lobectomy, sleeve resection, pneumonectomy. Lymph nodes having cancer should be removed. Chemotherapy after surgery'
            medicine = 'No medicine needed'
        elif stage == STAGE['III']: #10-12
            treatment = 'Radiation therapy, chemotherapy, surgery, immunotherapy'
            if 'positive' in {egfr, alk, ros1, kras}:
                medicine_dict = {'egfr': ['Afatinib', 'Erlotinib', 'Gefitinib'], 'alk': ['Alectinib', 'Brigatinib'],
                                 'ros1': ['Crizotinib', 'Xalkori'], 'kras': ['(KRAS mutation - no response to medicine)']}
                medicine = []
                for k, v in medicine_dict.items():
                    if specs[k] == 'positive':
                        medicine.extend(v)

                medicine = list(dict.fromkeys(medicine))
                medicine = ', '.join([m.capitalize() for m in medicine])

            else:
                medicine = 'Pembrolizumab, Durvalumab'
        else:  #13-15
            treatment = 'Radiation therapy, chemotherapy, surgery, immunotherapy, targeted therapy, photodynamic therapy, laser therapy'
            if 'positive' in {egfr, alk, ros1, kras, braf, mek, ret, met}:
                medicine_dict = {'egfr': ['Afatinib', 'Erlotinib', 'Gefitinib', 'cyramza'],
                                 'alk': ['Alectinib', 'Brigatinib', 'ceritinib', 'crizotinib'],
                                 'ros1': ['Crizotinib', 'Xalkori'],
                                 'braf': ['dabrafenib', 'trametinib'], 'mek': ['trametinib'],
                                 'ret': ['selpercatinib', 'pralsetinib'], 'met': ['capmatinib'],
                                 'kras': ['(KRAS mutation - no response to medicine)']}
                medicine = []
                for k, v in medicine_dict.items():
                    if specs[k] == 'positive':
                        medicine.extend(v)

                medicine = list(dict.fromkeys(medicine))
                medicine = ', '.join([m.capitalize() for m in medicine])
                medicine += ', Pembrolizumab, Nivolumab, Ipilimumab, Bevacizumab, Docetaxel'

            else:
                medicine = 'Pembrolizumab, Nivolumab, Ipilimumab, Bevacizumab, Docetaxel'

    else:
        if stage == STAGE['I']:     #16-18
            treatment = 'Lobectomy, sleeve resection, segmentectomy, wedge resection, lobectomy preferred. Chemotherapy after surgery. Prophylactic cranial irradiation recommended'
            medicine = 'No medicine needed'
        elif stage == STAGE['II']:  #19-24
            treatment = 'Lobectomy, sleeve resection, pneumonectomy. Lymph nodes having cancer should be removed. Chemotherapy after surgery, concurrent chemoradiation. Prophylactic cranial irradiation recommended'
            medicine = 'No medicine needed'
        elif stage == STAGE['III']: #25-27
            treatment = 'Chemotherapy, concurrent chemoradiation, prophylactic cranial irradiation'
            medicine = 'Etoposide, Cisplatin'
        else:  #28-30
            treatment = 'Chemotherapy, concurrent chemoradiation, prophylactic cranial irradiation, radiation therapy, palliative radiotherapy'
            medicine = 'Etoposide, Cisplatin, Atezolizumab, Durvalumab, Carboplatin, Irinotecan'


    return dict(zip(['stage', 'cell_type', 'grade', 'invasive_type', 'treatment', 'medicine'], [stage, cell_type, grade, invasive_type, treatment, medicine]))


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)
