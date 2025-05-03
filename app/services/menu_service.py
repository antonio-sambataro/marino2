from app import db
from app.models.menu import (
    Category, Product, PriceList, ProductPrice,
    VariantCategory, Variant, VariantCategoryAssociation
)

# Category functions
def get_categories(category_id=None):
    """Get all categories or a specific category by ID."""
    try:
        if category_id:
            category = Category.query.get(category_id)
            if not category:
                return {'success': False, 'message': 'Category not found'}
            return {'success': True, 'data': category.to_dict()}
        
        categories = Category.query.all()
        return {'success': True, 'data': [category.to_dict() for category in categories]}
    except Exception as e:
        return {'success': False, 'message': f'Error retrieving categories: {str(e)}'}

def create_category(name, shop_id=None):
    """Create a new category."""
    try:
        category = Category(name=name, shop_id=shop_id)
        db.session.add(category)
        db.session.commit()
        
        return {'success': True, 'data': category.to_dict(), 'message': 'Category created successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error creating category: {str(e)}'}

def update_category(category_id, name, shop_id=None):
    """Update an existing category."""
    try:
        category = Category.query.get(category_id)
        
        if not category:
            return {'success': False, 'message': 'Category not found'}
        
        category.name = name
        if shop_id is not None:
            category.shop_id = shop_id
        
        db.session.commit()
        
        return {'success': True, 'data': category.to_dict(), 'message': 'Category updated successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error updating category: {str(e)}'}

def delete_category(category_id):
    """Delete a category."""
    try:
        category = Category.query.get(category_id)
        
        if not category:
            return {'success': False, 'message': 'Category not found'}
        
        db.session.delete(category)
        db.session.commit()
        
        return {'success': True, 'message': 'Category deleted successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error deleting category: {str(e)}'}

# Product functions
def get_products(product_id=None, category_id=None, price_list_id=None):
    """Get all products or a specific product by ID with optional filtering."""
    try:
        if product_id:
            product = Product.query.get(product_id)
            if not product:
                return {'success': False, 'message': 'Product not found'}
            return {'success': True, 'data': product.to_dict()}
        
        query = Product.query
        
        if category_id:
            query = query.filter(Product.categories.any(id=category_id))
        
        if price_list_id:
            query = query.join(ProductPrice).filter(ProductPrice.list_id == price_list_id)
        
        products = query.all()
        return {'success': True, 'data': [product.to_dict() for product in products]}
    except Exception as e:
        return {'success': False, 'message': f'Error retrieving products: {str(e)}'}

def create_product(data):
    """Create a new product."""
    try:
        # Start a transaction
        db.session.begin()
        
        # Create product
        product = Product(
            name=data.get('name'),
            description=data.get('description', '')
        )
        
        # Add categories
        if 'categories' in data and data['categories']:
            for category_id in data['categories']:
                category = Category.query.get(category_id)
                if category:
                    product.categories.append(category)
        
        db.session.add(product)
        db.session.flush()  # Flush to get product ID
        
        # Add prices
        if 'prices' in data and data['prices']:
            for price_data in data['prices']:
                price = ProductPrice(
                    product_id=product.id,
                    list_id=price_data.get('list_id'),
                    price=price_data.get('price', 0)
                )
                db.session.add(price)
        
        # Add variant categories
        if 'variant_categories' in data and data['variant_categories']:
            for variant_category_id in data['variant_categories']:
                variant_category = VariantCategoryAssociation(
                    product_id=product.id,
                    variant_category_id=variant_category_id
                )
                db.session.add(variant_category)
        
        # Commit the transaction
        db.session.commit()
        
        return {'success': True, 'data': product.to_dict(), 'message': 'Product created successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error creating product: {str(e)}'}

def update_product(product_id, data):
    """Update an existing product."""
    try:
        # Start a transaction
        db.session.begin()
        
        product = Product.query.get(product_id)
        
        if not product:
            return {'success': False, 'message': 'Product not found'}
        
        # Update basic info
        if 'name' in data:
            product.name = data['name']
        
        if 'description' in data:
            product.description = data['description']
        
        # Update categories
        if 'categories' in data:
            # Clear existing categories
            product.categories = []
            
            # Add new categories
            for category_id in data['categories']:
                category = Category.query.get(category_id)
                if category:
                    product.categories.append(category)
        
        # Update prices
        if 'prices' in data:
            # Clear existing prices
            ProductPrice.query.filter_by(product_id=product.id).delete()
            
            # Add new prices
            for price_data in data['prices']:
                price = ProductPrice(
                    product_id=product.id,
                    list_id=price_data.get('list_id'),
                    price=price_data.get('price', 0)
                )
                db.session.add(price)
        
        # Update variant categories
        if 'variant_categories' in data:
            # Clear existing variant categories
            VariantCategoryAssociation.query.filter_by(product_id=product.id).delete()
            
            # Add new variant categories
            for variant_category_id in data['variant_categories']:
                variant_category = VariantCategoryAssociation(
                    product_id=product.id,
                    variant_category_id=variant_category_id
                )
                db.session.add(variant_category)
        
        # Commit the transaction
        db.session.commit()
        
        return {'success': True, 'data': product.to_dict(), 'message': 'Product updated successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error updating product: {str(e)}'}

