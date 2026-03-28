import { useCallback, useEffect, useRef, useState } from 'react'
import './App.css'

const API = 'http://localhost:8000'

const LABEL = {
  F_Breakage: 'Front Breakage',
  F_Crushed:  'Front Crushed',
  F_Normal:   'Front Normal',
  R_Breakage: 'Rear Breakage',
  R_Crushed:  'Rear Crushed',
  R_Normal:   'Rear Normal',
}

/* ── Inline SVG icons (no emojis) ── */
const IconUpload = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="22" height="22">
    <polyline points="16 16 12 12 8 16"/>
    <line x1="12" y1="12" x2="12" y2="21"/>
    <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
  </svg>
)

const IconImage = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <rect x="3" y="3" width="18" height="18" rx="2"/>
    <circle cx="8.5" cy="8.5" r="1.5"/>
    <polyline points="21 15 16 10 5 21"/>
  </svg>
)

const IconExpand = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="15" height="15">
    <polyline points="15 3 21 3 21 9"/>
    <polyline points="9 21 3 21 3 15"/>
    <line x1="21" y1="3" x2="14" y2="10"/>
    <line x1="3" y1="21" x2="10" y2="14"/>
  </svg>
)

const IconChart = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="15" height="15">
    <line x1="18" y1="20" x2="18" y2="10"/>
    <line x1="12" y1="20" x2="12" y2="4"/>
    <line x1="6"  y1="20" x2="6"  y2="14"/>
  </svg>
)

const IconPDF = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/>
    <line x1="16" y1="17" x2="8" y2="17"/>
    <polyline points="10 9 9 9 8 9"/>
  </svg>
)

const IconShare = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <circle cx="18" cy="5"  r="3"/>
    <circle cx="6"  cy="12" r="3"/>
    <circle cx="18" cy="19" r="3"/>
    <line x1="8.59"  y1="13.51" x2="15.42" y2="17.49"/>
    <line x1="15.41" y1="6.51"  x2="8.59"  y2="10.49"/>
  </svg>
)

const IconArrow = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
    <polyline points="9 18 15 12 9 6"/>
  </svg>
)

const IconBolt = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" width="15" height="15">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
  </svg>
)

const IconClose = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" width="14" height="14">
    <line x1="18" y1="6" x2="6" y2="18"/>
    <line x1="6"  y1="6" x2="18" y2="18"/>
  </svg>
)

const IconCar = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" width="40" height="40">
    <path d="M5 17H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h11l4 4h3a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2h-1"/>
    <circle cx="7"  cy="17" r="2"/>
    <circle cx="17" cy="17" r="2"/>
  </svg>
)

const IconChevron = ({ open }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" width="12" height="12"
    style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
    <polyline points="6 9 12 15 18 9"/>
  </svg>
)

