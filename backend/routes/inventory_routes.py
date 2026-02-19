from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models.inventory import Inventory

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Inventory.query
    
    if search:
        query = query.filter(
            (Inventory.model_name.ilike(f'%{search}%')) |
            (Inventory.brand.ilike(f'%{search}%')) |
            (Inventory.frame_type.ilike(f'%{search}%'))
        )
    
    # Sort by low stock first, then name
    # We can't easily sort by property 'is_low_stock' in SQL, so we'll just sort by updated_at for now
    # or we can do quantity ASC to show low stock first.
    items = query.order_by(Inventory.quantity.asc()).paginate(page=page, per_page=15)
    
    return render_template('inventory/list.html', items=items, search=search)

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        try:
            new_item = Inventory(
                model_name=request.form.get('model_name'),
                brand=request.form.get('brand'),
                frame_type=request.form.get('frame_type'),
                quantity=int(request.form.get('quantity', 0)),
                location=request.form.get('location'),
                shop_branch=request.form.get('shop_branch'),
                cost_price=float(request.form.get('cost_price', 0)),
                selling_price=float(request.form.get('selling_price', 0)),
                low_stock_threshold=int(request.form.get('low_stock_threshold', 5))
            )
            db.session.add(new_item)
            db.session.commit()
            flash('Item added to inventory!', 'success')
            return redirect(url_for('inventory.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding item: {str(e)}', 'danger')

    return render_template('inventory/add.html')

@inventory_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    item = Inventory.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            item.model_name = request.form.get('model_name')
            item.brand = request.form.get('brand')
            item.frame_type = request.form.get('frame_type')
            item.quantity = int(request.form.get('quantity', 0))
            item.location = request.form.get('location')
            item.shop_branch = request.form.get('shop_branch')
            item.cost_price = float(request.form.get('cost_price', 0))
            item.selling_price = float(request.form.get('selling_price', 0))
            item.low_stock_threshold = int(request.form.get('low_stock_threshold', 5))
            
            db.session.commit()
            flash('Inventory updated!', 'success')
            return redirect(url_for('inventory.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating item: {str(e)}', 'danger')

    return render_template('inventory/edit.html', item=item)
