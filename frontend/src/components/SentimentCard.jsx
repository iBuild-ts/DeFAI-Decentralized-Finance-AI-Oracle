import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

/**
 * SentimentCard Component
 * Displays sentiment information for a single token
 */
export default function SentimentCard({ token, sentiment }) {
  const {
    sentiment_label,
    sentiment_score,
    confidence,
    sample_size,
    bullish_count,
    neutral_count,
    bearish_count,
    trend,
    trend_strength,
    avg_likes,
    avg_retweets,
  } = sentiment;

  // Get colors based on sentiment
  const getColors = () => {
    switch (sentiment_label) {
      case 'bullish':
        return {
          bg: 'bg-green-50',
          border: 'border-green-200',
          text: 'text-green-700',
          badge: 'bg-green-100 text-green-800',
          score: 'text-green-600',
        };
      case 'bearish':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          text: 'text-red-700',
          badge: 'bg-red-100 text-red-800',
          score: 'text-red-600',
        };
      default:
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          text: 'text-yellow-700',
          badge: 'bg-yellow-100 text-yellow-800',
          score: 'text-yellow-600',
        };
    }
  };

  const colors = getColors();

  // Get trend icon
  const getTrendIcon = () => {
    switch (trend) {
      case 'rising':
        return <TrendingUp className="text-green-600" size={20} />;
      case 'falling':
        return <TrendingDown className="text-red-600" size={20} />;
      default:
        return <Minus className="text-yellow-600" size={20} />;
    }
  };

  return (
    <div className={`${colors.bg} ${colors.border} border rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow`}>
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-2xl font-bold text-gray-900">{token}</h3>
          <p className={`text-sm ${colors.text}`}>{sentiment_label.toUpperCase()}</p>
        </div>
        {getTrendIcon()}
      </div>

      {/* Sentiment Score */}
      <div className="mb-4">
        <div className="flex items-baseline gap-2 mb-2">
          <span className={`text-4xl font-bold ${colors.score}`}>
            {sentiment_score.toFixed(1)}
          </span>
          <span className="text-gray-600">/100</span>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              sentiment_label === 'bullish'
                ? 'bg-green-600'
                : sentiment_label === 'bearish'
                ? 'bg-red-600'
                : 'bg-yellow-600'
            }`}
            style={{ width: `${sentiment_score}%` }}
          />
        </div>
      </div>

      {/* Confidence & Trend */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-600 uppercase tracking-wide">Confidence</p>
          <p className="text-lg font-semibold text-gray-900">{(confidence * 100).toFixed(0)}%</p>
        </div>
        <div>
          <p className="text-xs text-gray-600 uppercase tracking-wide">Trend</p>
          <p className="text-lg font-semibold text-gray-900">{trend}</p>
        </div>
      </div>

      {/* Sentiment Distribution */}
      <div className="mb-4">
        <p className="text-xs text-gray-600 uppercase tracking-wide mb-2">Distribution</p>
        <div className="flex gap-2">
          <div className="flex-1">
            <div className="bg-green-200 rounded h-2 mb-1"></div>
            <p className="text-xs text-gray-600 text-center">{bullish_count}</p>
          </div>
          <div className="flex-1">
            <div className="bg-yellow-200 rounded h-2 mb-1"></div>
            <p className="text-xs text-gray-600 text-center">{neutral_count}</p>
          </div>
          <div className="flex-1">
            <div className="bg-red-200 rounded h-2 mb-1"></div>
            <p className="text-xs text-gray-600 text-center">{bearish_count}</p>
          </div>
        </div>
      </div>

      {/* Engagement Metrics */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
        <div>
          <p className="text-xs text-gray-600 uppercase tracking-wide">Avg Likes</p>
          <p className="text-lg font-semibold text-gray-900">{avg_likes.toFixed(0)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600 uppercase tracking-wide">Avg Retweets</p>
          <p className="text-lg font-semibold text-gray-900">{avg_retweets.toFixed(0)}</p>
        </div>
      </div>

      {/* Sample Size */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-600">Based on {sample_size} posts analyzed</p>
      </div>
    </div>
  );
}
