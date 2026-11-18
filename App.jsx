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
  Info,
  FolderOpen,
  HardDrive,
  Image as ImageIcon,
  Palette
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const PRESET_PROMPTS = [
  { label: '🗡️ Rusty Sword with Sapphire', prompt: 'A rusty medieval broadsword with a glowing blue sapphire in the hilt.' },
  { label: '🚀 Sci-Fi Spaceship', prompt: 'futuristic starfighter spaceship with swept wings and twin engines' },
  { label: '🪑 Low-Poly Chair', prompt: 'a minimalist modern wooden armchair' },
  { label: '🏎️ Flying Car', prompt: 'a sleek cyberpunk hovercar with aerofoil spoilers' },
  { label: '🌲 Pine Tree', prompt: 'a stylized low-poly pine tree with tiered foliage' },
  { label: '☕ Coffee Mug', prompt: 'a ceramic coffee mug with round handle' },
  { label: '🛡️ Battle Shield', prompt: 'an ornate medieval heater shield with central boss' },
  { label: '💎 Diamond Gem', prompt: 'a brilliant-cut faceted crystal gemstone' },
  { label: '🏡 Cottage House', prompt: 'a cozy low-poly house with pitched gable roof and chimney' },
];

export default function App() {
  const [prompt, setPrompt] = useState('A rusty medieval broadsword with a glowing blue sapphire in the hilt.');
  const [style, setStyle] = useState('realistic');
  const [provider, setProvider] = useState('auto');
  const [pipelineMode, setPipelineMode] = useState('full_asset'); // 'full_asset' (Week 2) | 'mesh_only' (Week 1)
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
      if (pipelineMode === 'full_asset') {
        // Week 2: End-to-end Text-to-3D + UV Unwrapping + Texture Generation
        const res = await fetch(`${API_BASE}/api/generate-full-asset`, {
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

        const fullModelUrl = `${API_BASE}${data.final_asset.obj_url}`;
        const fullTextureUrl = `${API_BASE}${data.final_asset.texture_url}`;

        const modelEntry = {
          model_id: data.model_id,
          prompt: data.prompt,
          style,
          filename: data.final_asset.obj_filename,
          texture_filename: data.final_asset.texture_filename,
          full_model_url: fullModelUrl,
          full_texture_url: fullTextureUrl,
          download_url: `${API_BASE}${data.final_asset.obj_download_url}`,
          texture_download_url: `${API_BASE}${data.final_asset.texture_url}?download=true`,
          pipeline_stages: data.pipeline_stages,
          metadata: {
            vertex_count: data.pipeline_stages.mesh_processing.processed_vertices,
            face_count: data.pipeline_stages['3d_generation'].vertex_count,
            uv_count: data.pipeline_stages.mesh_processing.processed_uvs,
            provider: `${data.pipeline_stages['3d_generation'].provider} + ${data.pipeline_stages.texture_generation.provider}`,
            generation_time_ms: data.total_pipeline_time_ms,
            unwrapping_method: data.pipeline_stages.mesh_processing.unwrapping_method,
            texture_status: data.pipeline_stages.texture_generation.status_message,
          }
        };

        setCurrentModel(modelEntry);
      } else {
        // Week 1: 3D Mesh Only
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

        const fullModelUrl = data.model_url.startsWith('http')
          ? data.model_url
          : `${API_BASE}${data.model_url}`;

        const modelEntry = {
          ...data,
          full_model_url: fullModelUrl,
          full_texture_url: null,
          download_url: `${API_BASE}${data.download_url}`,
        };

        setCurrentModel(modelEntry);
      }

      setLiveStats(null);
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
      full_texture_url: null,
      download_url: `${API_BASE}${item.download_url}`,
      file_size: item.file_size,
      metadata: {
        provider: item.is_processed ? 'Week 2 (UV Unwrapped)' : 'Week 1 Mesh',
        generation_time_ms: 0,
      }
    });
  };

  const handlePresetClick = (preset) => {
    setPrompt(preset.prompt);
    setError(null);
  };

  const handleOpenOutputFolder = async () => {
    try {
      await fetch(`${API_BASE}/api/open-folder`, { method: 'POST' });
    } catch (err) {
      console.error('Failed to open output folder:', err);
    }
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
              <span className="brand-badge">Week 2: Textures & UVs</span>
            </div>
            <p className="brand-subtitle">AI-Powered Text-to-3D Model Generation Pipeline</p>
          </div>
        </div>

        <div className="header-status">
          <button
            type="button"
            className="header-folder-btn"
            onClick={handleOpenOutputFolder}
            title="Open Desktop outputs folder where 3D models and textures are saved"
          >
            <FolderOpen size={15} />
            <span>Open Outputs Folder</span>
          </button>
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
                  placeholder="Describe your 3D asset (e.g. 'A rusty medieval broadsword with a glowing blue sapphire in the hilt')..."
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

              {/* Pipeline Mode Selector */}
              <div className="pipeline-mode-selector">
                <span className="setting-label">Pipeline Mode:</span>
                <div className="mode-toggle-group">
                  <button
                    type="button"
                    className={`mode-btn ${pipelineMode === 'full_asset' ? 'active' : ''}`}
                    onClick={() => setPipelineMode('full_asset')}
                  >
                    <Palette size={14} />
                    <span>Full Textured Asset (Week 2)</span>
                  </button>
                  <button
                    type="button"
                    className={`mode-btn ${pipelineMode === 'mesh_only' ? 'active' : ''}`}
                    onClick={() => setPipelineMode('mesh_only')}
                  >
                    <Shapes size={14} />
                    <span>3D Mesh Only (Week 1)</span>
                  </button>
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
                    <option value="realistic">Realistic PBR</option>
                    <option value="low-poly">Low-Poly</option>
                    <option value="stylized">Stylized</option>
                  </select>
                </div>

                <div className="setting-field">
                  <label>3D Engine</label>
                  <select 
                    value={provider} 
                    onChange={(e) => setProvider(e.target.value)}
                    disabled={isGenerating}
                  >
                    <option value="auto">Auto (Procedural + AI)</option>
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
                    <span>
                      {pipelineMode === 'full_asset'
                        ? 'Synthesizing Mesh, UVs & Texture...'
                        : 'Synthesizing 3D Geometry...'}
                    </span>
                  </>
                ) : (
                  <>
                    <Wand2 size={18} />
                    <span>
                      {pipelineMode === 'full_asset'
                        ? 'Generate Textured 3D Asset'
                        : 'Generate 3D Model'}
                    </span>
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
                <h2>Asset Details & Manifest</h2>
              </div>

              {/* Texture Map Preview if available */}
              {currentModel.full_texture_url && (
                <div className="texture-preview-box">
                  <div className="texture-preview-header">
                    <span className="preview-label">Generated Texture Map:</span>
                    <a
                      href={currentModel.texture_download_url}
                      download={currentModel.texture_filename}
                      className="texture-download-link"
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Download size={13} />
                      <span>PNG</span>
                    </a>
                  </div>
                  <div className="texture-img-wrap">
                    <img 
                      src={currentModel.full_texture_url} 
                      alt="Generated Texture" 
                      className="texture-thumb"
                    />
                  </div>
                  {currentModel.metadata?.texture_status && (
                    <p className="texture-note">{currentModel.metadata.texture_status}</p>
                  )}
                </div>
              )}

              <div className="info-grid">
                <div className="info-stat">
                  <span className="stat-label">Vertices</span>
                  <span className="stat-val">
                    {liveStats?.vertexCount ?? currentModel.metadata?.vertex_count ?? '—'}
                  </span>
                </div>
                <div className="info-stat">
                  <span className="stat-label">UV Coordinates</span>
                  <span className="stat-val">
                    {currentModel.metadata?.uv_count ?? (currentModel.full_texture_url ? 'Atlas Unwrapped' : '—')}
                  </span>
                </div>
                <div className="info-stat">
                  <span className="stat-label">UV Unwrapper</span>
                  <span className="stat-val">
                    {currentModel.metadata?.unwrapping_method ? 'xatlas' : 'Standard'}
                  </span>
                </div>
                <div className="info-stat">
                  <span className="stat-label">Format</span>
                  <span className="stat-val">Wavefront OBJ + MTL</span>
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

              {/* Output File Location & Folder Button */}
              <div className="output-folder-box">
                <div className="output-location-text">
                  <HardDrive size={14} className="text-primary" />
                  <span>Saved on Desktop in: <code>outputs/</code></span>
                </div>
                <button
                  type="button"
                  className="folder-action-btn"
                  onClick={handleOpenOutputFolder}
                  title="Open the folder containing this 3D model in File Explorer"
                >
                  <FolderOpen size={14} />
                  <span>Open Outputs Folder</span>
                </button>
              </div>

              {/* Direct OBJ Download Button */}
              <div className="download-buttons-group">
                <a
                  href={currentModel.download_url}
                  download={currentModel.filename}
                  className="download-btn"
                  target="_blank"
                  rel="noreferrer"
                >
                  <Download size={16} />
                  <span>Download OBJ Mesh</span>
                </a>
                {currentModel.full_texture_url && (
                  <a
                    href={currentModel.texture_download_url}
                    download={currentModel.texture_filename}
                    className="download-btn secondary"
                    target="_blank"
                    rel="noreferrer"
                  >
                    <ImageIcon size={16} />
                    <span>Download Texture PNG</span>
                  </a>
                )}
              </div>
            </section>
          )}

          {/* Session History */}
          {history.length > 0 && (
            <section className="panel-card history-card">
              <div className="card-header">
                <History size={18} />
                <h2>Recent Assets</h2>
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
              <div className="header-actions-row">
                <a
                  href={currentModel.download_url}
                  download={currentModel.filename}
                  className="header-download-btn"
                  title="Download Wavefront OBJ"
                >
                  <Download size={14} />
                  <span>Export OBJ</span>
                </a>
              </div>
            )}
          </div>

          <div className="viewport-canvas-wrapper">
            <ModelViewer
              modelUrl={currentModel?.full_model_url}
              textureUrl={currentModel?.full_texture_url}
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
