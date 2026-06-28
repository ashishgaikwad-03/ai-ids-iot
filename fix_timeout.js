const fs = require('fs');
const file = 'C:/PROJECT/AI-IDS-IoT-Network/3_Frontend_Dashboard/js/app.js';
let content = fs.readFileSync(file, 'utf8');
content = content.replace('now - d._lastHeartbeatMs > 45000', 'now - d._lastHeartbeatMs > 8000');
fs.writeFileSync(file, content, 'utf8');
console.log('Fixed 45000 timeout');
