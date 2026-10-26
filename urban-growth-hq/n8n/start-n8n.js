const { spawnSync, spawn } = require('child_process');

// Render's free filesystem and n8n database may be recreated independently.
// Import on every boot so the workflow cannot be skipped because of a stale marker.
const imported = spawnSync('n8n', [
  'import:workflow',
  '--input=/opt/urban-growth/workflows/urban-growth-lead-intake.json',
], { stdio: 'inherit', env: process.env });

if (imported.status !== 0) {
  process.exit(imported.status || 1);
}

const child = spawn('n8n', ['start'], { stdio: 'inherit', env: process.env });
child.on('exit', code => process.exit(code ?? 1));
