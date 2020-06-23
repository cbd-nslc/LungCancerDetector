from flask import render_template, flash, request
from flask_login import login_required, current_user

from app.home import blueprint
from app.base.models import User, Patient


@blueprint.route('/index')
@login_required
def index():
	page = request.args.get('page', 1, type=int)

	user = User.query.filter_by(username=current_user.username).first_or_404()

	paginate_patients = Patient.query.filter_by(doctor=user).paginate(page=page, per_page=10)

	# search for name of patient
	if request.args.get('search-filter'):
		search_value = request.args.get('search-filter').lower()

		filter_patients = []
		for patient in Patient.query.filter_by(doctor=user).all():
			# match if search_value in full name
			full_name = f'{patient.first_name} {patient.last_name}'.lower()
			if search_value in full_name:
				filter_patients.append(patient)

		flash(f'{len(filter_patients)} result(s) found', 'info')

		return render_template('index.html', patients=filter_patients, paginate_patients=paginate_patients, search=True)

	else:
		return render_template('index.html', patients=paginate_patients.items, paginate_patients=paginate_patients, search=False)

