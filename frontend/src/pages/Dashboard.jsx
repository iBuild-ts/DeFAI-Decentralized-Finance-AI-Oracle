import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './Dashboard.css';
import api from '../services/api';

/**
 * Modern Dashboard Component
 * Displays real-time sentiment analysis with sleek UI
 */
export default function Dashboard() {
  const [sentiments, setSentiments] = useState({});
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch tokens and sentiment data
  useEffect(() => {
    fetchTokens();
    fetchSentiments();
    const interval = setInterval(fetchSentiments, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchTokens = async () => {
    try {
      const response = await api.get('/tokens');
      if (response.data.tokens) {
        setTokens(response.data.tokens);
      } else if (response.data.data && response.data.data.tokens) {
        setTokens(response.data.data.tokens);
      }
    } catch (err) {
      console.error('Error fetching tokens:', err);
    }
  };

  const fetchSentiments = async () => {
    try {
      const response = await api.get('/sentiment');
      setSentiments(response.data.data || {});
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const getSentimentColor = (label) => {
    if (label === 'bullish') return '#10b981';
    if (label === 'bearish') return '#ef4444';
    return '#eab308';
  };

  const getSentimentClass = (label) => {
    if (label === 'bullish') return 'bullish';
    if (label === 'bearish') return 'bearish';
    return 'neutral';
  };

  const chartData = Object.entries(sentiments).map(([token, data]) => ({
    token,
    score: data.sentiment_score,
    confidence: data.confidence * 100,
    bullish: data.bullish_count,
    bearish: data.bearish_count,
  }));

  if (loading && Object.keys(sentiments).length === 0) {
    return (
      <div className="dashboard">
        <div className="dashboard-container">
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading sentiment data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && Object.keys(sentiments).length === 0) {
    return (
      <div className="dashboard">
        <div className="dashboard-container">
          <div className="error-container">
            <p>Error loading data: {error}</p>
            <p style={{ fontSize: '12px', marginTop: '10px', color: 'rgba(148, 163, 184, 0.7)' }}>
              Retrying...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <div>
              <div className="logo">DeFAI Oracle</div>
              <div className="logo-subtitle">Real-time Sentiment Analysis</div>
            </div>
          </div>
          <div className="header-right">
            <div className="status-indicator">
              <div className="status-dot"></div>
              Live
            </div>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="dashboard-container">
        {/* Sentiment Cards Grid */}
        <div className="sentiment-grid">
          {Object.entries(sentiments).map(([token, data]) => (
            <div key={token} className="sentiment-card">
              <div className="card-header">
                <div className="token-name">{token}</div>
                <div className={`sentiment-badge ${getSentimentClass(data.sentiment_label)}`}>
                  {data.sentiment_label}
                </div>
              </div>
              <div className="card-body">
                <div className="score-display">
                  <div className="score-number">{data.sentiment_score.toFixed(0)}</div>
                  <div className="score-label">/100</div>
                </div>
                <div className="card-stats">
                  <div className="stat-item">
                    <div className="stat-label">Bullish</div>
                    <div className="stat-value" style={{ color: '#10b981' }}>
                      {data.bullish_count}
                    </div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-label">Neutral</div>
                    <div className="stat-value" style={{ color: '#eab308' }}>
                      {data.neutral_count || 0}
                    </div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-label">Bearish</div>
                    <div className="stat-value" style={{ color: '#ef4444' }}>
                      {data.bearish_count}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Charts Section */}
        <div className="charts-section">
          <div className="chart-card">
            <div className="chart-title">Sentiment Comparison</div>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                  <XAxis dataKey="token" stroke="rgba(148, 163, 184, 0.6)" />
                  <YAxis stroke="rgba(148, 163, 184, 0.6)" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(15, 23, 42, 0.9)',
                      border: '1px solid rgba(148, 163, 184, 0.2)',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Legend />
                  <Bar dataKey="score" fill="#3b82f6" name="Sentiment Score" />
                  <Bar dataKey="confidence" fill="#8b5cf6" name="Confidence %" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(148, 163, 184, 0.6)' }}>
                No data available
              </div>
            )}
          </div>

          <div className="chart-card">
            <div className="chart-title">Sentiment Distribution</div>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                  <XAxis dataKey="token" stroke="rgba(148, 163, 184, 0.6)" />
                  <YAxis stroke="rgba(148, 163, 184, 0.6)" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(15, 23, 42, 0.9)',
                      border: '1px solid rgba(148, 163, 184, 0.2)',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Legend />
                  <Bar dataKey="bullish" fill="#10b981" name="Bullish" />
                  <Bar dataKey="bearish" fill="#ef4444" name="Bearish" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(148, 163, 184, 0.6)' }}>
                No data available
              </div>
            )}
          </div>
        </div>

        {/* Comparison Table */}
        <div className="table-section">
          <div className="table-title">Token Analysis</div>
          {chartData.length > 0 ? (
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Token</th>
                  <th>Score</th>
                  <th>Sentiment</th>
                  <th>Confidence</th>
                  <th>Bullish</th>
                  <th>Bearish</th>
                </tr>
              </thead>
              <tbody>
                {chartData.map((row) => {
                  const sentiment = sentiments[row.token];
                  return (
                    <tr key={row.token}>
                      <td className="token-cell">{row.token}</td>
                      <td><strong>{row.score.toFixed(1)}</strong>/100</td>
                      <td>
                        <span className={`sentiment-badge ${getSentimentClass(sentiment.sentiment_label)}`}>
                          {sentiment.sentiment_label}
                        </span>
                      </td>
                      <td>{row.confidence.toFixed(0)}%</td>
                      <td className="bullish-count">{row.bullish}</td>
                      <td className="bearish-count">{row.bearish}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: '24px', textAlign: 'center', color: 'rgba(148, 163, 184, 0.6)' }}>
              No sentiment data available yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
