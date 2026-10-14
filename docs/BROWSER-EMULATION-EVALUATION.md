# Browser emulation feasibility evaluation

The official js-dos `emulators` package offers a plausible low-level DOSBox-X fallback that can display the original guest without the vendor player UI. This is **source/API feasibility**, not proof that this Windows 3.1 guest or Yukon Trail runs correctly in a browser. No emulator was launched, no guest was imported, and no browser or alternate UI surface was accessed. The existing native JavaScript runtime decision is unchanged. Deployment remains separate.

Measured package/source identities, file hashes, bytes and limitations are in [browser-emulation-source-evidence.json](browser-emulation-source-evidence.json). Vendor downloads stay under ignored `local/tools/browser-emulation-evaluation/`; no package manifest, global dependencies or application controls were added. The later frozen trial package is recorded below.

## Pinned candidate and build identity

Candidate: official npm `emulators` **8.5.2**, tarball 9,781,713 bytes, unpacked 29,055,045 bytes. The downloaded tarball matches registry SHA512 integrity and SHA1. Registry `gitHead` is `6bbf0925d221a7304ea8e0dda1e89b8dc01569b2`; the matching source archive was downloaded and inspected. Its native DOSBox-X submodule is `788fde99d3d451eab3621009186e5abe516f2b9c` from the js-dos fork. This is a fork backend, not the installed native reference build. [Official package metadata](https://registry.npmjs.org/emulators/8.5.2), [pinned source](https://github.com/caiiiycuk/emulators/tree/6bbf0925d221a7304ea8e0dda1e89b8dc01569b2).

| Standard deployment file | Actual downloaded bytes |
|---|---:|
|emulators.js|90,630|
|wdosbox-x.js|285,604|
|wdosbox-x.wasm|8,045,933|
|Three-file total|8,422,167|
|wlibzip.js + wlibzip.wasm, if using bundle utilities|185,440|
|Five-file total|8,607,607|

Debug WASM is 8,427,514 bytes; JSPI WASM is 7,893,150 bytes. The metadata also records locally measured gzip sizes, which are not verified HTTP transfer sizes. Package source-map build metadata reports version `8.5.2 (99337d87ab1cca2641a1b99779d5ab74)`; its reported generated JS sizes differ from the final packaged JS sizes. Use the measured final-file SHA256 identities for a deployment pin. A source rebuild matching these artifacts has not been performed, and the exact compiler used for the published artifacts is unknown.

Pinned CMake config requests initial 64 MiB memory, growth, 32-bit WASM, filesystem support and an Asyncify standard backend; a separate JSPI target exists. Reading the standard WASM memory section confirms initial 1,024 pages=64 MiB, maximum 32,768 pages=2 GiB, non-shared memory. These are declared WASM limits, not measured working-set requirements or browser allocation guarantees. The source Dockerfile mentions Emscripten 3.1.28, but this is not sufficient to establish the toolchain used for the published JSPI/exception-handling artifacts. [Build targets](https://github.com/caiiiycuk/emulators/blob/6bbf0925d221a7304ea8e0dda1e89b8dc01569b2/targets/dosbox-x-sdl2.cmake), [base build flags](https://github.com/caiiiycuk/emulators/blob/6bbf0925d221a7304ea8e0dda1e89b8dc01569b2/CMakeLists.txt).

For comparison, upstream DOSBox-X head `378e6f8a25768594df87c9f5c99b5df9b3f6a8b0` was inspected through official GitHub metadata. Its current workflow inventory has no Emscripten workflow. That does not prove upstream has no WASM support; it means this evaluation has not identified a pinned upstream release artifact equivalent to the verified npm candidate. Vendor package licensing is recorded as GPL-2.0, without choosing a license for this repository or making a distribution decision for the separately provisioned guest/media.

## Guest directories and local assets

The low-level `emulators.dosboxXWorker(initFs)`/`dosboxXDirect(initFs)` factories return a CommandInterface. They accept ZIP bundle bytes, explicit `{path,contents}` entries, config strings or a DosConfig object. This supplies virtual filesystem contents; it is not a browser API for automatically mounting the host's macOS directory. A local preparation step would copy the separately provisioned guest's file tree into a fresh ignored bundle or manifest-driven file entries. Backend extraction operates under `/home/web_user`; DOSBox `MOUNT` would target that virtual directory. [Official low-level API](https://js-dos.com/emulators.html), [pinned input transport](https://github.com/caiiiycuk/emulators/blob/6bbf0925d221a7304ea8e0dda1e89b8dc01569b2/src/protocol/protocol.ts#L250).

The reference currently mounts a directory as C: and the unchanged original ISO as D:. Measured on 2026-10-13: current C: directory 1,663 files/27,124,735 file bytes; ISO 370,939,904 bytes; extracted YUKONRES 87,911,322 bytes. The directory measurement is not a frozen browser bundle identity; original guest/media provisioning and hashes remain governed by REFERENCE.md. In-memory import of the full ISO plus extracted guest, transfer buffers, WASM heap and persist ZIPs may consume substantially more than their byte sizes; actual peak use is unknown. Mounting an extracted disc directory instead might reduce inputs, but CD identity, paths and media behavior would need validation before replacing the ISO reference.

The upstream official guide documents Windows 3.1 installation in mounted folders and its disk-IO distinction; that is a compatibility lead, not proof for this js-dos fork/build. The existing S3/SB16 and mouse-integration configuration must be tested unchanged where supported. [Official DOSBox-X Windows 3.1 guide](https://dosbox-x.com/wiki/Guide:Installing-Windows-3.1x).

Backend scripts/WASM can be hosted from a pinned local `pathPrefix`; guest entries can come from local same-origin assets. No vendor player, cloud saves, networking, CDN or remote disk service is required by the proposed ordinary-filesystem path. Offline operation is inferred from these path/input APIs, not validated by a network trace. The loader fetches scripts and evaluates their source; workers are created from Blob URLs. A local HTTP server and compatible script/WASM/worker policy would be needed. Do not assume `file://` or a restrictive CSP works. The reviewed InitFs/fsWriteFile transport uses `contents.buffer`; a future importer should supply full, dedicated Uint8Arrays rather than subarray views with unrelated leading/trailing bytes. [Pinned module loader](https://github.com/caiiiycuk/emulators/blob/6bbf0925d221a7304ea8e0dda1e89b8dc01569b2/src/impl/modules.ts), [worker creation](https://github.com/caiiiycuk/emulators/blob/6bbf0925d221a7304ea8e0dda1e89b8dc01569b2/src/dos/dosbox/ts/worker.ts).

## Original frames, sound and mouse

The low-level interface exposes `onFrameSize`, RGB/RGBA `onFrame`, and Float32 `onSoundPush`. A small adapter could paint a canvas and feed an AudioContext while forwarding existing pointer/keyboard events. That route needs no js-dos player toolbar/sidebar, added virtual buttons or progress controls. Audio activation, keyboard focus, scaling and cursor visibility would still need tests. [Official CommandInterface](https://js-dos.com/command-interface.html).

Input methods include normalized absolute `sendMouseMotion(x,y)`, relative motion, buttons and keys. The pinned DOSBox-X native adapter has an explicit integration branch: it sets unlocked cursor coordinates from normalized positions, queues a cursor update, and forwards button events. However, `server_mouse_sync` is explicitly unimplemented for this backend; calling `sendMouseSync()` does not establish alignment. Compatibility with the supplied Windows integration driver and the exact guest viewport cannot be inferred from these methods. [Pinned mouse implementation](https://github.com/caiiiycuk/emulators/blob/6bbf0925d221a7304ea8e0dda1e89b8dc01569b2/native/jsdos/dosbox-x/jsdos-x-main.cpp#L10226).

## Save persistence and extraction

`fsTree`, `fsReadFile`, `fsWriteFile` and `fsDeleteFile` expose the virtual filesystem. `persist()` defaults to changed files; `persist(false)` asks for the full filesystem. Ordinary filesystem persistence returns ZIP bytes, whereas sockdrive persistence has a different representation. ZIP extraction overlays multiple initial bundles in order, and upstream tests exercise modified/new-file restoration across sessions. These source tests were inspected, not executed here. [Filesystem APIs](https://github.com/caiiiycuk/emulators/blob/6bbf0925d221a7304ea8e0dda1e89b8dc01569b2/src/emulators.ts), [upstream persistence tests](https://github.com/caiiiycuk/emulators/blob/6bbf0925d221a7304ea8e0dda1e89b8dc01569b2/test/src/test-dos.ts#L194).

The changed-files implementation uses a baseline timestamp and walks existing files. No deletion tombstone is emitted by the reviewed ZIP walker. Therefore changed-ZIP overlays alone do not establish reliable deletion semantics: a deleted base file could return when the original base is reloaded. Full filesystem snapshots used as replacement state, or explicit save-file extraction plus a separately recorded deletion list, are candidates for later validation. `fsReadFile` can extract a guest-visible save directly when C: is a directory mount; saves inside a mounted disk image need additional extraction. [ZIP walker](https://github.com/caiiiycuk/emulators/blob/6bbf0925d221a7304ea8e0dda1e89b8dc01569b2/native/libzip/jsdos-libzip.c), [backend packaging](https://github.com/caiiiycuk/emulators/blob/6bbf0925d221a7304ea8e0dda1e89b8dc01569b2/src/dos/dosbox/cpp/worker-protocol.cpp#L1004).

The low-level package leaves persistent browser storage to the host. Save ZIPs or extracted save bytes could be stored locally, but quota/eviction and original save flush/close timing are unknown. `pause()` is not evidence that Windows has flushed open file handles. DOSBox-X savestate trigger APIs are distinct from the game's Save/Load and have not been assessed for compatibility or persistence.

## Unresolved feasibility gates

No Chrome, Edge, Firefox or Safari pass is claimed. Standard WASM/Asyncify avoids depending on the optional JSPI API, but WASM exception handling, Blob workers, audio startup and rendering still need supported-browser verification. Default worker transport uses messages/transfers rather than shared WASM memory; cross-origin isolation was not established as a requirement for this ordinary path. OffscreenCanvas, AudioWorklet, OPFS/sockdrive and JSPI are optional paths with additional compatibility questions. Performance/cycle fidelity is unknown on both desktop and mobile.

After browser authorization, a separate bounded trial would need to prove: verified guest launch and original viewport; absolute pointer/button alignment; S3 palette and SB16 playback; native capture/state agreement; save-file hashes after original Save, extraction and fresh restore; deletion and storage exhaustion behavior; offline request trace; and Chrome/Edge/Firefox/Safari timing/memory checks. Browser authorization is currently pending. None of those tests were attempted through another surface. Until they pass, this is a fallback lead and not a reason to replace the chosen JavaScript port architecture.

## Reproduction

Read official registry metadata for 8.5.2, download its exact tarball into the ignored evaluation directory, verify the recorded SHA512/SHA1, then extract without installing. Download the source tar at the registry's exact gitHead; inspect the native subtree gitlink and the pinned source files listed in evidence JSON. Hash/size the final deployment files rather than trusting generated build-size labels. These commands perform downloads only:

```sh
mkdir -p local/tools/browser-emulation-evaluation
curl --fail --location --output local/tools/browser-emulation-evaluation/emulators-8.5.2.tgz https://registry.npmjs.org/emulators/-/emulators-8.5.2.tgz
curl --fail --location --output local/tools/browser-emulation-evaluation/emulators-source-8.5.2.tar.gz https://codeload.github.com/caiiiycuk/emulators/tar.gz/6bbf0925d221a7304ea8e0dda1e89b8dc01569b2
```

No vendor code or guest has been executed as part of this evaluation, so the native reference and port artifacts remain untouched.

## Frozen local trial preparation,2026-10-14

A reproducible trial asset set is now prepared, without executing an emulator or
accessing a browser. Source-only feasibility has advanced to verified input
packaging; guest/backend compatibility and performance remain untested. The
native JavaScript runtime decision remains unchanged pending an actual trial.

`tools/prepare_emulation_trial.py` verifies the frozen mouse-integrated guest
baseline, unchanged ISO and three pinned vendor artifact hashes before copying.
It writes a canonical guest ZIP, a byte-identical separate ISO, vendor files and
an ignored manifest. All guest member bytes and ZIP CRCs were independently
rechecked. The original baseline and ISO hashes remain unchanged. Three synthetic
checks cover path/type rejection, source drift, DOS case aliases, unknown metadata,
byte preservation and repeatability. No host directory is mounted in a browser.

The frozen baseline is
`local/emulator/baselines/yukon-mouse-integrated-pre-relaunch.tar.gz`, SHA256
`86a7b6ffcbd0e09353b4a6a29efefa54a084c2ce479a17add7724e288019e6dd`.
It is the known post-opening/pre-relaunch baseline, not the live White Pass guest.
823 regular files /21,734,040 file bytes and14 directory members are preserved;
838 recognized AppleDouble metadata records are omitted from the Windows virtual
filesystem. Omissions are recorded with source member/hash, not silently dropped
by a generic filename filter; unrecognized metadata-like files fail explicitly.
The installed EXE and Windows source font hashes match the supplied disc files.

Current ignored package:`public/game-assets/emulation-trial-20261014`.
Guest ZIP14,747,472bytes; separate original ISO370,939,904bytes; three vendor
files8,422,167bytes. These input bytes do not establish browser transfer/peak
memory or acceptable load time. Exact manifest/ZIP identities and integrity
checks are in [browser-emulation-trial-preparation.json](browser-emulation-trial-preparation.json).

The trial config retains S3/16MiB, normal Pentium/fixed20000cycles, integration
device and mouse, SB16 IRQ7/DMA1/HDMA5, and disabled MIDI from the reference.
Host mount paths become explicit `/home/web_user` virtual paths. The emulator
menu is hidden; original Windows/game controls remain the intended UI. The
startup `WIN C:\MECC\YUKON\YUKON.EXE` command requests direct original launch;
that syntax/behavior must be tested, not assumed. No Win31 or game file was
patched. No additional vendor/game toolbar or debugging UI was added.

```sh
python3 tools/prepare_emulation_trial.py \
  local/emulator/baselines/yukon-mouse-integrated-pre-relaunch.tar.gz \
  original/iso/YUKONCD.ISO \
  local/tools/browser-emulation-evaluation/package-8.5.2/package/dist \
  public/game-assets/FRESH-EMULATION-TRIAL
python3 -m unittest discover -s tests -p test_emulation_trial.py
```

The output must be fresh. Source media, vendor code and guest files stay ignored.
The low-level trial adapter and canvas-only entry point now exist at
`web/emulation-trial/`. The ordinary running server still selects the existing
native opening assets. The next step is authorized browser execution, with frame/input/sound,
original save close/extraction/fresh restore, complete journeys and supported
browser checks. Preparing this package does not satisfy any runtime/playtest gate.

Browser authorization has been given, but the tool continues to reject the exact
local URL as a saved-preference block. The user reported clearing it and no matching
origin rule, then reported saving an explicit origin browsing exception. A retry
after that report still received the same saved-preference denial. Official
OpenAI documentation explains that removing an exception restores defaults and
that schemes/nondefault ports matter. No alternate browser, raw browser execution
or other bypass was used. [Browser permission settings](https://learn.chatgpt.com/docs/browser),
[origin policies](https://learn.chatgpt.com/docs/config-file/config-reference).

## Prepared host adapter, not executed

`/emulation-trial/` has only a canvas showing the original emulator framebuffer.
There is no added toolbar, button or loading panel. Startup failures are explicit
console errors. The adapter pins the prepared manifest SHA256 and checks every
selected file's size/hash before launch. Backend modules subsequently fetch the
same local vendor paths themselves; the preflight is not a browser request trace
or a guarantee against files changing between requests. All URLs requested by
the adapter are local; the backend's actual request trace remains unverified.

The source API is `src/emulators.ts`/`src/protocol/protocol.ts` in pinned commit
`6bbf0925d221a7304ea8e0dda1e89b8dc01569b2`. Input uses `src/keys.ts` physical
key values. Pointer coordinates are normalized against the entire framebuffer,
without guessing a game-client offset. Browser left/middle/right0/1/2 maps to
backend0/2/1, as demonstrated by
`native/jsdos/dosbox-x/jsdos-x-main.cpp` SDL switch at lines5214–5225.
Held keys/buttons release on blur/cancel; those platform accommodations need
in-game alignment/timing checks. Unsupported keys remain host keys.

Pinned source-file SHA256 identities:

| File | SHA256 |
| --- | --- |
|src/keys.ts|b9fdb03df8e87239c3f31ce80c838fede900d22ff11a9ae8df28b7a1c3aba7d3|
|src/emulators.ts|04dd8d268f5960d60fc8fcb9d279c4b0c8278dade9310af050b496331fe30008|
|src/protocol/protocol.ts|96a97d86a4e8eabc0507a57b3a08cf9da60cbe56f9d51752b055fa435e68bcf5|
|native/jsdos/dosbox-x/jsdos-x-main.cpp|503d21bdbea38d5a54e8aeea2b3d818c8ffb140bfd6dd5aa4e9f7df64c7e9921|

Full RGB frame conversion retains all channels and alpha255. Native mono
Float32 chunks are scheduled at `ci.soundFrequency()` using Web Audio. A canvas
gesture creates/resumes audio. Samples before activation are counted and omitted;
queue underruns are counted, and a backlog above two seconds pauses the trial
with an explicit error. These are experimental policies with known startup-audio
loss, not observed original behavior or acceptable final fidelity. Volume,
latency, suspension and mixer output remain untested. No gain control is added.

There is no browser storage adapter yet. Original Save writes only the running
virtual guest; closing/reloading loses changes. Console-only
`globalThis.yukonTrial.commandInterface` exposes the source FS APIs for later
save-close/extraction/restore tests; it adds no game UI. No saving or extraction
has been executed through this entry.

Preparation checks, without executing any emulator:

```sh
node tests/test_emulation_contracts.mjs \
  local/tools/browser-emulation-evaluation/source/emulators-6bbf0925d221a7304ea8e0dda1e89b8dc01569b2
node --check web/emulation-trial/main.mjs
python3 -m unittest discover -s tests -p test_serve_port.py
```

The source comparison covers alphanumeric/function/selected special keys and
all three button values; adapter checks cover RGB conversion, malformed buffers,
scaled/clamped coordinates and altered/truncated/path-invalid staged assets.
Five server tests cover bounded roots, explicit optional mount and escaped paths
and symlinks. These checks do not demonstrate browser compatibility or game
fidelity. Full Python suite after this change:184 tests passed.

Once the exact-origin browser restriction is resolved, stop the prior loopback
server and use the same origin with the optional trial asset mount:

```sh
python3 tools/serve_port.py \
  --assets public/game-assets/seattle-opening-v2-20261013 \
  --trial-assets public/game-assets/emulation-trial-20261014 --port 8000
```

The trial URL is `http://127.0.0.1:8000/emulation-trial/`; the native opening
remains `/`. This command has not replaced the currently running server or been
used to bypass the saved browser restriction. Do not infer boot, playable Seattle,
save reliability or a runtime decision from the existence of this entry.
