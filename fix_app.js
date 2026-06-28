const fs = require('fs');
const file = 'C:/PROJECT/AI-IDS-IoT-Network/3_Frontend_Dashboard/js/app.js';
let content = fs.readFileSync(file, 'utf8');

// The new correct attack event pins block
const newPins = `  // Attack event pins (vertical dashed line + label)
  STATE.chartPins=[];
  let prevHad = data.length > 0 && (data[0].attackPps||0) > 0;
  data.forEach((d,i) => {
    const nowHas = (d.attackPps||0) > 0;
    if (nowHas && !prevHad) {
      const x=toX(i);
      const label=(d.lastAttackType||'Attack').replace(/_/g,' ');
      const shortLbl=label.split(/[-\\s]/)[0]||label;
      ctx.save();
      ctx.beginPath(); ctx.arc(x,PAD_T+cH,4,0,Math.PI*2);
      ctx.fillStyle='#dc2626'; ctx.fill();
      ctx.strokeStyle='#fff'; ctx.lineWidth=1.2; ctx.stroke();
      ctx.translate(x+10,PAD_T+cH - 8); ctx.rotate(-Math.PI/2);
      ctx.font='bold 9px Inter,sans-serif'; ctx.textAlign='center';
      ctx.fillStyle='#dc2626'; ctx.fillText(shortLbl,0,0);
      ctx.restore();
      STATE.chartPins.push({ x, pinY:PAD_T+cH, lineTop:PAD_T, lineBot:PAD_T+cH,
        hitR:16, time:d.time, pps:d.rawPps||d.pps||0, atkType:d.lastAttackType||'Attack', idx:i });
    }
    prevHad=nowHas;
  });`;

// We just replace all occurrences of the pins block.
// And remove any duplicate one.
const regex = /  \/\/ .?.? Attack event pins.*?\n  \}\);/gs;

let matches = content.match(regex);
console.log("Found matches: ", matches ? matches.length : 0);

if (matches && matches.length > 0) {
    // Replace all occurrences with empty string, then add newPins at the end of the function.
    content = content.replace(regex, '');
    
    // Now insert newPins right before the X-axis labels
    const xLabelsRegex = /  \/\/ .?.? X-axis labels/;
    if (xLabelsRegex.test(content)) {
        content = content.replace(xLabelsRegex, newPins + '\n\n' + '  // ?? X-axis labels ??');
        fs.writeFileSync(file, content, 'utf8');
        console.log('Successfully replaced pins block');
    } else {
        console.log('Could not find X-axis labels to insert before.');
    }
} else {
    console.log('Regex did not match pins block');
}
