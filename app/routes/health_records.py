from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, current_app, send_from_directory
from flask_login import login_required, current_user
import os
from app.extensions import db
from app.models.baby import BabyProfile
from app.models.health_record import GrowthRecord, VaccinationRecord, MedicalCheckupRecord
from app.forms.health_forms import GrowthRecordForm, VaccinationRecordForm, MedicalCheckupRecordForm
from app.utils import parent_required, get_active_baby, save_uploaded_file, log_audit

health_bp = Blueprint('health', __name__, url_prefix='/health')


@health_bp.route('/')
@login_required
@parent_required
def index():
    """Module 5: Unified Health Records Hub"""
    baby = get_active_baby()
    if not baby:
        flash("Please create or select a baby profile first to view health records.", "info")
        return redirect(url_for('baby.create'))

    category = request.args.get('category', 'all')
    growth_records = baby.growth_records.order_by(db.desc('recorded_date')).all()
    vaccination_records = baby.vaccination_records.order_by(db.desc('date_administered')).all()
    checkup_records = baby.checkup_records.order_by(db.desc('checkup_date')).all()

    return render_template(
        'health/index.html',
        baby=baby,
        category=category,
        growth_records=growth_records,
        vaccination_records=vaccination_records,
        checkup_records=checkup_records
    )


# =========================================================================
# GROWTH RECORDS
# =========================================================================

@health_bp.route('/growth')
@login_required
@parent_required
def growth():
    """Module 5: Growth Records & Interactive Percentile Charts"""
    baby = get_active_baby()
    if not baby:
        flash("Please select a baby profile first.", "info")
        return redirect(url_for('baby.create'))

    records = baby.growth_records.order_by(db.desc('recorded_date')).all()
    return render_template('health/growth.html', baby=baby, records=records)


@health_bp.route('/growth/add', methods=['GET', 'POST'])
@login_required
@parent_required
def add_growth():
    """Module 5: Add Growth Measurement"""
    baby = get_active_baby()
    if not baby:
        flash("Please add a baby profile first.", "info")
        return redirect(url_for('baby.create'))

    form = GrowthRecordForm()
    if form.validate_on_submit():
        record = GrowthRecord(
            baby_id=baby.id,
            recorded_date=form.recorded_date.data,
            weight_kg=form.weight_kg.data,
            height_cm=form.height_cm.data,
            head_circumference_cm=form.head_circumference_cm.data,
            notes=form.notes.data.strip() if form.notes.data else None,
            recorded_by=current_user.full_name
        )
        db.session.add(record)
        db.session.commit()

        log_audit(current_user.id, 'GROWTH_RECORD_ADDED', f"Logged growth for {baby.name}: {record.weight_kg}kg, {record.height_cm}cm", request.remote_addr)
        flash(f"Growth measurement for {baby.name} recorded successfully!", "success")
        return redirect(url_for('health.growth'))

    return render_template('health/add_growth.html', form=form, baby=baby)


