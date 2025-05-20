/**
 * Main JavaScript functionality for RoomRental platform
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
  
  // Initialize popovers
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });
  
  // Flash messages as toasts
  const flashMessages = document.querySelectorAll('.flash-message');
  flashMessages.forEach(message => {
    const toast = new bootstrap.Toast(message);
    toast.show();
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
      toast.hide();
    }, 5000);
  });
  
  // Add favorite toggle buttons functionality
  const favoriteButtons = document.querySelectorAll('.favorite-button');
  favoriteButtons.forEach(button => {
    button.addEventListener('click', toggleFavorite);
  });
  
  // Price range sliders
  const priceRangeMin = document.getElementById('price-range-min');
  const priceRangeMax = document.getElementById('price-range-max');
  const priceMinDisplay = document.getElementById('price-min-display');
  const priceMaxDisplay = document.getElementById('price-max-display');
  
  if (priceRangeMin && priceRangeMax) {
    priceRangeMin.addEventListener('input', function() {
      const minValue = parseInt(this.value);
      const maxValue = parseInt(priceRangeMax.value);
      
      if (minValue >= maxValue) {
        this.value = maxValue - 1000000;
      }
      
      if (priceMinDisplay) {
        priceMinDisplay.textContent = formatPrice(this.value);
      }
    });
    
    priceRangeMax.addEventListener('input', function() {
      const minValue = parseInt(priceRangeMin.value);
      const maxValue = parseInt(this.value);
      
      if (maxValue <= minValue) {
        this.value = minValue + 1000000;
      }
      
      if (priceMaxDisplay) {
        priceMaxDisplay.textContent = formatPrice(this.value);
      }
    });
  }
  
  // Mobile menu toggle
  const mobileMenuButton = document.querySelector('.navbar-toggler');
  const navbarCollapse = document.querySelector('.navbar-collapse');
  
  if (mobileMenuButton && navbarCollapse) {
    mobileMenuButton.addEventListener('click', function() {
      navbarCollapse.classList.toggle('show');
    });
  }
  
  // Scroll to top button
  const scrollTopButton = document.getElementById('scroll-top-button');
  
  if (scrollTopButton) {
    window.addEventListener('scroll', function() {
      if (window.pageYOffset > 300) {
        scrollTopButton.classList.add('show');
      } else {
        scrollTopButton.classList.remove('show');
      }
    });
    
    scrollTopButton.addEventListener('click', function() {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }
  
  // Property type select
  const propertyTypeSelect = document.getElementById('property-type');
  
  if (propertyTypeSelect) {
    propertyTypeSelect.addEventListener('change', function() {
      const selectedType = this.value;
      
      // You can add additional logic here to show/hide specific fields
      // based on the property type if needed
    });
  }
  
  // Initialize date pickers
  const datePickers = document.querySelectorAll('.datepicker');
  
  datePickers.forEach(datePicker => {
    // This assumes you're using the built-in date input
    // If you want to use a custom date picker library, you would initialize it here
    datePicker.min = new Date().toISOString().split('T')[0];
  });
});

/**
 * Format price in Vietnamese Dong
 * @param {number} price - Price to format
 * @returns {string} Formatted price
 */
function formatPrice(price) {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0
  }).format(price);
}

/**
 * Toggle favorite status for a property
 * @param {Event} event - Click event
 */
async function toggleFavorite(event) {
  event.preventDefault();
  
  const button = event.currentTarget;
  const propertyId = button.dataset.propertyId;
  const heartIcon = button.querySelector('i');
  
  try {
    // Show loading state
    button.disabled = true;
    heartIcon.className = 'fas fa-spinner fa-spin';
    
    const response = await fetch(`/property/${propertyId}/favorite`, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      if (data.is_favorite) {
        heartIcon.className = 'fas fa-heart text-danger';
        button.setAttribute('title', 'Remove from favorites');
        
        // Show toast notification
        showToast('Success', data.message, 'success');
      } else {
        heartIcon.className = 'far fa-heart';
        button.setAttribute('title', 'Add to favorites');
        
        // Show toast notification
        showToast('Success', data.message, 'success');
      }
    } else {
      // Error handling
      showToast('Error', data.message, 'danger');
    }
  } catch (error) {
    console.error('Error toggling favorite:', error);
    showToast('Error', 'Failed to update favorite status', 'danger');
    
    // Reset button state
    heartIcon.className = 'far fa-heart';
  } finally {
    button.disabled = false;
  }
}

/**
 * Show toast notification
 * @param {string} title - Toast title
 * @param {string} message - Toast message
 * @param {string} type - Toast type (success, danger, warning, info)
 */
function showToast(title, message, type = 'info') {
  // Create toast container if it doesn't exist
  let toastContainer = document.querySelector('.toast-container');
  
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
  }
  
  // Create toast element
  const toastId = 'toast-' + Date.now();
  const toastHtml = `
    <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="toast-header bg-${type} text-white">
        <strong class="me-auto">${title}</strong>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
      <div class="toast-body">
        ${message}
      </div>
    </div>
  `;
  
  toastContainer.insertAdjacentHTML('beforeend', toastHtml);
  
  // Initialize and show toast
  const toastElement = document.getElementById(toastId);
  const toast = new bootstrap.Toast(toastElement);
  toast.show();
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    toast.hide();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
      toastElement.remove();
    });
  }, 5000);
}
