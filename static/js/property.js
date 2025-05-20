/**
 * Property management functionality for RoomRental platform
 */

document.addEventListener('DOMContentLoaded', function() {
  // Property form validation
  const propertyForm = document.getElementById('property-form');
  
  if (propertyForm) {
    // Add a direct submit handler for debugging
    console.log('Property form found, adding submit event listener');
    
    propertyForm.addEventListener('submit', function(event) {
      console.log('Form submit event triggered');
      validatePropertyForm(event);
    });
    
    // Initialize stock image selection
    initImageSelection();
    
    // Initialize image upload functionality
    initImageUpload();
  } else {
    console.log('Property form not found');
  }
  
  // Delete property confirmation
  const deleteButtons = document.querySelectorAll('.delete-property-btn');
  
  deleteButtons.forEach(button => {
    button.addEventListener('click', confirmDeleteProperty);
  });
  
  // Property availability toggle
  const availabilityToggles = document.querySelectorAll('.availability-toggle');
  
  availabilityToggles.forEach(toggle => {
    toggle.addEventListener('change', togglePropertyAvailability);
  });
  
  // Toggle stock images section
  const useStockImages = document.getElementById('use-stock-images');
  if (useStockImages) {
    useStockImages.addEventListener('change', function() {
      const stockImagesContainer = document.querySelector('.stock-images-container');
      if (this.checked) {
        stockImagesContainer.style.display = 'block';
      } else {
        stockImagesContainer.style.display = 'none';
      }
    });
  }
  
  // Initialize property image carousel
  const propertyCarousel = document.getElementById('property-carousel');
  
  if (propertyCarousel) {
    new bootstrap.Carousel(propertyCarousel, {
      interval: 5000
    });
  }
});

/**
 * Validate property form before submission
 * @param {Event} event - Form submit event
 */
