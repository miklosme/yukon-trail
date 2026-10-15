// These are platform adapter checks, not a browser or original-game playtest.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {keyCode,mouseButton,mousePoint,rgbaFrame,verifiedFile} from '../web/emulation-trial/contracts.ts';
const sourceRoot=process.argv[2];
if (!sourceRoot) throw new Error('Pass pinned emulators source directory');
const keys=readFileSync(sourceRoot+'/src/keys.ts','utf8');
const expected=new Map([...keys.matchAll(/public KBD_(\w+) = (\d+);/g)].map(m=>[m[1],Number(m[2])]));
for(const letter of 'abcdefghijklmnopqrstuvwxyz') assert.equal(keyCode('Key'+letter.toUpperCase()),expected.get(letter));
for(let i=0;i<10;i++) {assert.equal(keyCode('Digit'+i),expected.get(String(i)));assert.equal(keyCode('Numpad'+i),expected.get('kp'+i));}
for(let i=1;i<=12;i++) assert.equal(keyCode('F'+i),expected.get('f'+i));
for(const [browser,native] of [['Escape','esc'],['Enter','enter'],['Tab','tab'],['Backspace','backspace'],['ArrowLeft','left'],['ArrowRight','right'],['ArrowUp','up'],['ArrowDown','down'],['ControlLeft','leftctrl'],['AltRight','rightalt'],['ShiftLeft','leftshift'],['NumpadEnter','kpenter'],['IntlBackslash','extra_lt_gt']]) assert.equal(keyCode(browser),expected.get(native));
assert.equal(keyCode('MetaLeft'),null);assert.equal(keyCode('F13'),null);
assert.equal(keyCode('toString'),null);
const mouse=readFileSync(sourceRoot+'/native/jsdos/dosbox-x/jsdos-x-main.cpp','utf8');
for(const [browser,sdl] of [[0,'LEFT'],[1,'MIDDLE'],[2,'RIGHT']] as const) {
  const match=mouse.match(new RegExp('case SDL_BUTTON_'+sdl+':\\s*Mouse_ButtonPressed\\((\\d+)\\)'));
  assert.ok(match);assert.equal(mouseButton(browser),Number(match[1]));
}
assert.equal(mouseButton(3),null);
assert.equal(mouseButton(-1),null);assert.equal(mouseButton('constructor' as never),null);
const rect={left:20,top:30,width:640,height:480};
assert.deepEqual(mousePoint(180,270,rect),[0.25,0.5]);
assert.deepEqual(mousePoint(-100,2000,rect),[0,1]);
assert.throws(()=>mousePoint(0,0,{...rect,width:0}));
const rgb=new Uint8Array([0,127,255,255,1,2]);
const output=rgbaFrame(2,1,rgb,null);
assert.deepEqual([...output],[0,127,255,255,255,1,2,255]);
rgb.fill(42);assert.equal(output[0],0);
assert.throws(()=>rgbaFrame(2,1,new Uint8Array(5),null));
assert.throws(()=>rgbaFrame(0,1,new Uint8Array(),null));
assert.throws(()=>rgbaFrame(1,1,null,new Uint8Array(3)));
const oldFetch=globalThis.fetch;
const content=new Uint8Array([1,2,3]);let requests=0;
globalThis.fetch=(async()=>{requests++;return new Response(content);}) as unknown as typeof fetch;
try {
  const {createHash}=await import('node:crypto');
  const sha256=createHash('sha256').update(content).digest('hex');
  assert.deepEqual(await verifiedFile('/emulation-assets/',{file:'guest.zip',bytes:3,sha256}),content);
  await assert.rejects(verifiedFile('/',{file:'guest.zip',bytes:4,sha256}),/identity mismatch/);
  await assert.rejects(verifiedFile('/',{file:'guest.zip',bytes:3,sha256:'0'.repeat(64)}),/identity mismatch/);
  await assert.rejects(verifiedFile('/',{file:'../guest.zip',bytes:3,sha256}),/Invalid staged/);
  assert.equal(requests,3);
} finally {globalThis.fetch=oldFetch;}
console.log('Pinned key/button source, frame conversion, geometry and staged identity checks passed; no emulator executed');
