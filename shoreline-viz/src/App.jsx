import { useState } from 'react'
import ChangeChart from './views/ChangeChart'
import TransectVisualizer from './views/TransectVisualizer'
import MapView from './map/MapView'
import 'maplibre-gl/dist/maplibre-gl.css'

const MONTHS = [
  { name: 'February', color: '#4e79a7' },
  { name: 'April', color: '#f28e2b' },
  { name: 'May', color: '#59a14f' },
  { name: 'June', color: '#e15759' },
  { name: 'July', color: '#76b7b2' },
  { name: 'August', color: '#edc948' },
  { name: 'December', color: '#b07aa1' },
]

const TABS = [
  { id: 'map', label: '🗺️ Map View' },
  { id: 'chart', label: '📊 Change Chart' },
  { id: 'transect', label: '📐 Transect' },
]

const TRANSECT_DATA = {
  'T.Mariyur Beach': { 'Feb-Apr': 2.76, 'Apr-May': 7.15, 'May-Jun': 0.68, 'Jun-Jul': 3.07, 'Jul-Aug': 12.60, 'Aug-Dec': 1.78, 'Feb-Dec': 4.79 },
  'Sayalkudi Beach': { 'Feb-Apr': 1.01, 'Apr-May': 0.69, 'May-Jun': 1.80, 'Jun-Jul': 0.64, 'Jul-Aug': 6.78, 'Aug-Dec': 6.39, 'Feb-Dec': 0.57 },
  'Keelvaipar Beach': { 'Feb-Apr': 1.19, 'Apr-May': 4.75, 'May-Jun': 0.90, 'Jun-Jul': 2.49, 'Jul-Aug': 3.28, 'Aug-Dec': 3.72, 'Feb-Dec': 6.62 },
  'Ervadi Beach': { 'Feb-Apr': null, 'Apr-May': 5.59, 'May-Jun': 3.75, 'Jun-Jul': 2.24, 'Jul-Aug': 1.81, 'Aug-Dec': 12.72, 'Feb-Dec': null },
}

export default function App() {
  const [show3D, setShow3D] = useState(false)
  const [activeTab, setActiveTab] = useState('map')
  const [visible, setVisible] = useState(
    Object.fromEntries(MONTHS.map(m => [m.name, true]))
  )
  const [beachPopup, setBeachPopup] = useState(null)

  const toggleMonth = (name) => {
    setVisible(prev => ({ ...prev, [name]: !prev[name] }))
  }

  const handleBeachClick = (name, x, y) => {
    setBeachPopup({ name, x, y })
  }

  return (
    <div className="flex w-screen h-screen" style={{ background: 'var(--bg-primary)' }}>

      {/* Sidebar */}
      <div className="w-56 shrink-0 flex flex-col py-4"
        style={{ background: 'var(--bg-secondary)', borderRight: '1px solid var(--border)' }}>

        {/* Title */}
        <div className="px-4 pb-4" style={{ borderBottom: '1px solid var(--border)' }}>
          <div className="font-bold text-sm tracking-widest" style={{ color: 'var(--accent-primary)' }}>
            SHORELINE VIZ
          </div>
          <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
            Tamil Nadu Coast · 2023
          </div>
        </div>

        {/* Tabs */}
        <div className="px-2 py-3 flex flex-col gap-1">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="px-3 py-2 rounded-md text-sm text-left transition-all"
              style={activeTab === tab.id ? {
                background: 'rgba(6,182,212,0.12)',
                border: '1px solid rgba(6,182,212,0.35)',
                color: 'var(--accent-primary)',
                fontWeight: 600,
              } : {
                border: '1px solid transparent',
                color: 'var(--text-primary)',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Month toggles */}
        {activeTab === 'map' && (
          <div className="px-4 pt-3 mt-2" style={{ borderTop: '1px solid var(--border)' }}>
            <div className="text-xs font-semibold tracking-widest mb-3"
              style={{ color: 'var(--text-secondary)' }}>
              MONTHS
            </div>
            {MONTHS.map(({ name, color }) => (
              <label key={name} className="flex items-center gap-2 cursor-pointer mb-2">
                <input
                  type="checkbox"
                  checked={visible[name]}
                  onChange={() => toggleMonth(name)}
                  className="accent-cyan-500"
                />
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: color }} />
                <span className="text-sm" style={{ color: 'var(--text-primary)' }}>{name}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Main content */}
      <div className="flex-1 relative overflow-hidden">

        {/* Map — always mounted */}
        <div className={`absolute inset-0 ${activeTab === 'map' ? 'block' : 'hidden'}`}>
          <MapView
            visible={visible}
            show3D={show3D}
            onBeachClick={handleBeachClick}
          />

          {/* Beach popup */}
          {beachPopup && (
            <div
              className="absolute rounded-lg px-4 py-3 min-w-[220px]"
              style={{
                left: beachPopup.x,
                top: beachPopup.y,
                transform: 'translate(-50%, -110%)',
                background: 'rgba(10,22,40,0.97)',
                border: '1px solid var(--border)',
              }}
            >
              <div className="flex justify-between items-center mb-3">
                <div className="font-bold" style={{ color: 'var(--accent-primary)' }}>
                  {beachPopup.name}
                </div>
                <button
                  onClick={() => setBeachPopup(null)}
                  className="text-xs ml-4 hover:text-white"
                  style={{ color: 'var(--text-secondary)' }}
                >✕</button>
              </div>

              <div className="text-xs font-semibold tracking-widest mb-2"
                style={{ color: 'var(--text-secondary)' }}>
                CHANGE (m)
              </div>

              {['Feb-Apr', 'Apr-May', 'May-Jun', 'Jun-Jul', 'Jul-Aug', 'Aug-Dec'].map(period => {
                const val = TRANSECT_DATA[beachPopup.name]?.[period]
                return (
                  <div key={period} className="flex justify-between items-center py-0.5">
                    <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{period}</span>
                    <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {val != null ? `${val}m` : '—'}
                    </span>
                  </div>
                )
              })}

              <div className="flex justify-between mt-2 pt-2"
                style={{ borderTop: '1px solid var(--border)' }}>
                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Feb-Dec Total</span>
                <span className="text-xs font-bold" style={{ color: 'var(--accent-secondary)' }}>
                  {TRANSECT_DATA[beachPopup.name]?.['Feb-Dec'] != null
                    ? `${TRANSECT_DATA[beachPopup.name]['Feb-Dec']}m`
                    : '—'}
                </span>
              </div>
            </div>
          )}

          {/* 3D Toggle */}
          <button
            onClick={() => setShow3D(p => !p)}
            className="absolute bottom-6 right-6 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
            style={show3D ? {
              background: 'var(--accent-primary)',
              color: 'var(--bg-primary)',
            } : {
              background: 'rgba(15,32,64,0.9)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
            }}
          >
            {show3D ? '3D On' : '3D Off'}
          </button>
        </div>

        {activeTab === 'chart' && <ChangeChart />}
        {activeTab === 'transect' && <TransectVisualizer />}
      </div>
    </div>
  )
}