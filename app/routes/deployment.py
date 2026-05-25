from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.client import Company, Requirement
from app.models.worker import Worker
from app.models.deployment import Deployment
from datetime import date, datetime

deployment_bp = Blueprint('deployment', __name__)

@deployment_bp.route('/deployment')
def index():
    """Main deployment page with company filter and post filter"""
    # Get filter parameters - handle empty values
    company_id = request.args.get('company_id', '')
    month = request.args.get('month', '')
    year = request.args.get('year', '')
    post = request.args.get('post', '')
    
    # Get all companies for filter
    companies = Company.query.all()
    
    # Get unique posts for filter dropdown
    all_posts = db.session.query(Requirement.post).distinct().all()
    post_list = sorted([p[0] for p in all_posts if p[0]])
    
    # Build requirements query - start with base query (NO filters)
    query = Requirement.query
    
    # Apply filters ONLY if they have values
    if company_id and company_id.strip():
        query = query.filter_by(company_id=int(company_id))
    
    if month and month.strip():
        query = query.filter_by(month=int(month))
    
    if year and year.strip():
        query = query.filter_by(year=int(year))
    
    if post and post.strip():
        query = query.filter(Requirement.post.ilike(f'%{post}%'))
    
    # Order by most recent first
    requirements = query.order_by(
        Requirement.year.desc(), 
        Requirement.month.desc(), 
        Requirement.company_id
    ).all()
    
    # For each requirement calculate deployed vs required
    req_data = []
    for req in requirements:
        deployed = Deployment.query.filter_by(
            company_id=req.company_id,
            post=req.post,
            is_active=True
        ).count()
        
        diff = deployed - req.required_count
        req_data.append({
            'req': req,
            'deployed': deployed,
            'diff': diff,
            'status': 'ok' if deployed == req.required_count
                     else ('short' if deployed < req.required_count else 'excess')
        })
    
    return render_template('deployment/index.html',
                         req_data=req_data, 
                         companies=companies,
                         post_list=post_list,
                         selected_company=company_id,
                         selected_month=month,
                         selected_year=year,
                         selected_post=post)

@deployment_bp.route('/deployment/add-requirement', methods=['GET', 'POST'])
def add_requirement():
    companies = Company.query.all()
    
    if request.method == 'POST':
        # Check if requirement already exists
        existing = Requirement.query.filter_by(
            company_id=request.form['company_id'],
            post=request.form['post'],
            month=int(request.form['month']),
            year=int(request.form['year'])
        ).first()
        
        if existing:
            flash('Requirement already exists for this company, post, and month!', 'danger')
            return redirect(url_for('deployment.add_requirement'))
        
        req = Requirement(
            company_id=request.form['company_id'],
            post=request.form['post'],
            required_count=int(request.form['required_count']),
            month=int(request.form['month']),
            year=int(request.form['year']),
            shift=request.form.get('shift', 'General'),
            notes=request.form.get('notes', '')
        )
        db.session.add(req)
        db.session.commit()
        flash('Requirement added successfully!', 'success')
        return redirect(url_for('deployment.index'))
    
    return render_template('deployment/add_requirement.html',
                         companies=companies,
                         current_month=date.today().month,
                         current_year=date.today().year)


@deployment_bp.route('/deployment/add', methods=['GET', 'POST'])
def add():
    """Deploy worker - ONLY show available workers (not currently deployed)"""
    companies = Company.query.all()
    
    # Get IDs of workers who are CURRENTLY ACTIVE deployed
    active_deployed_ids = [d.worker_id for d in Deployment.query.filter_by(is_active=True).all()]
    
    # Get ONLY workers who are NOT currently deployed
    if active_deployed_ids:
        available_workers = Worker.query.filter(
            Worker.is_active == True,
            ~Worker.id.in_(active_deployed_ids)
        ).all()
    else:
        available_workers = Worker.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        try:
            worker_id = int(request.form['worker_id'])
            company_id = int(request.form['company_id'])
            post = request.form['post']
            date_from_str = request.form['date_from']
            date_from_obj = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            
            # Check if worker already has active deployment
            old_deployment = Deployment.query.filter_by(
                worker_id=worker_id, 
                is_active=True
            ).first()
            
            if old_deployment:
                # End current deployment
                old_deployment.is_active = False
                old_deployment.date_to = date.today()
                db.session.add(old_deployment)
                flash(f'Previous deployment ended for this worker', 'info')
            
            # Create new deployment
            dep = Deployment(
                worker_id=worker_id,
                company_id=company_id,
                post=post,
                date_from=date_from_obj,
                is_active=True
            )
            db.session.add(dep)
            db.session.commit()
            flash('Worker deployed successfully!', 'success')
            return redirect(url_for('deployment.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error deploying worker: {str(e)}', 'danger')
    
    return render_template('deployment/add.html',
                         companies=companies, 
                         workers=available_workers,
                         today=date.today().isoformat())


@deployment_bp.route('/deployment/end/<int:id>')
def end(id):
    dep = Deployment.query.get_or_404(id)
    dep.is_active = False
    dep.date_to = date.today()
    db.session.commit()
    flash('Deployment ended successfully.', 'info')
    return redirect(url_for('deployment.index'))


@deployment_bp.route('/deployment/bulk-add', methods=['GET', 'POST'])
def bulk_add():
    companies = Company.query.all()
    
    # Get available workers (not deployed)
    active_deployed_ids = [d.worker_id for d in Deployment.query.filter_by(is_active=True).all()]
    
    if active_deployed_ids:
        available_workers = Worker.query.filter(
            Worker.is_active == True,
            ~Worker.id.in_(active_deployed_ids)
        ).all()
    else:
        available_workers = Worker.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        company_id = int(request.form['company_id'])
        post = request.form['post']
        date_from = datetime.strptime(request.form['date_from'], '%Y-%m-%d').date()
        worker_ids = request.form.getlist('worker_ids')

        if not worker_ids:
            flash('Please select at least one employee!', 'warning')
            return redirect(url_for('deployment.bulk_add'))

        count = 0
        for wid in worker_ids:
            wid = int(wid)
            
            # End existing deployment if any
            old = Deployment.query.filter_by(worker_id=wid, is_active=True).first()
            if old:
                old.is_active = False
                old.date_to = date.today()
                db.session.add(old)

            dep = Deployment(
                worker_id=wid,
                company_id=company_id,
                post=post,
                date_from=date_from,
                is_active=True
            )
            db.session.add(dep)
            count += 1

        db.session.commit()
        flash(f'{count} employee(s) deployed successfully!', 'success')
        return redirect(url_for('deployment.index'))

    return render_template('deployment/bulk_add.html',
                         companies=companies,
                         workers=available_workers,
                         today=date.today().isoformat())