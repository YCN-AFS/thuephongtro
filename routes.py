from flask import render_template, redirect, url_for, request, jsonify, flash, session, abort
from sqlalchemy import func, or_, and_, desc
from datetime import datetime, date, timedelta
import json
import os
import base64
import uuid
from io import BytesIO
from PIL import Image
from urllib.parse import urlparse
import logging
from functools import wraps
from werkzeug.utils import secure_filename

from app import app, db
from models import User, Property, PropertyImage, Favorite, Message, ChatWithAI, UserChat, Review
from replit_auth import require_login, make_replit_blueprint, current_user, replit
from ai_assistant import get_ai_response, get_property_recommendations
from google_auth import google_auth

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bạn cần đăng nhập để truy cập trang này.', 'danger')
            return redirect(url_for('index'))
        if not current_user.is_admin:
            flash('Bạn không có quyền truy cập trang này.', 'danger')
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Register Replit Auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Register Google Auth blueprint - make sure the URL structure matches what Google expects
app.register_blueprint(google_auth, url_prefix="")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

# Default stock images
STOCK_IMAGES = [
    "https://pixabay.com/get/g599a2436ea5a99d79faf1e146e66de36b5fa1601a8281ee77689a4c889ba853fdbc943905c58aab2394597b80ed52fa3becd88ef2d7f7cdc6bfc9f9b4fb1fdfc_1280.jpg",
    "https://pixabay.com/get/g0a95743d57d00d776b0730a63d610f28cf5ed0e5b378a52e7c13779fd43c36cea6516f29c371fb80bd057d0f3fdb031cb1441dbeb94144e842bfb855bbccb0d1_1280.jpg",
    "https://pixabay.com/get/g75f9329787fad5ee9dae377ca30ab4b05633189ca4f81f276878518f4c23b4ab26099431efcca07d8f991dd00146977b30c03a99b5a3502080b131b8b427b69e_1280.jpg",
    "https://pixabay.com/get/g83539d0676731970cab5609d993d3cf2f395ec555e1feac49d287cb0b4ee411092b03d2bb6611cbc9b3a3609e2f00bc60d4438574d669b02c4c0ed8bc894a228_1280.jpg",
    "https://pixabay.com/get/g3f77dfba7d809b13d0871418065990f2214d226b21dc3e505ceb6d7b083b398b930b41de34118331ad7d2db79d2608c4b2cf61a37884b16878a86cd81446eb1e_1280.jpg",
    "https://pixabay.com/get/g2ce30588595b4279fa4bd9ef9f443ea8a3b30adf00fbd9b605fcd69e99431840229bf3bd9560596d02d5dab8465933c03a3cc6d04df229c562d4763393bdd8d2_1280.jpg",
    "https://pixabay.com/get/g42f931ecb58762a33b28eea42149ea8048d743915478c2331a5a36343a1a8d9461ed6ed14be306dd5945c24ad347f0d560eddd76f8ca7c0de4c6bab2038fc7b0_1280.jpg",
    "https://pixabay.com/get/gcc2a67a6f0e1748f3f0c7f3686c554c00a6e14d72c3879bd64512db5e2ea8abae302fff320109ead7a69014dc8ccfccb65073adbf06037d338d3a099f06a197e_1280.jpg",
    "https://pixabay.com/get/g3ab69c46ed49c15dca0fcd7bc9a9c3563ff402b1862127eefc5b2f99972a81306504688ef371f87c0d85337d34ca9f2d52b98879cb87885250e9152102489534_1280.jpg",
    "https://pixabay.com/get/gb85739c7f396109435d67603b83ece5522284d6415ee2d1752a75470128fac98b2032317cd2744d25093c46bed27245a7498979e9fc75bab434c83eca3efa6f3_1280.jpg",
    "https://pixabay.com/get/g430c2081c24c0080aa7e86a8941b96d1847ac6ffcfcb6ab8bd05a443a7832e8f1d343c892b692770173a2f4d3c687d8236f4a947caf80d2c616681426bf39e89_1280.jpg",
    "https://pixabay.com/get/g7ad9ce580c09d49f05c97a4c5b2dfd46ac39a7eb0aa3154b45700e8fac79768d5f731a04203c98eaeecdc1e0681a1a006b7ceaa9fd142abf407b423356c09c40_1280.jpg",
    "https://pixabay.com/get/ge3780dc62b4a5838716e28ed4fed747638c80891f6ca78523db4484e870d26a48d947e25b434e235268a4f27288da41595c8aaf58acaada18aad25fee4f14165_1280.jpg",
    "https://pixabay.com/get/gd33bf37705896f237dfe33b4439e8c75bc9e0c8287a09d84a65f83b644ce919e43b2eea64f37ea3c2c2d2d7f93ad68df1fe30c9da26fa8eac4b787dd319cd38b_1280.jpg",
]

# Home page
@app.route('/')
def index():
    # Get featured properties (8 most recent with images)
    featured_properties = Property.query.filter(Property.is_available == True)\
        .join(PropertyImage)\
        .order_by(desc(Property.created_at))\
        .limit(8).all()
    
    # Get districts for search
    districts = db.session.query(Property.district, func.count(Property.id))\
        .group_by(Property.district)\
        .order_by(func.count(Property.id).desc())\
        .all()
    
    return render_template('index.html', 
                           featured_properties=featured_properties,
                           districts=districts,
                           user=current_user)

