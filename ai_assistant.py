import os
import google.generativeai as genai
from typing import List, Dict, Any
import logging
import re

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
SYSTEM_PROMPT = """Bạn là trợ lý bất động sản thông minh cho nền tảng cho thuê nhà ở Biên Hòa, Việt Nam.

QUY TắC QUAN TRỌNG:
- LUÔN phân tích thông tin người dùng đã cung cấp trong tin nhắn
- KHÔNG hỏi lại thông tin đã được cung cấp rõ ràng
- ĐƯA RA đề xuất cụ thể ngay lập tức khi có đủ thông tin
- Trả lời NGẮN GỌN, TRỰC TIẾP, không dài dòng
- KHÔNG sử dụng markdown
- Tối đa 2-3 câu cho mỗi phản hồi

BƯỚC XỬ LÝ THÔNG TIN:
1. ĐỌC KỸ tin nhắn người dùng để tìm: giá thuê, loại nhà, khu vực
2. TÌM KIẾM trong dữ liệu bất động sản những căn phù hợp
3. ĐƯA RA đề xuất CỤ THỂ với tên, giá, địa chỉ
4. CHỈ hỏi thêm nếu thông tin hoàn toàn không đủ

VÍ DỤ ĐÚNG: 
- Input: "tôi cần phòng trọ 5 triệu"
- Output: "Tôi tìm thấy 2 phòng phù hợp: Phòng trọ Trảng Dài 4.5 triệu/tháng, 25m². Căn hộ mini Tân Phong 5 triệu/tháng, 30m²."

VÍ DỤ SAI: "Bạn muốn tìm phòng ở khu vực nào?" (KHI ĐÃ NÓI RÕ 5 TRIỆU)
"""


def clean_markdown(text: str) -> str:
    """Remove markdown formatting from text"""
    # Remove bold and italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove headers
    text = re.sub(r'^#{1,6}\s*([^\n]+)', r'\1', text, flags=re.MULTILINE)
    
    # Remove code blocks
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove bullet points and numbered lists formatting
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text


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
        return "Xin lỗi, tôi cần kết nối với hệ thống AI để hoạt động. Vui lòng thử lại sau."
    
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
            context += "Dữ liệu bất động sản thực từ hệ thống:\n"
            for i, prop in enumerate(property_data[:8]):  # Show more properties for better recommendations
                context += f"\nBất động sản {i+1} (ID: {prop.get('id')}):\n"
                context += f"- Tiêu đề: {prop.get('title', 'Không có')}\n"
                context += f"- Giá: {prop.get('price', 'Không có'):,.0f} VND/tháng\n"
                context += f"- Địa điểm: {prop.get('district', 'Không có')}, {prop.get('city', 'Biên Hòa')}\n"
                context += f"- Loại: {prop.get('property_type', 'Không có')}\n"
                context += f"- Phòng ngủ: {prop.get('bedrooms', 'Không có')}, Phòng tắm: {prop.get('bathrooms', 'Không có')}\n"
                context += f"- Diện tích: {prop.get('area', 'Không có')} m²\n"
                
                # Format amenities in Vietnamese
                amenities = []
                amenity_translations = {
                    'has_air_conditioning': 'Điều hòa',
                    'has_parking': 'Chỗ đỗ xe',
                    'has_wifi': 'WiFi',
                    'has_washing_machine': 'Máy giặt',
                    'has_refrigerator': 'Tủ lạnh',
                    'has_tv': 'TV',
                    'has_kitchen': 'Bếp',
                    'has_balcony': 'Ban công'
                }
                
                for key, value in prop.items():
                    if key.startswith('has_') and value and key in amenity_translations:
                        amenities.append(amenity_translations[key])
                context += f"- Tiện nghi: {', '.join(amenities) if amenities else 'Không có'}\n"
        
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
        
        # Clean up response by removing markdown and formatting
        cleaned_response = clean_markdown(response.text)
        return cleaned_response
        
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
