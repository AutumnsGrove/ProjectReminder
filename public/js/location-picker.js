/**
 * Location Picker Component
 *
 * Handles location selection UI in the edit form:
 * - Address search with geocoding
 * - Interactive map with draggable marker
 * - "Use My Location" button
 * - Radius slider
 * - Location display and clearing
 *
 * Phase 6: Location Features
 */

const LocationPicker = (() => {
  let map = null;
  let marker = null;
  let radiusCircleLayerId = null;
  let currentLocation = {
    name: null,
    address: null,
    lat: null,
    lng: null,
    radius: 100
  };

  // DOM elements
  const els = {};

  /**
   * Initialize location picker component
   */
  async function init() {
    // Cache DOM elements
    els.locationSearch = document.getElementById('locationSearch');
    els.useMyLocationBtn = document.getElementById('useMyLocationBtn');
    els.mapContainer = document.getElementById('mapContainer');
    els.locationMap = document.getElementById('locationMap');
    els.radiusSlider = document.getElementById('radiusSlider');
    els.radiusValue = document.getElementById('radiusValue');
    els.locationDisplay = document.getElementById('locationDisplay');
    els.locationDisplayName = document.getElementById('locationDisplayName');
    els.locationDisplayAddress = document.getElementById('locationDisplayAddress');
    els.clearLocationBtn = document.getElementById('clearLocationBtn');
    els.useLocationBtn = document.getElementById('useLocationBtn');

    // Hidden form fields
    els.locationName = document.getElementById('locationName');
    els.locationAddress = document.getElementById('locationAddress');
    els.locationLat = document.getElementById('locationLat');
    els.locationLng = document.getElementById('locationLng');
    els.locationRadius = document.getElementById('locationRadius');

    // Initialize MapBox
    const initialized = await MapBoxUtils.init();
    if (!initialized) {
      console.error('Failed to initialize MapBox');
      return;
    }

    // Setup event listeners
    setupEventListeners();
  }

  /**
   * Setup all event listeners
   */
  function setupEventListeners() {
    // Search input - Enter key triggers geocoding
    els.locationSearch.addEventListener('keypress', async (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        await handleAddressSearch();
      }
    });

    // Use My Location button
    els.useMyLocationBtn.addEventListener('click', async () => {
      await handleUseMyLocation();
    });

    // Radius slider
    els.radiusSlider.addEventListener('input', (e) => {
      handleRadiusChange(parseInt(e.target.value));
    });

    // Clear location button
    els.clearLocationBtn.addEventListener('click', () => {
      clearLocation();
    });

    // Use This Location button - confirms selection and closes map
    if (els.useLocationBtn) {
      els.useLocationBtn.addEventListener('click', (e) => {
        e.preventDefault();
        handleUseThisLocation();
      });
    }
  }

  /**
   * Handle address search (geocoding)
   */
  async function handleAddressSearch() {
    const address = els.locationSearch.value.trim();
    if (!address) return;

    try {
      // Show loading state
      els.locationSearch.disabled = true;
      els.locationSearch.value = 'Searching...';

      // Geocode address
      const result = await MapBoxUtils.geocodeAddress(address);

      // Validate geocoding result before using it
      if (!result || !result.lat || !result.lng) {
        throw new Error('GEOCODE_NO_RESULTS');
      }

      // Set location (may throw if map initialization fails, but that's a different error)
      try {
        setLocation({
          name: address,
          address: result.formatted_address || address,
          lat: result.lat,
          lng: result.lng,
          radius: currentLocation.radius
        });

        // Clear search input only on success
        els.locationSearch.value = '';
      } catch (mapError) {
        // Map/UI error (not geocoding failure) - log but don't show confusing alert
        console.error('Map display error after successful geocoding:', mapError);
        // Restore the address so user can try again
        els.locationSearch.value = address;
      }

    } catch (error) {
      // Only show alert for actual geocoding failures
      if (error.message === 'GEOCODE_NO_RESULTS' || error.name === 'GeocodeError') {
        console.error('Geocoding failed:', error);
        alert('Could not find that location. Please try a different address.');
      } else {
        // Unexpected error - log for debugging but don't show confusing alert
        console.error('Unexpected error during address search:', error);
      }
      // Restore the address so user can try again
      els.locationSearch.value = address;
    } finally {
      els.locationSearch.disabled = false;
    }
  }

  /**
   * Handle "Use My Location" button
   */
  async function handleUseMyLocation() {
    try {
      // Show loading state
      els.useMyLocationBtn.disabled = true;
      els.useMyLocationBtn.textContent = '📍 Getting location...';

      // Get current location
      const location = await MapBoxUtils.getCurrentLocation();

      // Reverse geocode to get address
      const address = await MapBoxUtils.reverseGeocode(location.lat, location.lng);

      // Set location
      setLocation({
        name: 'Current Location',
        address: address,
        lat: location.lat,
        lng: location.lng,
        radius: currentLocation.radius
      });
    } catch (error) {
      console.error('Geolocation error:', error);
      alert(error.message || 'Failed to get your current location.');
    } finally {
      els.useMyLocationBtn.disabled = false;
      els.useMyLocationBtn.textContent = '📍 Use My Location';
    }
  }

  /**
   * Handle radius slider change
   */
  function handleRadiusChange(radius) {
    currentLocation.radius = radius;

    // Update radius display
    els.radiusValue.textContent = MapBoxUtils.formatDistance(radius);

    // Update hidden form field
    els.locationRadius.value = radius;

    // Update radius circle on map
    if (map && currentLocation.lat && currentLocation.lng) {
      updateRadiusCircle(currentLocation.lat, currentLocation.lng, radius);
    }
  }

  /**
   * Handle "Use This Location" button click
   * Confirms location selection and closes the map
   */
  function handleUseThisLocation() {
    if (!currentLocation.lat || !currentLocation.lng) {
      alert('Please select a location on the map first');
      return;
    }

    // Location is already saved in form fields by setLocation()
    // Just provide visual feedback by collapsing the map
    els.mapContainer.style.display = 'none';

    // Show a brief visual confirmation
    showConfirmationFeedback();
  }

  /**
   * Show visual confirmation that location was accepted
   */
  function showConfirmationFeedback() {
    if (els.locationDisplay) {
      // Add a brief highlight to show the location was confirmed
      const originalBackground = els.locationDisplay.style.backgroundColor;
      els.locationDisplay.style.backgroundColor = '#e8f5e9';

      // Remove highlight after 1 second
      setTimeout(() => {
        els.locationDisplay.style.backgroundColor = originalBackground;
      }, 1000);
    }
  }

  /**
   * Set location and update UI
   */
  function setLocation(location) {
    // Update current location state
    currentLocation = { ...location };

    // Update hidden form fields
    els.locationName.value = location.name || '';
    els.locationAddress.value = location.address || '';
    els.locationLat.value = location.lat || '';
    els.locationLng.value = location.lng || '';
    els.locationRadius.value = location.radius || 100;

    // Update location display
    els.locationDisplayName.textContent = location.name || 'Unknown Location';
    els.locationDisplayAddress.textContent = location.address || '';
    els.locationDisplay.style.display = 'flex';

    // Show map and initialize if needed
    showMap(location.lat, location.lng);
  }

  /**
   * Show map and add marker at location
   */
  function showMap(lat, lng) {
    // Show map container
    els.mapContainer.style.display = 'block';

    // Initialize map if not already created
    if (!map) {
      map = MapBoxUtils.createMap('locationMap', {
        center: [lng, lat],
        zoom: 14
      });

      // Wait for map style to load before adding layers (prevents "Style is not done loading" error)
      map.on('load', () => {
        // Add marker after style loads
        if (!marker) {
          marker = MapBoxUtils.addDraggableMarker(map, lat, lng, async (newCoords) => {
            // Marker was dragged - reverse geocode new position
            const address = await MapBoxUtils.reverseGeocode(newCoords.lat, newCoords.lng);

            // Update location (without recreating marker)
            currentLocation.lat = newCoords.lat;
            currentLocation.lng = newCoords.lng;
            currentLocation.address = address;

            // Update form fields
            els.locationAddress.value = address;
            els.locationLat.value = newCoords.lat;
            els.locationLng.value = newCoords.lng;

            // Update display
            els.locationDisplayAddress.textContent = address;

            // Update radius circle
            updateRadiusCircle(newCoords.lat, newCoords.lng, currentLocation.radius);
          });
        }

        // Add radius circle after style loads
        updateRadiusCircle(lat, lng, currentLocation.radius);
      });

      // Add map click handler (can be added immediately, doesn't require style)
      map.on('click', async (e) => {
        const clickedLat = e.lngLat.lat;
        const clickedLng = e.lngLat.lng;

        // Reverse geocode clicked location
        const address = await MapBoxUtils.reverseGeocode(clickedLat, clickedLng);

        // Update location
        setLocation({
          name: 'Custom Location',
          address: address,
          lat: clickedLat,
          lng: clickedLng,
          radius: currentLocation.radius
        });
      });
    } else {
      // Map already exists - fly to new location
      map.flyTo({
        center: [lng, lat],
        zoom: 14
      });

      // Update marker (map already loaded, safe to update immediately)
      if (marker) {
        marker.setLngLat([lng, lat]);
      }

      // Update radius circle (map already loaded, safe to update immediately)
      updateRadiusCircle(lat, lng, currentLocation.radius);
    }
  }

  /**
   * Update radius circle on map
   */
  function updateRadiusCircle(lat, lng, radius) {
    if (!map) return;

    // Remove old circle if exists
    if (radiusCircleLayerId) {
      MapBoxUtils.removeRadiusCircle(map, radiusCircleLayerId);
    }

    // Add new circle
    radiusCircleLayerId = MapBoxUtils.addRadiusCircle(map, lat, lng, radius);
  }

  /**
   * Clear location and reset form
   */
  function clearLocation() {
    // Reset current location state
    currentLocation = {
      name: null,
      address: null,
      lat: null,
      lng: null,
      radius: 100
    };

    // Clear hidden form fields
    els.locationName.value = '';
    els.locationAddress.value = '';
    els.locationLat.value = '';
    els.locationLng.value = '';
    els.locationRadius.value = '100';

    // Hide location display
    els.locationDisplay.style.display = 'none';

    // Hide map
    els.mapContainer.style.display = 'none';

    // Remove marker
    if (marker) {
      marker.remove();
      marker = null;
    }

    // Remove radius circle
    if (map && radiusCircleLayerId) {
      MapBoxUtils.removeRadiusCircle(map, radiusCircleLayerId);
      radiusCircleLayerId = null;
    }

    // Reset radius slider
    els.radiusSlider.value = '100';
    els.radiusValue.textContent = '100m';
  }

  /**
   * Load existing location into picker (for editing)
   */
  function loadLocation(locationData) {
    if (!locationData || !locationData.location_lat || !locationData.location_lng) {
      return;
    }

    setLocation({
      name: locationData.location_name || 'Saved Location',
      address: locationData.location_address || '',
      lat: locationData.location_lat,
      lng: locationData.location_lng,
      radius: locationData.location_radius || 100
    });

    // Update radius slider
    els.radiusSlider.value = locationData.location_radius || 100;
    els.radiusValue.textContent = MapBoxUtils.formatDistance(locationData.location_radius || 100);
  }

  /**
   * Get current location data for form submission
   */
  function getLocation() {
    if (!currentLocation.lat || !currentLocation.lng) {
      return null;
    }

    return {
      location_name: currentLocation.name,
      location_address: currentLocation.address,
      location_lat: currentLocation.lat,
      location_lng: currentLocation.lng,
      location_radius: currentLocation.radius
    };
  }

  // Public API
  return {
    init,
    loadLocation,
    getLocation,
    clearLocation
  };
})();