@health_bp.route('/growth/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
@parent_required
def edit_growth(record_id):
    """Module 5: Edit Growth Record"""
    record = GrowthRecord.query.get_or_404(record_id)
    if record.baby.parent_id != current_user.id:
        abort(403)

    form = GrowthRecordForm(obj=record)
    if form.validate_on_submit():
        record.recorded_date = form.recorded_date.data
        record.weight_kg = form.weight_kg.data
        record.height_cm = form.height_cm.data
        record.head_circumference_cm = form.head_circumference_cm.data
        record.notes = form.notes.data.strip() if form.notes.data else None

        db.session.commit()
        flash("Growth record updated successfully.", "success")
        return redirect(url_for('health.growth'))

    return render_template('health/add_growth.html', form=form, baby=record.baby, is_edit=True)


@health_bp.route('/growth/<int:record_id>/delete', methods=['POST'])
@login_required
@parent_required
def delete_growth(record_id):
    """Module 5: Delete Growth Record"""
    record = GrowthRecord.query.get_or_404(record_id)
    if record.baby.parent_id != current_user.id:
        abort(403)

    db.session.delete(record)
    db.session.commit()
    flash("Growth record has been deleted.", "info")
    return redirect(url_for('health.growth'))


@health_bp.route('/api/growth-data/<int:baby_id>')
@login_required
def growth_chart_data(baby_id):
    """
    API returning chronological baby growth logs plotted against
    WHO Child Growth Standards (Median / P15 / P85).
    """
    baby = BabyProfile.query.get_or_404(baby_id)

    # Permission check: Parent or authorized doctor
    if baby.parent_id != current_user.id and not current_user.is_doctor and not current_user.is_admin:
        abort(403)

    records = baby.growth_records.order_by(GrowthRecord.recorded_date.asc()).all()

    # Calculate age in months at each measurement date
    labels = []
    weights = []
    heights = []

    for r in records:
        days = (r.recorded_date - baby.date_of_birth).days
        months = round(max(0, days / 30.4375), 1)
        labels.append(f"{months} mos ({r.recorded_date.strftime('%b %d')})")
        weights.append(r.weight_kg)
        heights.append(r.height_cm)

    # Standard WHO Median Weight and Height curves for 0-24 months
    who_months = [0, 1, 2, 3, 4, 6, 9, 12, 18, 24]
    who_weight_median = [3.3, 4.5, 5.6, 6.4, 7.0, 7.9, 8.9, 9.6, 10.9, 12.0]  # Boys/Girls blended average
    who_height_median = [49.5, 54.0, 57.5, 60.5, 63.0, 66.5, 71.0, 75.0, 82.0, 87.0]

    return jsonify({
        'baby_name': baby.name,
        'gender': baby.gender,
        'records': {
            'labels': labels,
            'weights': weights,
            'heights': heights
        },
        'who_reference': {
            'months': who_months,
            'weight_median': who_weight_median,
            'height_median': who_height_median
        }
    })


# =========================================================================
# VACCINATION RECORDS
# =========================================================================

@health_bp.route('/vaccinations')
@login_required
@parent_required
def vaccinations():
    """Module 5: Vaccination Record Management"""
    baby = get_active_baby()
    if not baby:
        flash("Please select a baby profile first.", "info")
        return redirect(url_for('baby.create'))

    records = baby.vaccination_records.order_by(db.desc('date_administered')).all()
    return render_template('health/vaccinations.html', baby=baby, records=records)


@health_bp.route('/vaccinations/add', methods=['GET', 'POST'])
@login_required
@parent_required
def add_vaccination():
    """Module 5: Add Vaccination Record"""
    baby = get_active_baby()
    if not baby:
        flash("Please select a baby profile first.", "info")
        return redirect(url_for('baby.create'))

    form = VaccinationRecordForm()
    if form.validate_on_submit():
        record = VaccinationRecord(
            baby_id=baby.id,
            vaccine_name=form.vaccine_name.data,
            dose_number=form.dose_number.data,
            date_administered=form.date_administered.data,
            next_scheduled_date=form.next_scheduled_date.data,
            status=form.status.data,
            administered_by=form.administered_by.data.strip() if form.administered_by.data else None,
            batch_number=form.batch_number.data.strip() if form.batch_number.data else None,
            notes=form.notes.data.strip() if form.notes.data else None
        )
        db.session.add(record)
        db.session.commit()

        log_audit(current_user.id, 'VACCINE_RECORD_ADDED', f"Logged {record.vaccine_name} for {baby.name}", request.remote_addr)
        flash(f"Vaccination record for {record.vaccine_name} saved successfully!", "success")
        return redirect(url_for('health.vaccinations'))

    return render_template('health/add_vaccination.html', form=form, baby=baby)


@health_bp.route('/vaccinations/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
@parent_required
def edit_vaccination(record_id):
    """Module 5: Edit Vaccination Record"""
    record = VaccinationRecord.query.get_or_404(record_id)
    if record.baby.parent_id != current_user.id:
        abort(403)

    form = VaccinationRecordForm(obj=record)
    if form.validate_on_submit():
        record.vaccine_name = form.vaccine_name.data
        record.dose_number = form.dose_number.data
        record.date_administered = form.date_administered.data
        record.next_scheduled_date = form.next_scheduled_date.data
        record.status = form.status.data
        record.administered_by = form.administered_by.data.strip() if form.administered_by.data else None
        record.batch_number = form.batch_number.data.strip() if form.batch_number.data else None
        record.notes = form.notes.data.strip() if form.notes.data else None

        db.session.commit()
        flash(f"Vaccination record for {record.vaccine_name} updated successfully.", "success")
        return redirect(url_for('health.vaccinations'))

    return render_template('health/add_vaccination.html', form=form, baby=record.baby, is_edit=True)


@health_bp.route('/vaccinations/<int:record_id>/delete', methods=['POST'])
@login_required
@parent_required
def delete_vaccination(record_id):
    """Module 5: Delete Vaccination Record"""
    record = VaccinationRecord.query.get_or_404(record_id)
    if record.baby.parent_id != current_user.id:
        abort(403)

    db.session.delete(record)
    db.session.commit()
    flash("Vaccination record deleted.", "info")
    return redirect(url_for('health.vaccinations'))


# =========================================================================
# MEDICAL AND CHECKUP RECORDS
# =========================================================================

@health_bp.route('/checkups')
@login_required
@parent_required
def checkups():
    """Module 5: Medical and Checkup Records"""
    baby = get_active_baby()
    if not baby:
        flash("Please select a baby profile first.", "info")
        return redirect(url_for('baby.create'))

    records = baby.checkup_records.order_by(db.desc('checkup_date')).all()
    return render_template('health/checkups.html', baby=baby, records=records)


@health_bp.route('/checkups/add', methods=['GET', 'POST'])
@login_required
@parent_required
def add_checkup():
    """Module 5: Add Checkup Record"""
    baby = get_active_baby()
    if not baby:
        flash("Please select a baby profile first.", "info")
        return redirect(url_for('baby.create'))

    form = MedicalCheckupRecordForm()
    if form.validate_on_submit():
        record = MedicalCheckupRecord(
            baby_id=baby.id,
            checkup_date=form.checkup_date.data,
            visit_type=form.visit_type.data,
            provider_name=form.provider_name.data.strip() if form.provider_name.data else None,
            diagnosis=form.diagnosis.data.strip() if form.diagnosis.data else None,
            treatment_summary=form.treatment_summary.data.strip() if form.treatment_summary.data else None,
            clinical_notes=form.clinical_notes.data.strip() if form.clinical_notes.data else None
        )

        if form.document.data:
            doc_file = form.document.data
            doc_name = save_uploaded_file(doc_file, folder_name='documents')
            if doc_name:
                record.document_filename = doc_name
                record.document_original_name = doc_file.filename

        db.session.add(record)
        db.session.commit()

        log_audit(current_user.id, 'CHECKUP_RECORD_ADDED', f"Logged checkup for {baby.name} ({record.visit_type})", request.remote_addr)
        flash(f"Checkup record for {baby.name} saved successfully!", "success")
        return redirect(url_for('health.checkups'))

    return render_template('health/add_checkup.html', form=form, baby=baby)


@health_bp.route('/checkups/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
@parent_required
def edit_checkup(record_id):
    """Module 5: Edit Checkup Record"""
    record = MedicalCheckupRecord.query.get_or_404(record_id)
    if record.baby.parent_id != current_user.id:
        abort(403)

    form = MedicalCheckupRecordForm(obj=record)
    if form.validate_on_submit():
        record.checkup_date = form.checkup_date.data
        record.visit_type = form.visit_type.data
        record.provider_name = form.provider_name.data.strip() if form.provider_name.data else None
        record.diagnosis = form.diagnosis.data.strip() if form.diagnosis.data else None
        record.treatment_summary = form.treatment_summary.data.strip() if form.treatment_summary.data else None
        record.clinical_notes = form.clinical_notes.data.strip() if form.clinical_notes.data else None

        if form.document.data:
            doc_file = form.document.data
            doc_name = save_uploaded_file(doc_file, folder_name='documents')
            if doc_name:
                record.document_filename = doc_name
                record.document_original_name = doc_file.filename

        db.session.commit()
        flash("Checkup record updated successfully.", "success")
        return redirect(url_for('health.checkups'))

    return render_template('health/add_checkup.html', form=form, baby=record.baby, is_edit=True)


@health_bp.route('/checkups/<int:record_id>/delete', methods=['POST'])
@login_required
@parent_required
def delete_checkup(record_id):
    """Module 5: Delete Checkup Record"""
    record = MedicalCheckupRecord.query.get_or_404(record_id)
    if record.baby.parent_id != current_user.id:
        abort(403)

    db.session.delete(record)
    db.session.commit()
    flash("Checkup record deleted.", "info")
    return redirect(url_for('health.checkups'))


@health_bp.route('/document/<int:record_id>')
@login_required
def view_document(record_id):
    """Secure document viewer enforcing patient data privacy"""
    record = MedicalCheckupRecord.query.get_or_404(record_id)
    if record.baby.parent_id != current_user.id and not current_user.is_doctor and not current_user.is_admin:
        abort(403)

    if not record.document_filename:
        abort(404)

    doc_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
    return send_from_directory(doc_dir, record.document_filename)
