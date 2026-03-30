const numberFormatter = new Intl.NumberFormat("en-US")

const defaultView = {
  center: [41.03, -73.87],
  zoom: 7,
}

const worldBounds = L.latLngBounds(
  L.latLng(-85, -180),
  L.latLng(85, 180)
)

const pageShell = document.querySelector(".page-shell")
const tabButtons = [...document.querySelectorAll(".top-tab")]
const tabPanels = [...document.querySelectorAll(".tab-panel")]
const tabIndicator = document.getElementById("tab-indicator")

const stateFilter = document.getElementById("state-filter")
const metricFilter = document.getElementById("metric-filter")
const minimumFilter = document.getElementById("minimum-filter")

const dataFreshnessEl = document.getElementById("data-freshness")
const coverageNoteEl = document.getElementById("coverage-note")

const topStatesEl = document.getElementById("top-states")
const topLocationsEl = document.getElementById("top-locations")
const emptyStateEl = document.getElementById("empty-state")

let payload = null
let map = null
let markerLayer = null
let heatLayer = null
let legendControl = null
let currentLocations = []
let currentMetric = "donors"
let activePanel = "overview"

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const response = await fetch("./data/kevin_heatmap_data.json")
    if (!response.ok) {
      throw new Error(`Could not load heatmap payload (${response.status})`)
    }

    payload = await response.json()
    hydratePortal(payload)
  } catch (error) {
    dataFreshnessEl.textContent = error.message
    coverageNoteEl.textContent =
      "Run the exporter to regenerate client_portal/data/kevin_heatmap_data.json."
  }
})

function hydratePortal(data) {
  populateStateFilter(data.stateSummary)
  bindControls()
  bindTabs()

  const generatedAt = new Date(data.generatedAt)
  dataFreshnessEl.textContent = `Exported ${generatedAt.toLocaleString()}`

  render()
  requestAnimationFrame(updateTabIndicator)
  window.addEventListener("resize", updateTabIndicator)
}

function populateStateFilter(states) {
  const sortedStates = [...states].sort((left, right) => {
    if (left.State === "Unknown") {
      return 1
    }
    if (right.State === "Unknown") {
      return -1
    }
    return left.State.localeCompare(right.State)
  })

  sortedStates.forEach((state) => {
    const option = document.createElement("option")
    option.value = state.State
    option.textContent = `${state.State} (${numberFormatter.format(state.donors)})`
    stateFilter.appendChild(option)
  })
}

function bindControls() {
  ;[stateFilter, metricFilter, minimumFilter].forEach((control) => {
    control.addEventListener("change", render)
  })
}

function bindTabs() {
  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setActivePanel(button.dataset.panel)
    })
  })
}

function setActivePanel(panelName) {
  activePanel = panelName
  pageShell.classList.toggle("is-geography-active", panelName === "geography")

  tabButtons.forEach((button) => {
    const isActive = button.dataset.panel === panelName
    button.classList.toggle("is-active", isActive)
    button.setAttribute("aria-selected", String(isActive))
  })

  tabPanels.forEach((panel) => {
    panel.classList.toggle("is-active", panel.dataset.panel === panelName)
  })

  updateTabIndicator()

  if (panelName === "geography") {
    ensureMap()
    window.requestAnimationFrame(() => {
      map.invalidateSize()
      updateMap(currentLocations, currentMetric)
    })
  }
}

function updateTabIndicator() {
  const activeButton = document.querySelector(".top-tab.is-active")
  if (!activeButton) {
    return
  }

  tabIndicator.style.width = `${activeButton.offsetWidth}px`
  tabIndicator.style.transform = `translateX(${activeButton.offsetLeft}px)`
}

function ensureMap() {
  if (map) {
    return
  }

  map = L.map("map", {
    zoomControl: false,
    scrollWheelZoom: true,
    minZoom: 2,
    maxBounds: worldBounds,
    maxBoundsViscosity: 1,
    worldCopyJump: false,
  }).setView(defaultView.center, defaultView.zoom)

  L.control
    .zoom({
      position: "topright",
    })
    .addTo(map)

  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; CARTO',
    maxZoom: 18,
    noWrap: true,
    bounds: worldBounds,
  }).addTo(map)

  markerLayer = L.layerGroup().addTo(map)

  legendControl = L.control({ position: "bottomleft" })
  legendControl.onAdd = function onAdd() {
    const div = L.DomUtil.create("div", "map-legend")
    div.innerHTML = `
      <h4>Heatmap guide</h4>
      <p>The glow intensity follows the selected metric.</p>
      <p>Circle size still reflects total donor density.</p>
    `
    return div
  }
  legendControl.addTo(map)
}

