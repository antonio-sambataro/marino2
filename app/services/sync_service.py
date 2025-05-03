import requests
import json
import os
import logging
from datetime import datetime
from app import db
from app.models.menu import Category, Product, PriceList, ProductPrice, VariantCategory, Variant, VariantCategoryAssociation
from app.models.table import Room, Table
from flask import current_app
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

def sync_with_pos():
    """Sync products, categories, and variants with the POS system."""
    try:
        # Get API URL from configuration
        pos_api_url = current_app.config.get('POS_API_URL')
        if not pos_api_url:
            return {'success': False, 'message': 'POS API URL not configured'}
        
        logger.info(f"Starting sync with POS system: {pos_api_url}")
        
        # First backup current data
        backup_result = backup_data()
        if not backup_result['success']:
            logger.error(f"Failed to backup data before sync: {backup_result['message']}")
            return {'success': False, 'message': f"Failed to backup data: {backup_result['message']}"}
        
        # Get data from POS API with timeout and error handling
        try:
            response = requests.get(pos_api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"API connection error: {str(e)}")
            return {'success': False, 'message': f'API connection error: {str(e)}'}
        
        # Import the data
        result = import_data(data)
        
        if not result['success']:
            # If import failed, try to restore from backup
            logger.error(f"Sync failed, attempting to restore from backup: {result['message']}")
            restore_result = restore_from_backup()
            if restore_result['success']:
                return {'success': False, 'message': f"Sync failed but data restored from backup: {result['message']}"}
            else:
                return {'success': False, 'message': f"Sync failed and restore failed: {result['message']}. Restore error: {restore_result['message']}"}
        
        # Update last sync timestamp
        update_sync_timestamp()
        
        return result
    except Exception as e:
        logger.exception(f"Unexpected error during sync: {str(e)}")
        return {'success': False, 'message': f'Sync error: {str(e)}'}

def backup_data():
    """Backup data before sync."""
    try:
        # Get current data
        data = export_data()
        
        if not data['success']:
            return {'success': False, 'message': f"Failed to export data for backup: {data['message']}"}
        
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(current_app.root_path, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Save backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.json')
        
        with open(backup_file, 'w') as f:
            json.dump(data['data'], f, indent=2)
        
        logger.info(f"Data backup created: {backup_file}")
        return {'success': True, 'message': 'Data backup created successfully', 'file': backup_file}
    except Exception as e:
        logger.exception(f"Backup error: {str(e)}")
        return {'success': False, 'message': f'Backup error: {str(e)}'}

def restore_from_backup():
    """Restore data from latest backup."""
    try:
        # Find latest backup
        backup_dir = os.path.join(current_app.root_path, 'backups')
        if not os.path.exists(backup_dir):
            return {'success': False, 'message': 'No backup directory found'}
        
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('backup_') and f.endswith('.json')]
        if not backup_files:
            return {'success': False, 'message': 'No backup files found'}
        
        # Sort by timestamp (filename)
        backup_files.sort(reverse=True)
        latest_backup = os.path.join(backup_dir, backup_files[0])
        
        # Load backup data
        with open(latest_backup, 'r') as f:
            backup_data = json.load(f)
        
        # Clear current data
        clear_database()
        
        # Import data from backup
        result = import_data(backup_data)
        
        if result['success']:
            logger.info(f"Data restored from backup: {latest_backup}")
            return {'success': True, 'message': 'Data restored from backup successfully'}
        else:
            return {'success': False, 'message': f"Failed to restore from backup: {result['message']}"}
    except Exception as e:
        logger.exception(f"Restore error: {str(e)}")
        return {'success': False, 'message': f'Restore error: {str(e)}'}

def clear_database():
    """Clear all data from database tables to prepare for import."""
    try:
        # Delete in reverse order of dependencies
        VariantCategoryAssociation.query.delete()
        Variant.query.delete()
        VariantCategory.query.delete()
        ProductPrice.query.delete()
        Product.query.delete()
        Category.query.delete()
        PriceList.query.delete()
        Table.query.delete()
        Room.query.delete()
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error clearing database: {str(e)}")
        return False

def update_sync_timestamp():
    """Update the last sync timestamp."""
    try:
        sync_info_file = os.path.join(current_app.root_path, 'config', 'sync_info.json')
        
        sync_info = {
            'last_sync': datetime.now().isoformat(),
            'status': 'ok'
        }
        
        with open(sync_info_file, 'w') as f:
            json.dump(sync_info, f)
        
        return True
    except Exception as e:
        logger.error(f"Error updating sync timestamp: {str(e)}")
        return False

def get_sync_status():
    """Get the current sync status."""
    try:
        sync_info_file = os.path.join(current_app.root_path, 'config', 'sync_info.json')
        
        if not os.path.exists(sync_info_file):
            return {
                'success': True,
                'status': 'never_synced',
                'last_sync': None,
                'message': 'System has never been synchronized'
            }
        
        with open(sync_info_file, 'r') as f:
            sync_info = json.load(f)
        
        return {
            'success': True,
            'status': sync_info.get('status', 'unknown'),
            'last_sync': sync_info.get('last_sync'),
            'message': 'Sync status retrieved successfully'
        }
    except Exception as e:
        return {
            'success': False,
            'status': 'error',
            'message': f'Error retrieving sync status: {str(e)}'
        }

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
    except IntegrityError as e:
        # Handle integrity errors (e.g., duplicate keys)
        db.session.rollback()
        logger.exception(f"Database integrity error during import: {str(e)}")
        return {'success': False, 'message': f'Database integrity error: {str(e)}'}
    except Exception as e:
        # Rollback on error
        db.session.rollback()
        logger.exception(f"Import error: {str(e)}")
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
        logger.exception(f"Export error: {str(e)}")
        return {'success': False, 'message': f'Export error: {str(e)}'}

# The rest of the import functions remain mostly unchanged, but with added error handling

def import_price_lists(lists_data):
    """Import price lists from JSON data."""
    for list_data in lists_data:
        try:
            price_list = PriceList.query.get(list_data['id'])
            
            if price_list:
                # Update existing price list
                price_list.name = list_data['name']
            else:
                # Create new price list
                price_list = PriceList(id=list_data['id'], name=list_data['name'])
                db.session.add(price_list)
        except Exception as e:
            logger.warning(f"Error importing price list {list_data.get('id')}: {str(e)}")
            continue

def import_categories(categories_data):
    """Import categories from JSON data."""
    for category_data in categories_data:
        try:
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
        except Exception as e:
            logger.warning(f"Error importing category {category_data.get('id')}: {str(e)}")
            continue

def import_variant_categories(variant_categories_data):
    """Import variant categories from JSON data."""
    for vc_data in variant_categories_data:
        try:
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
        except Exception as e:
            logger.warning(f"Error importing variant category {vc_data.get('id')}: {str(e)}")
            continue

def import_products(products_data):
    """Import products from JSON data."""
    for product_data in products_data:
        try:
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
        except Exception as e:
            logger.warning(f"Error importing product {product_data.get('id')}: {str(e)}")
            continue

def import_rooms(rooms_data):
    """Import rooms from JSON data."""
    for room_data in rooms_data:
        try:
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
        except Exception as e:
            logger.warning(f"Error importing room {room_data.get('id')}: {str(e)}")
            continue

def import_tables(tables_data):
    """Import tables from JSON data."""
    for table_data in tables_data:
        try:
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
        except Exception as e:
            logger.warning(f"Error importing table {table_data.get('id')}: {str(e)}")
            continue