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

const overviewMetricsEl = document.getElementById("overview-metrics")
const overviewSegmentsEl = document.getElementById("overview-segments")
const overviewConcentrationEl = document.getElementById("overview-concentration")
const overviewSizeMixEl = document.getElementById("overview-size-mix")
const overviewPriorityStatesEl = document.getElementById("overview-priority-states")

const analyticsKpiTableEl = document.getElementById("analytics-kpi-table")
const analyticsTopDonorsEl = document.getElementById("analytics-top-donors")
const analyticsMonthlyPulseEl = document.getElementById("analytics-monthly-pulse")
const analyticsStatePerformanceEl = document.getElementById("analytics-state-performance")
const analyticsGiftFrequencyEl = document.getElementById("analytics-gift-frequency")
const analyticsSegmentMatrixEl = document.getElementById("analytics-segment-matrix")

const deliveryGivingBySizeEl = document.getElementById("delivery-giving-by-size")
const deliveryActivityMixEl = document.getElementById("delivery-activity-mix")
const deliveryCombinedPrioritiesEl = document.getElementById("delivery-combined-priorities")
const deliveryTopStatesEl = document.getElementById("delivery-top-states")

let payload = null
let map = null
let markerLayer = null
let heatLayer = null
let legendControl = null
let currentLocations = []
let currentMetric = "donors"
let activePanel = "overview"

const chartPalette = [
  "#f5f5f5",
  "#36cbb3",
  "#d29b43",
  "#6f7782",
  "#5b606a",
  "#2a9d8f",
]

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const response = await fetch("./data/portal_analytics_data.json")
    if (!response.ok) {
      throw new Error(`Could not load portal payload (${response.status})`)
    }

    payload = await response.json()
    hydratePortal(payload)
  } catch (error) {
    dataFreshnessEl.textContent = error.message
    coverageNoteEl.textContent =
      "Run app/functions/portal_analytics_export.py to regenerate the client portal payload."
  }
})

