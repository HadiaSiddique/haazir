/* Haazir illustrations: hand-made flat SVG (no external images, no people/patients). */
(function () {
  "use strict";
  const T = "#0b6e69", T2 = "#14918a", TL = "#d7efed", R = "#e53935", W = "#ffffff", G = "#3aa66b", S = "#f4f8f8", Y = "#ffcf5c";
  const cross = (x, y, s, c) => `<rect x="${x - s / 6}" y="${y - s / 2}" width="${s / 3}" height="${s}" rx="${s / 12}" fill="${c}"/><rect x="${x - s / 2}" y="${y - s / 6}" width="${s}" height="${s / 3}" rx="${s / 12}" fill="${c}"/>`;
  const tree = (x, y, s) => `<rect x="${x - 3}" y="${y - s * 0.35}" width="6" height="${s * 0.35}" fill="#7a5a3a"/><circle cx="${x}" cy="${y - s * 0.55}" r="${s * 0.32}" fill="${G}"/><circle cx="${x - s * 0.18}" cy="${y - s * 0.45}" r="${s * 0.22}" fill="#48b97a"/>`;
  const windows = (x0, y0, cols, rows, w, h, gx, gy) => {
    let o = "";
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) o += `<rect x="${x0 + c * (w + gx)}" y="${y0 + r * (h + gy)}" width="${w}" height="${h}" rx="2" fill="${(r + c) % 3 === 0 ? Y : "#bfe3f2"}"/>`;
    return o;
  };
  const cloud = (x, y, s) => `<g fill="${W}" opacity=".9"><ellipse cx="${x}" cy="${y}" rx="${s}" ry="${s * 0.45}"/><ellipse cx="${x - s * 0.6}" cy="${y + 4}" rx="${s * 0.6}" ry="${s * 0.35}"/><ellipse cx="${x + s * 0.6}" cy="${y + 4}" rx="${s * 0.6}" ry="${s * 0.35}"/></g>`;

  const hospital = (x, y, s) => `<g transform="translate(${x},${y}) scale(${s})">
    <rect x="0" y="40" width="180" height="150" rx="6" fill="${W}" stroke="${T}" stroke-width="3"/>
    <rect x="55" y="0" width="70" height="70" rx="6" fill="${W}" stroke="${T}" stroke-width="3"/>${cross(90, 35, 40, R)}
    ${windows(14, 58, 6, 3, 18, 18, 9, 14)}
    <rect x="70" y="140" width="40" height="50" rx="3" fill="${T}"/><rect x="88" y="140" width="4" height="50" fill="${T2}"/>
    <rect x="-6" y="186" width="192" height="8" rx="3" fill="${T2}"/>
    <rect x="62" y="116" width="56" height="14" rx="3" fill="${T}"/><text x="90" y="127" text-anchor="middle" font-family="Inter,sans-serif" font-size="10" font-weight="800" fill="${W}">HOSPITAL</text></g>`;
  const pharmacy = (x, y, s) => `<g transform="translate(${x},${y}) scale(${s})">
    <rect x="0" y="30" width="110" height="90" rx="6" fill="${W}" stroke="${T}" stroke-width="3"/>
    <path d="M-6 34 L55 0 L116 34 Z" fill="${T2}"/>
    <rect x="12" y="44" width="86" height="16" rx="3" fill="${G}"/><text x="55" y="56" text-anchor="middle" font-family="Inter,sans-serif" font-size="10" font-weight="800" fill="${W}">PHARMACY</text>
    <rect x="12" y="68" width="40" height="30" rx="3" fill="#bfe3f2"/><rect x="62" y="68" width="34" height="52" rx="3" fill="${T}"/>
    <g transform="translate(22,78) rotate(-30)"><rect width="22" height="10" rx="5" fill="${R}"/><rect x="11" width="11" height="10" rx="5" fill="${W}"/></g>
    ${cross(98, 18, 18, G)}</g>`;
  const bloodbank = (x, y, s) => `<g transform="translate(${x},${y}) scale(${s})">
    <rect x="0" y="26" width="90" height="80" rx="6" fill="${W}" stroke="${T}" stroke-width="3"/>
    <path d="M45 30 C45 30 26 52 26 64 A19 19 0 0 0 64 64 C64 52 45 30 45 30 Z" fill="${R}"/>${cross(45, 66, 14, W)}
    <rect x="30" y="86" width="30" height="20" rx="3" fill="${T}"/><rect x="10" y="10" width="70" height="16" rx="4" fill="${R}"/>
    <text x="45" y="22" text-anchor="middle" font-family="Inter,sans-serif" font-size="9" font-weight="800" fill="${W}">BLOOD BANK</text></g>`;
  const ambulance = (x, y, s) => `<g transform="translate(${x},${y}) scale(${s})">
    <rect x="0" y="10" width="110" height="52" rx="8" fill="${W}" stroke="${T}" stroke-width="3"/>
    <path d="M110 24 H138 L156 44 V62 H110 Z" fill="${W}" stroke="${T}" stroke-width="3" stroke-linejoin="round"/>
    <path d="M116 30 H136 L148 44 H116 Z" fill="#bfe3f2"/>
    <rect x="0" y="40" width="156" height="6" fill="${R}"/>${cross(52, 28, 22, R)}
    <rect x="40" y="0" width="22" height="10" rx="3" fill="${R}"/><rect x="40" y="0" width="11" height="10" rx="3" fill="#4fa3ff"/>
    <circle cx="32" cy="64" r="13" fill="#263238"/><circle cx="32" cy="64" r="5" fill="#cfd8dc"/>
    <circle cx="128" cy="64" r="13" fill="#263238"/><circle cx="128" cy="64" r="5" fill="#cfd8dc"/></g>`;

  // wide street scene for the home page
  const scene = `<svg viewBox="0 0 1200 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Illustration of a Lahore street with a hospital, pharmacy, blood bank and ambulance" preserveAspectRatio="xMidYMid slice">
    <defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e3f4f2"/><stop offset="1" stop-color="#f6fbfb"/></linearGradient></defs>
    <rect width="1200" height="230" fill="url(#sky)"/>
    ${cloud(150, 40, 34)}${cloud(620, 30, 28)}${cloud(1040, 50, 36)}
    <circle cx="1120" cy="42" r="20" fill="${Y}" opacity=".85"/>
    <path d="M0 150 Q 150 120 300 145 T 600 140 T 900 138 T 1200 142 V230 H0 Z" fill="${TL}"/>
    ${tree(60, 195, 70)}${tree(110, 198, 54)}${hospital(150, 6, 0.98)}${tree(370, 196, 66)}
    ${pharmacy(420, 76, 1)}${tree(560, 198, 58)}${bloodbank(600, 92, 1)}${tree(720, 196, 62)}
    <rect x="0" y="198" width="1200" height="32" fill="#cfd8dc"/><rect x="0" y="212" width="1200" height="3" fill="${W}" stroke-dasharray="26 18" stroke="${W}"/>
    ${ambulance(800, 140, 0.95)}${tree(1010, 196, 66)}${tree(1070, 198, 50)}${hospital(1100, 70, 0.55)}
  </svg>`;

  const spot = (inner, vb) => `<svg viewBox="${vb || "0 0 200 140"}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect width="100%" height="100%" rx="14" fill="${S}"/>${inner}</svg>`;
  window.HAAZIR_ART = {
    scene,
    hospital: spot(`${tree(22, 132, 40)}${hospital(30, 6, 0.66)}${tree(178, 132, 40)}`),
    pharmacy: spot(`${tree(30, 132, 40)}${pharmacy(45, 10, 1)}${tree(175, 132, 40)}`),
    bloodbank: spot(`${tree(32, 132, 40)}${bloodbank(55, 12, 1.05)}${tree(170, 132, 40)}`),
    ambulance: spot(`<rect x="0" y="112" width="200" height="28" fill="#cfd8dc"/>${ambulance(22, 36, 1)}`),
    phone: spot(`<rect x="70" y="14" width="60" height="112" rx="10" fill="${T}"/><rect x="76" y="26" width="48" height="84" rx="4" fill="${W}"/>
      <rect x="82" y="34" width="36" height="10" rx="5" fill="${TL}"/><rect x="82" y="50" width="30" height="10" rx="5" fill="${G}" opacity=".7"/><rect x="82" y="66" width="36" height="10" rx="5" fill="${TL}"/>
      <rect x="82" y="82" width="24" height="10" rx="5" fill="${G}" opacity=".7"/><circle cx="100" cy="118" r="3" fill="${W}"/>`),
    search: spot(`<rect x="30" y="40" width="140" height="34" rx="17" fill="${W}" stroke="${T}" stroke-width="3"/><circle cx="52" cy="57" r="8" fill="none" stroke="${T}" stroke-width="3"/>
      <path d="M58 63 L64 69" stroke="${T}" stroke-width="3" stroke-linecap="round"/><rect x="72" y="52" width="70" height="10" rx="5" fill="${TL}"/>
      <rect x="50" y="88" width="100" height="10" rx="5" fill="${R}" opacity=".85"/><rect x="62" y="104" width="76" height="8" rx="4" fill="${TL}"/>`),
    pin: spot(`<path d="M0 105 Q 60 85 120 100 T 200 96 V140 H0 Z" fill="${TL}"/><path d="M100 18 C78 18 64 34 64 52 C64 78 100 108 100 108 C100 108 136 78 136 52 C136 34 122 18 100 18 Z" fill="${T}"/>
      <circle cx="100" cy="52" r="14" fill="${W}"/>${cross(100, 52, 14, R)}`),
  };
})();
