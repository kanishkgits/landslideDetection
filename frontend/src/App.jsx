import React, { useEffect, useMemo, useState } from "react";
import {
  MapContainer, TileLayer, CircleMarker, Popup, useMap, useMapEvents
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./style.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const CITIES = [
  { name: "Darjeeling", state: "West Bengal", lat: 27.0410, lon: 88.2663, tag: "Himalayan region" },
  { name: "Siliguri", state: "West Bengal", lat: 26.7271, lon: 88.3953, tag: "Terai foothills" },
  { name: "Gangtok", state: "Sikkim", lat: 27.3389, lon: 88.6065, tag: "Eastern Himalaya" },
  { name: "Bhagalpur", state: "Bihar", lat: 25.2425, lon: 86.9842, tag: "Gangetic plains" },
];

function MapViewport({ position, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (position) map.flyTo(position, zoom || 10, { duration: 1.1 });
  }, [map, position, zoom]);
  return null;
}

function MapClick({ onChoose }) {
  useMapEvents({
    click(e) {
      onChoose(e.latlng.lat, e.latlng.lng);
    }
  });
  return null;
}

function formatNumber(value, digits = 1) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

function MetricCard({ label, value, detail, icon, accent = "" }) {
  return (
    <article className={`metric-card ${accent}`}>
      <div className="metric-top"><span>{label}</span><span className="metric-icon">{icon}</span></div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function ScoreCard({ title, value, suffix = "/100", description, tone = "teal", children }) {
  return (
    <article className={`score-card ${tone}`}>
      <div className="score-heading">{title}</div>
      <div className="score-value">{value}<span>{suffix}</span></div>
      {description && <p>{description}</p>}
      {children}
    </article>
  );
}

function App() {
  const [events, setEvents] = useState([]);
  const [health, setHealth] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [lat, setLat] = useState(String(CITIES[0].lat));
  const [lon, setLon] = useState(String(CITIES[0].lon));
  const [selectedCity, setSelectedCity] = useState("Darjeeling");
  const [mapPosition, setMapPosition] = useState([CITIES[0].lat, CITIES[0].lon]);
  const [mapZoom, setMapZoom] = useState(8);
  const [assessment, setAssessment] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/health`).then(r => { if (!r.ok) throw new Error("Health endpoint unavailable"); return r.json(); }),
      fetch(`${API}/api/v1/events?limit=2000`).then(r => { if (!r.ok) throw new Error("Event inventory unavailable"); return r.json(); })
    ]).then(([h, e]) => {
      setHealth(h);
      setEvents(e.items || []);
    }).catch(e => setError(e.message))
      .finally(() => setDataLoading(false));

    fetch(`${API}/api/v1/model/metrics`)
      .then(r => r.ok ? r.json() : null)
      .then(setMetrics)
      .catch(() => {});
  }, []);

  const validEvents = useMemo(() => events.filter(e =>
    Number.isFinite(Number(e.latitude)) && Number.isFinite(Number(e.longitude))
  ), [events]);

  const history = assessment?.historical_evidence;
  const finalScore = assessment?.final_score;
  const scoreValue = finalScore?.final_landslide_screening_score;

  function chooseCity(city) {
    setSelectedCity(city.name);
    setLat(String(city.lat));
    setLon(String(city.lon));
    setMapPosition([city.lat, city.lon]);
    setMapZoom(9);
    setAssessment(null);
    setError("");
  }

  function chooseCoordinates(latitude, longitude) {
    setLat(latitude.toFixed(5));
    setLon(longitude.toFixed(5));
    setSelectedCity("");
    setMapPosition([latitude, longitude]);
    setMapZoom(10);
    setAssessment(null);
  }

  function selectEvent(event) {
    chooseCoordinates(Number(event.latitude), Number(event.longitude));
  }

  async function assess() {
    const latitude = Number(lat), longitude = Number(lon);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude) ||
        latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
      setError("Enter valid latitude and longitude values.");
      return;
    }
    setBusy(true);
    setError("");
    setAssessment(null);
    try {
      const response = await fetch(`${API}/api/v1/live/assess`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ latitude, longitude })
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Assessment could not be completed.");
      setAssessment(result);
      setMapPosition([latitude, longitude]);
      setMapZoom(10);
    } catch (e) {
      setError(e.message || "Unable to connect to the assessment service.");
    } finally {
      setBusy(false);
    }
  }

  const modelReady = Boolean(health?.model_ready);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><span>Ｔ</span></div>
          <div><b>TerraGuard</b><small>LANDSLIDE INTELLIGENCE</small></div>
        </div>
        <div className="side-label">WORKSPACE</div>
        <a className="side-link active" href="#overview"><span>▦</span> Overview</a>
        <a className="side-link" href="#inventory"><span>◎</span> Event inventory</a>
        <a className="side-link" href="#assessment"><span>⌖</span> Location assessment</a>
        <a className="side-link" href="#model"><span>▤</span> Model performance</a>
        <div className="sidebar-bottom">
          <div className="side-status"><i className={modelReady ? "online" : ""}></i><div><b>{modelReady ? "Model available" : "Model pending"}</b><small>API service status</small></div></div>
          <small className="sidebar-foot">Research prototype · India</small>
        </div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar">
          <div className="breadcrumb">Monitoring <span>/</span> <b>Overview</b></div>
          <div className="topbar-right">
            <span className="live-indicator"><i></i> DATA SERVICES</span>
            <div className="avatar">TG</div>
          </div>
        </header>

        <section className="page-intro">
          <div>
            <div className="eyebrow">INDIA · GEOHAZARD MONITORING</div>
            <h1>Monitoring overview</h1>
            <p>Review reported landslide events and assess environmental conditions at selected locations.</p>
          </div>
          <div className={`service-chip ${modelReady ? "good" : "pending"}`}>
            <span className="service-dot"></span>{modelReady ? "ML model ready" : "ML model not trained"}
          </div>
        </section>

        <section className="disclaimer">
          <div className="disclaimer-icon">i</div>
          <div><b>Research-use notice</b><p>TerraGuard provides an experimental screening index, not a calibrated probability or official warning. Historical records are incomplete and reporting-biased; absence of catalog events does not establish safety.</p></div>
        </section>

        {error && <div className="error-banner"><b>Service notice</b><span>{error}</span><button onClick={() => setError("")}>Dismiss</button></div>}

        <section className="overview-grid">
          <MetricCard label="Catalog records loaded" value={dataLoading ? "…" : validEvents.length.toLocaleString("en-IN")} detail="Reported events in current inventory" icon="◉" />
          <MetricCard label="Model status" value={modelReady ? "Ready" : "Pending"} detail="Research classification model" icon="⌁" accent="mint" />
          <MetricCard label="Weather provider" value="Open-Meteo" detail="Archive and forecast inputs" icon="☁" accent="blue" />
          <MetricCard label="Coverage area" value="India" detail="Based on available catalog records" icon="⌖" accent="sand" />
        </section>

        <section className="section-block" id="inventory">
          <div className="section-heading">
            <div><div className="section-kicker">SPATIAL DATA</div><h2>Historical event inventory</h2><p>Explore reported NASA Global Landslide Catalog events. Select a marker or click the map to set assessment coordinates.</p></div>
            <div className="map-legend"><span><i></i> Reported landslide</span><span><i className="legend-target"></i> Selected location</span></div>
          </div>
          <div className="map-frame">
            <div className="map-toolbar"><span><b>INDIA</b> · Event distribution</span><span>{validEvents.length.toLocaleString("en-IN")} mapped records</span></div>
            <div className="map-canvas">
              <MapContainer center={[22.5, 82.5]} zoom={4} scrollWheelZoom>
                <MapViewport position={mapPosition} zoom={mapZoom} />
                <MapClick onChoose={chooseCoordinates} />
                <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                {validEvents.map((event, index) => (
                  <CircleMarker
                    key={event.source_record_id || index}
                    center={[Number(event.latitude), Number(event.longitude)]}
                    radius={4}
                    pathOptions={{ color: "#b85e46", fillColor: "#d77b5f", fillOpacity: 0.68, weight: 1 }}
                    eventHandlers={{ click: () => selectEvent(event) }}
                  >
                    <Popup><div className="map-popup"><b>{event.event_date || "Date unavailable"}</b><span>{Number(event.latitude).toFixed(4)}, {Number(event.longitude).toFixed(4)}</span><small>Reported catalog event · Select to assess this location</small></div></Popup>
                  </CircleMarker>
                ))}
                {mapPosition && <CircleMarker center={mapPosition} radius={8} pathOptions={{ color: "#176d63", fillColor: "#2c9c8b", fillOpacity: 0.95, weight: 3 }}><Popup>Selected assessment location</Popup></CircleMarker>}
              </MapContainer>
            </div>
            <div className="map-caption"><span>Map data © OpenStreetMap contributors</span><span>Click anywhere on the map to choose a location</span></div>
          </div>
        </section>

        <section className="section-block" id="assessment">
          <div className="section-heading">
            <div><div className="section-kicker">LOCATION ANALYSIS</div><h2>Assess a location</h2><p>Select a predefined location or enter coordinates for a custom assessment.</p></div>
          </div>
          <div className="assessment-layout">
            <div className="location-panel">
              <div className="subheading"><b>Predefined locations</b><span>SELECT A REGION</span></div>
              <div className="city-grid">
                {CITIES.map(city => (
                  <button key={city.name} className={`city-card ${selectedCity === city.name ? "selected" : ""}`} onClick={() => chooseCity(city)}>
                    <span className="city-pin">⌖</span><span className="city-copy"><b>{city.name}</b><small>{city.state} · {city.tag}</small></span><span className="city-arrow">↗</span>
                  </button>
                ))}
              </div>
              <div className="coordinate-fields">
                <label>Latitude<input type="number" step="any" value={lat} onChange={e => { setLat(e.target.value); setSelectedCity(""); }} /></label>
                <label>Longitude<input type="number" step="any" value={lon} onChange={e => { setLon(e.target.value); setSelectedCity(""); }} /></label>
              </div>
              <button className="primary-button" onClick={assess} disabled={busy}>
                {busy ? <><span className="spinner"></span> Running assessment…</> : <>Run location assessment <span>→</span></>}
              </button>
              <div className="coordinate-hint">Tip: select a point directly on the map to populate these coordinates.</div>
            </div>

            <div className="assessment-summary">
              <div className="summary-top"><div><span className="summary-label">CURRENT SELECTION</span><h3>{selectedCity || "Custom coordinates"}</h3><p>{Number(lat).toFixed(4)}, {Number(lon).toFixed(4)}</p></div><div className="target-icon">⌖</div></div>
              <div className="summary-divider"></div>
              {assessment ? (
                <div className="summary-complete"><span className="complete-mark">✓</span><div><b>Assessment completed</b><small>Results are displayed below.</small></div></div>
              ) : (
                <div className="summary-empty"><div className="empty-graphic">⌁</div><b>Assessment not yet run</b><p>Run an assessment to view historical evidence, model output and environmental indicators for this location.</p></div>
              )}
            </div>
          </div>

          {assessment && (
            <div className="results-section">
              <div className="results-title"><div><div className="section-kicker">ASSESSMENT OUTPUT</div><h2>Screening results</h2><p>Location-specific evidence and model indicators.</p></div><span className="result-tag">RESULT AVAILABLE</span></div>
              <div className="score-grid">
                <ScoreCard title="FINAL SCREENING INDEX" value={formatNumber(scoreValue)} description={finalScore?.interpretation || "Composite research screening index"} tone="score-primary">
                  <div className="score-scale"><span>0</span><div><i style={{ width: `${Math.max(0, Math.min(100, Number(scoreValue) || 0))}%` }}></i></div><span>100</span></div>
                  <small className="score-footnote">Heuristic index · not a probability</small>
                </ScoreCard>
                <ScoreCard title="HISTORICAL OCCURRENCE" value={formatNumber(history?.historical_occurrence_index)} description={history?.historical_index_label || "No inventory records available"} tone="score-sand">
                  <div className="mini-stats"><div><b>{history?.events_within_10km ?? 0}</b><span>Within 10 km</span></div><div><b>{history?.events_within_radius ?? 0}</b><span>Within {history?.radius_km ?? 25} km</span></div><div><b>{formatNumber(history?.nearest_reported_event_km, 2)}</b><span>Nearest · km</span></div></div>
                </ScoreCard>
                <ScoreCard title="ML RELATIVE EVENT SCORE" value={formatNumber((Number(assessment.relative_event_score) || 0) * 100)} suffix="/100" description={assessment.score_interpretation || "Relative classifier output"} tone="score-blue">
                  <small className="score-footnote">Not calibrated as event probability</small>
                </ScoreCard>
              </div>

              <div className="detail-grid">
                <article className="detail-card">
                  <div className="detail-card-heading"><div><h3>Composite score components</h3><p>Available inputs and their contribution to the final index.</p></div><span>WEIGHTED INPUTS</span></div>
                  {Object.entries(finalScore?.components || {}).map(([key, item]) => (
                    <div className="component-row" key={key}>
                      <div className="component-label"><span>{key.replaceAll("_", " ")}</span><b>{item.score === null ? "Unavailable" : `${formatNumber(item.score)} / 100`}</b></div>
                      <div className="component-track"><i style={{ width: `${Math.max(0, Math.min(100, Number(item.score) || 0))}%` }} /></div>
                      <small>{item.description} · weight {Math.round(item.weight * 100)}%</small>
                    </div>
                  ))}
                  <div className="available-weight">Available component weight: <b>{Math.round((finalScore?.available_weight_fraction || 0) * 100)}%</b></div>
                </article>
                <article className="detail-card">
                  <div className="detail-card-heading"><div><h3>Environmental inputs</h3><p>Values supplied to the assessment service.</p></div><span>LIVE DATA</span></div>
                  <div className="feature-list">
                    {Object.entries(assessment.features || {}).map(([key, value]) => (
                      <div key={key}><span>{key.replaceAll("_", " ")}</span><b>{typeof value === "number" ? formatNumber(value, 2) : String(value ?? "—")}</b></div>
                    ))}
                  </div>
                </article>
              </div>
            </div>
          )}
        </section>

        <section className="section-block" id="model">
          <div className="section-heading">
            <div><div className="section-kicker">MODEL VALIDATION</div><h2>Model performance</h2><p>Evaluation metrics for the current research classifier.</p></div>
            {metrics && <span className="result-tag">PAIR-GROUPED HOLDOUT</span>}
          </div>
          {metrics ? (
            <div className="model-panel">
              <div className="model-metrics">
                <div><span>Average precision</span><b>{formatNumber(metrics.average_precision, 3)}</b></div>
                <div><span>ROC-AUC</span><b>{formatNumber(metrics.roc_auc, 3)}</b></div>
                <div><span>Matched event groups</span><b>{metrics.event_pairs ?? "—"}</b></div>
                <div><span>Evaluation rows</span><b>{metrics.rows ?? "—"}</b></div>
              </div>
              <p>{metrics.interpretation || metrics.target || "Metrics describe model discrimination on the reported evaluation split."}</p>
            </div>
          ) : <div className="model-panel empty-model">Model evaluation metrics will be shown here after model training and evaluation.</div>}
        </section>

        <footer className="footer"><div className="footer-brand">TerraGuard <span>·</span> Landslide screening research prototype</div><div>NASA Global Landslide Catalog · Open-Meteo · OpenStreetMap</div><p>For research and informational use only. Not an emergency response or public warning system.</p></footer>
      </main>
    </div>
  );
}

export default App;
