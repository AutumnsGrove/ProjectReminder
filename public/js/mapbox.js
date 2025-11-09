/**
 * MapBox GL JS Utilities Module
 *
 * Provides MapBox integration for location-based reminders:
 * - Map initialization
 * - Geocoding (address → lat/lng)
 * - Reverse geocoding (lat/lng → address)
 * - Location picker component
 *
 * Phase 6: Location Features
 */

const MapBoxUtils = (() => {
  let mapboxToken = null;
  let mapInstance = null;

  /**
   * Initialize MapBox with access token from secrets
   *
   * @returns {Promise<boolean>} True if initialization succeeded
   */
  async function init() {
    try {
      // Load MapBox token from config.json
      const config = await Storage.loadConfig();
      const mapboxAccessToken = config.location?.mapbox_token;

      if (mapboxAccessToken) {
        mapboxToken = mapboxAccessToken;
        mapboxgl.accessToken = mapboxToken;
        return true;
      } else {
        console.error('MapBox access token not found in config');
        return false;
      }
    } catch (error) {
      console.error('Failed to load MapBox token:', error);
      return false;
    }
  }

  /**
   * Create a map instance in a container
   *
   * @param {string} containerId - DOM element ID for map container
   * @param {object} options - Map options (center, zoom, etc.)
   * @returns {mapboxgl.Map} Map instance
   */
  function createMap(containerId, options = {}) {
    const defaults = {
      container: containerId,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: options.center || [0, 0], // World center
      zoom: options.zoom || 1.5 // Zoom level to show whole world
    };

    mapInstance = new mapboxgl.Map({ ...defaults, ...options });

    // Add navigation controls
    mapInstance.addControl(new mapboxgl.NavigationControl());

    return mapInstance;
  }

  /**
   * Geocode address to coordinates (forward geocoding)
   *
   * @param {string} address - Human-readable address
   * @returns {Promise<object>} { lat, lng, formatted_address }
   */
  async function geocodeAddress(address) {
    if (!mapboxToken) {
      throw new Error('MapBox not initialized. Call init() first.');
    }

    const encodedAddress = encodeURIComponent(address);
    const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodedAddress}.json?access_token=${mapboxToken}&limit=1`;

    try {
      const response = await fetch(url);
      const data = await response.json();

      if (data.features && data.features.length > 0) {
        const feature = data.features[0];
        return {
          lat: feature.center[1], // MapBox returns [lng, lat]
          lng: feature.center[0],
          formatted_address: feature.place_name
        };
      } else {
        throw new Error('No results found for address');
      }
    } catch (error) {
      console.error('Geocoding error:', error);
      throw error;
    }
  }

  /**
   * Reverse geocode coordinates to address
   *
   * @param {number} lat - Latitude
   * @param {number} lng - Longitude
   * @returns {Promise<string>} Formatted address
   */
  async function reverseGeocode(lat, lng) {
    if (!mapboxToken) {
      throw new Error('MapBox not initialized. Call init() first.');
    }

    const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${lng},${lat}.json?access_token=${mapboxToken}&limit=1`;

    try {
      const response = await fetch(url);
      const data = await response.json();

      if (data.features && data.features.length > 0) {
        return data.features[0].place_name;
      } else {
        return `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
      }
    } catch (error) {
      console.error('Reverse geocoding error:', error);
      return `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    }
  }

  /**
   * Get current location using browser Geolocation API
   *
   * @returns {Promise<object>} { lat, lng }
   */
  function getCurrentLocation() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported by browser'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          let message = 'Failed to get current location';

          switch (error.code) {
            case error.PERMISSION_DENIED:
              message = 'Location permission denied. Please enable location access.';
              break;
            case error.POSITION_UNAVAILABLE:
              message = 'Location information unavailable.';
              break;
            case error.TIMEOUT:
              message = 'Location request timed out.';
              break;
          }

          reject(new Error(message));
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    });
  }

  /**
   * Add a draggable marker to the map
   *
   * @param {mapboxgl.Map} map - Map instance
   * @param {number} lat - Initial latitude
   * @param {number} lng - Initial longitude
   * @param {function} onDragEnd - Callback when marker is dragged (receives {lat, lng})
   * @returns {mapboxgl.Marker} Marker instance
   */
  function addDraggableMarker(map, lat, lng, onDragEnd) {
    const marker = new mapboxgl.Marker({
      draggable: true,
      color: '#FF6B6B'
    })
      .setLngLat([lng, lat])
      .addTo(map);

    marker.on('dragend', () => {
      const lngLat = marker.getLngLat();
      if (onDragEnd) {
        onDragEnd({
          lat: lngLat.lat,
          lng: lngLat.lng
        });
      }
    });

    return marker;
  }

  /**
   * Add a radius circle to the map
   *
   * @param {mapboxgl.Map} map - Map instance
   * @param {number} lat - Center latitude
   * @param {number} lng - Center longitude
   * @param {number} radiusMeters - Radius in meters
   * @returns {string} Layer ID for removal
   */
  function addRadiusCircle(map, lat, lng, radiusMeters) {
    const layerId = `radius-circle-${Date.now()}`;

    // Create circle GeoJSON
    const circleGeoJSON = createCircleGeoJSON(lat, lng, radiusMeters);

    map.addSource(layerId, {
      type: 'geojson',
      data: circleGeoJSON
    });

    map.addLayer({
      id: layerId,
      type: 'fill',
      source: layerId,
      paint: {
        'fill-color': '#FF6B6B',
        'fill-opacity': 0.15
      }
    });

    map.addLayer({
      id: `${layerId}-outline`,
      type: 'line',
      source: layerId,
      paint: {
        'line-color': '#FF6B6B',
        'line-width': 2,
        'line-opacity': 0.5
      }
    });

    return layerId;
  }

  /**
   * Remove radius circle from map
   *
   * @param {mapboxgl.Map} map - Map instance
   * @param {string} layerId - Layer ID from addRadiusCircle
   */
  function removeRadiusCircle(map, layerId) {
    if (map.getLayer(layerId)) {
      map.removeLayer(layerId);
      map.removeLayer(`${layerId}-outline`);
      map.removeSource(layerId);
    }
  }

  /**
   * Create GeoJSON circle polygon
   *
   * @param {number} lat - Center latitude
   * @param {number} lng - Center longitude
   * @param {number} radiusMeters - Radius in meters
   * @returns {object} GeoJSON feature collection
   */
  function createCircleGeoJSON(lat, lng, radiusMeters) {
    const points = 64;
    const km = radiusMeters / 1000;
    const coords = [];
    const distanceX = km / (111.320 * Math.cos(lat * Math.PI / 180));
    const distanceY = km / 110.574;

    for (let i = 0; i < points; i++) {
      const theta = (i / points) * (2 * Math.PI);
      const x = distanceX * Math.cos(theta);
      const y = distanceY * Math.sin(theta);
      coords.push([lng + x, lat + y]);
    }
    coords.push(coords[0]); // Close the circle

    return {
      type: 'FeatureCollection',
      features: [{
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [coords]
        }
      }]
    };
  }

  /**
   * Format distance in human-readable form
   *
   * @param {number} meters - Distance in meters
   * @returns {string} Formatted distance (e.g., "150m" or "1.2km")
   */
  function formatDistance(meters) {
    if (meters < 1000) {
      return `${Math.round(meters)}m`;
    } else {
      return `${(meters / 1000).toFixed(1)}km`;
    }
  }

  // Public API
  return {
    init,
    createMap,
    geocodeAddress,
    reverseGeocode,
    getCurrentLocation,
    addDraggableMarker,
    addRadiusCircle,
    removeRadiusCircle,
    formatDistance
  };
})();