/* ─────────────────── Component ─────────────────── */
export default function App() {
  const [file, setFile]           = useState(null)
  const [preview, setPreview]     = useState(null)
  const [dragging, setDragging]   = useState(false)
  const [loading, setLoading]     = useState(false)
  const [result, setResult]       = useState(null)
  const [error, setError]         = useState(null)
  const [showProbs, setShowProbs] = useState(false)
  const [stats, setStats]         = useState({ total_scans: '—', ai_accuracy: '—', system_status: '—' })
  const [procTime, setProcTime]   = useState(null)
  const [toast, setToast]         = useState(null)
  const inputRef = useRef()

  useEffect(() => {
    fetch(`${API}/stats`).then(r => r.json()).then(setStats).catch(() => {})
  }, [])

  const handleFile = useCallback((f) => {
    if (!f) return
    if (!['image/jpeg','image/jpg','image/png','image/webp'].includes(f.type)) {
      setError('Please upload a JPG, PNG, or WebP image.')
      return
    }
    setFile(f); setPreview(URL.createObjectURL(f))
    setResult(null); setError(null); setShowProbs(false)
  }, [])

  const onDrop = (e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files?.[0]) }

  const removeFile = () => {
    setFile(null); setPreview(null); setResult(null)
    setError(null); setProcTime(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const predict = async () => {
    if (!file) return
    setLoading(true); setError(null); setResult(null); setShowProbs(false)
    const body = new FormData()
    body.append('file', file)
    try {
      const res = await fetch(`${API}/predict`, { method: 'POST', body })
      if (!res.ok) { const d = await res.json().catch(()=>({})); throw new Error(d.detail||`Error ${res.status}`) }
      const data = await res.json()
      setResult(data); setProcTime(data.process_time_s)
      fetch(`${API}/stats`).then(r=>r.json()).then(setStats).catch(()=>{})
    } catch (e) {
      setError(e.message || 'Cannot reach server. Is the backend running on port 8000?')
    } finally { setLoading(false) }
  }

  const downloadReport = () => {
    if (!result?.prediction_id) return
    window.open(`${API}/report/${result.prediction_id}`, '_blank')
  }

  const shareLink = async () => {
    if (!result?.prediction_id) return
    try {
      const res = await fetch(`${API}/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prediction_id: result.prediction_id }),
      })
      const data = await res.json()
      const link = `${API}/share/${data.share_id}`
      await navigator.clipboard.writeText(link)
      showToast('Link copied to clipboard')
    } catch { showToast('Could not generate link') }
  }

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(null), 3000) }

  const sortedProbs = result
    ? Object.entries(result.all_probabilities).sort((a,b)=>b[1]-a[1])
    : []

  const fmtScans = (n) => typeof n === 'number' ? n.toLocaleString() : n

  return (
    <>
      <div className="page">
        {/* ── Header ── */}
        <header className="site-header">
          <h1 className="site-title">Vehicle Damage Detection</h1>
        </header>

        {/* ── Upload zone ── */}
        <div
          className={`upload-box${dragging ? ' dragging' : ''}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <div className="upload-icon"><IconUpload /></div>
          <div className="upload-text">
            <strong>Drag and drop new file here</strong>
            <span>JPG, PNG, WebP · up to 10 MB</span>
          </div>
          <button className="browse-btn" onClick={(e)=>{e.stopPropagation();inputRef.current?.click()}}>
            Browse Files
          </button>
          <input ref={inputRef} type="file" accept="image/jpeg,image/jpg,image/png,image/webp"
            onChange={(e)=>handleFile(e.target.files?.[0])} />
        </div>

        {/* ── Image panel ── */}
        <div className="image-panel">
          <div className="image-panel-header">
            <span className="image-panel-label">
              <IconImage /> Uploaded Image
            </span>
            {preview && (
              <button className="expand-btn" title="Open full size"
                onClick={()=>window.open(preview,'_blank')}>
                <IconExpand />
              </button>
            )}
          </div>
          <div className="image-area">
            {preview
              ? <img src={preview} alt="uploaded car" />
              : <div className="image-placeholder">
                  <span className="ph-icon"><IconCar /></span>
                  <span>No image uploaded yet</span>
                </div>
            }
          </div>
        </div>

        {/* ── Predict button ── */}
        <div className="predict-row">
          <button className="predict-btn" onClick={predict} disabled={!file||loading}>
            <IconBolt />
            {loading ? 'Analysing…' : 'Run Detection'}
          </button>
          {file && !loading && (
            <button className="remove-file-btn" onClick={removeFile} title="Remove image">
              <IconClose />
            </button>
          )}
        </div>

        {/* ── Error ── */}
        {error && <div className="error-bar"><span>&#9888;</span><span>{error}</span></div>}

        {/* ── Loader ── */}
        {loading && (
          <div className="loader-overlay">
            <div className="spinner"/>
            <span>Running ResNet50 inference…</span>
          </div>
        )}

        {/* ── Diagnostic + Actions ── */}
        {result && !loading && (
          <div className="bottom-grid result-enter">
            {/* Diagnostic card */}
            <div className="diagnostic-card">
              <div className="diag-header">
                <IconChart />
                <span className="diag-title">Diagnostic Output</span>
              </div>
              <div className="diag-body">
                <div className="class-box">
                  <div className="class-label">Predicted Class</div>
                  <div className="class-value">
                    {(LABEL[result.predicted_class]||result.predicted_class).toUpperCase()}
                  </div>
                </div>
                <div className="conf-box">
                  <div className="conf-label">Confidence Score</div>
                  <div className="conf-value">{result.confidence.toFixed(1)}%</div>
                </div>
              </div>

              <div className="conf-bar-track">
                <div className="conf-bar-fill" style={{width:`${result.confidence}%`}}/>
              </div>

              {/* Probabilities toggle */}
              <div className="prob-section">
                <button className="prob-toggle" onClick={()=>setShowProbs(v=>!v)}>
                  <IconChevron open={showProbs} />
                  All class probabilities
                </button>
                {showProbs && (
                  <div className="prob-list">
                    {sortedProbs.map(([cls,pct])=>{
                      const isTop = cls === result.predicted_class
                      return (
                        <div className="prob-row" key={cls}>
                          <span className={`prob-name${isTop?' top':''}`}>{LABEL[cls]||cls}</span>
                          <div className="prob-bar-track">
                            <div className={`prob-bar-fill${isTop?' top':''}`}
                              style={{width:`${Math.max(pct,0.5)}%`}}/>
                          </div>
                          <span className={`prob-pct${isTop?' top':''}`}>{pct.toFixed(1)}%</span>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Action buttons — stretch to match diagnostic card height */}
            <div className="action-col">
              <button className="action-btn" onClick={downloadReport}>
                <span className="action-btn-icon"><IconPDF /></span>
                <span className="action-btn-text">
                  <span className="action-btn-title">Generate Detailed<br/>PDF Report</span>
                </span>
                <span className="action-btn-arrow"><IconArrow /></span>
              </button>

              <button className="action-btn" onClick={shareLink}>
                <span className="action-btn-icon"><IconShare /></span>
                <span className="action-btn-text">
                  <span className="action-btn-title">Share Diagnostic<br/>via Secure Link</span>
                </span>
                <span className="action-btn-arrow"><IconArrow /></span>
              </button>
            </div>
          </div>
        )}

        {/* ── Stats bar ── */}
        <div className="stats-bar">
          <div className="stat-cell">
            <div className="stat-label">Total Scans</div>
            <div className="stat-value">{fmtScans(stats.total_scans)}</div>
          </div>
          <div className="stat-cell">
            <div className="stat-label">AI Accuracy</div>
            <div className="stat-value">
              {typeof stats.ai_accuracy==='number' ? `${stats.ai_accuracy}%` : stats.ai_accuracy}
            </div>
          </div>
          <div className="stat-cell">
            <div className="stat-label">Process Time</div>
            <div className="stat-value">{procTime!=null ? `${procTime.toFixed(2)}s` : '—'}</div>
          </div>
          <div className="stat-cell">
            <div className="stat-label">System Status</div>
            <div className="stat-status">
              <span className="status-dot"/>
              <span className="stat-value">{stats.system_status}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Toast ── */}
      {toast && <div className="share-toast">{toast}</div>}
    </>
  )
}
