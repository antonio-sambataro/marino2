from app import db

# Association table for product categories
product_category_assoc = db.Table('product_category',
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

class Category(db.Model):
    """Category model for product categorization."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    shop_id = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self):
        """Convert the category to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'shop_id': self.shop_id
        }

class PriceList(db.Model):
    """Price list model for product pricing."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<PriceList {self.name}>'
    
    def to_dict(self):
        """Convert the price list to a dictionary."""
        return {
            'id': self.id,
            'name': self.name
        }

class Product(db.Model):
    """Product model representing menu items."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Many-to-many relationship with categories
    categories = db.relationship('Category', secondary=product_category_assoc, backref=db.backref('products', lazy='dynamic'))
    
    # Relationship with prices
    prices = db.relationship('ProductPrice', back_populates='product', cascade='all, delete-orphan')
    
    # Relationship with variant categories
    variant_categories = db.relationship('VariantCategoryAssociation', back_populates='product', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def to_dict(self):
        """Convert the product to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'categories': [cat.id for cat in self.categories],
            'prices': [price.to_dict() for price in self.prices],
            'variant_categories': [assoc.variant_category_id for assoc in self.variant_categories]
        }
    
    def get_price(self, price_list_id):
        """Get the product price for a specific price list."""
        for price in self.prices:
            if price.list_id == price_list_id:
                return price.price
        return None

class ProductPrice(db.Model):
    """Product price for a specific price list."""
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('price_list.id'), primary_key=True)
    price = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product', back_populates='prices')
    price_list = db.relationship('PriceList')
    
    def __repr__(self):
        return f'<ProductPrice {self.product_id}:{self.list_id}>'
    
    def to_dict(self):
        """Convert the product price to a dictionary."""
        return {
            'list_id': self.list_id,
            'price': self.price
        }

class VariantCategory(db.Model):
    """Variant category model for product customization."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    min = db.Column(db.Integer, default=0)
    max = db.Column(db.Integer, default=1)
    has_price = db.Column(db.Boolean, default=True)
    
    # Relationship with variants
    variants = db.relationship('Variant', back_populates='category', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<VariantCategory {self.name}>'
    
    def to_dict(self):
        """Convert the variant category to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'min': self.min,
            'max': self.max,
            'has_price': self.has_price,
            'variants': [variant.to_dict() for variant in self.variants]
        }

class Variant(db.Model):
    """Variant model for product options."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, default=0)
    
    category_id = db.Column(db.Integer, db.ForeignKey('variant_category.id'), nullable=False)
    category = db.relationship('VariantCategory', back_populates='variants')
    
    def __repr__(self):
        return f'<Variant {self.name}>'
    
    def to_dict(self):
        """Convert the variant to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price
        }

class VariantCategoryAssociation(db.Model):
    """Association between products and variant categories."""
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    variant_category_id = db.Column(db.Integer, db.ForeignKey('variant_category.id'), primary_key=True)
    
    product = db.relationship('Product', back_populates='variant_categories')
    variant_category = db.relationship('VariantCategory')
    
    def __repr__(self):
        return f'<VariantCategoryAssociation {self.product_id}:{self.variant_category_id}>'