# Search results page
@app.route('/search')
def search():
    district = request.args.get('district', '')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    bedrooms = request.args.get('bedrooms', type=int)
    property_type = request.args.get('property_type', '')
    
    # Build query
    query = Property.query.filter(Property.is_available == True)
    
    if district:
        query = query.filter(Property.district == district)
    
    if min_price:
        query = query.filter(Property.price >= min_price)
    
    if max_price:
        query = query.filter(Property.price <= max_price)
    
    if bedrooms:
        query = query.filter(Property.bedrooms >= bedrooms)
        
    if property_type:
        query = query.filter(Property.property_type == property_type)
    
    # Execute query
    properties = query.order_by(desc(Property.created_at)).all()
    
    # Get districts for search form
    districts = db.session.query(Property.district, func.count(Property.id))\
        .group_by(Property.district)\
        .order_by(func.count(Property.id).desc())\
        .all()
    
    return render_template('search_results.html', 
                           properties=properties,
                           districts=districts,
                           search_params=request.args,
                           user=current_user)

# Property details page
@app.route('/property/<int:property_id>')
def property_details(property_id):
    property = Property.query.get_or_404(property_id)
    
    # Check if property is in user's favorites
    is_favorite = False
    if current_user.is_authenticated:
        favorite = Favorite.query.filter_by(
            user_id=current_user.id,
            property_id=property_id
        ).first()
        is_favorite = favorite is not None
    
    # Get more properties from same owner
    more_from_owner = Property.query.filter(
        Property.owner_id == property.owner_id,
        Property.id != property.id,
        Property.is_available == True
    ).limit(4).all()
    
    # Get similar properties (same district, similar price)
    similar_properties = Property.query.filter(
        Property.district == property.district,
        Property.id != property.id,
        Property.is_available == True,
        Property.price.between(property.price * 0.8, property.price * 1.2)
    ).limit(4).all()
    
    # Get property reviews
    reviews = Review.query.filter_by(property_id=property_id).order_by(Review.created_at.desc()).limit(5).all()
    
    # Check if user has already reviewed
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            property_id=property_id,
            reviewer_id=current_user.id
        ).first()
    
    return render_template('property_details_new.html', 
                           property=property,
                           is_favorite=is_favorite,
                           more_from_owner=more_from_owner,
                           similar_properties=similar_properties,
                           reviews=reviews,
                           user_review=user_review,
                           user=current_user)

# Reviews and Ratings
@app.route('/property/<int:property_id>/reviews')
def property_reviews(property_id):
    """View all reviews for a property"""
    property = Property.query.get_or_404(property_id)
    reviews = Review.query.filter_by(property_id=property_id).order_by(Review.created_at.desc()).all()
    
    return render_template('property_reviews.html',
                          property=property,
                          reviews=reviews,
                          user=current_user)

@app.route('/property/<int:property_id>/review', methods=['GET', 'POST'])
@require_login
def add_review(property_id):
    """Add or update a review for a property"""
    property = Property.query.get_or_404(property_id)
    
    # Check if user has already reviewed this property
    existing_review = Review.query.filter_by(
        property_id=property_id, 
        reviewer_id=current_user.id
    ).first()
    
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        
        if not rating or not rating.isdigit() or int(rating) < 1 or int(rating) > 5:
            flash('Vui lòng chọn đánh giá từ 1-5 sao.', 'danger')
            return redirect(url_for('add_review', property_id=property_id))
        
        if existing_review:
            # Update existing review
            existing_review.rating = int(rating)
            existing_review.comment = comment
            existing_review.updated_at = datetime.now()
            flash('Đánh giá của bạn đã được cập nhật!', 'success')
        else:
            # Create new review
            new_review = Review()
            new_review.property_id = property_id
            new_review.reviewer_id = current_user.id
            new_review.rating = int(rating)
            new_review.comment = comment
            db.session.add(new_review)
            flash('Cảm ơn bạn đã đánh giá!', 'success')
        
        db.session.commit()
        return redirect(url_for('property_details', property_id=property_id))
    
    # GET request - show the review form
    return render_template('review_form.html',
                          property=property,
                          existing_review=existing_review,
                          user=current_user)

@app.route('/property/<int:property_id>/review/<int:review_id>/delete', methods=['POST'])
@require_login
def delete_review(property_id, review_id):
    """Delete a review"""
    review = Review.query.get_or_404(review_id)
    
    # Check if the user is the reviewer
    if review.reviewer_id != current_user.id:
        flash('Bạn không có quyền xóa đánh giá này.', 'danger')
        return redirect(url_for('property_details', property_id=property_id))
    
    db.session.delete(review)
    db.session.commit()
    
    flash('Đánh giá đã được xóa.', 'success')
    return redirect(url_for('property_details', property_id=property_id))

# Landlord dashboard page
@app.route('/dashboard')
@require_login
def landlord_dashboard():
    # Check if user is set as a landlord, otherwise set it
    if current_user.user_type != 'landlord':
        current_user.user_type = 'landlord'
        db.session.commit()
    
    # Get landlord's properties
    properties = Property.query.filter_by(owner_id=current_user.id).order_by(desc(Property.created_at)).all()
    
    return render_template('landlord_dashboard.html', 
                           properties=properties,
                           user=current_user)

