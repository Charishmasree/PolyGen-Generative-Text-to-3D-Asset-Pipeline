import React, { useState, useEffect } from 'react';
import ModelViewer from './components/ModelViewer';
import { 
  Sparkles, 
  Download, 
  Layers, 
  Cpu, 
  Clock, 
  AlertCircle, 
  CheckCircle2, 
  History, 
  Send, 
  Wand2, 
  Shapes, 
  ExternalLink,
  ChevronRight,
  Info
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const PRESET_PROMPTS = [
  { label: 'Medieval Sword', prompt: 'a low-poly medieval broadsword with crossguard and wrapped hilt' },
  { label: 'Sci-Fi Spaceship', prompt: 'futuristic starfighter spaceship with swept wings and twin engines' },
  { label: 'Low-Poly Chair', prompt: 'a minimalist modern wooden armchair' },
  { label: 'Flying Car', prompt: 'a sleek cyberpunk hovercar with aerofoil spoilers' },
  { label: 'Pine Tree', prompt: 'a stylized low-poly pine tree with tiered foliage' },
  { label: 'Coffee Mug', prompt: 'a ceramic coffee mug with round handle' },
  { label: 'Battle Shield', prompt: 'an ornate medieval heater shield with central boss' },
  { label: 'Diamond Gem', prompt: 'a brilliant-cut faceted crystal gemstone' },
  { label: 'Cottage House', prompt: 'a cozy low-poly house with pitched gable roof and chimney' },
];

export default function App() {
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('low-poly');
  const [provider, setProvider] = useState('auto');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [currentModel, setCurrentModel] = useState(null);
  const [history, setHistory] = useState([]);
  const [backendStatus, setBackendStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [liveStats, setLiveStats] = useState(null);

  // Check backend health on mount
  useEffect(() => {
    fetchBackendHealth();
    fetchHistory();
  }, []);

  const fetchBackendHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        setBackendStatus('online');
      } else {
        setBackendStatus('offline');
      }
    } catch {
      setBackendStatus('offline');
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/history?limit=10`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data.models || []);
      }
    } catch {
      // Backend may not be running yet
    }
  };

  const handleGenerate = async (e) => {
    if (e) e.preventDefault();
    const cleanPrompt = prompt.trim();
    if (!cleanPrompt) {
      setError('Please enter a descriptive prompt first.');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: cleanPrompt,
          style,
          provider
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `Server error (${res.status})`);
      }

      // Prepend API base to model_url if relative
      const fullModelUrl = data.model_url.startsWith('http')
        ? data.model_url
        : `${API_BASE}${data.model_url}`;

      const modelEntry = {
        ...data,
        full_model_url: fullModelUrl,
        download_url: `${API_BASE}${data.download_url}`,
      };

      setCurrentModel(modelEntry);
      setLiveStats(null); // Reset until ModelViewer parses
      setBackendStatus('online');
      fetchHistory();
    } catch (err) {
      console.error('Generation failed:', err);
      setError(err.message || 'Failed to connect to backend server. Ensure FastAPI is running on port 8000.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelectHistoryItem = (item) => {
    const fullModelUrl = `${API_BASE}${item.model_url}`;
    setCurrentModel({
      model_id: item.model_id,
      prompt: item.filename.replace(/^polygen_/, '').replace(/_[a-f0-9]+\.obj$/, '').replace(/_/g, ' '),
      filename: item.filename,
      full_model_url: fullModelUrl,
      download_url: `${API_BASE}${item.download_url}`,
      file_size: item.file_size,
      metadata: {
        provider: 'cached',
        generation_time_ms: 0,
      }
    });
  };

  const handlePresetClick = (preset) => {
    setPrompt(preset.prompt);
    setError(null);
  };

  const handleModelLoaded = (stats) => {
    setLiveStats(stats);
  };

  const handleModelError = (errMsg) => {
    setError(errMsg);
  };

  return (
    <div className="polygen-app">
      {/* Top Navigation Bar */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-logo">
            <Shapes size={22} className="logo-icon" />
          </div>
          <div>
            <div className="brand-title-row">
              <h1 className="brand-title">PolyGen</h1>
              <span className="brand-badge">Week 1 MVP</span>
            </div>
            <p className="brand-subtitle">AI-Powered Text-to-3D Model Generation Pipeline</p>
          </div>
        </div>

        <div className="header-status">
          <div className={`status-pill ${backendStatus}`}>
            <span className="status-dot"></span>
            <span>
              {backendStatus === 'online' && 'FastAPI Connected (Port 8000)'}
              {backendStatus === 'offline' && 'Backend Offline (Run uvicorn)'}
              {backendStatus === 'checking' && 'Checking Connection...'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Studio Layout */}
      <main className="studio-layout">
        {/* Left Control Panel */}
        <aside className="control-sidebar">
          {/* Prompt Section */}
          <section className="panel-card">
            <div className="card-header">
              <Sparkles size={18} className="text-primary" />
              <h2>Text Prompt</h2>
            </div>

            <form onSubmit={handleGenerate} className="prompt-form">
              <div className="textarea-wrapper">
                <textarea
                  className="prompt-textarea"
                  rows={4}
                  placeholder="Describe any 3D object (e.g. 'a low-poly medieval broadsword', 'futuristic spaceship', 'wooden chair')..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  maxLength={500}
                  disabled={isGenerating}
                />
                <div className="char-count">{prompt.length} / 500</div>
              </div>

              {/* Quick Preset Prompts */}
              <div className="preset-container">
                <span className="preset-label">Suggested Prompts:</span>
                <div className="preset-chips">
                  {PRESET_PROMPTS.map((p, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className="preset-chip"
                      onClick={() => handlePresetClick(p)}
                      title={p.prompt}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Generation Settings */}
              <div className="settings-grid">
                <div className="setting-field">
                  <label>Art Style</label>
                  <select 
                    value={style} 
                    onChange={(e) => setStyle(e.target.value)}
                    disabled={isGenerating}
                  >
                    <option value="low-poly">Low-Poly</option>
                    <option value="realistic">Realistic</option>
                    <option value="stylized">Stylized</option>
                  </select>
                </div>

                <div className="setting-field">
                  <label>AI Provider</label>
                  <select 
                    value={provider} 
                    onChange={(e) => setProvider(e.target.value)}
                    disabled={isGenerating}
                  >
                    <option value="auto">Auto (Smart Local / Cloud)</option>
                    <option value="local">Local Procedural AI</option>
                    <option value="meshy">Meshy API (Cloud)</option>
                    <option value="tripo">Tripo3D API (Cloud)</option>
                  </select>
                </div>
              </div>

              {/* Generate Button */}
              <button
                type="submit"
                className={`generate-btn ${isGenerating ? 'loading' : ''}`}
                disabled={isGenerating || !prompt.trim()}
              >
                {isGenerating ? (
                  <>
                    <span className="btn-spinner"></span>
                    <span>Synthesizing 3D Model...</span>
                  </>
                ) : (
                  <>
                    <Wand2 size={18} />
                    <span>Generate 3D Model</span>
                  </>
                )}
              </button>
            </form>

            {/* Error Message Display */}
            {error && (
              <div className="error-banner">
                <AlertCircle size={18} />
                <div className="error-content">
                  <strong>Generation Error</strong>
                  <p>{error}</p>
                </div>
              </div>
            )}
          </section>

          {/* Active Model Metadata Card */}
          {currentModel && (
            <section className="panel-card model-info-card">
              <div className="card-header">
                <Layers size={18} className="text-secondary" />
                <h2>Generated Model Details</h2>
              </div>

              <div className="info-grid">
                <div className="info-stat">
                  <span className="stat-label">Vertices</span>
                  <span className="stat-val">
                    {liveStats?.vertexCount ?? currentModel.metadata?.vertex_count ?? '—'}
                  </span>
                </div>
                <div className="info-stat">
                  <span className="stat-label">Faces</span>
                  <span className="stat-val">
                    {liveStats?.faceCount ?? currentModel.metadata?.face_count ?? '—'}
                  </span>
                </div>
                <div className="info-stat">
                  <span className="stat-label">Dimensions</span>
                  <span className="stat-val">
                    {liveStats?.dimensions
                      ? `${liveStats.dimensions.width} × ${liveStats.dimensions.height} × ${liveStats.dimensions.depth}`
                      : 'Normalized'}
                  </span>
                </div>
                <div className="info-stat">
                  <span className="stat-label">File Format</span>
                  <span className="stat-val">Wavefront OBJ</span>
                </div>
              </div>

              <div className="model-meta-footer">
                <div className="meta-badge">
                  <Cpu size={14} />
                  <span>{currentModel.metadata?.provider || 'PolyGen Engine'}</span>
                </div>
                {currentModel.metadata?.generation_time_ms ? (
                  <div className="meta-badge">
                    <Clock size={14} />
                    <span>{currentModel.metadata.generation_time_ms} ms</span>
                  </div>
                ) : null}
              </div>

              {/* Direct OBJ Download Button */}
              <a
                href={currentModel.download_url}
                download={currentModel.filename}
                className="download-btn"
                target="_blank"
                rel="noreferrer"
              >
                <Download size={16} />
                <span>Download OBJ Model</span>
              </a>
            </section>
          )}

          {/* Session History */}
          {history.length > 0 && (
            <section className="panel-card history-card">
              <div className="card-header">
                <History size={18} />
                <h2>Recent Generations</h2>
              </div>
              <div className="history-list">
                {history.map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className={`history-item ${currentModel?.filename === item.filename ? 'active' : ''}`}
                    onClick={() => handleSelectHistoryItem(item)}
                  >
                    <span className="history-name">{item.filename}</span>
                    <ChevronRight size={14} className="history-arrow" />
                  </button>
                ))}
              </div>
            </section>
          )}
        </aside>

        {/* Right 3D Viewport Area */}
        <section className="viewer-viewport-pane">
          <div className="viewport-header">
            <div className="viewport-title-group">
              <h2 className="viewport-title">
                {currentModel ? currentModel.prompt : 'Interactive 3D Viewport'}
              </h2>
              {currentModel && (
                <span className="viewport-filename">{currentModel.filename}</span>
              )}
            </div>

            {currentModel && (
              <a
                href={currentModel.download_url}
                download={currentModel.filename}
                className="header-download-btn"
                title="Download Wavefront OBJ"
              >
                <Download size={14} />
                <span>Export OBJ</span>
              </a>
            )}
          </div>

          <div className="viewport-canvas-wrapper">
            <ModelViewer
              modelUrl={currentModel?.full_model_url}
              isLoading={isGenerating}
              onLoaded={handleModelLoaded}
              onError={handleModelError}
            />
          </div>
        </section>
      </main>
    </div>
  );
}

