module.exports = {
  testEnvironment: 'jsdom',
  testMatch: ['**/tests/frontend/**/*.test.js'],
  coverageDirectory: 'coverage-frontend',
  collectCoverageFrom: [
    'public/js/**/*.js',
    '!public/js/vendor/**',
    '!public/js/app.js', // Exclude main app file (UI-heavy)
    '!public/js/animations.js', // Exclude animations (DOM-heavy)
    '!public/js/location-picker.js', // Exclude location picker (MapBox integration)
    '!public/js/mapbox.js' // Exclude MapBox wrapper (external API)
  ],
  coverageThreshold: {
    global: {
      statements: 70,
      branches: 70,
      functions: 70,
      lines: 70
    }
  },
  testPathIgnorePatterns: [
    '/node_modules/',
    '/tests/test_.*\\.py$', // Ignore Python tests
    '/__pycache__/'
  ],
  moduleFileExtensions: ['js', 'json'],
  verbose: true
};