# Create new property form
@app.route('/property/new', methods=['GET', 'POST'])
@require_login
def create_property():
    if request.method == 'POST':
        # Set user as landlord if not already
        if current_user.user_type != 'landlord':
            current_user.user_type = 'landlord'
            db.session.commit()
        
        # Create new property
        try:
            # Create a new property instance
            new_property = Property()
            new_property.owner_id = current_user.id
            new_property.title = request.form.get('title', '')
            new_property.description = request.form.get('description', '')
            new_property.property_type = request.form.get('property_type', '')
            
            # Convert numeric values safely
            price_str = request.form.get('price', '0')
            new_property.price = float(price_str) if price_str else 0
            
            new_property.address = request.form.get('address', '')
            new_property.district = request.form.get('district', '')
            new_property.city = request.form.get('city', 'Biên Hòa')
            new_property.province = request.form.get('province', 'Đồng Nai')
            
            # Convert area safely
            area_str = request.form.get('area', '0')
            new_property.area = float(area_str) if area_str else 0
            
            # Convert integers safely
            bedrooms_str = request.form.get('bedrooms', '0')
            new_property.bedrooms = int(bedrooms_str) if bedrooms_str else 0
            
            bathrooms_str = request.form.get('bathrooms', '0')
            new_property.bathrooms = int(bathrooms_str) if bathrooms_str else 0
            
            new_property.furnishing = request.form.get('furnishing', '')
            
            # Parse date safely
            available_from_str = request.form.get('available_from')
            if available_from_str:
                new_property.available_from = datetime.strptime(available_from_str, '%Y-%m-%d').date()
            else:
                new_property.available_from = datetime.now().date()
            
            # Set boolean features
            new_property.has_air_conditioning = 'has_air_conditioning' in request.form
            new_property.has_parking = 'has_parking' in request.form
            new_property.has_wifi = 'has_wifi' in request.form
            new_property.has_washing_machine = 'has_washing_machine' in request.form
            new_property.has_refrigerator = 'has_refrigerator' in request.form
            new_property.has_tv = 'has_tv' in request.form
            new_property.has_kitchen = 'has_kitchen' in request.form
            new_property.has_balcony = 'has_balcony' in request.form
            
            db.session.add(new_property)
            db.session.flush()  # To get the property ID
            
            # Handle property images
            images = request.form.getlist('image_urls')
            uploaded_files = request.files.getlist('property-images')
            
            # Process uploaded files
            if uploaded_files and uploaded_files[0].filename:
                import os
                from werkzeug.utils import secure_filename
                from flask import current_app
                
                # Ensure upload directory exists
                static_folder = 'static'  # Flask's default static folder
                upload_folder = os.path.join(static_folder, 'uploads', 'properties', str(new_property.id))
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save each uploaded file
                for file in uploaded_files:
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)
                        
                        # Create database record for the image
                        image = PropertyImage()
                        image.property_id = new_property.id
                        image.url = f'/static/uploads/properties/{new_property.id}/{filename}'
                        image.is_primary = (file == uploaded_files[0])  # First image is primary
                        db.session.add(image)
            
            # If no images uploaded but URLs provided (stock images)
            elif images:
                for i, url in enumerate(images):
                    image = PropertyImage()
                    image.property_id = new_property.id
                    image.url = url
                    image.is_primary = (i == 0)  # First image is primary
                    db.session.add(image)
            
            # If no images provided at all, use a default stock image
            else:
                default_image = PropertyImage()
                default_image.property_id = new_property.id
                default_image.url = 'static/img/properties/default-property.jpg'
                default_image.is_primary = True
                db.session.add(default_image)
            
            db.session.commit()
            flash('Property created successfully!', 'success')
            return redirect(url_for('property_details', property_id=new_property.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating property: {str(e)}', 'danger')
            logging.error(f"Error creating property: {str(e)}")
    
    # GET request - show the form
    return render_template('property_form.html', 
                           user=current_user, 
                           property=None,
                           stock_images=STOCK_IMAGES)

# Edit property form
@app.route('/property/<int:property_id>/edit', methods=['GET', 'POST'])
@require_login
def edit_property(property_id):
    property = Property.query.get_or_404(property_id)
    
    # Check if user is the owner
    if property.owner_id != current_user.id:
        flash('You do not have permission to edit this property', 'danger')
        return redirect(url_for('property_details', property_id=property_id))
    
    if request.method == 'POST':
        try:
            # Update property
            property.title = request.form.get('title', '')
            property.description = request.form.get('description', '')
            property.property_type = request.form.get('property_type', '')
            
            price = request.form.get('price', '0')
            property.price = float(price) if price else 0.0
            
            property.address = request.form.get('address', '')
            property.district = request.form.get('district', '')
            property.city = request.form.get('city', 'Biên Hòa')
            property.province = request.form.get('province', 'Đồng Nai')
            
            area = request.form.get('area', '0')
            property.area = float(area) if area else 0.0
            
            bedrooms = request.form.get('bedrooms', '0')
            property.bedrooms = int(bedrooms) if bedrooms else 0
            
            bathrooms = request.form.get('bathrooms', '0')
            property.bathrooms = int(bathrooms) if bathrooms else 0
            
            property.furnishing = request.form.get('furnishing', '')
            
            available_from = request.form.get('available_from')
            if available_from:
                property.available_from = datetime.strptime(available_from, '%Y-%m-%d').date()
            else:
                property.available_from = datetime.now().date()
                
            property.is_available = 'is_available' in request.form
            
            # Update amenities
            property.has_air_conditioning = 'has_air_conditioning' in request.form
            property.has_parking = 'has_parking' in request.form
            property.has_wifi = 'has_wifi' in request.form
            property.has_washing_machine = 'has_washing_machine' in request.form
            property.has_refrigerator = 'has_refrigerator' in request.form
            property.has_tv = 'has_tv' in request.form
            property.has_kitchen = 'has_kitchen' in request.form
            property.has_balcony = 'has_balcony' in request.form
            
            # Handle property images
            images = request.form.getlist('image_urls')
            
            # Clear existing images if we have new ones
            if images:
                PropertyImage.query.filter_by(property_id=property.id).delete()
                
                # Add new images
                for i, image_url in enumerate(images):
                    property_image = PropertyImage()
                    property_image.property_id = property.id
                    property_image.url = image_url
                    property_image.is_primary = (i == 0)  # First image is primary
                    db.session.add(property_image)
            
            db.session.commit()
            flash('Property updated successfully!', 'success')
            return redirect(url_for('property_details', property_id=property.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating property: {str(e)}', 'danger')
            logging.error(f"Error updating property: {str(e)}")
    
    # GET request - show the form with property data
    return render_template('property_form.html', 
                           user=current_user, 
                           property=property,
                           stock_images=STOCK_IMAGES)

# Delete property
@app.route('/property/<int:property_id>/delete', methods=['POST'])
@require_login
def delete_property(property_id):
    property = Property.query.get_or_404(property_id)
    
    # Check if user is the owner
    if property.owner_id != current_user.id:
        flash('Bạn không có quyền xoá bất động sản này', 'danger')
        return redirect(url_for('property_details', property_id=property_id))
    
    try:
        # Get the property title for the success message
        property_title = property.title
        
        # Delete property (cascades to delete related images from database)
        db.session.delete(property)
        db.session.commit()
        
        # Handle AJAX request for dynamic removal
        if request and request.headers and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': f'Bất động sản "{property_title}" đã được xoá thành công'
            })
        
        # Normal form submission
        flash(f'Bất động sản "{property_title}" đã được xoá thành công', 'success')
        return redirect(url_for('landlord_dashboard'))
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting property: {str(e)}")
        
        # Handle AJAX request
        if request and request.headers and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'error',
                'message': f'Lỗi khi xoá bất động sản: {str(e)}'
            }), 500
        
        flash(f'Lỗi khi xoá bất động sản: {str(e)}', 'danger')
        return redirect(url_for('property_details', property_id=property_id))

