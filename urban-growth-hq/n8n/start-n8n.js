const { spawnSync, spawn } = require('child_process');
const fs = require('fs');

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

// Urban Growth is independent from Nexora: import only its dedicated workflow.
runN8n([
  'import:workflow',
  '--input=/opt/urban-growth/workflows/urban-growth-lead-intake.json',
]);

// n8n may assign/normalize IDs during import. Discover the actual stored ID instead
// of assuming the ID embedded in the source JSON, then publish that exact workflow.
const exportPath = '/tmp/urban-growth-workflows.json';
try { fs.unlinkSync(exportPath); } catch {}
runN8n(['export:workflow', '--all', `--output=${exportPath}`]);

let exported;
try {
  exported = JSON.parse(fs.readFileSync(exportPath, 'utf8'));
} catch (error) {
  console.error('Could not read exported n8n workflows:', error);
  process.exit(1);
}
const workflows = Array.isArray(exported) ? exported : (exported.data || exported.workflows || []);
const leadWorkflow = workflows.find((item) => item.name === 'Urban Growth HQ - Lead Intake');
if (!leadWorkflow?.id) {
  console.error('Urban Growth lead-intake workflow was not found after import; refusing to start without it.');
  process.exit(1);
}
runN8n(['publish:workflow', `--id=${leadWorkflow.id}`]);

// CLI publish writes to the database; starting n8n after publishing registers its webhook.
const child = spawn('n8n', ['start'], { stdio: 'inherit', env: process.env });
child.on('exit', code => process.exit(code ?? 1));
child.on('error', err => {
  console.error('Failed to start n8n:', err);
  process.exit(1);
});
