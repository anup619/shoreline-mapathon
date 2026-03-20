import { useState, useEffect, useRef } from 'react'
import DeckGL from 'deck.gl'
import { PathLayer, ScatterplotLayer, TextLayer, IconLayer } from '@deck.gl/layers'
import { PathStyleExtension } from '@deck.gl/extensions'
import Map from 'react-map-gl/maplibre'
import maplibregl from 'maplibre-gl'

const BEACHES = ['T.Mariyur Beach', 'Sayalkudi Beach', 'Keelvaipar Beach', 'Ervadi Beach']
const MONTHS = ['February', 'April', 'May', 'June', 'July', 'August', 'December']

const MONTH_COLORS = {
    'February': [78, 121, 167],
    'April': [242, 142, 43],
    'May': [89, 161, 79],
    'June': [225, 87, 89],
    'July': [118, 183, 178],
    'August': [237, 201, 72],
    'December': [176, 122, 161],
}

const BEACH_COORDS = {
    'T.Mariyur Beach': [78.534155, 9.136362],
    'Sayalkudi Beach': [78.478865, 9.127423],
    'Keelvaipar Beach': [78.253959, 8.995365],
    'Ervadi Beach': [78.719328, 9.194177],
}

const PIN_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="24" height="36">
  <path d="M12 0C5.373 0 0 5.373 0 12c0 9 12 24 12 24S24 21 24 12C24 5.373 18.627 0 12 0z"
    fill="#f97316" stroke="#ffffff" stroke-width="1.5"/>
  <circle cx="12" cy="12" r="4" fill="#ffffff"/>
</svg>`
const PIN_ICON_ATLAS = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(PIN_SVG)}`
const PIN_ICON_MAPPING = { pin: { x: 0, y: 0, width: 24, height: 36, anchorY: 36, mask: false } }

// compute bounding box + zoom to fit two points
function getBoundsViewState(pt1, pt2, distanceM, currentViewState) {
    const centerLon = (pt1[0] + pt2[0]) / 2
    const centerLat = (pt1[1] + pt2[1]) / 2

    let zoom
    if (distanceM < 4) zoom = 22
    else if (distanceM < 6) zoom = 21
    else if (distanceM < 8) zoom = 20
    else if (distanceM < 10) zoom = 19
    else zoom = 18

    return {
        ...currentViewState,
        longitude: centerLon,
        latitude: centerLat,
        zoom,
        transitionDuration: 600,
    }
}

