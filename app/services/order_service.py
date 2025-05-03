from datetime import datetime
from app import db
from app.models.order import Order, OrderItem, OrderVariant, OrderSubProduct, Payment, DeliveryAddress, PaymentMethod
from app.models.menu import Product, Variant
from app.models.table import Table
from sqlalchemy.orm import joinedload

def validate_order_data(data):
    """Validate order data before processing."""
    errors = []
    
    # Check required fields
    if 'delivery_type' not in data:
        errors.append('Missing required field: delivery_type')
    
    # Validate delivery type
    valid_delivery_types = ['shop', 'takeaway', 'delivery']
    if 'delivery_type' in data and data['delivery_type'] not in valid_delivery_types:
        errors.append(f"Invalid delivery_type. Must be one of: {', '.join(valid_delivery_types)}")
    
    # Validate table_id if delivery_type is 'shop'
    if data.get('delivery_type') == 'shop' and not data.get('table_id'):
        errors.append('Table ID is required for shop orders')
    
    # Validate table existence if provided
    if data.get('table_id'):
        table = Table.query.get(data.get('table_id'))
        if not table:
            errors.append(f"Table with ID {data.get('table_id')} not found")
    
    # Validate delivery address for delivery orders
    if data.get('delivery_type') == 'delivery':
        if not data.get('delivery_address') or not data.get('delivery_address', {}).get('address'):
            errors.append('Delivery address is required for delivery orders')
    
    # Validate origin
    valid_origins = ['selfordering', 'website', 'glovo', 'telephonic', 'direct']
    if 'origin' in data and data['origin'] not in valid_origins:
        errors.append(f"Invalid origin. Must be one of: {', '.join(valid_origins)}")
    
    # Validate products if provided
    if 'products' in data and data['products']:
        for i, product in enumerate(data['products']):
            # Check product_id or id
            product_id = product.get('id') or product.get('product_id')
            if not product_id:
                errors.append(f"Missing product ID in product at index {i}")
                continue
                
            # Verify product exists
            db_product = Product.query.get(product_id)
            if not db_product:
                errors.append(f"Product with ID {product_id} not found")
    
    # Validate payments if provided
    if 'payments' in data and data['payments']:
        for i, payment in enumerate(data['payments']):
            if not payment.get('id'):
                errors.append(f"Missing payment method ID in payment at index {i}")
            
            if not payment.get('amount'):
                errors.append(f"Missing amount in payment at index {i}")
    
    return errors

def get_orders(delivery_type=None, status=None, start_date=None, end_date=None):
    """Get all orders with optional filtering."""
    try:
        # Use eager loading to reduce database queries
        query = Order.query.options(
            joinedload(Order.table),
            joinedload(Order.order_items).joinedload(OrderItem.product),
            joinedload(Order.payments).joinedload(Payment.payment_method),
            joinedload(Order.address)
        )
        
        if delivery_type:
            query = query.filter(Order.delivery_type == delivery_type)
        
        if status:
            query = query.filter(Order.status == status)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Order.delivery_date >= start_date_obj)
            except ValueError:
                return {'success': False, 'message': 'Invalid start date format. Use YYYY-MM-DD'}, 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                end_date_obj = datetime.combine(end_date_obj.date(), datetime.max.time())
                query = query.filter(Order.delivery_date <= end_date_obj)
            except ValueError:
                return {'success': False, 'message': 'Invalid end date format. Use YYYY-MM-DD'}, 400
        
        # Order by delivery date, newest first
        query = query.order_by(Order.delivery_date.desc())
        
        orders = query.all()
        
        return {
            'success': True, 
            'data': [order.to_dict() for order in orders]
        }
    except Exception as e:
        return {'success': False, 'message': f'Error retrieving orders: {str(e)}'}, 500

def get_order(order_id):
    """Get an order by ID."""
    try:
        # Use eager loading for related data
        order = Order.query.options(
            joinedload(Order.table),
            joinedload(Order.order_items).joinedload(OrderItem.product),
            joinedload(Order.order_items).joinedload(OrderItem.variants).joinedload(OrderVariant.variant),
            joinedload(Order.order_items).joinedload(OrderItem.sub_products).joinedload(OrderSubProduct.product),
            joinedload(Order.payments).joinedload(Payment.payment_method),
            joinedload(Order.address)
        ).get(order_id)
        
        if not order:
            return {'success': False, 'message': 'Order not found'}, 404
        
        return {
            'success': True,
            'data': order.to_dict()
        }
    except Exception as e:
        return {'success': False, 'message': f'Error retrieving order: {str(e)}'}, 500

