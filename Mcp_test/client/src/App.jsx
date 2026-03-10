import { useState } from 'react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';

function App() {
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [days, setDays] = useState('3');
  const [preferences, setPreferences] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('请输入您的行程需求');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/api/plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          location: location.trim() || undefined,
          days: days ? parseInt(days) : undefined,
          preferences: preferences.trim() || undefined,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || data.message || '请求失败');
      }

      setResult(data);
    } catch (err) {
      setError(err.message || '行程规划失败，请稍后重试');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setQuery('');
    setLocation('');
    setDays('3');
    setPreferences('');
    setResult(null);
    setError(null);
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🗺️ 智能行程规划助手</h1>
        <p className="subtitle">基于 Langchain + MCP 的 AI 行程规划工具</p>
      </header>

      <main className="main">
        <div className="container">
          <form onSubmit={handleSubmit} className="form">
            <div className="form-group">
              <label htmlFor="query">
                <span className="label-text">行程需求 *</span>
                <span className="label-hint">描述您想去的地方和想做的事情</span>
              </label>
              <textarea
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="例如：想去北京玩，喜欢历史文化和美食，想要一个轻松的行程..."
                rows={4}
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="location">目的地</label>
                <input
                  id="location"
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="例如：北京"
                />
              </div>

              <div className="form-group">
                <label htmlFor="days">天数</label>
                <select
                  id="days"
                  value={days}
                  onChange={(e) => setDays(e.target.value)}
                >
                  <option value="1">1天</option>
                  <option value="2">2天</option>
                  <option value="3">3天</option>
                  <option value="4">4天</option>
                  <option value="5">5天</option>
                  <option value="7">7天</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="preferences">
                <span className="label-text">偏好</span>
                <span className="label-hint">例如：美食、购物、历史、自然风光等</span>
              </label>
              <input
                id="preferences"
                type="text"
                value={preferences}
                onChange={(e) => setPreferences(e.target.value)}
                placeholder="美食、购物、历史..."
              />
            </div>

            <div className="form-actions">
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="btn btn-primary"
              >
                {loading ? '规划中...' : '开始规划行程'}
              </button>
              {result && (
                <button
                  type="button"
                  onClick={handleReset}
                  className="btn btn-secondary"
                >
                  重新规划
                </button>
              )}
            </div>
          </form>

          {error && (
            <div className="error-box">
              <h3>❌ 错误</h3>
              <p>{error}</p>
            </div>
          )}

          {result && (
            <div className="result-box">
              <div className="result-header">
                <h2>📋 您的行程规划</h2>
                {result.toolCalls && result.toolCalls.length > 0 && (
                  <div className="tool-calls">
                    <span className="tool-calls-label">使用了 {result.toolCalls.length} 个工具</span>
                  </div>
                )}
              </div>
              <div className="result-content">
                {typeof result.plan === 'string' ? (
                  <div className="plan-text">{result.plan}</div>
                ) : (
                  <pre className="plan-json">{JSON.stringify(result.plan, null, 2)}</pre>
                )}
              </div>
            </div>
          )}

          {loading && (
            <div className="loading-box">
              <div className="spinner"></div>
              <p>AI 正在为您规划行程，请稍候...</p>
              <p className="loading-hint">正在调用高德地图和小红书 MCP 工具</p>
            </div>
          )}
        </div>
      </main>

      <footer className="footer">
        <p>
          <strong>技术栈：</strong>
          Langchain 1.0 · MCP Protocol · 高德地图 · 小红书
        </p>
        <p className="footer-hint">
          本项目用于演示如何通过 LLM 调用 MCP 工具
        </p>
      </footer>
    </div>
  );
}

export default App;