function validatePropertyForm(event) {
  const form = event.target;
  let isValid = true;
  
  // Check required fields
  const requiredFields = form.querySelectorAll('[required]');
  
  requiredFields.forEach(field => {
    if (!field.value.trim()) {
      isValid = false;
      showFieldError(field, 'Trường này không được để trống');
    } else {
      clearFieldError(field);
    }
  });
  
  // Validate price
  const priceField = form.querySelector('[name="price"]');
  
  if (priceField && priceField.value) {
    const price = parseFloat(priceField.value);
    
    if (isNaN(price) || price <= 0) {
      isValid = false;
      showFieldError(priceField, 'Vui lòng nhập giá hợp lệ');
    }
  }
  
  // Validate area
  const areaField = form.querySelector('[name="area"]');
  
  if (areaField && areaField.value) {
    const area = parseFloat(areaField.value);
    
    if (isNaN(area) || area <= 0) {
      isValid = false;
      showFieldError(areaField, 'Vui lòng nhập diện tích hợp lệ');
    }
  }
  
  // Validate bedrooms and bathrooms
  const bedroomsField = form.querySelector('[name="bedrooms"]');
  const bathroomsField = form.querySelector('[name="bathrooms"]');
  
  if (bedroomsField && bedroomsField.value) {
    const bedrooms = parseInt(bedroomsField.value);
    
    if (isNaN(bedrooms) || bedrooms < 0) {
      isValid = false;
      showFieldError(bedroomsField, 'Vui lòng nhập số phòng ngủ hợp lệ');
    }
  }
  
  if (bathroomsField && bathroomsField.value) {
    const bathrooms = parseInt(bathroomsField.value);
    
    if (isNaN(bathrooms) || bathrooms < 0) {
      isValid = false;
      showFieldError(bathroomsField, 'Vui lòng nhập số phòng tắm hợp lệ');
    }
  }
  
  // Check if at least one image is selected
  const selectedImages = getSelectedImages();
  const imageError = document.getElementById('image-error');
  
  // Make the image selection optional - don't prevent form submission if no images
  if (imageError) {
    imageError.style.display = 'none';
  }
  
  // Create hidden input fields for selected images
  if (isValid && selectedImages.length > 0) {
    selectedImages.forEach(imageUrl => {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'image_urls';
      input.value = imageUrl;
      form.appendChild(input);
    });
  }
  
  if (!isValid) {
    event.preventDefault();
    
    // Scroll to first error
    const firstError = form.querySelector('.invalid-feedback');
    if (firstError) {
      firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
}

/**
 * Show error message for a form field
 * @param {HTMLElement} field - Form field
 * @param {string} message - Error message
 */
function showFieldError(field, message) {
  field.classList.add('is-invalid');
  
  let errorElement = field.nextElementSibling;
  
  if (!errorElement || !errorElement.classList.contains('invalid-feedback')) {
    errorElement = document.createElement('div');
    errorElement.className = 'invalid-feedback';
    field.parentNode.insertBefore(errorElement, field.nextSibling);
  }
  
  errorElement.textContent = message;
}

/**
 * Clear error message for a form field
 * @param {HTMLElement} field - Form field
 */
function clearFieldError(field) {
  field.classList.remove('is-invalid');
  
  const errorElement = field.nextElementSibling;
  
  if (errorElement && errorElement.classList.contains('invalid-feedback')) {
    errorElement.textContent = '';
  }
}

/**
 * Initialize property image selection
 */
function initImageSelection() {
  const imageContainer = document.getElementById('image-selection-container');
  const imageItems = document.querySelectorAll('.image-item');
  
  if (!imageContainer) return;
  
  imageItems.forEach(item => {
    item.addEventListener('click', () => {
      item.classList.toggle('selected');
      
      // Update selected count
      updateSelectedImagesCount();
    });
  });
  
  // Initialize selected count
  updateSelectedImagesCount();
}

/**
 * Update selected images count
 */
function updateSelectedImagesCount() {
  const selectedCount = document.querySelectorAll('.image-item.selected').length;
  const countElement = document.getElementById('selected-images-count');
  
  if (countElement) {
    countElement.textContent = selectedCount;
  }
  
  // Show or hide error message
  const imageError = document.getElementById('image-error');
  if (imageError) {
    imageError.style.display = selectedCount === 0 ? 'block' : 'none';
  }
}

/**
 * Get selected image URLs
 * @returns {string[]} Array of selected image URLs
 */
function getSelectedImages() {
  const selectedItems = document.querySelectorAll('.image-item.selected');
  return Array.from(selectedItems).map(item => item.dataset.imageUrl);
}

/**
 * Confirm property deletion
 * @param {Event} event - Click event
 */
function confirmDeleteProperty(event) {
  event.preventDefault();
  
  const button = event.currentTarget;
  const propertyId = button.dataset.propertyId;
  const propertyTitle = button.dataset.propertyTitle;
  
  if (confirm(`Are you sure you want to delete "${propertyTitle}"? This action cannot be undone.`)) {
    // Submit the form
    const form = document.getElementById(`delete-property-form-${propertyId}`);
    if (form) {
      form.submit();
    }
  }
}

/**
 * Toggle property availability
 * @param {Event} event - Change event
 */
async function togglePropertyAvailability(event) {
  const toggle = event.currentTarget;
  const propertyId = toggle.dataset.propertyId;
  const isAvailable = toggle.checked;
  
  try {
    const response = await fetch(`/property/${propertyId}/edit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: `is_available=${isAvailable}`
    });
    
    if (response.ok) {
      showToast('Success', `Property availability updated to ${isAvailable ? 'available' : 'unavailable'}`, 'success');
    } else {
      toggle.checked = !isAvailable;
      showToast('Error', 'Failed to update property availability', 'danger');
    }
  } catch (error) {
    console.error('Error toggling availability:', error);
    toggle.checked = !isAvailable;
    showToast('Error', 'Failed to update property availability', 'danger');
  }
}

/**
 * Preview selected images in the form
 */
function previewSelectedImages() {
  const previewContainer = document.getElementById('image-preview-container');
  if (!previewContainer) return;
  
  // Clear current previews
  previewContainer.innerHTML = '';
  
  // Get selected images
  const selectedImages = getSelectedImages();
  
  if (selectedImages.length === 0) {
    previewContainer.innerHTML = '<p class="text-muted">No images selected</p>';
    return;
  }
  
  // Create image previews
  selectedImages.forEach(imageUrl => {
    const previewItem = document.createElement('div');
    previewItem.className = 'preview-item';
    
    const image = document.createElement('img');
    image.src = imageUrl;
    image.alt = 'Property Image';
    
    previewItem.appendChild(image);
    previewContainer.appendChild(previewItem);
  });
}
