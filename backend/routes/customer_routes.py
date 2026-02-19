from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models.customer import Customer

customer_bp = Blueprint('customer', __name__, url_prefix='/customers')

@customer_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    
    query = Customer.query

    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            (Customer.name.ilike(search_filter)) | 
            (Customer.phone.ilike(search_filter)) |
            (Customer.care_of.ilike(search_filter))
        )
    
    # Order by most recently updated/created
    customers = query.order_by(Customer.updated_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('customers/list.html', customers=customers, search_query=search_query)

@customer_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        care_of = request.form.get('care_of')
        phone = request.form.get('phone')
        
        # Basic validation
        if not name or not phone:
            flash('Name and Phone are required!', 'danger')
            return redirect(url_for('customer.add'))

        new_customer = Customer(name=name, care_of=care_of, phone=phone)
        
        try:
            db.session.add(new_customer)
            db.session.commit()
            flash('Customer added successfully!', 'success')
            return redirect(url_for('customer.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding customer: {str(e)}', 'danger')

    return render_template('customers/add.html')

@customer_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        customer.name = request.form.get('name')
        customer.care_of = request.form.get('care_of')
        customer.phone = request.form.get('phone')
        
        try:
            db.session.commit()
            flash('Customer updated successfully!', 'success')
            return redirect(url_for('customer.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating customer: {str(e)}', 'danger')
            
    return render_template('customers/edit.html', customer=customer)
