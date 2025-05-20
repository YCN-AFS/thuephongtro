from flask import render_template, redirect, url_for, request, jsonify, flash, session, abort
from sqlalchemy import func, or_, and_, desc
from datetime import datetime, date
import json
import os
import base64
import uuid
from io import BytesIO
from PIL import Image
from urllib.parse import urlparse
import logging

from app import app, db
from models import User, Property, PropertyImage, Favorite, Message, ChatWithAI, UserChat, Review
from replit_auth import require_login, make_replit_blueprint, current_user, replit
from ai_assistant import get_ai_response, get_property_recommendations
from google_auth import google_auth

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
        flash('You do not have permission to delete this property', 'danger')
        return redirect(url_for('property_details', property_id=property_id))
    
    try:
        db.session.delete(property)
        db.session.commit()
        flash('Property deleted successfully!', 'success')
        return redirect(url_for('landlord_dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting property: {str(e)}', 'danger')
        logging.error(f"Error deleting property: {str(e)}")
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
