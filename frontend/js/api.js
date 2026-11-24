/**
 * SmartRail AI+ — API Client
 * Connects frontend to the C++/Python backend (port 8080) and AI Service (port 8000)
 */

const API_CONFIG = {
  BACKEND_BASE_URL: 'http://localhost:8080/api',
  AI_BASE_URL: 'http://localhost:8000/ai',
  TOKEN_KEY: 'smartrail_token',
  USER_KEY: 'smartrail_user'
};

const API = {
  getToken() {
    return localStorage.getItem(API_CONFIG.TOKEN_KEY);
  },

  setAuth(token, user) {
    localStorage.setItem(API_CONFIG.TOKEN_KEY, token);
    localStorage.setItem(API_CONFIG.USER_KEY, JSON.stringify(user));
  },

  clearAuth() {
    localStorage.removeItem(API_CONFIG.TOKEN_KEY);
    localStorage.removeItem(API_CONFIG.USER_KEY);
  },

  getUser() {
    const u = localStorage.getItem(API_CONFIG.USER_KEY);
    return u ? JSON.parse(u) : null;
  },

  isLoggedIn() {
    return !!this.getToken();
  },

  async request(endpoint, options = {}, isAI = false) {
    const baseUrl = isAI ? API_CONFIG.AI_BASE_URL : API_CONFIG.BACKEND_BASE_URL;
    const url = `${baseUrl}${endpoint}`;

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    const token = this.getToken();
    if (token && !isAI) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, { ...options, headers });
      if (response.status === 401) {
        this.clearAuth();
        if (window.location.pathname.includes('/pages/') && !window.location.pathname.includes('login.html')) {
          window.location.href = 'login.html';
        }
      }
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'API request failed');
      }
      return data;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  },

  // Auth
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const res = await fetch(`${API_CONFIG.BACKEND_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    this.setAuth(data.access_token, data.user);
    return data;
  },

  async register(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  },

  async getProfile() {
    return this.request('/auth/profile');
  },

  async getStations() {
    return this.request('/stations');
  },

  // Trains
  async searchTrains(source, destination, date, travelClass = '', quota = 'GENERAL') {
    let q = `?source=${encodeURIComponent(source)}&destination=${encodeURIComponent(destination)}&journey_date=${encodeURIComponent(date)}&quota=${encodeURIComponent(quota)}`;
    if (travelClass) q += `&travel_class=${encodeURIComponent(travelClass)}`;
    return this.request(`/trains/search${q}`);
  },

  async getTrainDetails(trainNumber) {
    return this.request(`/trains/${encodeURIComponent(trainNumber)}`);
  },

  async getSeatAvailability(trainNumber, date) {
    return this.request(`/trains/availability/${encodeURIComponent(trainNumber)}?journey_date=${encodeURIComponent(date)}`);
  },

  // Bookings
  async createBooking(bookingData) {
    return this.request('/bookings', {
      method: 'POST',
      body: JSON.stringify(bookingData)
    });
  },

  async getBooking(pnr) {
    return this.request(`/bookings/${encodeURIComponent(pnr)}`);
  },

  async cancelBooking(pnr, reason = '') {
    return this.request(`/bookings/${encodeURIComponent(pnr)}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });
  },

  async getMyBookings() {
    return this.request('/bookings');
  },

  async pnrEnquiry(pnr) {
    return this.request(`/pnr/${encodeURIComponent(pnr)}`);
  },

  // Waitlist
  async getWaitlist(trainId, coachId, date) {
    return this.request(`/waitlist?train_id=${trainId}&coach_id=${coachId}&journey_date=${date}`);
  },

  // Telemetry
  async getTelemetry() {
    return this.request('/telemetry');
  },

  // Admin
  async getAdminMetrics() {
    return this.request('/admin/metrics');
  },

  async getAdminUsers() {
    return this.request('/admin/users');
  },

  // AI Services
  async predictWaitlist(payload) {
    return this.request('/waitlist-prediction', {
      method: 'POST',
      body: JSON.stringify(payload)
    }, true);
  },

  async getTrainRecommendations(payload) {
    return this.request('/train-recommendations', {
      method: 'POST',
      body: JSON.stringify(payload)
    }, true);
  },

  async getSeatRecommendations(payload) {
    return this.request('/seat-recommendations', {
      method: 'POST',
      body: JSON.stringify(payload)
    }, true);
  },

  async getAIModelMetrics() {
    return this.request('/model-metrics', {}, true);
  }
};
