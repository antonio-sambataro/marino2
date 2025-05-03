# -*- coding: utf-8 -*-
import logging
from flask import current_app
from app.models.order import Order
from app.models.menu import Product

logger = logging.getLogger(__name__)

# Mappatura categorie → stampanti
PRINT_MAPPING = {
    1: 'POKE',
    8: 'CUCINA',
    14: 'BAR',
    41: 'POKE',
    # aggiungi altre mappature se serve
}

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

        # Raggruppa gli articoli per destinazione
        printer_items = {}
        for item in order.order_items:
            product = Product.query.get(item.product_id)
            if not product:
                logger.warning(f"Product {item.product_id} not found, skipping")
                continue

            # Trova prima categoria mappata
            dest = next(
                (PRINT_MAPPING[cat.id] for cat in product.categories if cat.id in PRINT_MAPPING),
                'CUCINA'
            )

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
