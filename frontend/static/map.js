// map.js — Leaflet map with heatmap

let map;
let allMarkers  = [];
let allData     = [];
let heatLayer   = null;
let heatmapOn   = false;
let markerGroup = null;

function initMap() {
  map = L.map('map').setView([20.5937, 78.9629], 5);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© CartoDB', maxZoom: 18
  }).addTo(map);

  markerGroup = L.markerClusterGroup();
  map.addLayer(markerGroup);

  loadBlackspots();
}

async function loadBlackspots() {
  try {
    const res  = await fetch('/api/blackspots');
    const data = await res.json();
    if (data.success) {
      allData = data.blackspots;
      document.getElementById('spot-count').textContent = data.total;
      renderMarkers(allData);
    }
  } catch (err) {
    console.error('Error:', err);
  }
}

function renderMarkers(spots) {
  markerGroup.clearLayers();
  allMarkers = [];

  spots.forEach(spot => {
    const color  = spot.severity === 'fatal' ? '#e74c3c' : '#f39c12';
    const radius = spot.severity === 'fatal' ? 10 : 7;

    const circle = L.circleMarker([spot.lat, spot.lng], {
      radius, fillColor: color, color,
      weight: 1, opacity: 0.9, fillOpacity: 0.7
    });

    circle.bindPopup(`
      <div style="background:#1a1d2e;color:#fff;padding:12px;border-radius:8px;min-width:190px">
        <strong style="color:${color}">${spot.severity.toUpperCase()} ACCIDENT</strong>
        <hr style="border-color:#333;margin:6px 0"/>
        📍 <b>City:</b> ${spot.city}<br/>
        🌦 <b>Weather:</b> ${spot.weather}<br/>
        🛣 <b>Road:</b> ${spot.road}<br/>
        ⚠ <b>Risk Score:</b> ${spot.risk_score}
      </div>
    `);

    markerGroup.addLayer(circle);
    allMarkers.push(circle);
  });
}

// ─── HEATMAP ───────────────────────────
function toggleHeatmap() {
  const btn = document.getElementById('heatmap-btn');

  if (!heatmapOn) {
    // Build heatmap points [lat, lng, intensity]
    const heatPoints = allData.map(s => [
      s.lat, s.lng,
      s.severity === 'fatal' ? 1.0 : 0.5
    ]);

    heatLayer = L.heatLayer(heatPoints, {
      radius   : 25,
      blur     : 15,
      maxZoom  : 17,
      gradient : {
        0.0: 'blue',
        0.3: 'cyan',
        0.5: 'lime',
        0.7: 'yellow',
        1.0: 'red'
      }
    }).addTo(map);

    heatmapOn      = true;
    btn.textContent = '📍 Show Markers';
    btn.style.background = '#9b59b6';

  } else {
    if (heatLayer) { map.removeLayer(heatLayer); heatLayer = null; }
    heatmapOn      = false;
    btn.textContent = '🔥 Show Heatmap';
    btn.style.background = '#e74c3c';
  }
}

// ─── FILTER ────────────────────────────
function filterMap() {
  const city     = document.getElementById('city-filter').value;
  const severity = document.getElementById('severity-filter').value;

  let filtered = allData;
  if (city !== 'all')     filtered = filtered.filter(s => s.city === city);
  if (severity !== 'all') filtered = filtered.filter(s => s.severity === severity);

  document.getElementById('spot-count').textContent = filtered.length;
  renderMarkers(filtered);

  // Rebuild heatmap if on
  if (heatmapOn && heatLayer) {
    map.removeLayer(heatLayer);
    const pts = filtered.map(s => [s.lat, s.lng, s.severity==='fatal'?1.0:0.5]);
    heatLayer = L.heatLayer(pts, {
      radius:25, blur:15, maxZoom:17,
      gradient:{0.0:'blue',0.3:'cyan',0.5:'lime',0.7:'yellow',1.0:'red'}
    }).addTo(map);
  }
}

window.onload = initMap;