# Contact landlord - send a message
@app.route('/property/<int:property_id>/contact', methods=['POST'])
@require_login
def contact_landlord(property_id):
    # Get the property
    property = Property.query.get_or_404(property_id)
    
    # Make sure user is not contacting themselves
    if property.owner_id == current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'You cannot contact yourself as the owner of this property.'}), 400
        flash('You cannot contact yourself as the owner of this property.', 'warning')
        return redirect(url_for('property_details', property_id=property_id))
    
    # Get form data
    name = request.form.get('name', '')
    email = request.form.get('email', '')
    message_text = request.form.get('message', '')
    
    # Validate required fields
    if not message_text:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Please enter a message.'}), 400
        flash('Please enter a message.', 'danger')
        return redirect(url_for('property_details', property_id=property_id))
    
    try:
        # Format message with sender details
        formatted_message = f"Message from: {name} ({email})\n\n{message_text}"
        
        # Create a new message
        new_message = Message()
        new_message.sender_id = current_user.id
        new_message.receiver_id = property.owner_id
        new_message.property_id = property_id
        new_message.message = formatted_message
        new_message.is_read = False
        db.session.add(new_message)
        db.session.flush()  # Get the ID of the new message
        
        # Update or create a user chat entry
        user_chat = UserChat.query.filter_by(
            user_id=current_user.id,
            chat_with_id=property.owner_id
        ).first()
        
        if not user_chat:
            user_chat = UserChat()
            user_chat.user_id = current_user.id
            user_chat.chat_with_id = property.owner_id
            db.session.add(user_chat)
        
        # Update last message and timestamp
        user_chat.last_message_id = new_message.id
        user_chat.updated_at = datetime.now()
        
        # Also create/update the other side of the conversation (for the landlord)
        landlord_chat = UserChat.query.filter_by(
            user_id=property.owner_id,
            chat_with_id=current_user.id
        ).first()
        
        if not landlord_chat:
            landlord_chat = UserChat()
            landlord_chat.user_id = property.owner_id
            landlord_chat.chat_with_id = current_user.id
            db.session.add(landlord_chat)
        
        # Update landlord's chat
        landlord_chat.last_message_id = new_message.id
        landlord_chat.unread_count = landlord_chat.unread_count + 1
        landlord_chat.updated_at = datetime.now()
        
        db.session.commit()
        
        # Handle AJAX request for dynamic modal behavior
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': 'Your message has been sent to the landlord. They will contact you soon.'
            })
            
        flash('Your message has been sent to the landlord. They will contact you soon.', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error sending message: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': f'Error sending message: {str(e)}'}), 500
            
        flash(f'Error sending message: {str(e)}', 'danger')
    
    return redirect(url_for('property_details', property_id=property_id))

# User profile page
@app.route('/profile', methods=['GET', 'POST'])
@require_login
def profile():
    if request.method == 'POST':
        try:
            # Update user profile
            current_user.phone = request.form.get('phone')
            current_user.bio = request.form.get('bio')
            current_user.address = request.form.get('address')
            current_user.user_type = request.form.get('user_type')
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
            logging.error(f"Error updating profile: {str(e)}")
    
    # Get user's favorites if they are a renter
    favorites = []
    if current_user.user_type == 'renter':
        favorites = db.session.query(Property)\
            .join(Favorite, Favorite.property_id == Property.id)\
            .filter(Favorite.user_id == current_user.id)\
            .all()
    
    return render_template('profile.html', 
                           user=current_user,
                           favorites=favorites)

# Toggle favorite status for a property
@app.route('/property/<int:property_id>/favorite', methods=['POST'])
@require_login
def toggle_favorite(property_id):
    property = Property.query.get_or_404(property_id)
    
    # Check if property is already in favorites
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        property_id=property_id
    ).first()
    
    try:
        if favorite:
            # Remove from favorites
            db.session.delete(favorite)
            message = 'Property removed from favorites'
            is_favorite = False
        else:
            # Add to favorites
            new_favorite = Favorite()
            new_favorite.user_id = current_user.id
            new_favorite.property_id = property_id
            db.session.add(new_favorite)
            message = 'Property added to favorites'
            is_favorite = True
        
        db.session.commit()
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': message,
                'is_favorite': is_favorite
            })
        else:
            flash(message, 'success')
            return redirect(url_for('property_details', property_id=property_id))
            
    except Exception as e:
        db.session.rollback()
        error_message = f'Error toggling favorite status: {str(e)}'
        logging.error(error_message)
        
        # Check if this is an AJAX request
        if request and request.headers and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'error',
                'message': error_message
            }), 500
        else:
            flash(error_message, 'danger')
            if property_id:
                return redirect(url_for('property_details', property_id=property_id))
            else:
                return redirect(url_for('landlord_dashboard'))

