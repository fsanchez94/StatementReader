// Simple test to verify the frontend can communicate with Django backend
const API_BASE = 'http://127.0.0.1:5000/api';

// Test parser types endpoint
fetch(`${API_BASE}/parser-types/`)
  .then(response => response.json())
  .then(data => {
    console.log('✅ Parser types loaded:', data.length, 'types available');
    console.log('Available parsers:', data.map(p => p.label));
  })
  .catch(error => {
    console.error('❌ Failed to load parser types:', error);
  });

console.log('Testing Django backend API from browser context...');
console.log('Frontend should be accessible at: http://localhost:3000');
console.log('Django admin should be accessible at: http://127.0.0.1:5000/admin/');