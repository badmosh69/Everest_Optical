from flask import Blueprint, render_template
from flask_login import login_required, current_user
from extensions import db
from models.customer import Customer
from models.order import Order
from models.inventory import Inventory
from models.audit_log import AuditLog
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Key Metrics
    total_customers = Customer.query.count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='Pending').count()
    low_stock_items = Inventory.query.filter(Inventory.quantity <= Inventory.low_stock_threshold).count()
    
    # Total Revenue (Sum of total_amount from Orders)
    revenue_result = db.session.query(func.sum(Order.total_amount)).scalar()
    total_revenue = revenue_result if revenue_result else 0.0

    # Recent Activity (Last 5 Audit Logs)
    recent_activity = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(5).all()
    
    # Recent Orders (Last 5)
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

    return render_template('dashboard/index.html', 
                           user=current_user,
                           total_customers=total_customers,
                           total_orders=total_orders,
                           pending_orders=pending_orders,
                           low_stock_items=low_stock_items,
                           total_revenue=total_revenue,
                           recent_activity=recent_activity,
                           recent_orders=recent_orders)
