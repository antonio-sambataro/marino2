import requests
from app import db
from app.models.menu import Category, Product, PriceList, ProductPrice, VariantCategory, Variant, VariantCategoryAssociation
from app.models.table import Room, Table
from flask import current_app

def sync_with_pos():
    """Sync products, categories, and variants with the POS system."""
    try:
        # Get API URL from configuration
        pos_api_url = current_app.config.get('POS_API_URL')
        if not pos_api_url:
            return {'success': False, 'message': 'POS API URL not configured'}
        
        # Get data from POS API
        response = requests.get(pos_api_url)
        response.raise_for_status()
        data = response.json()
        
        # Import the data
        result = import_data(data)
        
        return result
    except requests.RequestException as e:
        return {'success': False, 'message': f'API connection error: {str(e)}'}
    except Exception as e:
        return {'success': False, 'message': f'Sync error: {str(e)}'}

def import_data(data):
    """Import data from JSON to database."""
    try:
        # Start a transaction
        db.session.begin()
        
        # Import price lists
        if 'lists' in data and data['lists']:
            import_price_lists(data['lists'])
        
        # Import categories
        if 'categories' in data and data['categories']:
            import_categories(data['categories'])
        
        # Import variant categories
        if 'variants_categories' in data and data['variants_categories']:
            import_variant_categories(data['variants_categories'])
        
        # Import products (depends on categories, price lists, variants)
        if 'products' in data and data['products']:
            import_products(data['products'])
        
        # Import rooms
        if 'rooms' in data and data['rooms']:
            import_rooms(data['rooms'])
        
        # Import tables (depends on rooms)
        if 'tables' in data and data['tables']:
            import_tables(data['tables'])
        
        # Commit the transaction
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Data imported successfully',
            'data': {
                'listsCount': len(data.get('lists', [])),
                'categoriesCount': len(data.get('categories', [])),
                'productsCount': len(data.get('products', [])),
                'roomsCount': len(data.get('rooms', [])),
                'tablesCount': len(data.get('tables', [])),
                'variantCategoriesCount': len(data.get('variants_categories', []))
            }
        }
    except Exception as e:
        # Rollback on error
        db.session.rollback()
        return {'success': False, 'message': f'Import error: {str(e)}'}

def export_data():
    """Export all data from database to JSON format."""
    try:
        # Get all data from database
        price_lists = PriceList.query.all()
        categories = Category.query.all()
        products = Product.query.all()
        rooms = Room.query.all()
        tables = Table.query.all()
        variant_categories = VariantCategory.query.all()
        
        # Format data as JSON
        data = {
            'lists': [p.to_dict() for p in price_lists],
            'categories': [c.to_dict() for c in categories],
            'products': [p.to_dict() for p in products],
            'rooms': [r.to_dict() for r in rooms],
            'tables': [t.to_dict() for t in tables],
            'variants_categories': [v.to_dict() for v in variant_categories]
        }
        
        return {'success': True, 'data': data}
    except Exception as e:
        return {'success': False, 'message': f'Export error: {str(e)}'}

def import_price_lists(lists_data):
    """Import price lists from JSON data."""
    for list_data in lists_data:
        price_list = PriceList.query.get(list_data['id'])
        
        if price_list:
            # Update existing price list
            price_list.name = list_data['name']
        else:
            # Create new price list
            price_list = PriceList(id=list_data['id'], name=list_data['name'])
            db.session.add(price_list)

def import_categories(categories_data):
    """Import categories from JSON data."""
    for category_data in categories_data:
        category = Category.query.get(category_data['id'])
        
        if category:
            # Update existing category
            category.name = category_data['name']
            category.shop_id = category_data.get('shop_id')
        else:
            # Create new category
            category = Category(
                id=category_data['id'],
                name=category_data['name'],
                shop_id=category_data.get('shop_id')
            )
            db.session.add(category)

