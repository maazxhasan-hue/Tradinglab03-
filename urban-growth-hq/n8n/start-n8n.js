const { spawnSync, spawn } = require('child_process');

function runN8n(args) {
  const result = spawnSync('n8n', args, { stdio: 'inherit', env: process.env });
  if (result.error) {
    console.error('Could not run n8n command:', result.error);
    process.exit(1);
  }
  if (result.status !== 0) {
    console.error('n8n command failed:', args.join(' '));
    process.exit(result.status || 1);
  }
}

// The service's free filesystem may be recreated. Restore the versioned workflow on boot.
// Imports default to draft; n8n 2.x uses publish:workflow to enable production triggers.
runN8n([
  'import:workflow',
  '--input=/opt/urban-growth/workflows/urban-growth-lead-intake.json',
]);
runN8n(['publish:workflow', '--id=urbanGrowthLeadIntake01']);

const child = spawn('n8n', ['start'], { stdio: 'inherit', env: process.env });
child.on('exit', code => process.exit(code ?? 1));
child.on('error', err => {
  console.error('Failed to start n8n:', err);
  process.exit(1);
});
