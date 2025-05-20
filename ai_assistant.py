import os
import google.generativeai as genai
from typing import List, Dict, Any
import logging

# Configure Google Generative AI API
API_KEY = os.environ.get("GEMINI_API_KEY", "")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    logging.warning("GEMINI_API_KEY not found. AI assistant will not work properly.")

# Model configuration
model_name = "gemini-1.5-flash"  # Using the Gemini 2.0 API with the 1.5-flash model
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 1024,
}

# System prompt for room recommendation
SYSTEM_PROMPT = """You are a helpful property assistant for a rental platform in Biên Hòa, Vietnam. 
You help users find suitable rental properties based on their preferences.
Provide concise, friendly, and informative responses focused on the user's rental needs.
If asked about specific properties, use the provided property data to give accurate recommendations.
Do not make up information about properties if it's not in the data provided.
If the user asks for information outside of rental properties in Biên Hòa, politely redirect them.
Always maintain a helpful and professional tone."""


def get_ai_response(user_message: str, property_data: List[Dict[Any, Any]] = None, chat_history: List[Dict[str, str]] = None) -> str:
    """
    Get AI response based on user message and optionally property data
    
    Args:
        user_message: The user's message or query
        property_data: Optional list of property dictionaries with details
        chat_history: Optional list of previous chat messages
        
    Returns:
        AI generated response as string
    """
    if not API_KEY:
        return "I'm sorry, but I'm not available at the moment. Please try again later."
    
    try:
        # Create model
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=SYSTEM_PROMPT
        )
        
        # Prepare context with property data if available
        context = ""
        if property_data:
            context += "Here's information about available properties:\n"
            for i, prop in enumerate(property_data[:10]):  # Limit to first 10 properties
                context += f"\nProperty {i+1}:\n"
                context += f"- Title: {prop.get('title', 'N/A')}\n"
                context += f"- Price: {prop.get('price', 'N/A')} VND/month\n"
                context += f"- Location: {prop.get('district', 'N/A')}, {prop.get('city', 'Biên Hòa')}\n"
                context += f"- Type: {prop.get('property_type', 'N/A')}\n"
                context += f"- Bedrooms: {prop.get('bedrooms', 'N/A')}, Bathrooms: {prop.get('bathrooms', 'N/A')}\n"
                context += f"- Area: {prop.get('area', 'N/A')} m²\n"
                amenities = []
                for key, value in prop.get('amenities', {}).items():
                    if value:
                        amenities.append(key.replace('_', ' '))
                context += f"- Amenities: {', '.join(amenities) if amenities else 'N/A'}\n"
        
        # Initialize chat
        chat = model.start_chat(history=[])
        
        # Add chat history if available
        if chat_history:
            for msg in chat_history:
                if msg.get('role') == 'user':
                    chat.send_message(msg.get('content', ''))
                else:
                    # This part is a bit tricky as we can't directly add model responses
                    # We'll skip this for now, but in a production app you'd need 
                    # to handle this differently
                    pass
        
        # Generate response
        response = chat.send_message(context + "\n\n" + user_message if context else user_message)
        return response.text
        
    except Exception as e:
        logging.error(f"Error in AI response generation: {str(e)}")
        return "I'm sorry, but I encountered an error. Please try again later."


def get_property_recommendations(preferences: Dict[str, Any], properties: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
    """
    Get property recommendations based on user preferences
    
    Args:
        preferences: Dictionary of user preferences
        properties: List of all available properties
        
    Returns:
        List of recommended properties
    """
    recommendations = []
    
    # Filter properties based on price range
    min_price = preferences.get('min_price')
    max_price = preferences.get('max_price')
    if min_price is not None:
        properties = [p for p in properties if p.get('price', 0) >= min_price]
    if max_price is not None:
        properties = [p for p in properties if p.get('price', 0) <= max_price]
    
    # Filter by location
    district = preferences.get('district')
    if district:
        properties = [p for p in properties if district.lower() in p.get('district', '').lower()]
    
    # Filter by property type
    property_type = preferences.get('property_type')
    if property_type:
        properties = [p for p in properties if property_type.lower() == p.get('property_type', '').lower()]
    
    # Filter by number of bedrooms and bathrooms
    bedrooms = preferences.get('bedrooms')
    if bedrooms is not None:
        properties = [p for p in properties if p.get('bedrooms', 0) >= bedrooms]
    
    bathrooms = preferences.get('bathrooms')
    if bathrooms is not None:
        properties = [p for p in properties if p.get('bathrooms', 0) >= bathrooms]
    
    # Filter by amenities
    amenities = preferences.get('amenities', [])
    for amenity in amenities:
        amenity_key = f"has_{amenity.lower().replace(' ', '_')}"
        properties = [p for p in properties if p.get('amenities', {}).get(amenity_key, False)]
    
    return properties
