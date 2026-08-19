/*
 * Minimal two-bar comparison chart, drawn on canvas. No charting library:
 * every chart in this app compares exactly two named options (buy/lease,
 * pay-off/invest), so a small custom renderer is simpler than pulling in a
 * dependency for one chart type.
 *
 * Mark spec: thin bars with rounded data-ends anchored to the baseline,
 * a hairline baseline, and a direct dollar label above each bar. The
 * "better" option gets the status-good color plus a text label -- color
 * never carries that meaning alone.
 */

function drawComparisonChart(canvas, bars) {
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const cssWidth = canvas.clientWidth || 420;
  const cssHeight = 220;

  canvas.width = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  canvas.style.height = `${cssHeight}px`;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, cssWidth, cssHeight);

  const styles = getComputedStyle(document.body);
  const neutral = styles.getPropertyValue("--series-1").trim();
  const good = styles.getPropertyValue("--status-good").trim();
  const ink = styles.getPropertyValue("--text-primary").trim();
  const mutedInk = styles.getPropertyValue("--text-muted").trim();
  const baselineColor = styles.getPropertyValue("--baseline").trim();

  const values = bars.map((b) => b.value);
  const maxValue = Math.max(...values, 1);

  const padding = { top: 32, bottom: 36, left: 16, right: 16 };
  const plotHeight = cssHeight - padding.top - padding.bottom;
  const gap = 40;
  const barWidth = (cssWidth - padding.left - padding.right - gap * (bars.length - 1)) / bars.length;
  const baselineY = cssHeight - padding.bottom;

  // Baseline
  ctx.strokeStyle = baselineColor;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding.left, baselineY + 0.5);
  ctx.lineTo(cssWidth - padding.right, baselineY + 0.5);
  ctx.stroke();

  bars.forEach((bar, i) => {
    const x = padding.left + i * (barWidth + gap);
    const barHeight = Math.max((bar.value / maxValue) * plotHeight, 2);
    const y = baselineY - barHeight;
    const radius = Math.min(6, barWidth / 2);

    ctx.fillStyle = bar.highlight ? good : neutral;
    ctx.beginPath();
    ctx.moveTo(x, baselineY);
    ctx.lineTo(x, y + radius);
    ctx.arcTo(x, y, x + radius, y, radius);
    ctx.lineTo(x + barWidth - radius, y);
    ctx.arcTo(x + barWidth, y, x + barWidth, y + radius, radius);
    ctx.lineTo(x + barWidth, baselineY);
    ctx.closePath();
    ctx.fill();

    // Value label, direct on the mark.
    ctx.fillStyle = ink;
    ctx.font = "600 13px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "center";
    const valueLabel = `$${Math.round(bar.value).toLocaleString()}`;
    ctx.fillText(valueLabel, x + barWidth / 2, y - 10);

    // Category label below the baseline.
    ctx.fillStyle = mutedInk;
    ctx.font = "500 12px system-ui, -apple-system, sans-serif";
    const categoryLabel = bar.highlight ? `${bar.label} ✓ ${bar.highlightLabel || "better"}` : bar.label;
    ctx.fillText(categoryLabel, x + barWidth / 2, baselineY + 20);
  });
}
