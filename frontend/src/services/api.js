import axios from 'axios';

/**
 * API Service
 * Handles all communication with the DeFAI Oracle backend
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for API key if needed
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('apiKey');
  if (apiKey) {
    config.headers.Authorization = `Bearer ${apiKey}`;
  }
  return config;
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('apiKey');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * Sentiment API Endpoints
 */
export const sentimentAPI = {
  /**
   * Get sentiment for a single token
   * @param {string} token - Token symbol
   * @returns {Promise} Sentiment data
   */
  getTokenSentiment: (token) => api.get(`/sentiment/${token}`),

  /**
   * Get sentiment for all tokens
   * @returns {Promise} Sentiment data for all tokens
   */
  getAllSentiments: () => api.get('/sentiment'),

  /**
   * Get sentiment history for a token
   * @param {string} token - Token symbol
   * @param {number} hours - Number of hours to look back
   * @returns {Promise} Historical sentiment data
   */
  getTokenHistory: (token, hours = 24) =>
    api.get(`/sentiment/${token}/history?hours=${hours}`),

  /**
   * Get sentiment trend for a token
   * @param {string} token - Token symbol
   * @param {number} hours - Time period for trend analysis
   * @returns {Promise} Trend analysis
   */
  getTokenTrend: (token, hours = 24) =>
    api.get(`/sentiment/${token}/trend?hours=${hours}`),

  /**
   * Get sentiment summary
   * @returns {Promise} Summary of all token sentiments
   */
  getSummary: () => api.get('/summary'),

  /**
   * Compare sentiment across multiple tokens
   * @param {string[]} tokens - List of token symbols
   * @returns {Promise} Comparison data
   */
  compareTokens: (tokens) => {
    const params = tokens.map(t => `tokens=${t}`).join('&');
    return api.get(`/compare?${params}`);
  },

  /**
   * Analyze specific tokens
   * @param {string[]} tokens - List of token symbols
   * @returns {Promise} Analysis results
   */
  analyzeTokens: (tokens) => api.post('/analyze', { tokens }),

  /**
   * Export sentiment history
   * @param {string} filepath - Path to save export
   * @returns {Promise} Export status
   */
  exportHistory: (filepath = 'sentiment_history.json') =>
    api.post(`/export/history?filepath=${filepath}`),
};

/**
 * Health & Info API Endpoints
 */
export const infoAPI = {
  /**
   * Get health status
   * @returns {Promise} Health check response
   */
  getHealth: () => api.get('/health'),

  /**
   * Get configured tokens
   * @returns {Promise} List of tokens
   */
  getTokens: () => api.get('/tokens'),

  /**
   * Get pipeline statistics
   * @returns {Promise} Pipeline stats
   */
  getStats: () => api.get('/stats'),
};

/**
 * WebSocket Service
 */
export const createWebSocketConnection = (onMessage, onError) => {
  const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/api/v1/ws/sentiment`;
  
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('WebSocket connected');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (err) {
      console.error('Error parsing WebSocket message:', err);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    if (onError) onError(error);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    // Attempt to reconnect after 3 seconds
    setTimeout(() => {
      createWebSocketConnection(onMessage, onError);
    }, 3000);
  };

  return ws;
};

export default api;
