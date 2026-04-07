export default eventHandler((event) => {
  setHeader(event, "content-type", "image/svg+xml");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="Trekky">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a" />
      <stop offset="100%" stop-color="#0369a1" />
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)" />
  <circle cx="1020" cy="120" r="140" fill="rgba(255,255,255,0.12)" />
  <circle cx="180" cy="540" r="220" fill="rgba(255,255,255,0.08)" />
  <text x="96" y="280" font-family="Arial, sans-serif" font-size="92" font-weight="700" fill="#ffffff">Trekky</text>
  <text x="96" y="360" font-family="Arial, sans-serif" font-size="34" fill="#dbeafe">Chia se dam me, trai nghiem va goc nhin rieng</text>
</svg>`;
});
