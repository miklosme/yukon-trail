import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {openingJournal,observedOpening} from '../web/rules/opening.ts';
import {win16EditText} from '../web/platform/text.ts';
if (!process.argv[2]) throw new Error('Pass prepared original journal.json');
const assets=JSON.parse(readFileSync(process.argv[2], 'utf8'));
// Source CSTR504 strings + original004 paragraphs; invisible arrival trailing
// space corrected against the original event0 instruction output, not pixels.
const expected='<><><><><><><><><><><><><><><><><><><>\r\n'+
  'This journal is the property of seattle\r\n'+
  '<><><><><><><><><><><><><><><><><><><>\r\n\r\n'+
  'August 23, 1897. Arrived at Seattle. \r\n\r\n'+
  'August 23, 1897. Seattle. We have:\r\n      0 pounds of food\r\n      $350 in cash';
assert.equal(openingJournal(assets,'seattle'),expected);
// Exact original event0→event4 output, independently executed by journal worker.
// Header and the later UI WM_CHAR20 request are outside this byte comparison.
const native=JSON.parse(readFileSync(new URL('../docs/journal-status-recovery-evidence.json',import.meta.url), 'utf8'));
const tail=Buffer.from(expected.slice(expected.indexOf('August 23')),'latin1');
assert.equal(tail.toString('hex'),native.capture094.original_first_event4.text_hex);
assert.equal(createHash('sha256').update(tail).digest('hex'),'6bce15cb4e07d7910fa5869e22e70c5cadb16b0fccc159304387e5c4d2de6220');
assert.deepEqual(observedOpening,{day:23,month:8,year:1897,cash:350,food:0});
assert.equal(win16EditText('first\nsecond\r\nthird'),'first\r\nsecond\r\nthird');
assert.throws(()=>win16EditText('🙂'),TypeError);
assert.throws(()=>win16EditText('x'.repeat(0x2800)),RangeError);
assert.throws(()=>openingJournal(assets,''),RangeError);
console.log('Opening visible state/text matches independently recorded original004; no hidden-state initialization claim');
