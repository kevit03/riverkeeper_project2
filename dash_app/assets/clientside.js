/* Clientside helpers — pie "grow in place" hover feedback.
 * Instead of using Plotly's `pull` (which moves the slice away from the pie),
 * we use CSS (see style.css: `.js-plotly-plot .slice:hover`) to brighten,
 * scale, and shadow the hovered slice. This callback just dims sibling
 * slices so the hovered one visually "pops" while staying attached.
 */

window.dash_clientside = window.dash_clientside || {};

window.dash_clientside.riverkeeper = {
    pullSlice: function (hoverData, currentFigure) {
        if (!currentFigure || !currentFigure.data || !currentFigure.data.length) {
            return window.dash_clientside.no_update;
        }
        const trace = currentFigure.data[0];
        if (!trace || !trace.labels) {
            return window.dash_clientside.no_update;
        }

        const n = trace.labels.length;
        let hovered = -1;
        if (hoverData && hoverData.points && hoverData.points.length) {
            const idx = hoverData.points[0].pointNumber;
            if (typeof idx === "number" && idx >= 0 && idx < n) {
                hovered = idx;
            }
        }

        // Build per-slice border widths: thicker white ring on hovered slice
        // so it reads as "larger" without actually detaching from the pie.
        const lineWidths = new Array(n).fill(3);
        if (hovered >= 0) {
            for (let i = 0; i < n; i++) {
                lineWidths[i] = i === hovered ? 6 : 2;
            }
        }

        const next = JSON.parse(JSON.stringify(currentFigure));
        next.data[0].pull = new Array(n).fill(0);
        next.data[0].marker = next.data[0].marker || {};
        next.data[0].marker.line = next.data[0].marker.line || {};
        next.data[0].marker.line.width = lineWidths;
        next.data[0].marker.line.color = "#FFFFFF";
        next.layout = next.layout || {};
        next.layout.transition = { duration: 250, easing: "cubic-in-out" };
        return next;
    }
};