function getMetricValue(location, metric) {
  if (metric === "activeDonors") {
    return location.activeDonors
  }
  if (metric === "totalDonations") {
    return location.totalDonations
  }
  return location.donors
}

function getFilteredLocations() {
  const selectedState = stateFilter.value
  const minimumCluster = Number(minimumFilter.value)

  return payload.locations.filter((location) => {
    const stateMatches =
      selectedState === "all" || location.State === selectedState
    return stateMatches && location.donors >= minimumCluster
  })
}

function buildRenderData(locations) {
  const stateAggregates = new Map()
  const groupedLocationMap = new Map()

  locations.forEach((location) => {
    const current = stateAggregates.get(location.State) || {
      state: location.State,
      donors: 0,
      totalDonations: 0,
      locations: 0,
    }
    current.donors += location.donors
    current.totalDonations += location.totalDonations
    current.locations += 1
    stateAggregates.set(location.State, current)

    const label = location.displayLabel || "Unknown location"
    const groupedLocation = groupedLocationMap.get(label) || {
      displayLabel: label,
      donors: 0,
      activeDonors: 0,
      totalDonations: 0,
      largestGift: 0,
      groupedPoints: 0,
    }
    groupedLocation.donors += location.donors
    groupedLocation.activeDonors += location.activeDonors
    groupedLocation.totalDonations += location.totalDonations
    groupedLocation.largestGift = Math.max(groupedLocation.largestGift, location.largestGift)
    groupedLocation.groupedPoints += 1
    groupedLocationMap.set(label, groupedLocation)
  })

  const rankedStates = Array.from(stateAggregates.values()).sort((left, right) => {
    if (right.donors !== left.donors) {
      return right.donors - left.donors
    }
    return right.totalDonations - left.totalDonations
  })

  const groupedLocations = Array.from(groupedLocationMap.values())
  const rankedLocations = [...groupedLocations].sort((left, right) => {
    const donorDifference = right.donors - left.donors
    if (donorDifference !== 0) {
      return donorDifference
    }
    return right.totalDonations - left.totalDonations
  })

  return {
    locations,
    rankedStates,
    groupedLocations,
    rankedLocations,
    largestCluster: rankedLocations[0] || null,
  }
}

function render() {
  if (!payload) {
    return
  }

  currentMetric = metricFilter.value
  currentLocations = getFilteredLocations()
  const renderData = buildRenderData(currentLocations)

  updateRankings(renderData, currentMetric)
  updateCoverageNote(renderData)

  if (activePanel === "geography") {
    ensureMap()
    updateMap(currentLocations, currentMetric)
  }
}

function updateRankings(renderData, metric) {
  const rankedStates = renderData.rankedStates.slice(0, 5)
  topStatesEl.innerHTML = rankedStates.length
    ? rankedStates
        .map(
          (state, index) => `
            <article class="ranking-item">
              <div class="ranking-item__index">${index + 1}</div>
              <div>
                <h3>${state.state}</h3>
                <p>${numberFormatter.format(state.locations)} mapped clusters</p>
              </div>
              <div class="ranking-item__value">${numberFormatter.format(state.donors)} donors</div>
            </article>
          `
        )
        .join("")
    : '<p class="muted">No state coverage for the current filter.</p>'

  const rankedLocations = [...renderData.groupedLocations]
    .sort((left, right) => {
      const metricDifference =
        getMetricValue(right, metric) - getMetricValue(left, metric)
      if (metricDifference !== 0) {
        return metricDifference
      }
      return right.donors - left.donors
    })
    .slice(0, 5)

  topLocationsEl.innerHTML = rankedLocations.length
    ? rankedLocations
        .map(
          (location, index) => `
            <article class="ranking-item">
              <div class="ranking-item__index">${index + 1}</div>
              <div>
                <h3>${location.displayLabel}</h3>
                <p>${formatCurrency(location.totalDonations)} total${location.groupedPoints > 1 ? ` across ${location.groupedPoints} map points` : ""}</p>
              </div>
              <div class="ranking-item__value">${formatMetricValue(location, metric)}</div>
            </article>
          `
        )
        .join("")
    : '<p class="muted">No location coverage for the current filter.</p>'
}

