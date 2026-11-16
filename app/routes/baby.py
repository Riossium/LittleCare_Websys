from flask import Blueprint, render_template, redirect, url_for, flash, request, session, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.baby import BabyProfile
from app.forms.baby_forms import BabyProfileForm
from app.utils import parent_required, save_uploaded_file, log_audit

baby_bp = Blueprint('baby', __name__, url_prefix='/baby')


@baby_bp.route('/list')
@login_required
@parent_required
def list_babies():
    """Module 4: List all baby profiles for logged-in parent"""
    babies = current_user.baby_profiles.filter_by(is_active=True).all()
    active_baby_id = session.get('active_baby_id')
    return render_template('baby/list.html', babies=babies, active_baby_id=active_baby_id)


@baby_bp.route('/create', methods=['GET', 'POST'])
@login_required
@parent_required
def create():
    """Module 4: Add New Baby Profile"""
    form = BabyProfileForm()
    if form.validate_on_submit():
        baby = BabyProfile(
            parent_id=current_user.id,
            name=form.name.data.strip(),
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            blood_type=form.blood_type.data if form.blood_type.data else None,
            birth_weight=form.birth_weight.data,
            birth_height=form.birth_height.data,
            birth_head_circumference=form.birth_head_circumference.data,
            allergies=form.allergies.data.strip() if form.allergies.data else None,
            pediatrician_notes=form.pediatrician_notes.data.strip() if form.pediatrician_notes.data else None,
            is_active=True
        )

        if form.profile_photo.data:
            filename = save_uploaded_file(form.profile_photo.data, folder_name='babies')
            if filename:
                baby.profile_photo = filename

        db.session.add(baby)
        db.session.commit()

        # Set as current active baby
        session['active_baby_id'] = baby.id

        log_audit(current_user.id, 'BABY_PROFILE_CREATED', f"Created baby profile for {baby.name}", request.remote_addr)
        flash(f"Welcome, baby {baby.name}! Health profile created successfully.", "success")
        return redirect(url_for('parent.dashboard'))

    return render_template('baby/create.html', form=form)


@baby_bp.route('/<int:baby_id>')
@login_required
@parent_required
def view(baby_id):
    """Module 4: View Baby Profile Details"""
    baby = BabyProfile.query.filter_by(id=baby_id, parent_id=current_user.id, is_active=True).first_or_404()
    recent_growth = baby.growth_records.order_by(db.desc('recorded_date')).limit(5).all()
    recent_vaccines = baby.vaccination_records.order_by(db.desc('date_administered')).limit(5).all()
    recent_checkups = baby.checkup_records.order_by(db.desc('checkup_date')).limit(5).all()
    return render_template(
        'baby/view.html',
        baby=baby,
        recent_growth=recent_growth,
        recent_vaccines=recent_vaccines,
        recent_checkups=recent_checkups
    )


@baby_bp.route('/<int:baby_id>/edit', methods=['GET', 'POST'])
@login_required
@parent_required
def edit(baby_id):
    """Module 4: Edit Baby Profile"""
    baby = BabyProfile.query.filter_by(id=baby_id, parent_id=current_user.id, is_active=True).first_or_404()
    form = BabyProfileForm(obj=baby)

    if form.validate_on_submit():
        baby.name = form.name.data.strip()
        baby.date_of_birth = form.date_of_birth.data
        baby.gender = form.gender.data
        baby.blood_type = form.blood_type.data if form.blood_type.data else None
        baby.birth_weight = form.birth_weight.data
        baby.birth_height = form.birth_height.data
        baby.birth_head_circumference = form.birth_head_circumference.data
        baby.allergies = form.allergies.data.strip() if form.allergies.data else None
        baby.pediatrician_notes = form.pediatrician_notes.data.strip() if form.pediatrician_notes.data else None

        if form.profile_photo.data:
            filename = save_uploaded_file(form.profile_photo.data, folder_name='babies')
            if filename:
                baby.profile_photo = filename

        db.session.commit()
        log_audit(current_user.id, 'BABY_PROFILE_UPDATED', f"Updated baby profile for {baby.name}", request.remote_addr)
        flash(f"Profile details for {baby.name} have been updated successfully.", "success")
        return redirect(url_for('baby.view', baby_id=baby.id))

    return render_template('baby/edit.html', form=form, baby=baby)


@baby_bp.route('/select/<int:baby_id>')
@login_required
@parent_required
def select(baby_id):
    """Module 4: Switch Active Baby Profile"""
    baby = BabyProfile.query.filter_by(id=baby_id, parent_id=current_user.id, is_active=True).first_or_404()
    session['active_baby_id'] = baby.id
    flash(f"Switched active profile to {baby.name}.", "info")
    referrer = request.referrer
    if referrer and '/auth/' not in referrer:
        return redirect(referrer)
    return redirect(url_for('parent.dashboard'))


@baby_bp.route('/<int:baby_id>/delete', methods=['POST'])
@login_required
@parent_required
def delete(baby_id):
    """Module 4: Delete / Archive Baby Profile"""
    baby = BabyProfile.query.filter_by(id=baby_id, parent_id=current_user.id).first_or_404()
    name = baby.name
    baby.is_active = False  # Soft delete
    db.session.commit()

    if session.get('active_baby_id') == baby.id:
        session.pop('active_baby_id', None)

    log_audit(current_user.id, 'BABY_PROFILE_DELETED', f"Archived baby profile {name}", request.remote_addr)
    flash(f"Baby profile for {name} has been archived.", "warning")
    return redirect(url_for('baby.list_babies'))
