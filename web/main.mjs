import {loadAssets} from './platform/assets.mjs';
import {windowsDisplayIndices, rgbaFromIndices} from './render/indexed.mjs';
import {openingJournal} from './rules/opening.mjs';
import {win16EditText,journalEditOpeningText} from './platform/text.mjs';
import {currentJournalStatus,journalInventoryEntries} from './rules/journal-status.mjs';
import {openingJournalProjection,openingJournalCacheWords} from './rules/opening-journal-state.mjs';
import {initialSeattlePopulation} from './rules/seattle-population.mjs';
const stage = document.getElementById('stage');
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d', {alpha:false});
const nameDialog = document.getElementById('nameDialog');
const journalView = document.getElementById('journalView');
const journalText = document.getElementById('journalText');
const menus = document.getElementById('menus');
const gameMenu = document.getElementById('gameMenu');
const assets = await loadAssets('/game-assets/');
if (!assets.journalStatus) throw new Error('Prepare the recovered journal-status assets for this build');
if (!assets.seattlePopulation) throw new Error('Prepare the recovered initial Seattle actor assets for this build');
// Bounded initial construction only, with explicit controlled clocks. Animation,
// native cached hit buffers and subsequent scene constructors remain unsupported.
const wharfInitialPopulation=initialSeattlePopulation(assets.seattlePopulation,{
  sceneId:4000,partnerWord:65535,property320Word:0,downtownVisitWord:0,
  regionArrivalWord:0,clockMs:0,mmclockMs:0,
});
const graphics = new Map();
let view = 'name';
let ownerName = '';
let journal = '';
const journalState=openingJournalProjection();
let journalSnapshot=openingJournalCacheWords();
let paintVersion = 0;
function resize() {
  const scale = Math.min(innerWidth / 640, innerHeight / 480);
  stage.style.transform = `scale(${scale})`;
  stage.style.left = `${(innerWidth - 640 * scale) / 2}px`;
  stage.style.top = `${(innerHeight - 480 * scale) / 2}px`;
}
addEventListener('resize',resize); resize();
async function graphic(id, frame, excludedIndex = null) {
  const key = `${id}/${frame}/${excludedIndex}`;
  if (!graphics.has(key)) {
    const source = await assets.frame(id,frame);
    const indices = windowsDisplayIndices(source.indices);
    const rgba = rgbaFromIndices(indices,assets.palette);
    if (excludedIndex !== null) {
      for (let i=0;i<indices.length;i++) if (indices[i] === excludedIndex) rgba[i*4+3]=0;
    }
    const surface = document.createElement('canvas');
    surface.width=source.width; surface.height=source.height;
    surface.getContext('2d').putImageData(new ImageData(rgba,source.width,source.height),0,0);
    graphics.set(key,surface);
  }
  return graphics.get(key);
}
function shell(active) {
  ctx.imageSmoothingEnabled=false;
  ctx.fillStyle='#a2a2a6'; ctx.fillRect(0,0,640,480);
  ctx.fillStyle='#000';ctx.fillRect(19,20,602,441);
  ctx.fillStyle=active?'#a6cbf3':'#fff';ctx.fillRect(20,21,600,18);
  ctx.fillStyle='#fff';ctx.fillRect(20,40,600,18);
  ctx.fillStyle='#c3c3c3';ctx.fillRect(20,21,18,17);ctx.fillRect(602,21,18,17);
  ctx.strokeStyle='#000';ctx.strokeRect(20.5,21.5,17,16);ctx.strokeRect(602.5,21.5,17,16);
  ctx.fillStyle='#000';ctx.fillRect(24,27,10,1);ctx.fillRect(24,29,10,1);
  ctx.beginPath();ctx.moveTo(607,27);ctx.lineTo(615,27);ctx.lineTo(611,32);ctx.fill();
  ctx.font='14px "Times New Roman"';ctx.textAlign='center';ctx.fillText('The Yukon Trail',320,34);
}
async function paint() {
  const targetView = view;
  const version = ++paintVersion;
  const background = await graphic(targetView==='journal'?37000:4000,0);
  const items = [];
  const actors=[];
  if (targetView==='journal') {
    // Complete original NE13:0df4 table and selector, using only known words.
    for (const {frame,anchorXY:[x,y]} of journalInventoryEntries(assets.journalStatus,journalState)) {
      items.push([await graphic(37001,frame,0),x+20,y+59]);
    }
  }
  if (targetView==='wharf') {
    // Source head→next draw order; retain the first-arrival37500 frame1.
    for (const pose of wharfInitialPopulation.context_head_to_next) {
      if (!pose.visible_word) continue;
      const image=await graphic(pose.bitmap_id,pose.frame,0);
      const [top,left,bottom,right]=pose.rectangle_tlbr;
      if (right-left+1!==image.width||bottom-top+1!==image.height)
        throw new Error('Source pose and imported actor frame geometry differ');
      actors.push({image,x:left+20,y:top+59,flip:pose.flip_byte});
    }
  }
  if (version !== paintVersion) return;
  shell(targetView!=='name');
  ctx.save();ctx.beginPath();ctx.rect(20,59,600,400);ctx.clip();
  ctx.drawImage(background,20,59);
  for (const {image,x,y,flip} of actors) {
    ctx.save();ctx.translate(x+(flip?image.width:0),y);if(flip)ctx.scale(-1,1);
    ctx.drawImage(image,0,0);ctx.restore();
  }
  for (const [image,x,y] of items) ctx.drawImage(image,x,y);
  ctx.restore();
  nameDialog.hidden=targetView!=='name'; journalView.hidden=targetView!=='journal';
  menus.inert=targetView==='name';
}
nameDialog.addEventListener('submit',async event => {
  event.preventDefault();
  if (view!=='name') return;
  ownerName=document.getElementById('ownerName').value;
  journal=openingJournal(assets.journal,ownerName);
  journalSnapshot=openingJournalCacheWords();
  journalText.value=journalEditOpeningText(journal);
  view='journal'; await paint(); focusJournalEnd();
});
document.getElementById('journalDone').addEventListener('click',async () => {
  journal=win16EditText(journalText.value);
  view='wharf';gameMenu.hidden=true;await paint();
});
function openJournal() {
  if (view==='name') return;
  if (view==='journal') throw new Error('Original repeated journal-open behavior remains unsupported');
  // Original094 pounds branch; settings/default migration remains separate.
  const status=currentJournalStatus(assets.journalStatus,journalState,journalSnapshot,journal,0);
  journal=status.text;journalSnapshot=status.snapshotWords;
  gameMenu.hidden=true;journalText.value=journalEditOpeningText(journal);view='journal';
  paint().then(focusJournalEnd);
}
function focusJournalEnd() {
  journalText.focus();
  // DOM textarea normalizes CRLF to LF; select using its actual value length.
  const end=journalText.value.length;
  journalText.setSelectionRange(end,end);
}
document.getElementById('seeJournal').addEventListener('click',openJournal);
menus.addEventListener('click',event => {
  const menu=event.target.closest('button')?.dataset.menu;
  if (!menu || view==='name') return;
  if (menu!=='Game') throw new Error(`Original ${menu} menu behavior remains unsupported in this opening build`);
  gameMenu.hidden=!gameMenu.hidden;
});
addEventListener('keydown',event => {
  if (event.ctrlKey && event.key.toLowerCase()==='j' && view!=='name') {
    event.preventDefault();openJournal();
  }
  if (event.key==='Escape') gameMenu.hidden=true;
});
canvas.addEventListener('click',()=> {
  gameMenu.hidden=true;
  if (view==='wharf') throw new Error('Seattle scene child interaction/navigation is not yet implemented');
});
await paint();document.getElementById('ownerName').focus();