def import_variant_categories(variant_categories_data):
    """Import variant categories from JSON data."""
    for vc_data in variant_categories_data:
        variant_category = VariantCategory.query.get(vc_data['id'])
        
        if variant_category:
            # Update existing variant category
            variant_category.name = vc_data['name']
            variant_category.min = vc_data.get('min', 0)
            variant_category.max = vc_data.get('max', 1)
            variant_category.has_price = vc_data.get('has_price', True)
            
            # Delete existing variants
            Variant.query.filter_by(category_id=variant_category.id).delete()
        else:
            # Create new variant category
            variant_category = VariantCategory(
                id=vc_data['id'],
                name=vc_data['name'],
                min=vc_data.get('min', 0),
                max=vc_data.get('max', 1),
                has_price=vc_data.get('has_price', True)
            )
            db.session.add(variant_category)
        
        # Add variants
        if 'variants' in vc_data and vc_data['variants']:
            for variant_data in vc_data['variants']:
                variant = Variant(
                    id=variant_data['id'],
                    name=variant_data['name'],
                    price=variant_data.get('price', 0),
                    category_id=variant_category.id
                )
                db.session.add(variant)

def import_products(products_data):
    """Import products from JSON data."""
    for product_data in products_data:
        product = Product.query.get(product_data['id'])
        
        if product:
            # Update existing product
            product.name = product_data['name']
            product.description = product_data.get('description', '')
            
            # Clear existing categories
            product.categories = []
            
            # Clear existing variant categories
            VariantCategoryAssociation.query.filter_by(product_id=product.id).delete()
            
            # Delete existing prices
            ProductPrice.query.filter_by(product_id=product.id).delete()
        else:
            # Create new product
            product = Product(
                id=product_data['id'],
                name=product_data['name'],
                description=product_data.get('description', '')
            )
            db.session.add(product)
        
        # Add categories
        if 'categories' in product_data and product_data['categories']:
            for category_id in product_data['categories']:
                category = Category.query.get(category_id)
                if category:
                    product.categories.append(category)
        
        # Add prices
        if 'prices' in product_data and product_data['prices']:
            for price_data in product_data['prices']:
                price = ProductPrice(
                    product_id=product.id,
                    list_id=price_data['list_id'],
                    price=price_data['price']
                )
                db.session.add(price)
        
        # Add variant categories
        if 'variant_categories' in product_data and product_data['variant_categories']:
            for vc_data in product_data['variant_categories']:
                if isinstance(vc_data, dict) and 'variants_category_id' in vc_data:
                    # Handle format from API
                    vc_id = vc_data['variants_category_id']
                elif isinstance(vc_data, int):
                    # Handle simple ID format
                    vc_id = vc_data
                else:
                    continue
                
                vc_assoc = VariantCategoryAssociation(
                    product_id=product.id,
                    variant_category_id=vc_id
                )
                db.session.add(vc_assoc)

def import_rooms(rooms_data):
    """Import rooms from JSON data."""
    for room_data in rooms_data:
        room = Room.query.get(room_data['id'])
        
        if room:
            # Update existing room
            room.name = room_data['name']
            room.shop_id = room_data.get('shop_id')
        else:
            # Create new room
            room = Room(
                id=room_data['id'],
                name=room_data['name'],
                shop_id=room_data.get('shop_id')
            )
            db.session.add(room)

def import_tables(tables_data):
    """Import tables from JSON data."""
    for table_data in tables_data:
        table = Table.query.get(table_data['id'])
        
        if table:
            # Update existing table
            table.name = table_data['name']
            table.room_id = table_data['room_id']
            table.availables_covers = table_data.get('availables_covers', 4)
        else:
            # Create new table
            table = Table(
                id=table_data['id'],
                name=table_data['name'],
                room_id=table_data['room_id'],
                availables_covers=table_data.get('availables_covers', 4)
            )
            db.session.add(table)