def create_order(order_data):
    """Create a new order."""
    try:
        # Validate order data
        validation_errors = validate_order_data(order_data)
        if validation_errors:
            return {
                'success': False, 
                'message': 'Validation errors', 
                'errors': validation_errors
            }, 400
        
        # Parse delivery date
        delivery_date = None
        if 'delivery_date' in order_data and order_data['delivery_date']:
            try:
                delivery_date = datetime.strptime(order_data['delivery_date'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return {'success': False, 'message': 'Invalid delivery date format. Use YYYY-MM-DD HH:MM:SS'}, 400
        else:
            delivery_date = datetime.utcnow()
        
        # Start a transaction
        db.session.begin()
        
        # Create the order
        order = Order(
            delivery_type=order_data.get('delivery_type'),
            delivery_date=delivery_date,
            table_id=int(order_data.get('table_id')) if order_data.get('table_id') else None,
            origin=order_data.get('origin', 'website'),
            status=order_data.get('status', 'confirmed'),
            total=float(order_data.get('total', 0)),
            notes=order_data.get('notes'),
            name=order_data.get('name'),
            surname=order_data.get('surname'),
            mobile=order_data.get('mobile'),
            email=order_data.get('email'),
            covers=int(order_data.get('covers')) if order_data.get('covers') else None,
            invoice=bool(int(order_data.get('invoice', 0))),
            delivery_price=float(order_data.get('delivery_price', 0)),
            discount=float(order_data.get('discount', 0))
        )
        
        # Add delivery address if provided
        if order_data.get('delivery_address'):
            addr_data = order_data['delivery_address']
            address = DeliveryAddress(
                address=addr_data.get('address', ''),
                number=addr_data.get('number'),
                zipcode=addr_data.get('zipcode'),
                city=addr_data.get('city'),
                province=addr_data.get('province'),
                doorphone=addr_data.get('doorphone'),
                coord=addr_data.get('coord')
            )
            order.address = address
        
        # Add order items
        if 'products' in order_data and order_data['products']:
            for item_data in order_data['products']:
                # Get product ID - handle both 'id' and 'product_id' in the JSON
                product_id = item_data.get('id') or item_data.get('product_id')
                if not product_id:
                    continue
                
                # Verify product exists
                product = Product.query.get(int(product_id))
                if not product:
                    continue
                
                # Create order item
                item = OrderItem(
                    product_id=int(product_id),
                    qty=int(item_data.get('qty', 1)),
                    price=float(item_data.get('price', 0)),
                    notes=item_data.get('notes')
                )
                
                # Add variants if any
                if 'variants' in item_data and item_data['variants']:
                    for variant_data in item_data['variants']:
                        variant_id = variant_data.get('id')
                        if not variant_id:
                            continue
                        
                        # Verify variant exists
                        variant = Variant.query.get(int(variant_id))
                        if not variant:
                            continue
                        
                        variant = OrderVariant(
                            variant_id=int(variant_id),
                            qty=int(variant_data.get('qty', 1)),
                            price=float(variant_data.get('price', 0))
                        )
                        item.variants.append(variant)
                
                # Add sub-products if any
                if 'products' in item_data and item_data['products']:
                    for sub_data in item_data['products']:
                        sub_product_id = sub_data.get('id') or sub_data.get('product_id')
                        if not sub_product_id:
                            continue
                        
                        # Verify sub-product exists
                        sub_product_obj = Product.query.get(int(sub_product_id))
                        if not sub_product_obj:
                            continue
                        
                        sub_product = OrderSubProduct(
                            product_id=int(sub_product_id),
                            qty=int(sub_data.get('qty', 1)),
                            price=float(sub_data.get('price', 0))
                        )
                        item.sub_products.append(sub_product)
                
                order.order_items.append(item)
        
        # Add payments
        if 'payments' in order_data and order_data['payments']:
            for payment_data in order_data['payments']:
                payment_method_id = payment_data.get('id')
                if not payment_method_id:
                    continue
                
                # Check if payment method exists, create if not
                payment_method = PaymentMethod.query.get(int(payment_method_id))
                if not payment_method:
                    payment_method = PaymentMethod(
                        id=int(payment_method_id),
                        name=payment_data.get('name', f'Payment Method {payment_method_id}')
                    )
                    db.session.add(payment_method)
                
                payment = Payment(
                    payment_method_id=int(payment_method_id),
                    amount=float(payment_data.get('amount', 0))
                )
                order.payments.append(payment)
        
        # Save to database
        db.session.add(order)
        db.session.commit()
        
        return {
            'success': True, 
            'message': 'Order created successfully',
            'order_id': order.id
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error creating order: {str(e)}'}, 500

def update_order_status(order_id, status):
    """Update an order's status."""
    try:
        order = Order.query.get(order_id)
        
        if not order:
            return {'success': False, 'message': 'Order not found'}, 404
        
        valid_statuses = ['confirmed', 'preparing', 'ready', 'completed', 'cancelled']
        if status not in valid_statuses:
            return {'success': False, 'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}, 400
        
        order.status = status
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Order status updated to {status}'
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error updating order status: {str(e)}'}, 500

def add_item_to_order(order_id, item_data):
    """Add an item to an order."""
    try:
        order = Order.query.get(order_id)
        
        if not order:
            return {'success': False, 'message': 'Order not found'}, 404
        
        # Validate required fields
        if 'product_id' not in item_data:
            return {'success': False, 'message': 'Missing required field: product_id'}, 400
        
        if 'qty' not in item_data:
            return {'success': False, 'message': 'Missing required field: qty'}, 400
        
        if 'price' not in item_data:
            return {'success': False, 'message': 'Missing required field: price'}, 400
        
        # Verify product exists
        product = Product.query.get(int(item_data['product_id']))
        if not product:
            return {'success': False, 'message': f'Product with ID {item_data["product_id"]} not found'}, 400
        
        # Create order item
        item = OrderItem(
            order_id=order.id,
            product_id=int(item_data['product_id']),
            qty=int(item_data['qty']),
            price=float(item_data['price']),
            notes=item_data.get('notes')
        )
        
        # Add variants if any
        if 'variants' in item_data and item_data['variants']:
            for variant_data in item_data['variants']:
                if 'id' not in variant_data:
                    continue
                
                # Verify variant exists
                variant = Variant.query.get(int(variant_data['id']))
                if not variant:
                    continue
                
                variant = OrderVariant(
                    variant_id=int(variant_data['id']),
                    qty=int(variant_data.get('qty', 1)),
                    price=float(variant_data.get('price', 0))
                )
                item.variants.append(variant)
        
        order.order_items.append(item)
        
        # Update order total
        order.total += item.price * item.qty
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Item added to order successfully',
            'item_id': item.id
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error adding item to order: {str(e)}'}, 500

def update_order_item(order_id, item_id, item_data):
    """Update an item in an order."""
    try:
        order = Order.query.get(order_id)
        
        if not order:
            return {'success': False, 'message': 'Order not found'}, 404
        
        item = OrderItem.query.get(item_id)
        
        if not item or item.order_id != order.id:
            return {'success': False, 'message': 'Item not found in this order'}, 404
        
        # Calculate old subtotal for updating order total
        old_subtotal = item.price * item.qty
        
        # Update item fields
        if 'qty' in item_data:
            item.qty = int(item_data['qty'])
        
        if 'price' in item_data:
            item.price = float(item_data['price'])
        
        if 'notes' in item_data:
            item.notes = item_data['notes']
        
        # Calculate new subtotal
        new_subtotal = item.price * item.qty
        
        # Update order total
        order.total = order.total - old_subtotal + new_subtotal
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Order item updated successfully'
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error updating order item: {str(e)}'}, 500

def remove_item_from_order(order_id, item_id):
    """Remove an item from an order."""
    try:
        order = Order.query.get(order_id)
        
        if not order:
            return {'success': False, 'message': 'Order not found'}, 404
        
        item = OrderItem.query.get(item_id)
        
        if not item or item.order_id != order.id:
            return {'success': False, 'message': 'Item not found in this order'}, 404
        
        # Update order total
        order.total -= item.price * item.qty
        
        # Remove item
        db.session.delete(item)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Item removed from order successfully'
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error removing item from order: {str(e)}'}, 500

def add_payment_to_order(order_id, payment_data):
    """Add a payment to an order."""
    try:
        order = Order.query.get(order_id)
        
        if not order:
            return {'success': False, 'message': 'Order not found'}, 404
        
        # Validate required fields
        if 'payment_method_id' not in payment_data:
            return {'success': False, 'message': 'Missing required field: payment_method_id'}, 400
        
        if 'amount' not in payment_data:
            return {'success': False, 'message': 'Missing required field: amount'}, 400
        
        # Check if payment method exists
        payment_method_id = int(payment_data['payment_method_id'])
        payment_method = PaymentMethod.query.get(payment_method_id)
        
        if not payment_method:
            # Create new payment method if it doesn't exist
            payment_method = PaymentMethod(
                id=payment_method_id,
                name=payment_data.get('name', f'Payment Method {payment_method_id}')
            )
            db.session.add(payment_method)
        
        # Create payment
        payment = Payment(
            order_id=order.id,
            payment_method_id=payment_method_id,
            amount=float(payment_data['amount'])
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Payment added to order successfully',
            'payment_id': payment.id
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error adding payment to order: {str(e)}'}, 500