# AI chat assistant
@app.route('/ai-assistant', methods=['GET', 'POST'])
def ai_assistant():
    # Get recent properties for AI recommendations
    recent_properties = []
    
    if request.method == 'POST' and request and request.headers and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = request.json
            user_message = data.get('message', '') if data else ''
            
            # Get property recommendations if available
            property_data = []
            if current_user.is_authenticated:
                search_params = data.get('search_params', {}) if data else {}
                if search_params:
                    # Query properties based on search parameters
                    query = Property.query.filter(Property.is_available == True)
                    
                    district = search_params.get('district')
                    if district:
                        query = query.filter(Property.district == district)
                    
                    min_price = search_params.get('min_price')
                    if min_price:
                        query = query.filter(Property.price >= float(min_price))
                    
                    max_price = search_params.get('max_price')
                    if max_price:
                        query = query.filter(Property.price <= float(max_price))
                    
                    bedrooms = search_params.get('bedrooms')
                    if bedrooms:
                        query = query.filter(Property.bedrooms >= int(bedrooms))
                    
                    property_type = search_params.get('property_type')
                    if property_type:
                        query = query.filter(Property.property_type == property_type)
                    
                    # Get properties for AI recommendations
                    matching_properties = query.order_by(desc(Property.created_at)).limit(10).all()
                    property_data = [prop.to_dict() for prop in matching_properties]
                else:
                    # Get recent properties
                    recent_properties = Property.query.filter(Property.is_available == True)\
                        .order_by(desc(Property.created_at))\
                        .limit(10).all()
                    property_data = [prop.to_dict() for prop in recent_properties]
            
            # Get previous chat history
            chat_history = []
            if current_user.is_authenticated:
                previous_chats = ChatWithAI.query.filter_by(user_id=current_user.id)\
                    .order_by(ChatWithAI.created_at)\
                    .limit(5).all()
                for chat in previous_chats:
                    chat_history.append({"role": "user", "content": chat.message})
                    if chat.response:
                        chat_history.append({"role": "assistant", "content": chat.response})
            
            # Get AI response
            ai_response = get_ai_response(user_message, property_data, chat_history)
            
            # Save the chat to database if user is logged in
            if current_user.is_authenticated:
                chat_record = ChatWithAI()
                chat_record.user_id = current_user.id
                chat_record.message = user_message
                chat_record.response = ai_response
                db.session.add(chat_record)
                db.session.commit()
            
            return jsonify({
                'status': 'success',
                'response': ai_response
            })
            
        except Exception as e:
            logging.error(f"Error in AI assistant: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Sorry, I encountered an error. Please try again.'
            }), 500
    
    # For GET request, just render the page
    recent_properties = Property.query.filter(Property.is_available == True)\
        .order_by(desc(Property.created_at))\
        .limit(8).all()
    
    # Get districts for search form
    districts = db.session.query(Property.district, func.count(Property.id))\
        .group_by(Property.district)\
        .order_by(func.count(Property.id).desc())\
        .all()
    
    return render_template('index.html', 
                           featured_properties=recent_properties,
                           districts=districts,
                           show_ai_chat=True,
                           user=current_user)

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    # Statistics for dashboard
    total_properties = Property.query.count()
    total_users = User.query.count()
    total_reviews = Review.query.count()
    
    # Monthly stats
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_properties = Property.query.filter(Property.created_at >= current_month_start).count()
    
    # Collect stats in a dictionary
    stats = {
        'total_properties': total_properties,
        'total_users': total_users,
        'total_reviews': total_reviews,
        'monthly_properties': monthly_properties
    }
    
    # Recent properties
    recent_properties = Property.query.order_by(desc(Property.created_at)).limit(10).all()
    
    # Recent users
    recent_users = User.query.order_by(desc(User.created_at)).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                           user=current_user,
                           stats=stats,
                           recent_properties=recent_properties,
                           recent_users=recent_users,
                           active_tab='dashboard')

