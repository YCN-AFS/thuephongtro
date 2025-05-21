from datetime import datetime

from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, ForeignKey, func
from werkzeug.security import generate_password_hash, check_password_hash


# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    user_type = db.Column(db.String, default='renter')  # 'landlord' or 'renter'
    phone = db.Column(db.String, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    address = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    properties = db.relationship('Property', backref='owner', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)


# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)


class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    property_type = db.Column(db.String(50), nullable=False)  # apartment, house, room
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), default="Biên Hòa")
    province = db.Column(db.String(100), default="Đồng Nai")
    country = db.Column(db.String(100), default="Vietnam")
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    area = db.Column(db.Float, nullable=False)  # in square meters
    bedrooms = db.Column(db.Integer, nullable=False)
    bathrooms = db.Column(db.Integer, nullable=False)
    furnishing = db.Column(db.String(50), nullable=True)  # unfurnished, semi-furnished, fully-furnished
    available_from = db.Column(db.Date, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    # Amenities
    has_air_conditioning = db.Column(db.Boolean, default=False)
    has_parking = db.Column(db.Boolean, default=False)
    has_wifi = db.Column(db.Boolean, default=False)
    has_washing_machine = db.Column(db.Boolean, default=False)
    has_refrigerator = db.Column(db.Boolean, default=False)
    has_tv = db.Column(db.Boolean, default=False)
    has_kitchen = db.Column(db.Boolean, default=False)
    has_balcony = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    images = db.relationship('PropertyImage', backref='property', lazy=True, cascade="all, delete-orphan")
    favorites = db.relationship('Favorite', backref='property', lazy=True, cascade="all, delete-orphan")
    # reviews relationship is added by the Review model with backref
    
    @property
    def average_rating(self):
        """Calculate average rating for this property"""
        if not self.reviews or len(self.reviews) == 0:
            return 0
        return round(sum(review.rating for review in self.reviews) / len(self.reviews), 1)
    
    @property
    def rating_count(self):
        """Get the number of ratings for this property"""
        return len(self.reviews) if self.reviews else 0
    
    def to_dict(self):
        """Convert property to dictionary format for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'address': self.address,
            'district': self.district,
            'city': self.city,
            'province': self.province,
            'area': self.area,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'property_type': self.property_type,
            'furnishing': self.furnishing,
            'available_from': self.available_from.isoformat() if self.available_from else None,
            'is_available': self.is_available,
            'images': [img.url for img in self.images],
            'owner': {
                'id': self.owner.id,
                'name': f"{self.owner.first_name} {self.owner.last_name}".strip() or "User",
                'phone': self.owner.phone,
                'profile_image': self.owner.profile_image_url
            },
            'amenities': {
                'air_conditioning': self.has_air_conditioning,
                'parking': self.has_parking,
                'wifi': self.has_wifi,
                'washing_machine': self.has_washing_machine,
                'refrigerator': self.has_refrigerator,
                'tv': self.has_tv,
                'kitchen': self.has_kitchen,
                'balcony': self.has_balcony
            },
            'ratings': {
                'average': self.average_rating,
                'count': self.rating_count
            },
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class PropertyImage(db.Model):
    __tablename__ = 'property_images'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'property_id', name='uq_user_property'),
    )


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])
    property = db.relationship('Property', foreign_keys=[property_id])


class UserChat(db.Model):
    __tablename__ = 'user_chats'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    chat_with_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    last_message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)
    unread_count = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = db.relationship('User', foreign_keys=[user_id])
    chat_with = db.relationship('User', foreign_keys=[chat_with_id])
    last_message = db.relationship('Message', foreign_keys=[last_message_id])
    
    __table_args__ = (
        UniqueConstraint('user_id', 'chat_with_id', name='uq_user_chat_with'),
    )


class ChatWithAI(db.Model):
    __tablename__ = 'ai_chats'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', foreign_keys=[user_id])
    
    
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    reviewer_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    property = db.relationship('Property', backref=db.backref('reviews', lazy=True, cascade="all, delete-orphan"))
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
