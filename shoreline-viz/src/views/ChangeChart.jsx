import { useState } from 'react'
import {
    ComposedChart, Bar, Line, XAxis, YAxis,
    CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const APP_DATA = {
    transectChanges: {
        'T.Mariyur Beach': { 'Feb-Apr': 2.76, 'Apr-May': 7.15, 'May-Jun': 0.68, 'Jun-Jul': 3.07, 'Jul-Aug': 12.60, 'Aug-Dec': 1.78 },
        'Sayalkudi Beach': { 'Feb-Apr': 1.01, 'Apr-May': 0.69, 'May-Jun': 1.80, 'Jun-Jul': 0.64, 'Jul-Aug': 6.78, 'Aug-Dec': 6.39 },
        'Keelvaipar Beach': { 'Feb-Apr': 1.19, 'Apr-May': 4.75, 'May-Jun': 0.90, 'Jun-Jul': 2.49, 'Jul-Aug': 3.28, 'Aug-Dec': 3.72 },
        'Ervadi Beach': { 'Feb-Apr': null, 'Apr-May': 5.59, 'May-Jun': 3.75, 'Jun-Jul': 2.24, 'Jul-Aug': 1.81, 'Aug-Dec': 12.72 },
    },
    tidalData: {
        'February': { MTL: 0.525 },
        'April': { MTL: 0.500 },
        'May': { MTL: 0.575 },
        'June': { MTL: 0.525 },
        'July': { MTL: 0.475 },
        'August': { MTL: 0.550 },
        'December': { MTL: 0.725 },
    },
    referenceMTL: 0.554,
}

const BEACHES = ['T.Mariyur Beach', 'Sayalkudi Beach', 'Keelvaipar Beach', 'Ervadi Beach']
const PERIODS = ['Feb-Apr', 'Apr-May', 'May-Jun', 'Jun-Jul', 'Jul-Aug', 'Aug-Dec']

// map each period to the ending month's MTL
const PERIOD_MTL = {
    'Feb-Apr': APP_DATA.tidalData['April'].MTL,
    'Apr-May': APP_DATA.tidalData['May'].MTL,
    'May-Jun': APP_DATA.tidalData['June'].MTL,
    'Jun-Jul': APP_DATA.tidalData['July'].MTL,
    'Jul-Aug': APP_DATA.tidalData['August'].MTL,
    'Aug-Dec': APP_DATA.tidalData['December'].MTL,
}

const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
        <div className="rounded-lg px-3 py-2 text-xs"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <div className="font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>{label}</div>
            {payload.map((p, i) => (
                <div key={i} style={{ color: p.color }} className="flex gap-2">
                    <span>{p.name}:</span>
                    <span className="font-bold">{p.value != null ? p.value.toFixed(2) : 'N/A'}m</span>
                </div>
            ))}
        </div>
    )
}

export default function ChangeChart() {
    const [selectedBeach, setSelectedBeach] = useState('T.Mariyur Beach')

    const chartData = PERIODS.map(period => ({
        period,
        change: APP_DATA.transectChanges[selectedBeach][period],
        MTL: PERIOD_MTL[period],
        referenceMTL: APP_DATA.referenceMTL,
    }))

    return (
        <div className="flex flex-col h-full p-6" style={{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>

            {/* Header */}
            <div className="mb-6">
                <h2 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                    Shoreline Position Change
                </h2>
                <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
                    Transect-based displacement between consecutive months (metres)
                </p>
            </div>

            {/* Beach selector */}
            <div className="mb-6">
                <label className="text-xs font-semibold tracking-widest block mb-2"
                    style={{ color: 'var(--text-secondary)' }}>
                    SELECT BEACH
                </label>
                <div className="flex gap-2 flex-wrap">
                    {BEACHES.map(beach => (
                        <button
                            key={beach}
                            onClick={() => setSelectedBeach(beach)}
                            className="px-3 py-1.5 rounded-md text-sm transition-all"
                            style={selectedBeach === beach ? {
                                background: 'rgba(6,182,212,0.12)',
                                border: '1px solid rgba(6,182,212,0.35)',
                                color: 'var(--accent-primary)',
                                fontWeight: 600,
                            } : {
                                border: '1px solid rgba(255,255,255,0.1)',
                                color: 'var(--text-primary)',
                            }}
                        >
                            {beach}
                        </button>
                    ))}
                </div>
            </div>

            {/* Chart */}
            <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(6,182,212,0.08)" />
                        <XAxis
                            dataKey="period"
                            tick={{ fill: '#94a3b8', fontSize: 12 }}
                            axisLine={{ stroke: 'rgba(6,182,212,0.15)' }}
                            tickLine={false}
                        />
                        <YAxis
                            yAxisId="change"
                            tick={{ fill: '#94a3b8', fontSize: 12 }}
                            axisLine={false}
                            tickLine={false}
                            label={{ value: 'Change (m)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }}
                        />
                        <YAxis
                            yAxisId="tidal"
                            orientation="right"
                            domain={[0.3, 0.9]}
                            tick={{ fill: '#94a3b8', fontSize: 12 }}
                            axisLine={false}
                            tickLine={false}
                            label={{ value: 'MTL (m)', angle: 90, position: 'insideRight', fill: '#64748b', fontSize: 11 }}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12, paddingTop: 16 }} />
                        <Bar
                            yAxisId="change"
                            dataKey="change"
                            name="Shoreline Change"
                            fill="var(--accent-primary)"
                            fillOpacity={0.85}
                            radius={[4, 4, 0, 0]}
                        />
                        <Line
                            yAxisId="tidal"
                            dataKey="MTL"
                            name="MTL"
                            stroke="var(--accent-secondary)"
                            strokeWidth={2}
                            dot={{ fill: '#34d399', r: 4 }}
                            strokeDasharray="5 5"
                        />
                        <Line
                            yAxisId="tidal"
                            dataKey="referenceMTL"
                            name="Reference MTL"
                            stroke="rgba(255,255,255,0.2)"
                            strokeWidth={1}
                            dot={false}
                            strokeDasharray="2 4"
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>

            {/* December tidal note */}
            <div className="mt-4 px-3 py-2 rounded-lg"
                style={{ background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.2)' }}>
                <p className="text-xs" style={{ color: 'var(--accent-primary)' }}>
                    ⚠ December MTL (0.725m) is +0.171m above reference — Aug-Dec changes may partially reflect tidal position, not just coastal change.
                </p>
            </div>
        </div>
    )
}