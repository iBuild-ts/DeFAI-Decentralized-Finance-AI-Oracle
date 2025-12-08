import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

/**
 * TokenComparison Component
 * Displays comparison of sentiment across multiple tokens
 */
export default function TokenComparison({ sentiments }) {
  // Prepare data for chart
  const chartData = Object.entries(sentiments).map(([token, data]) => ({
    token,
    score: data.sentiment_score,
    confidence: data.confidence * 100,
    bullish: data.bullish_count,
    bearish: data.bearish_count,
  }));

  // Find best and worst
  const best = chartData.reduce((prev, current) =>
    prev.score > current.score ? prev : current
  );
  const worst = chartData.reduce((prev, current) =>
    prev.score < current.score ? prev : current
  );

  return (
    <div className="space-y-6">
      {/* Chart */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
            <XAxis dataKey="token" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
              labelStyle={{ color: '#f1f5f9' }}
            />
            <Legend />
            <Bar dataKey="score" fill="#3b82f6" name="Sentiment Score" />
            <Bar dataKey="confidence" fill="#10b981" name="Confidence %" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Comparison Table */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-700 border-b border-slate-600">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold text-white">Token</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-white">Score</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-white">Sentiment</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-white">Confidence</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-white">Bullish</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-white">Bearish</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {chartData.map((row) => {
              const sentiment = sentiments[row.token];
              const isBest = row.token === best.token;
              const isWorst = row.token === worst.token;
              
              return (
                <tr
                  key={row.token}
                  className={`hover:bg-slate-700 transition-colors ${
                    isBest ? 'bg-green-900 bg-opacity-20' : isWorst ? 'bg-red-900 bg-opacity-20' : ''
                  }`}
                >
                  <td className="px-6 py-4 text-sm font-medium text-white">{row.token}</td>
                  <td className="px-6 py-4 text-sm text-white">
                    <span className="font-bold">{row.score.toFixed(1)}</span>
                    <span className="text-slate-400">/100</span>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        sentiment.sentiment_label === 'bullish'
                          ? 'bg-green-900 text-green-200'
                          : sentiment.sentiment_label === 'bearish'
                          ? 'bg-red-900 text-red-200'
                          : 'bg-yellow-900 text-yellow-200'
                      }`}
                    >
                      {sentiment.sentiment_label.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-white">
                    {(sentiment.confidence * 100).toFixed(0)}%
                  </td>
                  <td className="px-6 py-4 text-sm text-green-400 font-medium">
                    {row.bullish}
                  </td>
                  <td className="px-6 py-4 text-sm text-red-400 font-medium">
                    {row.bearish}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Best/Worst Summary */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-green-900 bg-opacity-20 border border-green-700 rounded-lg p-4">
          <p className="text-green-200 text-sm font-medium mb-2">Best Sentiment</p>
          <p className="text-white text-2xl font-bold">{best.token}</p>
          <p className="text-green-300 text-sm mt-1">{best.score.toFixed(1)}/100</p>
        </div>
        <div className="bg-red-900 bg-opacity-20 border border-red-700 rounded-lg p-4">
          <p className="text-red-200 text-sm font-medium mb-2">Worst Sentiment</p>
          <p className="text-white text-2xl font-bold">{worst.token}</p>
          <p className="text-red-300 text-sm mt-1">{worst.score.toFixed(1)}/100</p>
        </div>
      </div>
    </div>
  );
}
