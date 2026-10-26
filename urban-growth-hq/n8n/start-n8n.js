const { spawnSync, spawn } = require('child_process');

function runN8n(args) {
  const result = spawnSync('n8n', args, { stdio: 'inherit', env: process.env });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status || 1);
}

// Render's free filesystem can be recreated, so import the source workflow on each boot.
// n8n 2.x imports workflows unpublished by default in single-instance mode; explicitly
// activate this one after import so the production webhook is registered.
runN8n([
  'import:workflow',
  '--input=/opt/urban-growth/workflows/urban-growth-lead-intake.json',
]);
runN8n(['update:workflow', '--id=urbanGrowthLeadIntake01', '--active=true']);

const child = spawn('n8n', ['start'], { stdio: 'inherit', env: process.env });
child.on('exit', code => process.exit(code ?? 1));
child.on('error', err => {
  console.error('Failed to start n8n:', err);
  process.exit(1);
});
