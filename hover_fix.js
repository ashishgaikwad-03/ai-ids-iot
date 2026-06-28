const fs = require('fs');
const file = 'C:/PROJECT/AI-IDS-IoT-Network/3_Frontend_Dashboard/js/app.js';
let content = fs.readFileSync(file, 'utf8');

// 1. Remove the attack pins drawing block
const drawPinsRegex = /  \/\/ Attack event pins.*?prevHad=nowHas;\r?\n  \}\);/s;
if (drawPinsRegex.test(content)) {
    content = content.replace(drawPinsRegex, '');
    console.log('Removed draw pins block');
} else {
    console.log('Could not find draw pins block');
}

// 2. Rewrite hitTestPin
const hitTestRegex = /function hitTestPin\(e, canvas\) \{[\s\S]*?return null;\r?\n\}/;
const newHitTest = `function hitTestPin(e, canvas) {
  if (!STATE.chartLayout || STATE.chartLayout.n < 2) return null;
  const { PAD_L, cW, n, data, PAD_T, cH } = STATE.chartLayout;
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  
  if (mx < PAD_L || mx > PAD_L + cW || my < PAD_T || my > PAD_T + cH) return null;
  
  const idx = Math.round(((mx - PAD_L) / cW) * (n - 1));
  if (idx >= 0 && idx < n) {
    const d = data[idx];
    if ((d.attackPps || 0) > 0) {
      return {
        x: e.clientX,
        pinY: my,
        time: d.time,
        pps: d.rawPps || d.pps || 0,
        atkType: d.lastAttackType || 'Attack'
      };
    }
  }
  return null;
}`;

if (hitTestRegex.test(content)) {
    content = content.replace(hitTestRegex, newHitTest);
    console.log('Replaced hitTestPin');
} else {
    console.log('Could not find hitTestPin');
}

fs.writeFileSync(file, content, 'utf8');
console.log('Done');
