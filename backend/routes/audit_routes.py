from flask import Blueprint, render_template, request
from flask_login import login_required
from models.audit_log import AuditLog

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    table_filter = request.args.get('table_name', '')
    
    query = AuditLog.query
    
    if table_filter:
        query = query.filter(AuditLog.table_name == table_filter)
        
    logs = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=20)
    
    return render_template('audit/list.html', logs=logs, table_filter=table_filter)
