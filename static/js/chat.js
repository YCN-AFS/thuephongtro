/**
 * AI Chat functionality for RoomRental platform
 */

class AIChat {
  constructor() {
    this.chatToggle = document.getElementById('ai-chat-toggle');
    this.chatWindow = document.getElementById('ai-chat-window');
    this.chatMessages = document.getElementById('ai-chat-messages');
    this.chatInput = document.getElementById('ai-chat-input');
    this.chatForm = document.getElementById('ai-chat-form');
    this.chatClose = document.getElementById('ai-chat-close');
    this.isOpen = false;
    this.isLoading = false;
    this.searchParams = {};
    
    this.initEventListeners();
  }
  
  /**
   * Initialize event listeners for chat functionality
   */
  initEventListeners() {
    if (this.chatToggle) {
      this.chatToggle.addEventListener('click', () => this.toggleChat());
    }
    
    if (this.chatClose) {
      this.chatClose.addEventListener('click', () => this.closeChat());
    }
    
    if (this.chatForm) {
      this.chatForm.addEventListener('submit', (e) => this.sendMessage(e));
    }
    
    // Check if chat window should be open based on URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('openChat') === 'true') {
      this.openChat();
    }
    
    // Get search parameters if available
    this.extractSearchParams();
  }
  
  /**
   * Extract search parameters from URL or page elements
   */
  extractSearchParams() {
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
      const district = searchForm.querySelector('[name="district"]')?.value;
      const minPrice = searchForm.querySelector('[name="min_price"]')?.value;
      const maxPrice = searchForm.querySelector('[name="max_price"]')?.value;
      const bedrooms = searchForm.querySelector('[name="bedrooms"]')?.value;
      const propertyType = searchForm.querySelector('[name="property_type"]')?.value;
      
      if (district) this.searchParams.district = district;
      if (minPrice) this.searchParams.min_price = minPrice;
      if (maxPrice) this.searchParams.max_price = maxPrice;
      if (bedrooms) this.searchParams.bedrooms = bedrooms;
      if (propertyType) this.searchParams.property_type = propertyType;
    }
  }
  
  /**
   * Toggle chat window open/closed
   */
  toggleChat() {
    if (this.isOpen) {
      this.closeChat();
    } else {
      this.openChat();
    }
  }
  
  /**
   * Open chat window
   */
  openChat() {
    if (!this.chatWindow) return;
    
    this.chatWindow.style.display = 'flex';
    this.isOpen = true;
    
    // Focus input field
    if (this.chatInput) {
      setTimeout(() => {
        this.chatInput.focus();
      }, 300);
    }
  }
  
  /**
   * Close chat window
   */
  closeChat() {
    if (!this.chatWindow) return;
    
    this.chatWindow.style.display = 'none';
    this.isOpen = false;
  }
  
  /**
   * Send a message to the AI assistant
   * @param {Event} event - Form submit event
   */
  async sendMessage(event) {
    event.preventDefault();
    
    if (!this.chatInput || this.isLoading) return;
    
    const message = this.chatInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    this.addUserMessage(message);
    
    // Clear input field
    this.chatInput.value = '';
    
    // Set loading state
    this.isLoading = true;
    this.addLoadingIndicator();
    
    try {
      const response = await fetch('/ai-assistant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          message: message,
          search_params: this.searchParams
        })
      });
      
      const data = await response.json();
      
      // Remove loading indicator
      this.removeLoadingIndicator();
      
      if (data.status === 'success') {
        this.addBotMessage(data.response);
        
        // Add property recommendations if available
        if (data.recommended_properties && data.recommended_properties.length > 0) {
          this.addPropertyRecommendations(data.recommended_properties);
        }
      } else {
        this.addBotMessage('Xin lỗi, tôi gặp sự cố. Vui lòng thử lại sau.');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      this.removeLoadingIndicator();
      this.addBotMessage('Sorry, I encountered a problem. Please try again later.');
    } finally {
      this.isLoading = false;
      
      // Scroll to bottom
      this.scrollToBottom();
    }
  }
  
  /**
   * Add user message to chat
   * @param {string} message - Message text
   */
  addUserMessage(message) {
    if (!this.chatMessages) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = 'ai-chat-message user';
    
    const contentElement = document.createElement('div');
    contentElement.className = 'ai-chat-message-content';
    contentElement.textContent = message;
    
    messageElement.appendChild(contentElement);
    this.chatMessages.appendChild(messageElement);
    this.scrollToBottom();
  }
  
  /**
   * Add bot message to chat
   * @param {string} message - Message text
   */
  addBotMessage(message) {
    if (!this.chatMessages) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = 'ai-chat-message bot';
    
    const contentElement = document.createElement('div');
    contentElement.className = 'ai-chat-message-content';
    
    // Support for line breaks
    const formattedMessage = message.replace(/\n/g, '<br>');
    contentElement.innerHTML = formattedMessage;
    
    messageElement.appendChild(contentElement);
    
    this.chatMessages.appendChild(messageElement);
    this.scrollToBottom();
  }
  
  /**
   * Add loading indicator to chat
   */
  addLoadingIndicator() {
    if (!this.chatMessages) return;
    
    const loadingElement = document.createElement('div');
    loadingElement.className = 'ai-chat-message bot';
    loadingElement.id = 'loading-indicator';
    
    const contentElement = document.createElement('div');
    contentElement.className = 'ai-chat-message-content';
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'ai-chat-loading';
    loadingDiv.innerHTML = `
      <span>Đang suy nghĩ</span>
      <div class="dots">
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
      </div>
    `;
    
    contentElement.appendChild(loadingDiv);
    loadingElement.appendChild(contentElement);
    this.chatMessages.appendChild(loadingElement);
    this.scrollToBottom();
  }
  
  /**
   * Remove loading indicator from chat
   */
  removeLoadingIndicator() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
      loadingIndicator.remove();
    }
  }
  
  /**
   * Add property recommendations with images and view buttons
   * @param {Array} properties - Array of recommended properties
   */
  addPropertyRecommendations(properties) {
    if (!this.chatMessages || !properties.length) return;
    
    const recommendationsElement = document.createElement('div');
    recommendationsElement.className = 'ai-chat-message bot';
    
    const contentElement = document.createElement('div');
    contentElement.className = 'ai-chat-message-content';
    
    const titleElement = document.createElement('div');
    titleElement.style.fontWeight = 'bold';
    titleElement.style.marginBottom = '10px';
    titleElement.textContent = 'Các bất động sản đề xuất:';
    contentElement.appendChild(titleElement);
    
    properties.forEach(property => {
      const propertyCard = document.createElement('div');
      propertyCard.className = 'ai-property-card';
      propertyCard.style.cssText = `
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin: 8px 0;
        padding: 12px;
        background: #f9f9f9;
      `;
      
      // Property image
      if (property.primary_image) {
        const imageElement = document.createElement('img');
        imageElement.src = property.primary_image;
        imageElement.alt = property.title;
        imageElement.style.cssText = `
          width: 100%;
          height: 120px;
          object-fit: cover;
          border-radius: 6px;
          margin-bottom: 8px;
        `;
        propertyCard.appendChild(imageElement);
      }
      
      // Property info
      const infoElement = document.createElement('div');
      infoElement.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 4px;">${property.title}</div>
        <div style="color: #FF5A5F; font-weight: bold; margin-bottom: 4px;">${property.price.toLocaleString('vi-VN')} VND/tháng</div>
        <div style="font-size: 12px; color: #666; margin-bottom: 8px;">${property.district}, ${property.city}</div>
        <div style="font-size: 12px; color: #666;">${property.bedrooms} PN • ${property.bathrooms} PT • ${property.area}m²</div>
      `;
      propertyCard.appendChild(infoElement);
      
      // View button
      const viewButton = document.createElement('button');
      viewButton.textContent = 'Xem chi tiết';
      viewButton.style.cssText = `
        background: #FF5A5F;
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 12px;
        cursor: pointer;
        margin-top: 8px;
        width: 100%;
      `;
      viewButton.onclick = () => {
        window.open(`/property/${property.id}`, '_blank');
      };
      propertyCard.appendChild(viewButton);
      
      contentElement.appendChild(propertyCard);
    });
    
    recommendationsElement.appendChild(contentElement);
    this.chatMessages.appendChild(recommendationsElement);
    this.scrollToBottom();
  }

  /**
   * Scroll chat messages to bottom
   */
  scrollToBottom() {
    if (this.chatMessages) {
      this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
  }
}

// Initialize AI Chat
document.addEventListener('DOMContentLoaded', function() {
  window.aiChat = new AIChat();
});
