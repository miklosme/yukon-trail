// Experimental host adapter. No guest execution has been validated yet.
import {keyCode,mousePoint,mouseButton,rgbaFrame,sha256,verifiedFile} from './contracts.mjs';
const base='/emulation-assets/';
const manifestHash='bc6d56f8ee78243935559786871a98242608f745759c23dfff1f41209cf23412';
const canvas=document.querySelector('canvas');
const context=canvas.getContext('2d',{alpha:false});
let ci=null, audio=null, nextSound=0, failed=false;
const keys=new Set(), buttons=new Set(), sources=new Set();
const diagnostics={frames:0,samplesBeforeGesture:0,audioUnderruns:0};
// Console-only handoff; no extra in-game controls or automatic persistence.
globalThis.yukonTrial={diagnostics,get commandInterface(){return ci;}};
function fit() {
  const scale=Math.min(innerWidth/canvas.width,innerHeight/canvas.height);
  canvas.style.width=`${canvas.width*scale}px`;
  canvas.style.height=`${canvas.height*scale}px`;
}
function release() {
  if (ci) {
    for (const key of keys) ci.sendKeyEvent(key,false);
    for (const button of buttons) ci.sendMouseButton(button,false);
  }
  keys.clear(); buttons.clear();
}
function fail(error) {
  failed=true; release(); ci?.pause();
  for (const source of sources) source.stop();
  sources.clear(); console.error('Yukon emulation trial stopped:',error);
}
function activateAudio() {
  if (!audio) audio=new AudioContext();
  audio.resume().catch(fail);
}
function sound(samples) {
  if (failed) return;
  if (!(samples instanceof Float32Array)) return fail(new Error('Unexpected audio buffer'));
  if (!audio || audio.state!=='running') {
    diagnostics.samplesBeforeGesture+=samples.length; return;
  }
  const rate=ci.soundFrequency();
  if (!Number.isSafeInteger(rate) || rate<=0) return fail(new Error('Invalid sound frequency'));
  if (samples.some(value=>!Number.isFinite(value))) return fail(new Error('Invalid audio samples'));
  if (!samples.length) return;
  const now=audio.currentTime;
  if (nextSound<now) {
    if (nextSound!==0) diagnostics.audioUnderruns++;
    nextSound=now;
  }
  // A failed trial stops explicitly instead of silently dropping a growing queue.
  if (nextSound-now+samples.length/rate>2)
    return fail(new Error('Audio backlog exceeds the trial limit of two seconds'));
  const buffer=audio.createBuffer(1,samples.length,rate);
  buffer.copyToChannel(samples,0);
  const source=audio.createBufferSource(); source.buffer=buffer;
  source.connect(audio.destination); sources.add(source);
  source.onended=()=>{sources.delete(source);source.disconnect();};
  source.start(nextSound); nextSound+=buffer.duration;
}
canvas.addEventListener('keydown',event=>{
  if (!ci || failed || event.metaKey) return;
  const key=keyCode(event.code); if (key===null) return;
  event.preventDefault(); activateAudio();
  if (!keys.has(key)) {keys.add(key);ci.sendKeyEvent(key,true);}
});
canvas.addEventListener('keyup',event=>{
  const key=keyCode(event.code);
  if (ci && keys.delete(key)) {event.preventDefault();ci.sendKeyEvent(key,false);}
});
function motion(event) {
  if (ci && !failed) ci.sendMouseMotion(...mousePoint(event.clientX,event.clientY,canvas.getBoundingClientRect()));
}
canvas.addEventListener('pointermove',motion);
canvas.addEventListener('pointerdown',event=>{
  if (!ci || failed || event.button<0 || event.button>2) return;
  event.preventDefault(); canvas.focus(); activateAudio(); motion(event);
  canvas.setPointerCapture(event.pointerId);
  const button=mouseButton(event.button);
  buttons.add(button);ci.sendMouseButton(button,true);
});
canvas.addEventListener('pointerup',event=>{
  motion(event);
  const button=mouseButton(event.button);
  if (ci && buttons.delete(button)) ci.sendMouseButton(button,false);
});
canvas.addEventListener('contextmenu',event=>event.preventDefault());
canvas.addEventListener('pointercancel',release);
canvas.addEventListener('lostpointercapture',release);
canvas.addEventListener('blur',release);
window.addEventListener('blur',release);
window.addEventListener('resize',fit);fit();
async function start() {
  const response=await fetch(base+'manifest.json');
  if (!response.ok) throw new Error(`Cannot load trial manifest: ${response.status}`);
  const bytes=new Uint8Array(await response.arrayBuffer());
  if (await sha256(bytes)!==manifestHash) throw new Error('Trial manifest identity mismatch');
  const manifest=JSON.parse(new TextDecoder().decode(bytes));
  if (manifest.schema!=='yukon-emulation-trial-v1' || manifest.vendor.version!=='8.5.2')
    throw new Error('Unsupported trial package');
  const scriptBytes=await verifiedFile(base,manifest.vendor.files['emulators.js']);
  // Preflight both backend files. Vendor loading then uses these same local paths.
  for (const name of ['wdosbox-x.js','wdosbox-x.wasm'])
    await verifiedFile(base,manifest.vendor.files[name]);
  const guest=await verifiedFile(base,manifest.guest);
  const iso=await verifiedFile(base,manifest.iso);
  const scriptURL=URL.createObjectURL(new Blob([scriptBytes],{type:'text/javascript'}));
  try {
    await new Promise((resolve,reject)=>{
      const script=document.createElement('script');script.src=scriptURL;
      script.onload=resolve;script.onerror=()=>reject(new Error('Vendor script load failed'));
      document.head.append(script);
    });
  } finally {URL.revokeObjectURL(scriptURL);}
  const backend=globalThis.emulators;
  if (!backend || backend.version!=='8.5.2') throw new Error('Unexpected emulator API');
  backend.pathPrefix=base+'vendor/';
  ci=await backend.dosboxXWorker([guest,{path:'YUKONCD.ISO',contents:iso}]);
  const events=ci.events();
  function resize(width,height) {
    // Validate dimensions before allocating a frame or altering the display.
    if (!Number.isSafeInteger(width) || !Number.isSafeInteger(height)
        || width<=0 || height<=0 || width>4096 || height>4096)
      return fail(new Error('Unsupported trial frame dimensions'));
    canvas.width=width;canvas.height=height;fit();
  }
  events.onFrameSize(resize);
  events.onFrame((rgb,rgba)=>{
    if (failed) return;
    try {context.putImageData(new ImageData(rgbaFrame(canvas.width,canvas.height,rgb,rgba),canvas.width,canvas.height),0,0);diagnostics.frames++;}
    catch(error){fail(error);}
  });
  events.onSoundPush(sound);
  events.onStdout(message=>console.info('DOSBox-X:',message));
  events.onMessage((type,...args)=>console.info('DOSBox-X',type,...args));
  events.onExit(()=>{release();for(const source of sources)source.stop();sources.clear();});
  if (ci.width()>0 && ci.height()>0) resize(ci.width(),ci.height());
  canvas.focus();
}
start().catch(fail);
