/**
 * Map functionality for RoomRental platform
 * Uses Leaflet.js as a lightweight alternative to Google Maps
 */

class PropertyMap {
  constructor(mapElementId, latitude, longitude, propertyTitle) {
    this.mapElement = document.getElementById(mapElementId);
    this.latitude = latitude || 10.95;  // Default to Biên Hòa coordinates
    this.longitude = longitude || 106.82;
    this.propertyTitle = propertyTitle || 'Property Location';
    this.map = null;
    this.marker = null;
    
    if (this.mapElement) {
      this.initMap();
    }
  }
  
  /**
   * Initialize the map
   */
  initMap() {
    // Load Leaflet CSS
    if (!document.getElementById('leaflet-css')) {
      const link = document.createElement('link');
      link.id = 'leaflet-css';
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.3/dist/leaflet.css';
      link.integrity = 'sha256-kLaT2GOSpHechhsozzB+flnD+zUyjE2LlfWPgU04xyI=';
      link.crossOrigin = '';
      document.head.appendChild(link);
    }
    
    // Load Leaflet JS if not already loaded
    if (typeof L === 'undefined') {
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.3/dist/leaflet.js';
      script.integrity = 'sha256-WBkoXOwTeyKclOHuWtc+i2uENFpDZ9YPdf5Hf+D7ewM=';
      script.crossOrigin = '';
      script.onload = () => this.renderMap();
      document.head.appendChild(script);
    } else {
      this.renderMap();
    }
  }
  
  /**
   * Render the map after Leaflet is loaded
   */
  renderMap() {
    // Initialize map
    this.map = L.map(this.mapElement).setView([this.latitude, this.longitude], 15);
    
    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(this.map);
    
    // Add marker
    this.marker = L.marker([this.latitude, this.longitude]).addTo(this.map);
    
    // Add popup with property title
    this.marker.bindPopup(this.propertyTitle).openPopup();
    
    // Fix map display issue (sometimes needed when map is in a tab or hidden container)
    setTimeout(() => {
      this.map.invalidateSize();
    }, 100);
  }
}

/**
 * Initialize map on property details page
 */
document.addEventListener('DOMContentLoaded', function() {
  const propertyMap = document.getElementById('property-map');
  
  if (propertyMap) {
    const latitude = parseFloat(propertyMap.dataset.latitude) || null;
    const longitude = parseFloat(propertyMap.dataset.longitude) || null;
    const propertyTitle = propertyMap.dataset.propertyTitle || 'Property Location';
    
    // Initialize map with property coordinates
    new PropertyMap('property-map', latitude, longitude, propertyTitle);
  }
  
  // Tab change event for map resize
  const propertyDetailTabs = document.querySelectorAll('button[data-bs-toggle="tab"]');
  
  propertyDetailTabs.forEach(tab => {
    tab.addEventListener('shown.bs.tab', function(event) {
      if (event.target.getAttribute('href') === '#location') {
        window.dispatchEvent(new Event('resize'));
      }
    });
  });
});
