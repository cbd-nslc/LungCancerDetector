from flask import render_template, flash
from flask_login import login_required, current_user

from app.home import blueprint
from app.base.models import User, Patient


@blueprint.route('/index')
@login_required
def index():
	patients = []
	for p in Patient.query.all():
		if p.doctor == current_user:
			patients.append(p)

	# User.query.order_by(User.username).all()
	return render_template('index.html', patients=enumerate(patients), num_patients=len(patients))


# @blueprint.route('/<template>')
# @login_required
# def route_template(template):
#     return render_template(template + '.html')
