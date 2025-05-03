from app import create_app
from app.models.user import User
from app.models.menu import Category, Product, PriceList
from app.models.order import Order
from app.models.table import Room, Table
from app import db

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Add database models to the Flask shell context."""
    return {
        'db': db,
        'User': User,
        'Category': Category,
        'Product': Product,
        'PriceList': PriceList,
        'Order': Order,
        'Room': Room,
        'Table': Table
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)