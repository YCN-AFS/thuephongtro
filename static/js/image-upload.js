/**
 * Image upload functionality for property listings
 */

/**
 * Preview selected images before upload
 * @param {HTMLInputElement} input - File input element
 */
function previewImages(input) {
  const previewContainer = document.getElementById('image-preview-container');
  const errorContainer = document.getElementById('upload-error');
  const files = input.files;
  
  if (!files || files.length === 0) return;
  
  // Clear error message
  errorContainer.style.display = 'none';
  errorContainer.textContent = '';
  
  // Check each file
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    
    // Validate file type
    if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
      errorContainer.textContent = 'Chỉ chấp nhận các định dạng JPG, JPEG và PNG.';
      errorContainer.style.display = 'block';
      continue;
    }
    
    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      errorContainer.textContent = 'Kích thước tập tin không được vượt quá 5MB.';
      errorContainer.style.display = 'block';
      continue;
    }
    
    // Create preview element
    const preview = document.createElement('div');
    preview.className = 'position-relative border rounded p-1 image-preview-item';
    preview.style.width = '120px';
    preview.style.height = '120px';
    
    // Create image element
    const img = document.createElement('img');
    img.className = 'img-fluid h-100 w-100 object-fit-cover';
    img.file = file;
    preview.appendChild(img);
    
    // Add primary indicator for first image
    const isPrimary = previewContainer.children.length === 0;
    if (isPrimary) {
      const badge = document.createElement('div');
      badge.className = 'position-absolute top-0 end-0 p-1';
      badge.innerHTML = '<span class="badge bg-success">Chính</span>';
      badge.dataset.primaryBadge = 'true';
      preview.appendChild(badge);
    }
    
    // Add remove button
    const removeBtn = document.createElement('button');
    removeBtn.className = 'btn btn-sm btn-danger position-absolute bottom-0 end-0 p-0 m-1';
    removeBtn.style.width = '20px';
    removeBtn.style.height = '20px';
    removeBtn.innerHTML = '<i class="fas fa-times" style="font-size: 10px;"></i>';
    removeBtn.onclick = function(e) {
      e.preventDefault(); // Prevent form submission
      preview.remove();
      updatePrimaryImageIndicator();
    };
    preview.appendChild(removeBtn);
    
    // Add hidden input field for the form
    const hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.name = 'uploaded_images_index';
    hiddenInput.value = i;
    preview.appendChild(hiddenInput);
    
    // Add to preview container
    previewContainer.appendChild(preview);
    
    // Read the file and set the image source
    const reader = new FileReader();
    reader.onload = (function(aImg) {
      return function(e) {
        aImg.src = e.target.result;
      };
    })(img);
    reader.readAsDataURL(file);
  }
}

/**
 * Initialize image upload functionality
 */
function initImageUpload() {
  const fileInput = document.getElementById('property-images');
  if (!fileInput) return;
  
  // Make the preview container sortable if Sortable library is available
  const previewContainer = document.getElementById('image-preview-container');
  if (previewContainer && typeof Sortable !== 'undefined') {
    new Sortable(previewContainer, {
      animation: 150,
      ghostClass: 'sortable-ghost',
      onEnd: function() {
        // The order has changed, update UI to show which is primary
        updatePrimaryImageIndicator();
        // Update hidden inputs to reflect the new order
        updateImageOrder();
      }
    });
  }
}

/**
 * Update primary image indicator after reordering
 */
function updatePrimaryImageIndicator() {
  const previewContainer = document.getElementById('image-preview-container');
  if (!previewContainer || previewContainer.children.length === 0) return;
  
  // Remove all primary badges
  document.querySelectorAll('[data-primary-badge="true"]').forEach(badge => {
    badge.remove();
  });
  
  // Add primary badge to first image
  const firstPreview = previewContainer.children[0];
  const badge = document.createElement('div');
  badge.className = 'position-absolute top-0 end-0 p-1';
  badge.innerHTML = '<span class="badge bg-success">Chính</span>';
  badge.dataset.primaryBadge = 'true';
  firstPreview.appendChild(badge);
}

/**
 * Update hidden inputs to reflect the new image order
 */
function updateImageOrder() {
  const previewContainer = document.getElementById('image-preview-container');
  if (!previewContainer || previewContainer.children.length === 0) return;
  
  // Update the index values for the hidden inputs
  Array.from(previewContainer.children).forEach((preview, index) => {
    const hiddenInput = preview.querySelector('input[name="uploaded_images_index"]');
    if (hiddenInput) {
      hiddenInput.value = index;
    }
  });
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
  initImageUpload();
  
  // Add event listener to toggle between upload and stock images
  const useStockImages = document.getElementById('use-stock-images');
  if (useStockImages) {
    useStockImages.addEventListener('change', function() {
      const uploadSection = document.querySelector('.card.mb-4:has(#property-images)');
      const stockImagesContainer = document.querySelector('.stock-images-container');
      if (this.checked) {
        stockImagesContainer.style.display = 'block';
        uploadSection.style.opacity = '0.5';
      } else {
        stockImagesContainer.style.display = 'none';
        uploadSection.style.opacity = '1';
      }
    });
  }
});