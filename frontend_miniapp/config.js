// Food KH MiniApp Configuration
const urlParams = new URLSearchParams(window.location.search);
const paramApi = urlParams.get('api');
if (paramApi) {
  localStorage.setItem('FOODKH_API_URL', paramApi.replace(/\/+$/, ''));
}

// Fallback to local storage or production backend
export const API_BASE_URL = localStorage.getItem('FOODKH_API_URL') || 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:8000' 
    : 'https://fruitshop-backendapi.onrender.com');

export const KHR_EXCHANGE_RATE = 4100;
