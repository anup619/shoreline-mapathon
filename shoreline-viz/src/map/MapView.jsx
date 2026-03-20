import { useState, useEffect } from 'react'
import DeckGL from 'deck.gl'
import { PathLayer, TextLayer, IconLayer } from '@deck.gl/layers'
import Map from 'react-map-gl/maplibre'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

const INITIAL_VIEW = {
    longitude: 78.49,
    latitude: 9.11,
    zoom: 11,
    pitch: 0,
    bearing: 0
}

const MONTH_COLORS = {
    'February': [78, 121, 167],
    'April': [242, 142, 43],
    'May': [89, 161, 79],
    'June': [225, 87, 89],
    'July': [118, 183, 178],
    'August': [237, 201, 72],
    'December': [176, 122, 161],
}

const BEACH_HEIGHTS = {
    'T.Mariyur Beach': 4.79,
    'Sayalkudi Beach': 0.57,
    'Keelvaipar Beach': 6.62,
    'Ervadi Beach': 0.0,
}

const MONTH_ELEVATION = {
    'February': 0,
    'April': 2000,
    'May': 4000,
    'June': 6000,
    'July': 8000,
    'August': 10000,
    'December': 12000,
}

const PIN_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="24" height="36">
  <path d="M12 0C5.373 0 0 5.373 0 12c0 9 12 24 12 24S24 21 24 12C24 5.373 18.627 0 12 0z"
    fill="#f97316" stroke="#ffffff" stroke-width="1.5"/>
  <circle cx="12" cy="12" r="4" fill="#ffffff"/>
</svg>
`

const PIN_ICON_ATLAS = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(PIN_SVG)}`

const PIN_ICON_MAPPING = {
    pin: { x: 0, y: 0, width: 24, height: 36, anchorY: 36, mask: false }
}

export default function MapView({ visible, show3D, onBeachClick }) {
    const [viewState, setViewState] = useState(INITIAL_VIEW)
    const [shorelineData, setShorelineData] = useState(null)
    const [beachData, setBeachData] = useState(null)

    useEffect(() => {
        fetch('/geojson/shorelines.geojson')
            .then(r => r.json())
            .then(setShorelineData)

        fetch('/geojson/beach_points.geojson')
            .then(r => r.json())
            .then(setBeachData)
    }, [])

    // update pitch when 3D toggled
    useEffect(() => {
        setViewState(v => ({ ...v, pitch: show3D ? 55 : 0, bearing: show3D ? -20 : 0, transitionDuration: 800 }))
    }, [show3D])

    const shorelines = shorelineData?.features
        .filter(f => visible[f.properties.month]) ?? []

    const beaches = beachData?.features ?? []

    const layers = [
        // shoreline paths
        new PathLayer({
            id: 'shorelines',
            data: shorelines,
            getPath: f => f.geometry.coordinates.map(coord => [
                coord[0], coord[1], show3D ? MONTH_ELEVATION[f.properties.month] || 0 : 0
            ]),
            getColor: f => MONTH_COLORS[f.properties.month] || [255, 255, 255],
            getWidth: show3D ? 50 : 3,
            widthUnits: show3D ? 'meters' : 'pixels',
            pickable: false,
            updateTriggers: {
                getPath: [show3D],
                getWidth: [show3D]
            }
        }),

        // location pin icons
        new IconLayer({
            id: 'beach-pins',
            data: beaches,
            iconAtlas: PIN_ICON_ATLAS,
            iconMapping: PIN_ICON_MAPPING,
            getIcon: () => 'pin',
            getPosition: f => f.geometry.coordinates,
            getSize: show3D ? 48 : 40,
            pickable: true,
            onClick: ({ object, x, y }) => {
                if (object) onBeachClick(object.properties.name, x, y)
            },
            updateTriggers: {
                getSize: [show3D]
            }
        }),

        // beach labels
        new TextLayer({
            id: 'beach-labels',
            data: beaches,
            getPosition: f => f.geometry.coordinates,
            getText: f => f.properties.name,
            getSize: 13,
            getColor: [255, 255, 255],
            getBackgroundColor: [15, 23, 42, 180],
            background: true,
            getBorderRadius: 4,
            getPixelOffset: [0, -52],
            fontWeight: 'bold',
        }),
    ]

    return (
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
    )
}