const fs = require('fs');
const file = 'C:/PROJECT/AI-IDS-IoT-Network/3_Frontend_Dashboard/js/app.js';
let content = fs.readFileSync(file, 'utf8');

const newFunction = `function drawTrafficChart() {
  const canvas = document.getElementById('traffic-chart');
  if (!canvas) return;

  const dpr  = window.devicePixelRatio || 1;
  const rect = canvas.parentElement.getBoundingClientRect();
  const W = Math.max(rect.width  || 500, 200);
  const H = Math.max(rect.height || 180, 120);

  canvas.style.width  = W + 'px';
  canvas.style.height = H + 'px';
  canvas.width  = W * dpr;
  canvas.height = H * dpr;

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, W, H);

  const data = STATE.trafficHistory;

  // Background
  const bgGrad = ctx.createLinearGradient(0, 0, 0, H);
  bgGrad.addColorStop(0, '#0a0f1d');
  bgGrad.addColorStop(1, '#050810');
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, W, H);

  // Idle placeholder
  if (data.length < 2) {
    const cx = W / 2, cy = H / 2;
    ctx.shadowColor = '#00f0ff'; ctx.shadowBlur = 15;
    ctx.beginPath(); ctx.arc(cx, cy - 20, 10, 0, Math.PI * 2);
    ctx.fillStyle = '#00f0ff'; ctx.fill();
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#e2e8f0'; ctx.font = '600 13px "Roboto Mono", monospace'; ctx.textAlign = 'center';
    ctx.fillText('ESTABLISHING SECURE CONNECTION...', cx, cy + 15);
    return;
  }

  const PAD_L = 42, PAD_R = 12, PAD_T = 20, PAD_B = 30;
  const cW = W - PAD_L - PAD_R;
  const cH = H - PAD_T - PAD_B;
  const n  = data.length;

  // Smart Y-axis
  const atkVals   = data.map(d => d.attackPps || 0);
  const totalVals = data.map((d, i) => atkVals[i] > 0 ? 0 : (d.pps || 0));
  const allVals   = [...totalVals, ...atkVals];
  const sorted    = [...allVals].sort((a,b) => a-b);
  const p95       = sorted[Math.floor(sorted.length * 0.95)] || 0;
  const rawYMax   = Math.max(p95 * 1.4, 5);
  const niceMax   = v => { if(v<=0) return 5; const m=Math.pow(10,Math.floor(Math.log10(v))); return Math.ceil(v/m)*m*(v/m<2?2:1); };
  const yMax      = niceMax(rawYMax);

  const toX = i   => PAD_L + (n > 1 ? (i / (n - 1)) * cW : cW / 2);
  const toY = val => PAD_T + cH - Math.min(val / yMax, 1) * cH;

  STATE.chartLayout = { PAD_L, PAD_R, PAD_T, PAD_B, cW, cH, W, H, n, data };

  // Cyber Grid
  ctx.lineWidth = 1;
  ctx.strokeStyle = 'rgba(0, 240, 255, 0.05)';
  ctx.beginPath();
  for (let i = 0; i <= cW; i += 40) {
    ctx.moveTo(PAD_L + i, PAD_T); ctx.lineTo(PAD_L + i, PAD_T + cH);
  }
  for (let i = 0; i <= cH; i += 30) {
    ctx.moveTo(PAD_L, PAD_T + i); ctx.lineTo(PAD_L + cW, PAD_T + i);
  }
  ctx.stroke();

  // Grid lines + Y labels
  const STEPS = 4;
  ctx.font = '10px "Roboto Mono", monospace';
  for (let i = 0; i <= STEPS; i++) {
    const val = (yMax / STEPS) * (STEPS - i);
    const y   = PAD_T + (cH / STEPS) * i;
    ctx.strokeStyle = i === STEPS ? 'rgba(0, 240, 255, 0.3)' : 'rgba(0, 240, 255, 0.1)';
    ctx.setLineDash(i === STEPS ? [] : [2, 4]);
    ctx.beginPath(); ctx.moveTo(PAD_L,y); ctx.lineTo(PAD_L+cW,y); ctx.stroke();
    ctx.fillStyle = '#00f0ff'; ctx.textAlign='right'; ctx.globalAlpha = 0.7;
    ctx.fillText(Math.round(val)||'0', PAD_L-8, y+3);
    ctx.globalAlpha = 1.0;
  }
  ctx.setLineDash([]);
  ctx.save(); ctx.translate(11, PAD_T+cH/2); ctx.rotate(-Math.PI/2);
  ctx.fillStyle='rgba(0,240,255,0.5)'; ctx.font='bold 9px "Roboto Mono", monospace'; ctx.textAlign='center';
  ctx.fillText('PKT/S',0,0); ctx.restore();

  // Blue fill: TOTAL pps
  ctx.beginPath();
  ctx.moveTo(toX(0), toY(totalVals[0]));
  for (let i=1;i<n;i++) {
    const x0=toX(i-1),y0=toY(totalVals[i-1]),x1=toX(i),y1=toY(totalVals[i]);
    ctx.bezierCurveTo((x0+x1)/2,y0,(x0+x1)/2,y1,x1,y1);
  }
  ctx.lineTo(toX(n-1), PAD_T+cH); ctx.lineTo(toX(0), PAD_T+cH); ctx.closePath();
  const blueGrad = ctx.createLinearGradient(0,PAD_T,0,PAD_T+cH);
  blueGrad.addColorStop(0,'rgba(0,240,255,0.4)');
  blueGrad.addColorStop(1,'rgba(0,240,255,0.01)');
  ctx.fillStyle=blueGrad; ctx.fill();

  // Red fill: ATTACK pps
  const hasAnyAttack = atkVals.some(v => v > 0);
  if (hasAnyAttack) {
    ctx.beginPath();
    ctx.moveTo(toX(0), toY(atkVals[0]));
    for (let i=1;i<n;i++) {
      const x0=toX(i-1),y0=toY(atkVals[i-1]),x1=toX(i),y1=toY(atkVals[i]);
      ctx.bezierCurveTo((x0+x1)/2,y0,(x0+x1)/2,y1,x1,y1);
    }
    ctx.lineTo(toX(n-1), PAD_T+cH); ctx.lineTo(toX(0), PAD_T+cH); ctx.closePath();
    const redGrad = ctx.createLinearGradient(0,PAD_T,0,PAD_T+cH);
    redGrad.addColorStop(0,'rgba(255,0,85,0.6)');
    redGrad.addColorStop(1,'rgba(255,0,85,0.02)');
    ctx.fillStyle=redGrad; ctx.fill();

    // Red stroke
    ctx.beginPath();
    ctx.moveTo(toX(0), toY(atkVals[0]));
    for (let i=1;i<n;i++) {
      const x0=toX(i-1),y0=toY(atkVals[i-1]),x1=toX(i),y1=toY(atkVals[i]);
      ctx.bezierCurveTo((x0+x1)/2,y0,(x0+x1)/2,y1,x1,y1);
    }
    ctx.shadowColor = '#ff0055'; ctx.shadowBlur = 12;
    ctx.strokeStyle='#ff0055'; ctx.lineWidth=2.5; ctx.stroke();
    ctx.shadowBlur = 0;
  }

  // Blue stroke
  ctx.beginPath();
  ctx.moveTo(toX(0), toY(totalVals[0]));
  for (let i=1;i<n;i++) {
    const x0=toX(i-1),y0=toY(totalVals[i-1]),x1=toX(i),y1=toY(totalVals[i]);
    ctx.bezierCurveTo((x0+x1)/2,y0,(x0+x1)/2,y1,x1,y1);
  }
  ctx.shadowColor = '#00f0ff'; ctx.shadowBlur = 10;
  ctx.strokeStyle='#00f0ff'; ctx.lineWidth=2.5; ctx.stroke();
  ctx.shadowBlur = 0;

  // Live dot pulsing
  const lx=toX(n-1), ly=toY(totalVals[n-1]);
  const pulse = (Math.sin(Date.now() / 200) + 1) / 2;
  ctx.beginPath(); ctx.arc(lx,ly, 4 + pulse * 4, 0, Math.PI*2);
  ctx.fillStyle='rgba(0,240,255,' + (1 - pulse) + ')'; ctx.fill();
  
  ctx.beginPath(); ctx.arc(lx,ly, 4, 0, Math.PI*2);
  ctx.fillStyle='#fff'; ctx.fill();
  ctx.shadowColor='#00f0ff'; ctx.shadowBlur=8; ctx.stroke();
  ctx.shadowBlur=0;

  // Attack event pins
  STATE.chartPins=[];
  let prevHad = data.length > 0 && (data[0].attackPps||0) > 0;
  data.forEach((d,i) => {
    const nowHas = (d.attackPps||0) > 0;
    if (nowHas && !prevHad) {
      const x=toX(i);
      const label=(d.lastAttackType||'Attack').replace(/_/g,' ');
      const shortLbl=label.split(/[-\\s]/)[0]||label;
      ctx.save();
      
      // Vertical laser line
      ctx.beginPath(); ctx.moveTo(x, PAD_T); ctx.lineTo(x, PAD_T+cH);
      ctx.strokeStyle='rgba(255,0,85,0.4)'; ctx.setLineDash([4,4]); ctx.stroke();
      ctx.setLineDash([]);
      
      // Base crosshair
      ctx.beginPath(); ctx.arc(x,PAD_T+cH, 4, 0, Math.PI*2);
      ctx.fillStyle='#050810'; ctx.fill();
      ctx.strokeStyle='#ff0055'; ctx.lineWidth=2; ctx.stroke();
      
      ctx.beginPath(); ctx.moveTo(x-8, PAD_T+cH); ctx.lineTo(x+8, PAD_T+cH); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(x, PAD_T+cH-8); ctx.lineTo(x, PAD_T+cH+8); ctx.stroke();

      // Label
      ctx.translate(x+14,PAD_T+cH - 12); ctx.rotate(-Math.PI/2);
      ctx.font='bold 10px "Roboto Mono", monospace'; ctx.textAlign='center';
      ctx.shadowColor='#ff0055'; ctx.shadowBlur=8;
      ctx.fillStyle='#ff0055'; ctx.fillText(shortLbl.toUpperCase(),0,0);
      ctx.restore();
      
      STATE.chartPins.push({ x, pinY:PAD_T+cH, lineTop:PAD_T, lineBot:PAD_T+cH,
        hitR:16, time:d.time, pps:d.rawPps||d.pps||0, atkType:d.lastAttackType||'Attack', idx:i });
    }
    prevHad=nowHas;
  });

  // X-axis labels
  ctx.fillStyle='#64748b'; ctx.font='10px "Roboto Mono", monospace'; ctx.textAlign='center';
  const step=Math.max(1,Math.floor(n/6));
  for (let i=0;i<n;i+=step) ctx.fillText(data[i].time, toX(i), PAD_T+cH+16);
  if (n>1) ctx.fillText(data[n-1].time, toX(n-1), PAD_T+cH+16);
}
`;

const startIndex = content.indexOf('function drawTrafficChart() {');
const endIndex = content.indexOf('function initChartClick() {');

if (startIndex !== -1 && endIndex !== -1) {
    // Find the comment right before initChartClick
    const prevBlock = content.substring(startIndex, endIndex);
    const lastCommentIdx = prevBlock.lastIndexOf('//');
    
    let replacement = newFunction + '\n\n';
    if (lastCommentIdx !== -1) {
        replacement += prevBlock.substring(lastCommentIdx);
    }
    
    content = content.substring(0, startIndex) + replacement + content.substring(endIndex);
    fs.writeFileSync(file, content, 'utf8');
    console.log('Successfully replaced drawTrafficChart block via absolute indices');
} else {
    console.log('Could not find start or end bounds');
}
