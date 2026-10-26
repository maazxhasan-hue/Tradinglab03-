const fs = require('fs');
const path = require('path');
const { spawnSync, spawn } = require('child_process');
const home = process.env.HOME || '/home/node';
const marker = path.join(home, '.n8n', 'urban-growth-lead-intake-imported');
fs.mkdirSync(path.dirname(marker), { recursive: true });
if (!fs.existsSync(marker)) {
  const imported = spawnSync('n8n', ['import:workflow', '--input=/opt/urban-growth/workflows/urban-growth-lead-intake.json'], { stdio: 'inherit' });
  if (imported.status !== 0) process.exit(imported.status || 1);
  fs.writeFileSync(marker, new Date().toISOString());
}
const child = spawn('n8n', ['start'], { stdio: 'inherit', env: process.env });
child.on('exit', code => process.exit(code ?? 1));
