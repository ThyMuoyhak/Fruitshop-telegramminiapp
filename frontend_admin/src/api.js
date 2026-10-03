// API Client for Food KH Admin Portal
const DEFAULT_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const getApiUrl = () => {
  return localStorage.getItem('foodkh_api_url') || DEFAULT_API_URL;
};

export const setApiUrl = (url) => {
  if (!url) {
    localStorage.removeItem('foodkh_api_url');
  } else {
    localStorage.setItem('foodkh_api_url', url.replace(/\/+$/, ''));
  }
};

export const getAuthToken = () => {
  return localStorage.getItem('foodkh_admin_token') || '';
};

export const setAuthToken = (token) => {
  if (!token) {
    localStorage.removeItem('foodkh_admin_token');
  } else {
    localStorage.setItem('foodkh_admin_token', token);
  }
};

async function request(endpoint, options = {}) {
  const baseUrl = getApiUrl();
  const token = getAuthToken();

  const headers = {
    ...(options.headers || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Auto set JSON header if body is not FormData
  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${baseUrl}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Unauthorized
    setAuthToken(null);
    window.dispatchEvent(new Event('auth:unauthorized'));
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMsg = data?.detail || data?.message || `Request failed with status ${response.status}`;
    throw new Error(errorMsg);
  }

  return data;
}

export const api = {
  // Auth
  async login(username, password) {
    const data = await request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    if (data.token) {
      setAuthToken(data.token);
    }
    return data;
  },

  async getMe() {
    return request('/api/auth/me');
  },

  logout() {
    setAuthToken(null);
  },

  // Stats & Analytics
  async getStats() {
    return request('/api/admin/stats');
  },

  // Products
  async getProducts() {
    return request('/api/products');
  },

  async createProduct(productData) {
    return request('/api/products', {
      method: 'POST',
      body: JSON.stringify(productData),
    });
  },

  async updateProduct(id, productData) {
    return request(`/api/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(productData),
    });
  },

  async toggleProduct(id) {
    return request(`/api/products/${id}/toggle`, {
      method: 'PATCH',
    });
  },

  async deleteProduct(id) {
    return request(`/api/products/${id}`, {
      method: 'DELETE',
    });
  },

  // Categories
  async getCategories() {
    return request('/api/categories');
  },

  async createCategory(categoryData) {
    return request('/api/categories', {
      method: 'POST',
      body: JSON.stringify(categoryData),
    });
  },

  async deleteCategory(id) {
    return request(`/api/categories/${id}`, {
      method: 'DELETE',
    });
  },

  // Orders
  async getOrders() {
    return request('/api/orders');
  },

  async updateOrderStatus(id, status) {
    return request(`/api/orders/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },

  // Image Upload
  async uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    return request('/api/upload', {
      method: 'POST',
      body: formData,
    });
  },
};