function updateCoverageNote(renderData) {
  const stateCount = renderData.rankedStates.length
  if (!renderData.largestCluster) {
    coverageNoteEl.textContent = "No mapped clusters match the current filter selection."
    return
  }

  coverageNoteEl.textContent = `Showing ${numberFormatter.format(renderData.groupedLocations.length)} grouped locations across ${numberFormatter.format(stateCount)} states. Largest location group: ${renderData.largestCluster.displayLabel}.`
}

function updateMap(locations, metric) {
  if (!map) {
    return
  }

  markerLayer.clearLayers()

  if (heatLayer) {
    map.removeLayer(heatLayer)
    heatLayer = null
  }

  if (!locations.length) {
    emptyStateEl.hidden = false
    map.setView(defaultView.center, defaultView.zoom)
    return
  }

  emptyStateEl.hidden = true

  const maxMetric = Math.max(...locations.map((location) => getMetricValue(location, metric)), 1)
  const heatPoints = locations.map((location) => [
    location.lat_round,
    location.lon_round,
    normalizeMetric(getMetricValue(location, metric), metric, maxMetric),
  ])

  heatLayer = L.heatLayer(heatPoints, {
    radius: 30,
    blur: 22,
    maxZoom: 11,
    minOpacity: 0.32,
    gradient: {
      0.2: "#0ea5e9",
      0.45: "#22d3ee",
      0.7: "#f59e0b",
      1: "#fb7185",
    },
  }).addTo(map)

  locations.forEach((location) => {
    const marker = L.circleMarker([location.lat_round, location.lon_round], {
      radius: 4.5 + Math.sqrt(location.donors) * 0.85,
      color: "#d8fdf8",
      weight: 1,
      fillColor: "#38bdf8",
      fillOpacity: 0.82,
    })

    marker.bindPopup(buildPopup(location))
    marker.addTo(markerLayer)
  })

  fitMapToLocations(locations)
}

function normalizeMetric(value, metric, maxMetric) {
  if (metric === "totalDonations") {
    return Math.max(0.14, Math.log1p(value) / Math.log1p(maxMetric))
  }
  return Math.max(0.14, value / maxMetric)
}

function fitMapToLocations(locations) {
  const latLngs = locations.map((location) => [location.lat_round, location.lon_round])
  if (!latLngs.length) {
    map.setView(defaultView.center, defaultView.zoom)
    return
  }

  if (latLngs.length === 1) {
    map.setView(latLngs[0], 9)
    return
  }

  const bounds = L.latLngBounds(latLngs)
  map.fitBounds(bounds.pad(0.18), { maxZoom: 9 })
}

function buildPopup(location) {
  const recentGift = location.recentGiftDate || "No recent gift date"
  const localArea = location.sampleLocalArea
    ? `<p><strong>Local area:</strong> ${location.sampleLocalArea}</p>`
    : ""

  return `
    <div class="map-popup">
      <h3>${location.displayLabel}</h3>
      <p><strong>Donors:</strong> ${numberFormatter.format(location.donors)}</p>
      <p><strong>Active donors:</strong> ${numberFormatter.format(location.activeDonors)}</p>
      <p><strong>Total donations:</strong> ${formatCurrency(location.totalDonations)}</p>
      <p><strong>Average gift:</strong> ${formatCurrency(location.averageDonation)}</p>
      <p><strong>Largest gift:</strong> ${formatCurrency(location.largestGift)}</p>
      <p><strong>Most recent gift:</strong> ${recentGift}</p>
      ${localArea}
    </div>
  `
}

function formatMetricValue(location, metric) {
  const metricValue = getMetricValue(location, metric)
  if (metric === "totalDonations") {
    return formatCurrency(metricValue)
  }
  return numberFormatter.format(metricValue)
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value)
}
