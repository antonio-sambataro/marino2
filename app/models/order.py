
from datetime import datetime
from app import db
from app.models.table import Table  # Add this import

class Order(db.Model):
    """Order model representing customer orders."""
    id = db.Column(db.Integer, primary_key=True)
    delivery_type = db.Column(db.String(20), nullable=False)  # 'shop', 'takeaway', 'delivery'
    delivery_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=True)
    origin = db.Column(db.String(20), nullable=False)  # 'selfordering', 'website', 'glovo', etc.
    status = db.Column(db.String(20), default='confirmed')  # 'confirmed', 'preparing', 'ready', 'completed', 'cancelled'
    total = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # Customer info (optional for shop orders)
    name = db.Column(db.String(100), nullable=True)
    surname = db.Column(db.String(100), nullable=True)
    mobile = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    
    covers = db.Column(db.Integer, nullable=True)
    invoice = db.Column(db.Boolean, default=False)
    delivery_price = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    
    # Relationships
    table = db.relationship('Table', backref='orders')
    order_items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='order', cascade='all, delete-orphan')
    address = db.relationship('DeliveryAddress', uselist=False, back_populates='order', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.id}>'
    
    def to_dict(self):
        """Convert the order to a dictionary."""
        result = {
            'id': self.id,
            'delivery_type': self.delivery_type,
            'delivery_date': self.delivery_date.strftime('%Y-%m-%d %H:%M:%S'),
            'table_id': str(self.table_id) if self.table_id else None,
            'origin': self.origin,
            'status': self.status,
            'total': self.total,
            'notes': self.notes,
            'name': self.name,
            'surname': self.surname,
            'mobile': self.mobile,
            'email': self.email,
            'covers': self.covers,
            'invoice': 1 if self.invoice else 0,
            'delivery_price': self.delivery_price,
            'products': [item.to_dict() for item in self.order_items],
            'discount': self.discount,
            'payments': [payment.to_dict() for payment in self.payments]
        }
        
        if self.address:
            result['delivery_address'] = self.address.to_dict()
        else:
            result['delivery_address'] = None
            
        return result

class OrderItem(db.Model):
    """Order item model representing products in an order."""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Product')
    variants = db.relationship('OrderVariant', back_populates='order_item', cascade='all, delete-orphan')
    sub_products = db.relationship('OrderSubProduct', back_populates='parent_item', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'
    
    def to_dict(self):
        """Convert the order item to a dictionary."""
        return {
            'id': str(self.product_id),
            'qty': str(self.qty),
            'price': self.price,
            'notes': self.notes,
            'variants': [variant.to_dict() for variant in self.variants],
            'products': [sub.to_dict() for sub in self.sub_products]
        }

class OrderVariant(db.Model):
    """Order variant model representing product variants in an order item."""
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_item.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('variant.id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False, default=0.0)
    
    # Relationships
    order_item = db.relationship('OrderItem', back_populates='variants')
    variant = db.relationship('Variant')
    
    def __repr__(self):
        return f'<OrderVariant {self.id}>'
    
    def to_dict(self):
        """Convert the order variant to a dictionary."""
        return {
            'id': str(self.variant_id),
            'qty': str(self.qty),
            'price': self.price
        }

class OrderSubProduct(db.Model):
    """Order sub-product model representing products inside another product."""
    id = db.Column(db.Integer, primary_key=True)
    parent_item_id = db.Column(db.Integer, db.ForeignKey('order_item.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    # Relationships
    parent_item = db.relationship('OrderItem', back_populates='sub_products')
    product = db.relationship('Product')
    
    def __repr__(self):
        return f'<OrderSubProduct {self.id}>'
    
    def to_dict(self):
        """Convert the order sub-product to a dictionary."""
        return {
            'id': str(self.product_id),
            'qty': str(self.qty),
            'price': self.price
        }

class Payment(db.Model):
    """Payment model representing order payments."""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_method.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    
    # Relationships
    order = db.relationship('Order', back_populates='payments')
    payment_method = db.relationship('PaymentMethod')
    
    def __repr__(self):
        return f'<Payment {self.id}>'
    
    def to_dict(self):
        """Convert the payment to a dictionary."""
        return {
            'id': str(self.payment_method_id),
            'name': self.payment_method.name,
            'amount': self.amount
        }

class PaymentMethod(db.Model):
    """Payment method model representing available payment methods."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<PaymentMethod {self.name}>'
    
    def to_dict(self):
        """Convert the payment method to a dictionary."""
        return {
            'id': self.id,
            'name': self.name
        }

class DeliveryAddress(db.Model):
    """Delivery address model for delivery orders."""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    number = db.Column(db.String(20), nullable=True)
    zipcode = db.Column(db.String(20), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    province = db.Column(db.String(20), nullable=True)
    doorphone = db.Column(db.String(100), nullable=True)
    coord = db.Column(db.String(100), nullable=True)
    
    # Relationships
    order = db.relationship('Order', back_populates='address')
    
    def __repr__(self):
        return f'<DeliveryAddress {self.id}>'
    
    def to_dict(self):
        """Convert the delivery address to a dictionary."""
        return {
            'address': self.address,
            'number': self.number,
            'zipcode': self.zipcode,
            'city': self.city,
            'province': self.province,
            'doorphone': self.doorphone,
            'coord': self.coord
        }
