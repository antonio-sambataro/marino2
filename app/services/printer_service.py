# -*- coding: utf-8 -*-
import logging
import os
import json
from flask import current_app
from app.models.order import Order
from app.models.menu import Product, Category

logger = logging.getLogger(__name__)

# Default printer mapping if config file not found
DEFAULT_PRINT_MAPPING = {
    'POKE': [1, 41],  # Poke category IDs
    'CUCINA': [8],    # Kitchen category IDs 
    'BAR': [14]       # Bar category IDs
}

def get_print_mapping():
    """Get printer mapping from configuration file or use default."""
    try:
        config_path = os.path.join(current_app.root_path, 'config', 'printer_mapping.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            logger.warning("Printer mapping file not found, using default mapping")
            return DEFAULT_PRINT_MAPPING
    except Exception as e:
        logger.error(f"Error loading printer mapping: {e}")
        return DEFAULT_PRINT_MAPPING

def get_printer_for_category(category_id, print_mapping):
    """Get the printer name for a category ID based on mapping."""
    for printer, category_ids in print_mapping.items():
        if category_id in category_ids:
            return printer
    return 'CUCINA'  # Default printer if no mapping found

def print_order_to_kitchen(order_id):
    """Invia un ordine alle stampanti di cucina basandosi sulle categorie dei prodotti."""
    try:
        if not current_app.config.get('ENABLE_PRINTING', False):
            logger.info(f"Printing disabled. Skipping order {order_id}")
            return True

        order = Order.query.get(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return False

        logger.info(f"Processing order {order_id} for printing")
        
        # Get printer mapping from configuration
        print_mapping = get_print_mapping()

        # Raggruppa gli articoli per destinazione
        printer_items = {}
        for item in order.order_items:
            product = Product.query.get(item.product_id)
            if not product:
                logger.warning(f"Product {item.product_id} not found, skipping")
                continue

            # Get the first category ID and find its printer destination
            category_id = None
            if product.categories:
                category_id = product.categories[0].id
            
            # Find printer for this category
            dest = get_printer_for_category(category_id, print_mapping)

            printer_items.setdefault(dest, []).append({
                'name':    product.name,
                'qty':     item.qty,
                'notes':   item.notes,
                'variants': [
                    {
                        'name': v.variant.name if v.variant else "Unknown variant",
                        'qty':  v.qty
                    } for v in item.variants
                ]
            })

        logger.info(f"Print queue: {printer_items}")

        # Invia ciascun gruppo alla stampante
        for printer, items in printer_items.items():
            if not items:
                logger.info(f"{printer}: Nessun Articolo da Stampare")
                logger.info(f"{printer}: OK")
                continue

            success = send_to_printer(printer, order, items)
            if success:
                lines = len(items) * 2 + 2
                logger.info(f"{printer}: Righe stampate {lines}")
                logger.info(f"{printer}: OK")
            else:
                logger.error(f"{printer}: Errore di stampa")

        return True

    except Exception as e:
        logger.error(f"Print error: {e}")
        return False


def send_to_printer(printer_name, order, items):
    """Formatta e invia i dati all'ipotetica stampante ESC/POS."""
    try:
        # Header
        header = [
            f"ORDINE #{order.id}",
            f"TIPO: {order.delivery_type.upper()}",
            f"ORIGINE: {order.origin}",
            f"DATA: {order.delivery_date.strftime('%d/%m/%Y %H:%M')}"
        ]

        if order.table_id:
            table_name = order.table.name if order.table else order.table_id
            header.append(f"TAVOLO: {table_name}")

        if order.covers:
            header.append(f"COPERTI: {order.covers}")

        if order.name:
            surname = order.surname or ""
            header.append(f"CLIENTE: {order.name} {surname}".strip())

        # Articoli
        item_lines = []
        for it in items:
            item_lines.append(f"{it['qty']}x {it['name']}")
            for var in it['variants']:
                item_lines.append(f"  + {var['name']} x{var['qty']}")
            if it['notes']:
                item_lines.append(f"  NOTE: {it['notes']}")

        # Footer
        footer = [
            "=" * 40,
            f"TOTALE ORDINE: €{order.total:.2f}"
        ]

        # Contenuto stampa
        print_content = header + ["", "ARTICOLI:"] + item_lines + [""] + footer
        logger.debug(f"Printer {printer_name} will print:\n" + "\n".join(print_content))

        # Qui si integrerebbe il vero driver ESC/POS, p.es.:
        # printer = get_printer_connection(printer_name)
        # printer.text("\n".join(print_content))
        # printer.cut()

        return True

    except Exception as e:
        logger.error(f"Error sending to printer {printer_name}: {e}")
        return False