function hydratePortal(data) {
  populateStateFilter(data.geography.stateSummary)
  bindControls()
  bindTabs()

  const generatedAt = new Date(data.overview.generatedAt)
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

function render() {
  if (!payload) {
    return
  }

  currentMetric = metricFilter.value
  currentLocations = getFilteredLocations()
  const renderData = buildRenderData(currentLocations)

  renderOverview()
  renderAnalytics()
  renderDelivery()
  updateRankings(renderData, currentMetric)
  updateCoverageNote(renderData)

  if (activePanel === "geography") {
    ensureMap()
    updateMap(currentLocations, currentMetric)
  }
}

function renderOverview() {
  const overview = payload.overview
  const concentration = payload.concentration.concentration
  const segmentSummary = payload.engagement.segmentSummary
  const sizeMix = payload.reporting.donorSizeTable
  const priorityStates = joinStatePerformance().slice(0, 6)

  overviewMetricsEl.innerHTML = [
    metricCard("Total donors", numberFormatter.format(overview.totalDonors), "Engagement summary across the donor base"),
    metricCard("Active rate", formatPercent(overview.activeRate), `${numberFormatter.format(overview.activeDonors)} currently active donors`),
    metricCard("Top 5% donation share", formatPercent(concentration.topSliceShare), `${numberFormatter.format(concentration.topSliceCount)} donors drive this share`),
    metricCard("Mapped locations", numberFormatter.format(overview.mappedLocations), `${numberFormatter.format(overview.statesCovered)} states covered in the geography layer`),
  ].join("")

  overviewSegmentsEl.innerHTML = `
    <div class="chart-layout">
      ${renderDonutChart({
        ariaLabel: "Active versus inactive donor distribution",
        centerValue: formatPercent(overview.activeRate),
        centerLabel: "active",
        segments: segmentSummary.map((segment, index) => ({
          label: segment.Segment,
          value: segment.donorCount,
          detail: `${formatCompactCurrency(segment.totalRaised)} raised`,
          color: chartPalette[index + 1],
        })),
      })}
      <div class="chart-side-list">
        ${segmentSummary
          .map(
            (segment) => `
              <article class="split-metric">
                <p class="split-metric__label">${segment.Segment}</p>
                <div class="split-metric__value">${numberFormatter.format(segment.donorCount)}</div>
                <p class="split-metric__meta">${formatCompactCurrency(segment.totalRaised)} raised</p>
                <p class="split-metric__meta">Avg gift ${formatCompactCurrency(segment.avgGift)}</p>
              </article>
            `
          )
          .join("")}
      </div>
    </div>
  `

  overviewConcentrationEl.innerHTML = `
    <div class="chart-layout">
      ${renderDonutChart({
        ariaLabel: "Top five percent donor concentration share",
        centerValue: formatPercent(concentration.topSliceShare),
        centerLabel: "top 5%",
        segments: [
          {
            label: "Top 5% donors",
            value: concentration.topSliceTotal,
            detail: formatCurrency(concentration.topSliceTotal),
            color: chartPalette[1],
          },
          {
            label: "Remaining donors",
            value: concentration.overallTotal - concentration.topSliceTotal,
            detail: formatCurrency(concentration.overallTotal - concentration.topSliceTotal),
            color: chartPalette[3],
          },
        ],
      })}
      <div class="chart-side-list">
        <article class="list-stack__hero">
          <div>
            <p class="eyebrow">Contribution share</p>
            <div class="list-stack__value">${formatPercent(concentration.topSliceShare)}</div>
          </div>
          <p class="muted">Top ${numberFormatter.format(concentration.topSliceCount)} donors account for ${formatCurrency(concentration.topSliceTotal)} of ${formatCurrency(concentration.overallTotal)}.</p>
        </article>
        ${payload.concentration.topDonors
          .slice(0, 4)
          .map(
            (donor, index) => `
              <article class="list-row">
                <span class="list-row__index">${index + 1}</span>
                <div class="list-row__copy">
                  <h3>${donor["Account ID"]}</h3>
                  <p>Top donor concentration slice</p>
                </div>
                <div class="list-row__value">${formatCurrency(donor.donationAmount)}</div>
              </article>
            `
          )
          .join("")}
      </div>
    </div>
  `

  overviewSizeMixEl.innerHTML = `
    <div class="chart-stack">
      ${renderColumnChart({
        ariaLabel: "Donor count by giving tier",
        rows: sizeMix.map((row, index) => ({
          label: compactCategoryLabel(row.category),
          value: row.count,
          valueLabel: numberFormatter.format(row.count),
          color: chartPalette[index + 1] || chartPalette[1],
        })),
      })}
      <div class="chart-legend chart-legend--stacked">
        ${sizeMix
          .map(
            (row, index) => `
              <div class="chart-legend__row">
                <span class="chart-dot" style="background:${chartPalette[index + 1] || chartPalette[1]}"></span>
                <span>${row.category}</span>
                <strong>${numberFormatter.format(row.count)}</strong>
              </div>
            `
          )
          .join("")}
      </div>
    </div>
  `

  overviewPriorityStatesEl.innerHTML = renderTable(
    ["State", "Active donors", "Total donations"],
    priorityStates.map((state) => [
      state.state,
      numberFormatter.format(state.activeDonors),
      formatCurrency(state.totalDonations),
    ])
  )
}

function renderAnalytics() {
  const engagement = payload.engagement
  const concentration = payload.concentration
  const reporting = payload.reporting

  analyticsKpiTableEl.innerHTML = renderTable(
    ["Segment", "Donors", "Total raised", "Avg gift", "Median gift", "Latest gift"],
    engagement.segmentSummary.map((segment) => [
      segment.Segment,
      numberFormatter.format(segment.donorCount),
      formatCurrency(segment.totalRaised),
      formatCurrency(segment.avgGift),
      formatCurrency(segment.medianGift),
      formatDisplayDate(segment.latestGift),
    ])
  )

  analyticsTopDonorsEl.innerHTML = concentration.topDonors
    .slice(0, 8)
    .map(
      (donor, index) => `
        <article class="list-row">
          <span class="list-row__index">${index + 1}</span>
          <div class="list-row__copy">
            <h3>${donor["Account ID"]}</h3>
            <p>Top donor by lifetime giving</p>
          </div>
          <div class="list-row__value">${formatCurrency(donor.donationAmount)}</div>
        </article>
      `
    )
    .join("")

  analyticsMonthlyPulseEl.innerHTML = `
    <div class="chart-stack">
      ${renderColumnChart({
        ariaLabel: "Monthly donation totals for the last twelve months",
        rows: concentration.monthlyTotal.map((month, index) => ({
          label: formatMonth(month.month),
          value: month.donationAmount,
          valueLabel: formatCompactCurrency(month.donationAmount),
          color: chartPalette[index % 2 === 0 ? 1 : 3],
        })),
      })}
      ${
        concentration.monthlySpikes.length
          ? `<p class="chart-note">Spike months: ${concentration.monthlySpikes
              .map((month) => formatMonth(month.month))
              .join(", ")}</p>`
          : `<p class="chart-note">No major monthly spikes crossed the current threshold in the export window.</p>`
      }
    </div>
  `

  const statePerformance = joinStatePerformance()
  analyticsStatePerformanceEl.innerHTML = `
    <div class="chart-table-stack">
      ${renderColumnChart({
        ariaLabel: "Top active states by donor count",
        rows: statePerformance.slice(0, 6).map((state, index) => ({
          label: state.state,
          value: state.activeDonors,
          valueLabel: numberFormatter.format(state.activeDonors),
          color: chartPalette[index + 1] || chartPalette[1],
        })),
      })}
      ${renderTable(
        ["State", "Donors", "Active donors", "Total donations"],
        statePerformance.map((state) => [
          state.state,
          numberFormatter.format(state.donorCount),
          numberFormatter.format(state.activeDonors),
          formatCurrency(state.totalDonations),
        ])
      )}
    </div>
  `

  analyticsGiftFrequencyEl.innerHTML = `
    <div class="chart-stack">
      ${renderColumnChart({
        ariaLabel: "Active donor gift frequency distribution",
        rows: engagement.giftFrequency
          .filter((row) => row.giftCount > 0)
          .slice(0, 8)
          .map((row, index) => ({
            label: `${row.giftCount}`,
            value: row.donorCount,
            valueLabel: numberFormatter.format(row.donorCount),
            color: chartPalette[index % chartPalette.length],
        })),
      })}
      <p class="chart-note">This cadence view shows how many active donors are giving repeatedly within the last 18 months.</p>
    </div>
  `

  const matrixColumns = Object.keys(reporting.crossTab[0] || {}).filter(
    (key) => key !== "sizeCategory"
  )
  analyticsSegmentMatrixEl.innerHTML = renderTable(
    ["Size", ...matrixColumns],
    reporting.crossTab.map((row) => [
      row.sizeCategory,
      ...matrixColumns.map((column) => numberFormatter.format(row[column] || 0)),
    ])
  )
}

function renderDelivery() {
  const reporting = payload.reporting
  const sizeCounts = new Map(reporting.donorSizeTable.map((row) => [row.category, row.count]))

  deliveryGivingBySizeEl.innerHTML = `
    <div class="chart-table-stack">
      ${renderColumnChart({
        ariaLabel: "Total donations by donor size",
        rows: reporting.givingBySize.map((row, index) => ({
          label: compactCategoryLabel(row.category),
          value: row.totalDonations,
          valueLabel: formatCompactCurrency(row.totalDonations),
          color: chartPalette[index + 1] || chartPalette[1],
        })),
      })}
      ${renderTable(
        ["Donor size", "Donors", "Total donations"],
        reporting.givingBySize.map((row) => [
          row.category,
          numberFormatter.format(sizeCounts.get(row.category) || 0),
          formatCurrency(row.totalDonations),
        ])
      )}
    </div>
  `

  deliveryActivityMixEl.innerHTML = renderDonutChart({
    ariaLabel: "Donor activity distribution",
    centerValue: numberFormatter.format(
      reporting.donorActivityTable.reduce((sum, row) => sum + row.count, 0)
    ),
    centerLabel: "donors",
    segments: reporting.donorActivityTable.map((row, index) => ({
      label: row.category,
      value: row.count,
      detail: `${numberFormatter.format(row.count)} donors`,
      color: chartPalette[index + 1] || chartPalette[1],
    })),
  })

  deliveryCombinedPrioritiesEl.innerHTML = reporting.combinedCategory
    .slice(0, 8)
    .map(
      (row, index) => `
        <article class="list-row">
          <span class="list-row__index">${index + 1}</span>
          <div class="list-row__copy">
            <h3>${row.category}</h3>
            <p>Most common combined segment</p>
          </div>
          <div class="list-row__value">${numberFormatter.format(row.count)}</div>
        </article>
      `
    )
    .join("")

  deliveryTopStatesEl.innerHTML = renderTable(
    ["State", "Donor count"],
    reporting.topStates.map((row) => [
      row.State,
      numberFormatter.format(row.donorCount),
    ])
  )
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

  return payload.geography.locations.filter((location) => {
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

function renderDonutChart({ ariaLabel, centerValue, centerLabel, segments }) {
  const validSegments = segments.filter((segment) => segment.value > 0)
  if (!validSegments.length) {
    return '<p class="muted">No chart segments available.</p>'
  }

  const total = validSegments.reduce((sum, segment) => sum + segment.value, 0)
  const radius = 48
  const circumference = 2 * Math.PI * radius
  let accumulated = 0

  const segmentMarkup = validSegments
    .map((segment) => {
      const length = (segment.value / total) * circumference
      const circle = `
        <circle
          cx="70"
          cy="70"
          r="${radius}"
          stroke="${segment.color}"
          stroke-width="18"
          stroke-dasharray="${length} ${circumference - length}"
          stroke-dashoffset="${-accumulated}"
        ></circle>
      `
      accumulated += length
      return circle
    })
    .join("")

  return `
    <div class="donut-chart" role="img" aria-label="${ariaLabel}">
      <svg viewBox="0 0 140 140">
        <g transform="rotate(-90 70 70)">
          <circle cx="70" cy="70" r="${radius}" stroke="rgba(255,255,255,0.08)" stroke-width="18"></circle>
          ${segmentMarkup}
        </g>
        <text x="70" y="66" text-anchor="middle" class="donut-chart__value">${centerValue}</text>
        <text x="70" y="85" text-anchor="middle" class="donut-chart__label">${centerLabel}</text>
      </svg>
      <div class="chart-legend">
        ${validSegments
          .map(
            (segment) => `
              <div class="chart-legend__row">
                <span class="chart-dot" style="background:${segment.color}"></span>
                <span>${segment.label}</span>
                <strong>${segment.detail || numberFormatter.format(segment.value)}</strong>
              </div>
            `
          )
          .join("")}
      </div>
    </div>
  `
}

function renderColumnChart({ ariaLabel, rows }) {
  const validRows = rows.filter((row) => row.value > 0)
  if (!validRows.length) {
    return '<p class="muted">No chart rows available.</p>'
  }

  const chartRows = validRows.slice(0, 8)
  const width = 420
  const height = 220
  const paddingTop = 18
  const paddingBottom = 46
  const paddingLeft = 10
  const usableHeight = height - paddingTop - paddingBottom
  const maxValue = Math.max(...chartRows.map((row) => row.value), 1)
  const barSlot = (width - paddingLeft * 2) / chartRows.length
  const barWidth = Math.min(34, barSlot * 0.58)

  const gridLines = [0.25, 0.5, 0.75].map((step) => {
    const y = paddingTop + usableHeight * step
    return `<line x1="${paddingLeft}" y1="${y}" x2="${width - paddingLeft}" y2="${y}" class="chart-grid-line"></line>`
  })

  const bars = chartRows
    .map((row, index) => {
      const x = paddingLeft + index * barSlot + (barSlot - barWidth) / 2
      const barHeight = Math.max(8, (row.value / maxValue) * usableHeight)
      const y = paddingTop + usableHeight - barHeight
      const textX = x + barWidth / 2
      return `
        <g>
          <rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" fill="${row.color}" class="chart-bar"></rect>
          <text x="${textX}" y="${y - 8}" text-anchor="middle" class="chart-bar__value">${row.valueLabel}</text>
          <text x="${textX}" y="${height - 14}" text-anchor="middle" class="chart-axis-label">${row.label}</text>
        </g>
      `
    })
    .join("")

  return `
    <div class="chart-block" role="img" aria-label="${ariaLabel}">
      <svg viewBox="0 0 ${width} ${height}" class="chart-svg">
        ${gridLines.join("")}
        ${bars}
      </svg>
    </div>
  `
}

function renderBarRows(rows) {
  if (!rows.length) {
    return '<p class="muted">No summary rows available.</p>'
  }

  const maxValue = Math.max(...rows.map((row) => row.value), 1)

  return rows
    .map(
      (row) => `
        <article class="bar-row">
          <div class="bar-row__header">
            <span>${row.label}</span>
            <span>${row.valueLabel}</span>
          </div>
          <div class="bar-row__track">
            <span class="bar-row__fill" style="width: ${(row.value / maxValue) * 100}%"></span>
          </div>
        </article>
      `
    )
    .join("")
}

function renderTable(headers, rows) {
  if (!rows.length) {
    return '<p class="muted">No table rows available.</p>'
  }

  return `
    <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>${headers.map((header) => `<th>${header}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `
}

function metricCard(label, value, detail) {
  return `
    <article class="metric-card">
      <p class="metric-card__label">${label}</p>
      <div class="metric-card__value">${value}</div>
      <p class="metric-card__detail">${detail}</p>
    </article>
  `
}

function joinStatePerformance() {
  const totalDonationsByState = new Map(
    payload.concentration.topStates.map((row) => [
      row.State,
      { donorCount: row.donorCount, totalDonations: row.totalDonations },
    ])
  )

  return payload.engagement.topActiveStates.map((row) => {
    const totalRow = totalDonationsByState.get(row.State) || {
      donorCount: 0,
      totalDonations: 0,
    }
    return {
      state: row.State,
      donorCount: totalRow.donorCount,
      activeDonors: row.activeDonors,
      totalDonations: totalRow.totalDonations,
    }
  })
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

function formatCompactCurrency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value)
}

function formatPercent(value) {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value)
}

function formatDisplayDate(value) {
  if (!value) {
    return "Unknown"
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

function formatMonth(value) {
  const [year, month] = value.split("-")
  const date = new Date(Number(year), Number(month) - 1, 1)
  return date.toLocaleDateString("en-US", {
    month: "short",
    year: "2-digit",
  })
}

function compactCategoryLabel(value) {
  return value
    .replace(" Donor", "")
    .replace("No Giving History", "No history")
}