export default function TransectVisualizer() {
    const [transectData, setTransectData] = useState(null)
    const [shorelineData, setShorelineData] = useState(null)
    const [selectedBeach, setSelectedBeach] = useState('T.Mariyur Beach')
    const [refMonth, setRefMonth] = useState('February')
    const [compareMonth, setCompareMonth] = useState('April')
    const [mode, setMode] = useState('compare') // 'compare' | 'animate'
    const [animStep, setAnimStep] = useState(0)
    const [isAnimating, setIsAnimating] = useState(false)
    const [opacity, setOpacity] = useState(255)
    const animRef = useRef(null)
    const fadeRef = useRef(null)

    const [viewState, setViewState] = useState({
        longitude: 78.534155,
        latitude: 9.136362,
        zoom: 16,
        pitch: 0,
        bearing: 0,
    })

    useEffect(() => {
        fetch('/geojson/transects.json').then(r => r.json()).then(setTransectData)
        fetch('/geojson/shorelines.geojson').then(r => r.json()).then(setShorelineData)
    }, [])

    // zoom to beach when changed
    useEffect(() => {
        const coords = BEACH_COORDS[selectedBeach]
        setViewState(v => ({
            ...v,
            longitude: coords[0],
            latitude: coords[1],
            zoom: 16,
            transitionDuration: 800,
        }))
    }, [selectedBeach])

    // animation — cycles compare month, fades between
    const animMonths = MONTHS.filter(m => m !== refMonth)

    useEffect(() => {
        if (mode !== 'animate') return
        if (isAnimating) {
            animRef.current = setInterval(() => {
                // fade out
                setOpacity(0)
                setTimeout(() => {
                    setAnimStep(s => {
                        const next = (s + 1) % animMonths.length
                        setCompareMonth(animMonths[next])
                        return next
                    })
                    // fade in
                    setTimeout(() => setOpacity(255), 200)
                }, 300)
            }, 2000)
        } else {
            clearInterval(animRef.current)
            setOpacity(255)
        }
        return () => clearInterval(animRef.current)
    }, [isAnimating, mode, refMonth, animMonths.length])

    // find current transect
    const currentTransect = transectData?.find(t => {
        const m1Match = t.month1 === refMonth && t.month2 === compareMonth
        const m2Match = t.month1 === compareMonth && t.month2 === refMonth
        return t.beach === selectedBeach && (m1Match || m2Match) && t.distance_m < 100
    })

    // zoom to fit intersections when transect changes
    useEffect(() => {
        if (!currentTransect) return
        setViewState(v => getBoundsViewState(
            currentTransect.intersection1,
            currentTransect.intersection2,
            currentTransect.distance_m,
            v
        ))
    }, [currentTransect])

    // get shoreline features for ref and compare months
    const refShoreFeature = shorelineData?.features.find(f => f.properties.month === refMonth)
    const cmpShoreFeature = shorelineData?.features.find(f => f.properties.month === compareMonth)

    const layers = []

    // reference shoreline — dashed style (thinner, more transparent)
    if (refShoreFeature) {
        layers.push(new PathLayer({
            id: 'shore-ref',
            data: [refShoreFeature],
            getPath: f => f.geometry.coordinates,
            getColor: [...MONTH_COLORS[refMonth], 180],
            getWidth: 2,
            widthUnits: 'pixels',
            getDashArray: [6, 4],
            dashJustified: true,
            extensions: [new PathStyleExtension({ dash: true })]
        }))
    }

    // comparing shoreline — solid, prominent, with fade
    if (cmpShoreFeature) {
        layers.push(new PathLayer({
            id: 'shore-cmp',
            data: [cmpShoreFeature],
            getPath: f => f.geometry.coordinates,
            getColor: [...MONTH_COLORS[compareMonth], opacity],
            getWidth: 3,
            widthUnits: 'pixels',
            updateTriggers: { getColor: [compareMonth, opacity] }
        }))
    }

    if (currentTransect) {
        const { transect, intersection1, intersection2, distance_m } = currentTransect

        // full transect — dashed
        layers.push(new PathLayer({
            id: 'transect-dashed',
            data: [{ path: transect }],
            getPath: d => d.path,
            getColor: [255, 255, 255, 100],
            getWidth: 1,
            widthUnits: 'pixels',
            getDashArray: [6, 4],
            dashJustified: true,
            extensions: [new PathStyleExtension({ dash: true })]
        }))

        // solid segment between intersections — the actual measurement
        layers.push(new PathLayer({
            id: 'transect-solid',
            data: [{ path: [intersection1, intersection2] }],
            getPath: d => d.path,
            getColor: [255, 200, 50, 255],
            getWidth: 3,
            widthUnits: 'pixels',
        }))

        // arrow head at intersection2
        layers.push(new ScatterplotLayer({
            id: 'arrow-head',
            data: [{ position: intersection2 }],
            getPosition: d => d.position,
            getRadius: 5,
            radiusUnits: 'pixels',
            getFillColor: [255, 200, 50, 255],
        }))

        // intersection dot 1 — ref month color
        layers.push(new ScatterplotLayer({
            id: 'int1',
            data: [{ position: intersection1 }],
            getPosition: d => d.position,
            getRadius: 7,
            radiusUnits: 'pixels',
            getFillColor: [...MONTH_COLORS[refMonth], 255],
            getLineColor: [255, 255, 255],
            stroked: true,
            lineWidthMinPixels: 2,
        }))

        // intersection dot 2 — compare month color
        layers.push(new ScatterplotLayer({
            id: 'int2',
            data: [{ position: intersection2 }],
            getPosition: d => d.position,
            getRadius: 7,
            radiusUnits: 'pixels',
            getFillColor: [...MONTH_COLORS[compareMonth], opacity],
            getLineColor: [255, 255, 255],
            stroked: true,
            lineWidthMinPixels: 2,
            updateTriggers: { getFillColor: [compareMonth, opacity] }
        }))

        // shoreline labels
        const midTransect = transect[Math.floor(transect.length / 2)]

        layers.push(new TextLayer({
            id: 'label-ref',
            data: [{ position: intersection1, text: refMonth }],
            getPosition: d => d.position,
            getText: d => d.text,
            getSize: 12,
            getColor: MONTH_COLORS[refMonth],
            getBackgroundColor: [15, 23, 42, 200],
            background: true,
            getPixelOffset: [-50, 0],
            fontWeight: 'bold',
        }))

        layers.push(new TextLayer({
            id: 'label-cmp',
            data: [{ position: intersection2, text: compareMonth }],
            getPosition: d => d.position,
            getText: d => d.text,
            getSize: 12,
            getColor: MONTH_COLORS[compareMonth],
            getBackgroundColor: [15, 23, 42, 200],
            background: true,
            getPixelOffset: [50, 0],
            fontWeight: 'bold',
        }))

        // distance label — midpoint of measurement segment
        const midLon = (intersection1[0] + intersection2[0]) / 2
        const midLat = (intersection1[1] + intersection2[1]) / 2

        layers.push(new TextLayer({
            id: 'distance-label',
            data: [{ position: [midLon, midLat] }],
            getPosition: d => d.position,
            getText: () => `${distance_m}m`,
            getSize: 15,
            getColor: [255, 200, 50],
            getBackgroundColor: [15, 23, 42, 220],
            background: true,
            getPixelOffset: [30, 0],
            fontWeight: 'bold',
        }))
    }

    // beach pin
    layers.push(new IconLayer({
        id: 'beach-pin',
        data: [{ position: BEACH_COORDS[selectedBeach] }],
        iconAtlas: PIN_ICON_ATLAS,
        iconMapping: PIN_ICON_MAPPING,
        getIcon: () => 'pin',
        getPosition: d => d.position,
        getSize: 36,
    }))

    layers.push(new TextLayer({
        id: 'beach-label',
        data: [{ position: BEACH_COORDS[selectedBeach], text: selectedBeach }],
        getPosition: d => d.position,
        getText: d => d.text,
        getSize: 13,
        getColor: [255, 255, 255],
        getBackgroundColor: [15, 23, 42, 180],
        background: true,
        getPixelOffset: [0, -52],
        fontWeight: 'bold',
    }))

    return (
        <div className="flex flex-col h-full" style={{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>

            {/* Header */}
            <div className="px-6 py-4" style={{ borderBottom: '1px solid var(--border)' }}>
                <h2 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                    Transect Visualizer
                </h2>
                <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
                    Perpendicular transect showing shoreline displacement between two months
                </p>
            </div>

            {/* Controls */}
            <div className="px-6 py-3 flex flex-wrap gap-6 items-end"
                style={{ borderBottom: '1px solid var(--border)' }}>

                {/* Beach */}
                <div>
                    <label className="text-xs font-semibold tracking-widest block mb-2"
                        style={{ color: 'var(--text-secondary)' }}>BEACH</label>
                    <select
                        value={selectedBeach}
                        onChange={e => setSelectedBeach(e.target.value)}
                        className="text-sm rounded-md px-3 py-1.5 focus:outline-none"
                        style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
                    >
                        {BEACHES.map(b => <option key={b} value={b}>{b}</option>)}
                    </select>
                </div>

                {/* Mode toggle */}
                <div>
                    <label className="text-xs font-semibold tracking-widest block mb-2"
                        style={{ color: 'var(--text-secondary)' }}>MODE</label>
                    <div className="flex rounded-md overflow-hidden" style={{ border: '1px solid var(--border)' }}>
                        {['compare', 'animate'].map(m => (
                            <button
                                key={m}
                                onClick={() => { setMode(m); setIsAnimating(false) }}
                                className="px-3 py-1.5 text-sm capitalize transition-all"
                                style={mode === m ? {
                                    background: 'rgba(6,182,212,0.15)',
                                    color: 'var(--accent-primary)',
                                    fontWeight: 600,
                                } : {
                                    color: 'var(--text-secondary)',
                                }}
                            >
                                {m}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Reference month */}
                <div>
                    <label className="text-xs font-semibold tracking-widest block mb-2"
                        style={{ color: 'var(--text-secondary)' }}>REFERENCE</label>
                    <select
                        value={refMonth}
                        onChange={e => { setRefMonth(e.target.value); setAnimStep(0) }}
                        className="text-sm rounded-md px-3 py-1.5 focus:outline-none"
                        style={{
                            background: 'var(--bg-secondary)',
                            border: `1px solid rgb(${MONTH_COLORS[refMonth].join(',')})`,
                            color: 'var(--text-primary)'
                        }}
                    >
                        {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                </div>

                {/* Compare month */}
                {mode === 'compare' && (
                    <div>
                        <label className="text-xs font-semibold tracking-widest block mb-2"
                            style={{ color: 'var(--text-secondary)' }}>COMPARE</label>
                        <select
                            value={compareMonth}
                            onChange={e => setCompareMonth(e.target.value)}
                            className="text-sm rounded-md px-3 py-1.5 focus:outline-none"
                            style={{
                                background: 'var(--bg-secondary)',
                                border: `1px solid rgb(${MONTH_COLORS[compareMonth].join(',')})`,
                                color: 'var(--text-primary)'
                            }}
                        >
                            {MONTHS.filter(m => m !== refMonth).map(m => (
                                <option key={m} value={m}>{m}</option>
                            ))}
                        </select>
                    </div>
                )}

                {/* Animate controls */}
                {mode === 'animate' && (
                    <div className="flex items-end gap-3">
                        <button
                            onClick={() => setIsAnimating(p => !p)}
                            className="px-4 py-1.5 rounded-md text-sm font-semibold transition-all"
                            style={isAnimating ? {
                                background: 'var(--accent-primary)',
                                color: 'var(--bg-primary)',
                            } : {
                                border: '1px solid var(--border)',
                                color: 'var(--text-primary)',
                            }}
                        >
                            {isAnimating ? '⏹ Stop' : '▶ Play'}
                        </button>

                        <div className="flex gap-1.5 items-center pb-1">
                            {animMonths.map((m, i) => (
                                <button
                                    key={m}
                                    onClick={() => { setCompareMonth(m); setAnimStep(i) }}
                                    className="transition-all"
                                    style={{
                                        width: i === animStep ? 20 : 6,
                                        height: 6,
                                        borderRadius: 3,
                                        background: i === animStep
                                            ? `rgb(${MONTH_COLORS[m].join(',')})`
                                            : 'rgba(6,182,212,0.2)'
                                    }}
                                    title={m}
                                />
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Map */}
            <div className="flex-1 relative">
                <DeckGL
                    viewState={viewState}
                    onViewStateChange={e => setViewState(e.viewState)}
                    controller={true}
                    layers={layers}
                    style={{ position: 'absolute', inset: 0 }}
                    getCursor={({ isHovering }) => isHovering ? 'pointer' : 'grab'}
                >
                    <Map
                        mapLib={maplibregl}
                        mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
                    />
                </DeckGL>

                {/* Info card */}
                <div
                    className="absolute top-4 right-4 rounded-lg px-4 py-3 min-w-[220px]"
                    style={{ background: 'rgba(10,22,40,0.97)', border: '1px solid var(--border)' }}
                >
                    <div className="text-xs font-semibold tracking-widest mb-3"
                        style={{ color: 'var(--text-secondary)' }}>
                        TRANSECT INFO
                    </div>

                    <div className="flex items-center gap-2 mb-2">
                        <span className="w-6 border-t border-dashed"
                            style={{ borderColor: `rgb(${MONTH_COLORS[refMonth].join(',')})` }} />
                        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Reference</span>
                        <span className="text-sm font-semibold ml-auto" style={{ color: 'var(--text-primary)' }}>
                            {refMonth}
                        </span>
                    </div>
                    <div className="flex items-center gap-2 mb-3">
                        <span className="w-6 border-t-2"
                            style={{ borderColor: `rgb(${MONTH_COLORS[compareMonth].join(',')})` }} />
                        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Comparing</span>
                        <span className="text-sm font-semibold ml-auto" style={{ color: 'var(--text-primary)' }}>
                            {compareMonth}
                        </span>
                    </div>

                    {currentTransect ? (
                        <div className="pt-3" style={{ borderTop: '1px solid var(--border)' }}>
                            <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>Displacement</div>
                            <div className="font-bold text-2xl" style={{ color: 'var(--accent-primary)' }}>
                                {currentTransect.distance_m}m
                            </div>
                            <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
                                {selectedBeach}
                            </div>
                        </div>
                    ) : (
                        <div className="pt-3" style={{ borderTop: '1px solid var(--border)' }}>
                            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                                No valid transect for this combination
                            </div>
                        </div>
                    )}

                    {/* Legend */}
                    <div className="pt-3 mt-3 flex flex-col gap-1.5"
                        style={{ borderTop: '1px solid var(--border)' }}>
                        {[
                            { style: 'dashed', color: `rgb(${MONTH_COLORS[refMonth].join(',')})`, label: 'Reference shoreline' },
                            { style: 'solid', color: `rgb(${MONTH_COLORS[compareMonth].join(',')})`, label: 'Comparing shoreline' },
                            { style: 'dashed', color: 'rgba(255,255,255,0.4)', label: 'Transect line' },
                            { style: 'solid', color: '#ffc832', label: 'Displacement' },
                        ].map(({ style, color, label }) => (
                            <div key={label} className="flex items-center gap-2">
                                <div className="w-6 border-t-2" style={{
                                    borderColor: color,
                                    borderStyle: style,
                                }} />
                                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}