// Run every original-oracle check that needs only versioned evidence in docs/.
// Checks that need ignored local inputs (prepared asset packages, original
// saves, the pinned emulators source) are listed in docs/PORT-RUN.md and run
// individually with their arguments. Works under `bun` or `node` (>=23).
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const selfContained = [
  'countdown-oracle.ts',
  'seaday-oracle.ts',
  'seaweather-oracle.ts',
  'seaday-block-oracle.ts',
  'seamessage-oracle.ts',
  'seaday-combined-oracle.ts',
  'ticket-oracle.ts',
  'timers-oracle.ts',
  'voyage-oracle.ts',
  'test_browser_calendar.ts',
  'test_browser_indexed.ts',
  'test_browser_initial.ts',
  'test_browser_journal_status.ts',
  'test_browser_navigation.ts',
  'test_browser_scene_resources.ts',
  'test_browser_seattle.ts',
  'test_browser_seattle_conditions.ts',
  'test_journal_edit_text.ts',
  'test_opening_journal_projection.ts',
  'test_selected_assets.ts',
];

let failures = 0;
for (const name of selfContained) {
  const script = fileURLToPath(new URL(name, import.meta.url));
  const result = spawnSync(process.execPath, [script], {stdio: 'inherit'});
  if (result.status !== 0) { failures++; console.error(`FAILED: ${name}`); }
}
console.log(`${selfContained.length - failures}/${selfContained.length} self-contained oracle checks passed`);
process.exit(failures ? 1 : 0);