def delete_product(product_id):
    """Delete a product."""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return {'success': False, 'message': 'Product not found'}
        
        db.session.delete(product)
        db.session.commit()
        
        return {'success': True, 'message': 'Product deleted successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error deleting product: {str(e)}'}

# Price list functions
def get_price_lists(price_list_id=None):
    """Get all price lists or a specific price list by ID."""
    try:
        if price_list_id:
            price_list = PriceList.query.get(price_list_id)
            if not price_list:
                return {'success': False, 'message': 'Price list not found'}
            return {'success': True, 'data': price_list.to_dict()}
        
        price_lists = PriceList.query.all()
        return {'success': True, 'data': [price_list.to_dict() for price_list in price_lists]}
    except Exception as e:
        return {'success': False, 'message': f'Error retrieving price lists: {str(e)}'}

def create_price_list(name):
    """Create a new price list."""
    try:
        price_list = PriceList(name=name)
        db.session.add(price_list)
        db.session.commit()
        
        return {'success': True, 'data': price_list.to_dict(), 'message': 'Price list created successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error creating price list: {str(e)}'}

def update_price_list(price_list_id, name):
    """Update an existing price list."""
    try:
        price_list = PriceList.query.get(price_list_id)
        
        if not price_list:
            return {'success': False, 'message': 'Price list not found'}
        
        price_list.name = name
        db.session.commit()
        
        return {'success': True, 'data': price_list.to_dict(), 'message': 'Price list updated successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error updating price list: {str(e)}'}

def delete_price_list(price_list_id):
    """Delete a price list."""
    try:
        price_list = PriceList.query.get(price_list_id)
        
        if not price_list:
            return {'success': False, 'message': 'Price list not found'}
        
        db.session.delete(price_list)
        db.session.commit()
        
        return {'success': True, 'message': 'Price list deleted successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error deleting price list: {str(e)}'}

# Variant category functions
def get_variant_categories(variant_category_id=None):
    """Get all variant categories or a specific variant category by ID."""
    try:
        if variant_category_id:
            variant_category = VariantCategory.query.get(variant_category_id)
            if not variant_category:
                return {'success': False, 'message': 'Variant category not found'}
            return {'success': True, 'data': variant_category.to_dict()}
        
        variant_categories = VariantCategory.query.all()
        return {'success': True, 'data': [variant_category.to_dict() for variant_category in variant_categories]}
    except Exception as e:
        return {'success': False, 'message': f'Error retrieving variant categories: {str(e)}'}

def create_variant_category(data):
    """Create a new variant category."""
    try:
        # Start a transaction
        db.session.begin()
        
        # Create variant category
        variant_category = VariantCategory(
            name=data.get('name'),
            min=data.get('min', 0),
            max=data.get('max', 1),
            has_price=data.get('has_price', True)
        )
        
        db.session.add(variant_category)
        db.session.flush()  # Flush to get variant category ID
        
        # Add variants
        if 'variants' in data and data['variants']:
            for variant_data in data['variants']:
                variant = Variant(
                    name=variant_data.get('name'),
                    price=variant_data.get('price', 0),
                    category_id=variant_category.id
                )
                db.session.add(variant)
        
        # Commit the transaction
        db.session.commit()
        
        return {'success': True, 'data': variant_category.to_dict(), 'message': 'Variant category created successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error creating variant category: {str(e)}'}

def update_variant_category(variant_category_id, data):
    """Update an existing variant category."""
    try:
        # Start a transaction
        db.session.begin()
        
        variant_category = VariantCategory.query.get(variant_category_id)
        
        if not variant_category:
            return {'success': False, 'message': 'Variant category not found'}
        
        # Update basic info
        if 'name' in data:
            variant_category.name = data['name']
        
        if 'min' in data:
            variant_category.min = data['min']
        
        if 'max' in data:
            variant_category.max = data['max']
        
        if 'has_price' in data:
            variant_category.has_price = data['has_price']
        
        # Update variants
        if 'variants' in data:
            # Delete existing variants
            Variant.query.filter_by(category_id=variant_category.id).delete()
            
            # Add new variants
            for variant_data in data['variants']:
                variant = Variant(
                    name=variant_data.get('name'),
                    price=variant_data.get('price', 0),
                    category_id=variant_category.id
                )
                db.session.add(variant)
        
        # Commit the transaction
        db.session.commit()
        
        return {'success': True, 'data': variant_category.to_dict(), 'message': 'Variant category updated successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error updating variant category: {str(e)}'}

def delete_variant_category(variant_category_id):
    """Delete a variant category."""
    try:
        variant_category = VariantCategory.query.get(variant_category_id)
        
        if not variant_category:
            return {'success': False, 'message': 'Variant category not found'}
        
        db.session.delete(variant_category)
        db.session.commit()
        
        return {'success': True, 'message': 'Variant category deleted successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error deleting variant category: {str(e)}'}