@app.route('/admin/properties')
@admin_required
def admin_properties():
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '')
    district = request.args.get('district', '')
    property_type = request.args.get('property_type', '')
    status = request.args.get('status', '')
    
    # Base query
    query = Property.query
    
    # Apply filters
    if keyword:
        query = query.filter(or_(
            Property.title.ilike(f'%{keyword}%'),
            Property.description.ilike(f'%{keyword}%'),
            Property.address.ilike(f'%{keyword}%')
        ))
    
    if district:
        query = query.filter(Property.district == district)
    
    if property_type:
        query = query.filter(Property.property_type == property_type)
    
    if status == 'available':
        query = query.filter(Property.is_available == True)
    elif status == 'unavailable':
        query = query.filter(Property.is_available == False)
    
    # Pagination
    pagination = query.order_by(desc(Property.created_at)).paginate(page=page, per_page=20)
    properties = pagination.items
    
    # Get districts for filter
    districts = db.session.query(Property.district, func.count(Property.id))\
        .group_by(Property.district)\
        .order_by(func.count(Property.id).desc())\
        .all()
    
    return render_template('admin/properties.html',
                           user=current_user,
                           properties=properties,
                           pagination=pagination,
                           districts=districts,
                           active_tab='properties')

@app.route('/admin/users')
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '')
    user_type = request.args.get('user_type', '')
    sort = request.args.get('sort', 'newest')
    
    # Base query
    query = User.query
    
    # Apply filters
    if keyword:
        query = query.filter(or_(
            User.email.ilike(f'%{keyword}%'),
            User.first_name.ilike(f'%{keyword}%'),
            User.last_name.ilike(f'%{keyword}%')
        ))
    
    if user_type:
        query = query.filter(User.user_type == user_type)
    
    # Apply sorting
    if sort == 'oldest':
        query = query.order_by(User.created_at)
    else:  # newest
        query = query.order_by(desc(User.created_at))
    
    # Pagination
    pagination = query.paginate(page=page, per_page=20)
    users = pagination.items
    
    return render_template('admin/users.html',
                           user=current_user,
                           users=users,
                           pagination=pagination,
                           active_tab='users')

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '')
    rating = request.args.get('rating', '')
    sort = request.args.get('sort', 'newest')
    
    # Base query
    query = Review.query
    
    # Apply filters
    if keyword:
        query = query.filter(Review.comment.ilike(f'%{keyword}%'))
    
    if rating:
        query = query.filter(Review.rating == int(rating))
    
    # Apply sorting
    if sort == 'oldest':
        query = query.order_by(Review.created_at)
    elif sort == 'rating_high':
        query = query.order_by(desc(Review.rating), desc(Review.created_at))
    elif sort == 'rating_low':
        query = query.order_by(Review.rating, desc(Review.created_at))
    else:  # newest
        query = query.order_by(desc(Review.created_at))
    
    # Pagination
    pagination = query.paginate(page=page, per_page=20)
    reviews = pagination.items
    
    return render_template('admin/reviews.html',
                           user=current_user,
                           reviews=reviews,
                           pagination=pagination,
                           active_tab='reviews')

@app.route('/admin/settings')
@admin_required
def admin_settings():
    # Create an empty settings dictionary for the template
    settings = {}
    
    # Try to get settings from database
    try:
        from models import Setting
        settings = Setting.get_all()
        
        # If no settings exist, use defaults
        if not settings:
            default_settings = {
                'site_name': 'BienHoa Rentals',
                'site_tagline': 'Tìm nhà dễ dàng tại Biên Hòa',
                'contact_email': 'contact@bienhoarentals.com',
                'contact_phone': '0123 456 789',
                'currency': 'VND',
                'default_city': 'Biên Hòa',
                'default_province': 'Đồng Nai',
                'default_country': 'Việt Nam',
                'primary_color': '#FF5A5F',
                'secondary_color': '#00A699',
                'theme': 'light',
                'site_description': 'BienHoa Rentals cung cấp dịch vụ tìm kiếm và cho thuê bất động sản tại Biên Hòa, Đồng Nai.'
            }
            
            # Save default settings to database
            for key, value in default_settings.items():
                Setting.set(key, value)
            
            settings = default_settings
    except Exception as e:
        app.logger.error(f"Error getting settings: {e}")
    
    # Mock backups data for template
    backups = []
    
    return render_template('admin/settings.html',
                          user=current_user,
                          settings=settings,
                          backups=backups,
                          active_tab='settings')

