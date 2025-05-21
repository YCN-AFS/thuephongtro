from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy import UniqueConstraint
from app import db


# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    user_type = db.Column(db.String, default='renter')  # 'landlord', 'renter', or 'admin'
    phone = db.Column(db.String, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    address = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    @property
    def is_admin(self):
        return self.user_type == 'admin'

    # Relationships
    properties = db.relationship('Property', backref='owner', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)


# (IMPORTANT) This table is mandatory for OAuth with Replit Auth.
# It's used by flask-dance to store OAuth tokens.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    # Unique constraint based on user_id, session_key and provider
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

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    images = db.relationship('PropertyImage', backref='property', lazy=True, cascade="all, delete-orphan")
    favorites = db.relationship('Favorite', backref='property', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='property', lazy=True, cascade="all, delete-orphan")

    def average_rating(self):
        """Calculate average rating for this property"""
        if not self.reviews:
            return 0
        return sum(review.rating for review in self.reviews) / len(self.reviews)
    
    def rating_count(self):
        """Get the number of ratings for this property"""
        return len(self.reviews)
    
    def to_dict(self):
        """Convert property to dictionary format for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'property_type': self.property_type,
            'price': self.price,
            'address': self.address,
            'district': self.district,
            'city': self.city,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'area': self.area,
            'is_available': self.is_available,
            'image_url': self.images[0].url if self.images else None,
            'average_rating': self.average_rating(),
            'rating_count': self.rating_count()
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
    
    # Ensure a user can only favorite a property once
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
    
    # Relationships
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
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    chat_with = db.relationship('User', foreign_keys=[chat_with_id])
    last_message = db.relationship('Message', foreign_keys=[last_message_id])
    
    # Ensure a user can only have one chat with another user
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
    
    # Relationship
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
    
    # Relationships
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])


class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @classmethod
    def get(cls, key, default=None):
        """Get a setting value by key"""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            return setting.value
        return default
    
    @classmethod
    def set(cls, key, value):
        """Set a setting value by key"""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = cls(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
        return setting
    
    @classmethod
    def get_all(cls):
        """Get all settings as a dictionary"""
        settings = {}
        for setting in cls.query.all():
            settings[setting.key] = setting.value
        return settings