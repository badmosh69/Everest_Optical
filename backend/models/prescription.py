from extensions import db

class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Right Eye (RE)
    re_sph = db.Column(db.Numeric(5, 2))
    re_cyl = db.Column(db.Numeric(5, 2))
    re_axis = db.Column(db.Integer)
    
    # Left Eye (LE)
    le_sph = db.Column(db.Numeric(5, 2))
    le_cyl = db.Column(db.Numeric(5, 2))
    le_axis = db.Column(db.Integer)
    
    image_path = db.Column(db.String(255)) # Path to uploaded image
    
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    customer = db.relationship('Customer', backref=db.backref('prescriptions', lazy=True, order_by='Prescription.created_at.desc()'))
    creator = db.relationship('User')

    def __repr__(self):
        return f'<Prescription {self.id} for Customer {self.customer_id}>'
