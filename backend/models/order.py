from extensions import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'))
    
    status = db.Column(db.String(20), default='Pending')
    delivery_mode = db.Column(db.String(50), default='Self') # Self, Courier, Home
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    delivery_date = db.Column(db.Date)
    
    advance_amount = db.Column(db.Numeric(10, 2), default=0.00)
    discount = db.Column(db.Numeric(10, 2), default=0.00)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    # Balance is calculated column in DB, but mapped here as readonly or processed in app
    # SQLAlchemy doesn't always play nice with GENERATED ALWAYS AS, so we can calculate it in python for display
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    customer = db.relationship('Customer', backref=db.backref('orders', lazy=True, order_by='Order.created_at.desc()'))
    prescription = db.relationship('Prescription')
    creator = db.relationship('User')
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

    @property
    def balance_amount(self):
        # Total is already net of discount? No, usually Total = (Items * Price) - Discount. 
        # But here total_amount is stored in DB. 
        # Let's assume total_amount IS the final amount to be paid.
        # So Balance = Total - Advance.
        # Wait, if I add discount, does total_amount change? 
        # Yes, in the route I should calculate total_amount = (Sum Items) - Discount.
        # So this property remains: Total - Advance.
        return (self.total_amount or 0) - (self.advance_amount or 0)

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id')) # Nullable for now until Inv Phase
    
    # We store these explicitly to preserve history even if inventory price changes
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Relationships
    # inventory = db.relationship('Inventory') # Uncomment in Phase 6

    @property
    def total_price(self):
        return (self.quantity or 0) * (self.unit_price or 0)
