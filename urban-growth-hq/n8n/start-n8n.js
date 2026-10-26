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

// Urban Growth must remain independent from Nexora. Restore only its own workflow.
// n8n CLI commands run before the server starts; publish the workflow, then start n8n.
for (const workflow of [
  'urban-growth-lead-intake.json',
]) {
  runN8n([
    'import:workflow',
    `--input=/opt/urban-growth/workflows/${workflow}`,
  ]);
}

runN8n(['publish:workflow', '--id=urbanGrowthLeadIntake01']);
// The supported publish command activates the published workflow; avoid the deprecated update command.

const child = spawn('n8n', ['start'], { stdio: 'inherit', env: process.env });
child.on('exit', code => process.exit(code ?? 1));
child.on('error', err => {
  console.error('Failed to start n8n:', err);
  process.exit(1);
});
