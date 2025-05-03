from app import db

class Room(db.Model):
    """Room model representing restaurant dining areas."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    shop_id = db.Column(db.Integer, nullable=True)
    
    # Relationships
    tables = db.relationship('Table', back_populates='room', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Room {self.name}>'
    
    def to_dict(self):
        """Convert the room to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'shop_id': self.shop_id
        }

class Table(db.Model):
    """Table model representing restaurant tables."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    availables_covers = db.Column(db.Integer, default=4)
    
    # Relationships
    room = db.relationship('Room', back_populates='tables')
    
    def __repr__(self):
        return f'<Table {self.name}>'
    
    def to_dict(self):
        """Convert the table to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'room_id': self.room_id,
            'availables_covers': self.availables_covers
        }
