from extensions import db

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(10), nullable=False) # INSERT, UPDATE, DELETE
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    field_name = db.Column(db.String(50))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    # Relationship
    user = db.relationship('User')

    def __repr__(self):
        return f'<AuditLog {self.action} {self.table_name}:{self.record_id}>'
