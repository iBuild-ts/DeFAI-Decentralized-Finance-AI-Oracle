import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Zap, AlertCircle } from 'lucide-react';
import SentimentCard from '../components/SentimentCard';
import TokenComparison from '../components/TokenComparison';
import api from '../services/api';

/**
 * Main Dashboard Component
 * Displays real-time sentiment analysis for multiple tokens
 */
export default function Dashboard() {
  const [sentiments, setSentiments] = useState({});
  const [history, setHistory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState('24h');

  // Fetch initial data
  useEffect(() => {
    fetchSentiments();
    const interval = setInterval(fetchSentiments, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  // Fetch sentiment data
  const fetchSentiments = async () => {
    try {
      const response = await api.get('/sentiment');
      setSentiments(response.data.data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  // Fetch historical data
  useEffect(() => {
    fetchHistory();
  }, [selectedTimeframe]);

  const fetchHistory = async () => {
    try {
      const hours = selectedTimeframe === '24h' ? 24 : selectedTimeframe === '7d' ? 168 : 720;
      const response = await api.get(`/sentiment/DOGE/history?hours=${hours}`);
      
      // Format data for chart
      const chartData = response.data.data.map(item => ({
        timestamp: new Date(item.timestamp).toLocaleTimeString(),
        score: item.sentiment_score,
      }));
      
      setHistory(chartData);
    } catch (err) {
      console.error('Error fetching history:', err);
    }
  };

  // Get sentiment color
  const getSentimentColor = (label) => {
    switch (label) {
      case 'bullish':
        return 'text-green-600';
      case 'bearish':
        return 'text-red-600';
      default:
        return 'text-yellow-600';
    }
  };

  // Get sentiment background color
  const getSentimentBgColor = (label) => {
    switch (label) {
      case 'bullish':
        return 'bg-green-50 border-green-200';
      case 'bearish':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-yellow-50 border-yellow-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-900 to-slate-800">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading sentiment data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-white">DeFAI Oracle</h1>
              <p className="text-slate-400 text-sm">Real-time Sentiment Analysis for Base Memecoins</p>
            </div>
            <div className="text-right">
              <p className="text-slate-400 text-sm">Last updated: {new Date().toLocaleTimeString()}</p>
              <p className="text-green-400 text-sm">● Live</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="text-red-600" size={20} />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Sentiment Overview */}
        <section className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">Sentiment Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(sentiments).map(([token, data]) => (
              <SentimentCard
                key={token}
                token={token}
                sentiment={data}
              />
            ))}
          </div>
        </section>

        {/* Sentiment Trends */}
        <section className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-white">Sentiment Trends</h2>
            <div className="flex gap-2">
              {['24h', '7d', '30d'].map(tf => (
                <button
                  key={tf}
                  onClick={() => setSelectedTimeframe(tf)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedTimeframe === tf
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>
          
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="timestamp" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#3b82f6" 
                  dot={false}
                  strokeWidth={2}
                  name="Sentiment Score"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Token Comparison */}
        <section className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">Token Comparison</h2>
          <TokenComparison sentiments={sentiments} />
        </section>

        {/* Recent Alerts */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-4">Recent Alerts</h2>
          <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
            {alerts.length === 0 ? (
              <div className="p-6 text-center text-slate-400">
                <p>No alerts at this time</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-700">
                {alerts.map((alert, idx) => (
                  <div key={idx} className="p-4 hover:bg-slate-700 transition-colors">
                    <p className="text-white">{alert.message}</p>
                    <p className="text-slate-400 text-sm">{alert.timestamp}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