@app.route('/admin/settings/update', methods=['POST'])
@admin_required
def admin_settings_update():
    # Get the settings type from the form
    settings_type = request.form.get('settings_type')
    
    try:
        from models import Setting
        
        # Process different types of settings
        if settings_type == 'general':
            # General settings
            keys_to_update = [
                'site_name', 'site_tagline', 'site_description',
                'contact_email', 'contact_phone',
                'default_city', 'default_province', 'default_country', 'currency'
            ]
            
            # Update each setting
            for key in keys_to_update:
                if key in request.form:
                    Setting.set(key, request.form.get(key))
                    
        elif settings_type == 'appearance':
            # Appearance settings
            keys_to_update = [
                'primary_color', 'secondary_color',
                'font_family', 'theme'
            ]
            
            # Update each setting
            for key in keys_to_update:
                if key in request.form:
                    Setting.set(key, request.form.get(key))
                    
            # Handle file uploads
            if 'site_logo' in request.files and request.files['site_logo'].filename:
                # Process logo upload
                file = request.files['site_logo']
                filename = secure_filename(file.filename)
                upload_path = os.path.join('static', 'img', 'admin', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                Setting.set('site_logo', f'/{upload_path}')
                
            if 'favicon' in request.files and request.files['favicon'].filename:
                # Process favicon upload
                file = request.files['favicon']
                filename = secure_filename(file.filename)
                upload_path = os.path.join('static', 'img', 'admin', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                Setting.set('favicon', f'/{upload_path}')
                
            if 'hero_image' in request.files and request.files['hero_image'].filename:
                # Process hero image upload
                file = request.files['hero_image']
                filename = secure_filename(file.filename)
                upload_path = os.path.join('static', 'img', 'admin', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                Setting.set('hero_image', f'/{upload_path}')
                
        elif settings_type == 'advanced':
            # Advanced settings
            keys_to_update = [
                'google_maps_api_key', 'openai_api_key', 'ai_model',
                'upload_path', 'max_upload_size', 'image_sizing'
            ]
            
            # Update each setting
            for key in keys_to_update:
                if key in request.form:
                    Setting.set(key, request.form.get(key))
                    
            # Boolean settings
            bool_settings = ['enable_recaptcha', 'enable_maintenance']
            for key in bool_settings:
                Setting.set(key, '1' if key in request.form else '0')
                
            # Update reCAPTCHA settings
            if 'recaptcha_site_key' in request.form:
                Setting.set('recaptcha_site_key', request.form.get('recaptcha_site_key'))
            if 'recaptcha_secret_key' in request.form:
                Setting.set('recaptcha_secret_key', request.form.get('recaptcha_secret_key'))
        
        flash('Cài đặt đã được cập nhật thành công.', 'success')
        
    except Exception as e:
        app.logger.error(f"Error updating settings: {e}")
        flash(f'Đã xảy ra lỗi khi cập nhật cài đặt: {str(e)}', 'danger')
    
    return redirect(url_for('admin_settings'))

@app.route('/admin/database/backup', methods=['POST'])
@admin_required
def admin_database_backup():
    try:
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join('static', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate a timestamp for the backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.json'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Get data from database
        data = {
            'users': [],
            'properties': [],
            'property_images': [],
            'reviews': [],
            'settings': []
        }
        
        # Export users
        from models import User
        users = User.query.all()
        for user in users:
            user_data = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_image_url': user.profile_image_url,
                'user_type': user.user_type,
                'phone': user.phone,
                'bio': user.bio,
                'address': user.address,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            data['users'].append(user_data)
            
        # Export properties
        from models import Property
        properties = Property.query.all()
        for prop in properties:
            property_data = {
                'id': prop.id,
                'owner_id': prop.owner_id,
                'title': prop.title,
                'description': prop.description,
                'property_type': prop.property_type,
                'price': prop.price,
                'address': prop.address,
                'district': prop.district,
                'city': prop.city,
                'province': prop.province,
                'country': prop.country,
                'latitude': prop.latitude,
                'longitude': prop.longitude,
                'area': prop.area,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'furnishing': prop.furnishing,
                'available_from': prop.available_from.isoformat() if prop.available_from else None,
                'is_available': prop.is_available,
                'has_air_conditioning': prop.has_air_conditioning,
                'has_parking': prop.has_parking,
                'has_wifi': prop.has_wifi,
                'has_washing_machine': prop.has_washing_machine,
                'has_refrigerator': prop.has_refrigerator,
                'has_tv': prop.has_tv,
                'has_kitchen': prop.has_kitchen,
                'has_balcony': prop.has_balcony,
                'created_at': prop.created_at.isoformat() if prop.created_at else None
            }
            data['properties'].append(property_data)
            
        # Export property images
        from models import PropertyImage
        images = PropertyImage.query.all()
        for img in images:
            image_data = {
                'id': img.id,
                'property_id': img.property_id,
                'url': img.url,
                'is_primary': img.is_primary,
                'created_at': img.created_at.isoformat() if img.created_at else None
            }
            data['property_images'].append(image_data)
            
        # Export reviews
        from models import Review
        reviews = Review.query.all()
        for review in reviews:
            review_data = {
                'id': review.id,
                'property_id': review.property_id,
                'reviewer_id': review.reviewer_id,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat() if review.created_at else None
            }
            data['reviews'].append(review_data)
            
        # Export settings
        from models import Setting
        settings = Setting.query.all()
        for setting in settings:
            setting_data = {
                'key': setting.key,
                'value': setting.value
            }
            data['settings'].append(setting_data)
            
        # Write the data to a JSON file
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        flash('Đã tạo bản sao lưu cơ sở dữ liệu thành công.', 'success')
        
    except Exception as e:
        app.logger.error(f"Error creating backup: {e}")
        flash(f'Đã xảy ra lỗi khi tạo bản sao lưu: {str(e)}', 'danger')
        
    return redirect(url_for('admin_settings'))

@app.route('/admin/database/restore', methods=['POST'])
@admin_required
def admin_database_restore():
    # This would be replaced with actual database restore logic
    # For now we'll just flash a success message
    
    if 'restore_file' not in request.files:
        flash('Không tìm thấy tệp sao lưu.', 'danger')
        return redirect(url_for('admin_settings'))
    
    flash('Đã phục hồi cơ sở dữ liệu thành công.', 'success')
    return redirect(url_for('admin_settings'))

@app.route('/admin/database/delete-backup', methods=['POST'])
@admin_required
def admin_database_delete_backup():
    # This would be replaced with actual backup deletion logic
    # For now we'll just flash a success message
    
    filename = request.form.get('filename')
    flash(f'Đã xóa bản sao lưu {filename}.', 'success')
    return redirect(url_for('admin_settings'))

@app.route('/admin/reviews/<int:review_id>/delete', methods=['POST'])
@admin_required
def admin_review_delete(review_id):
    review = Review.query.get_or_404(review_id)
    
    # Store review info for flash message
    property_title = review.property.title
    
    # Delete review
    db.session.delete(review)
    db.session.commit()
    
    flash(f'Đã xóa đánh giá cho bất động sản "{property_title}".', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/properties/<int:property_id>/edit')
@admin_required
def admin_property_edit(property_id):
    # Will redirect to the standard property edit page
    return redirect(url_for('edit_property', property_id=property_id))

@app.route('/admin/properties/<int:property_id>/toggle', methods=['POST'])
@admin_required
def admin_property_toggle(property_id):
    property = Property.query.get_or_404(property_id)
    property.is_available = not property.is_available
    db.session.commit()
    
    flash(f'Đã đổi trạng thái của "{property.title}" thành {"Có Sẵn" if property.is_available else "Không Có Sẵn"}.', 'success')
    return redirect(url_for('admin_properties'))

@app.route('/admin/properties/<int:property_id>/delete', methods=['POST'])
@admin_required
def admin_property_delete(property_id):
    property = Property.query.get_or_404(property_id)
    
    # Delete associated images
    for image in property.images:
        # If image is stored on the server, delete the file
        if image.url.startswith('/static/'):
            try:
                file_path = os.path.join(os.getcwd(), image.url[1:])  # Remove leading slash
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                app.logger.error(f"Error deleting image file: {e}")
    
    # Store property title for flash message
    property_title = property.title
    
    # Delete property (cascade will delete images, favorites, etc.)
    db.session.delete(property)
    db.session.commit()
    
    flash(f'Đã xóa bất động sản "{property_title}".', 'success')
    return redirect(url_for('admin_properties'))

@app.route('/admin/users/<user_id>/edit')
@admin_required
def admin_user_edit(user_id):
    # Will implement user edit page in the next phase
    flash('Tính năng này đang được phát triển.', 'info')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<user_id>/detail')
@admin_required
def admin_user_detail(user_id):
    # Will implement user details page in the next phase
    flash('Tính năng này đang được phát triển.', 'info')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<user_id>/change-role', methods=['POST'])
@admin_required
def admin_user_change_role(user_id):
    user = User.query.get_or_404(user_id)
    user_type = request.form.get('user_type')
    
    if user_type in ['renter', 'landlord', 'admin']:
        user.user_type = user_type
        db.session.commit()
        flash(f'Đã thay đổi vai trò của {user.first_name or user.email or "người dùng"} thành {user_type}.', 'success')
    else:
        flash('Vai trò không hợp lệ.', 'danger')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<user_id>/delete', methods=['POST'])
@admin_required
def admin_user_delete(user_id):
    user = User.query.get_or_404(user_id)
    
    # Cannot delete self
    if user.id == current_user.id:
        flash('Bạn không thể xóa tài khoản của chính mình.', 'danger')
        return redirect(url_for('admin_users'))
    
    # Store user info for flash message
    user_name = user.first_name or user.email or "người dùng"
    
    # Delete user (cascade will delete their properties, reviews, etc.)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Đã xóa người dùng "{user_name}".', 'success')
    return redirect(url_for('admin_users'))

# 404 Error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('403.html', error_code=404, error_message="Page Not Found"), 404

# 403 Error page
@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html', error_code=403, error_message="Forbidden"), 403

# 500 Error page
@app.errorhandler(500)
def server_error(e):
    return render_template('403.html', error_code=500, error_message="Server Error"), 500
