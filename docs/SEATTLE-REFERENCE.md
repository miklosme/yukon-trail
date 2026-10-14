# Constrained Seattle original reference

Date: 2026-10-13 (America/Los_Angeles). **Restored Windows boot and original Seattle name/journal/Linda acceptance are now observed. Constrained purchases and remaining interviews are in progress.**

Requested scope: fresh Seattle, all four partner interviews, a purchase with journal state before and after, and an unaffordable-purchase response recorded without dismissing its speech early. This is a constrained test, not a blind test. No game save has yet been made. Historical access failures below preceded the successful fallback observations.

## Verified setup

The pre-relaunch integrated-mouse baseline archive matched the versioned reference manifest: 14,752,406 bytes, SHA-256 `86a7b6ffcbd0e09353b4a6a29efefa54a084c2ce479a17add7724e288019e6dd`. Python 3.14.5 `tarfile` inspected all 1,676 members before extraction: only regular files and directories; no absolute paths, `..` path components, symlinks, or hardlinks. Extraction used the `data` filter into a new directory, `local/emulator/seattle-reference-2026-10-13/`. The existing guest `local/emulator/windows/` was preserved.

Copied the baseline configuration to `local/emulator/seattle-reference-2026-10-13.conf`, changing only C: mount and native capture destination. D: retains the unchanged original ISO. Configuration SHA-256 is `ed929a6c12568c0a41e27541ee3b9615cb7bed3697a5f63e899cc61852a1cbcd`; 748 bytes. Captures are directed into the new ignored `local/evidence/seattle-reference-2026-10-13/` directory. The restored executable matches the original at 404,272 bytes, SHA-256 `9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`. Source ISO, extracted resource archive, and existing reference configuration identities were rechecked and are recorded in [seattle-reference-evidence.json](seattle-reference-evidence.json).

Launch command (repository root):

```sh
local/tools/dosbox-x/dosbox-x-sdl2/dosbox-x.app/Contents/MacOS/dosbox-x \
  -nopromptfolder -conf /Users/miklosme/github/yukon-trail/local/emulator/seattle-reference-2026-10-13.conf
```

DOSBox-X 2026.10.01 ARM SDL2 accepted this configuration and remained running (shell session 75582 during this session). **This is process launch evidence only. Windows boot, scene, mouse alignment, audio and restored-game operation were not visually verified.** The process was left running without forced termination, since guest shutdown state could not be observed.

## Concrete blocker and next action

First native CUA `cua.getApp('dosbox-x')` returned “Sky Computer Use request timed out” after 667.0643 seconds. A second native inventory `cua.getState()` with explicit 60-second timeout returned “js execution timed out; kernel reset” after 60.0174 seconds. No UI action was submitted. The failure is in the computer-use service, not an observed game error. No alternative UI-control technology was used.

When native UI access returns, inspect the separately restored guest, verify Windows boot, select MECC/The Yukon Trail, and capture initial journal before spending. Record all partner interviews, then chosen contribution/journal, purchase/journal and insufficient-funds dialogue with native PNG/AVI/WAV via DOSBox-X Capture. Allow the full response audio to finish before dismissing it. Preserve the existing guest and reference captures. Capture filenames and hashes must be appended to the evidence manifest and observations added here. No Seattle behavior coverage was added by this setup attempt.

## Follow-up service check

A later goal turn revalidated shell session 75582: the same process remained running. New DOSBox logs show D: ISO mounting (one data track, zero audio tracks), Windows 3.10 Enhanced Mode initialization, and display activity. They also contain unsupported INT10, interrupt, and mouse-reset diagnostics. These logs do not establish visible boot or game failure.

One bounded `cua.getState()` returned successfully in 5.9994 seconds and listed DOSBox-X as running. `cua.getApp('com.dosbox-x')` then reported an ambiguous bundle identifier between the SDL1 and SDL2 bundles. Using the exact known SDL2 app path returned “Sky Computer Use request timed out” after 120.0129 seconds despite a 60-second JavaScript timeout. Thus inventory access recovered, but native app binding/observation still failed. No UI input, screenshot, or native capture was submitted; the existing isolated process was preserved without restart. AppleScript/System Events fallback was not used because no specific user authorization for that alternative UI technology had arrived. Next action remains observing this same guest when native app access returns.

## Authorized AppleScript fallback

The human subsequently explicitly authorized AppleScript fallback. Read-only scoped `osascript` queries to System Events failed immediately: requesting DOSBox-X process/name/PID/window/menu inventory returned `68:72: execution error: An error of type -10822 has occurred. (-10822)`; requesting only processes whose name contains `dosbox` returned the same error at `40:101`. Both exited 1. A plain AppleScript constant-return probe exited 0 with `AppleScript engine available`, isolating the failure to System Events access rather than the interpreter. The numerical error does not by itself establish an OS permission denial or its precise cause. No permission, security setting, UI input, emulator restart, or native capture followed. Native UI remains inaccessible via both tested surfaces. Exact commands/results are preserved in the evidence manifest. The next concrete action is restoring working System Events or CUA app observation, then capturing the same isolated guest before gameplay.

## Restored boot verified through root proxy

Root execution context could access the authorized System Events fallback while the worker still returned `-10822`. Therefore earlier failures are worker-specific access evidence, not a general host LaunchServices outage. Root observed DOSBox-X process 94413 with one KRNL386 window and the Capture menu, then clicked its exact `Take screenshot [F12+P]` item. Independent subagent inspection of native `krnl386_000.png` proves Windows boot: Program Manager is open with MECC group and The Yukon Trail icon selected. This supersedes the earlier unverified-boot status. Capture identity is in the evidence manifest. Original game launch/gameplay is not yet established by this image.

## Initial original journal observed

Root began native AVI/WAV capture, launched the selected game with Return, and captured its transition to Seattle Wharf. `krnl386_002.png` shows the blank Enter Your Name dialog. Individual letter inputs entered `seattle`, verified in `003` before Return. `004` then shows the original journal: owner `seattle`; August 23, 1897, arrived Seattle; August 23, 1897, Seattle: 0 pounds of food, $350 in cash. This is the independent pre-spending checkpoint.

Mouse input through System Events `click at` has not been validated: mapped Done click and guest Game-menu click both left the journal visible in native `005` and `007`. Tab+Return also left it open (`006`). The journal caret moved to a new line after Return, showing that keyboard input reached editable journal text, not Done. No financial/game progression action was performed. The native guest pointer stayed near (510,357) across these images. Root confirmed frontmost DOSBox-X, window position (436,263), size (640,508); coordinate mapping and mouse delivery remain unresolved. Native PNG identities through `007` are recorded in the manifest; ongoing AVI/WAV will be hashed after finalization.

Escalating the worker's scoped System Events query outside its shell sandbox subsequently succeeded (PID 94413, same KRNL386 window), confirming that earlier `-10822` worker failures were sandbox-specific. Root's additional authorized public ApplicationServices mouse-event test at the observed Done position still left journal and guest pointer unchanged in independent native `008` inspection. No mouse-delivery success or financial state change is claimed. The proxy input problem remains distinct from a game progression blocker.

## Verified input and Linda operation

The human-authorized `osascript` JavaScript fallback uses public ApplicationServices mouse events. **Refocus DOSBox-X before every guest input.** Set System Events process `dosbox-x` frontmost, then post mouse-moved (type 5), left-down (type 1), and left-up (type 2) using `CGEventCreateMouseEvent`/`CGEventPost`. Allow 0.2 s after move, 0.5 s while down, and at least 1 s afterward. Earlier attempts failed because the app was no longer frontmost after the CUA timeout. Root's refocused event successfully closed Done in native `009`; the subagent subsequently performed the remaining original inputs directly through escalated authorized `osascript`. No OS permission or security setting was changed.

Observed host DOSBox-X window position is (436,263), size 640×508; guest native (x,y) maps to host (436+x,291+y), accounting for 28 px host window chrome. Requery geometry after any window move. Native capture remains the exact observed DOSBox-X Capture → `Take screenshot [F12+P]`, with AVI/WAV toggles named `Record video to AVI [F12+I]` and `Record audio to WAV [F12+W]`. Initial author-added journal blank lines from the earlier Tab/Return input remain documented; they did not change the displayed resource balances.

Actions and native evidence:

1. `009` verified journal dismissal to Wharf; Downtown sign → `011` Seattle street. Ticket window/door click attempts (`012`–`015`) only moved the guest pointer; clicking the Ticket Office sign at guest (70,205) entered the office (`016`). These failed hotspot clicks are not progression blockers.
2. Game menu (`017`) exposes See Journal & Outfit, Ctrl+J. Ctrl+J did not open it in this input method. Clicking Game then Return selected the highlighted journal entry and opened `020`: August 24, 1897, 0 lb food, $350 cash. The earlier initial journal `004` was August 23, so date progression occurred before acceptance.
3. Seated red-clothed female at guest (243,341) → `021`, Linda's introduction: outsiders may call her Linda, born and raised in destination area, can lead to gold. Chose “Why should I choose you to be my partner?” → `022`: speed to gold fields, carrying more supplies and covering more ground than outsiders. Chose cash question → `023`: “I have $500.” Chose “Nice talking to you. I'll let you know later.” No partnership formed at this point.
4. Opened journal again before acceptance: `024` shows August 24, 1897, 0 lb food, $350 cash. Closed Done, reopened Linda (`025`, already-introduced response), chose “OK! Great! Let's be partners!” → `026`: trusts player with money; needs ship tickets to Alaska. Chose “OK. I'll go get the tickets.”
5. Immediately opened journal (`027`) without tickets, supplies, or travel. Added original journal text: “August 24, 1897. Seattle. Teamed up with a native of Alaska who said I could call her Linda. Her knowledge of the area and packing experience will be very helpful. She added $500 to our partnership.” Current entry: August 24, 1897, 0 pounds of food, $850 in cash. **Observed operation: $350 → $850, food unchanged at 0, displayed date unchanged at August 24 across acceptance.** Root independently inspected `024`/`027` and confirmed these values and prose.
6. Closed journal, left Ticket Office (`028`) and returned to Wharf (`029`). Post-partnership silhouette appears at bottom left. No tickets or supplies have been purchased.

Native `000.avi` and `000.wav` were finalized after `027`; hashes/sizes are in the evidence manifest. A separate `001` recording began for subsequent purchase/refusal work. Audio/video integrity and resource matching remain to be checked. No claim about all partner interviews, original saves, or purchases is made yet.

## Whipsaw purchase and preserved checkpoint

In the Linda run, immediately before the supply exchange `032` shows August 24, 1897, 0 lb food and $850 cash. Closed Done, spoke with Pioneer Outfitters merchant (`033`), chose supplies (`034`), then whipsaw (`035`). The merchant calls it a two-person saw for making boards from tree trunks, costing $8. Chose “OK, it's a deal.” The merchant's next choices omit whipsaw (`036`). Ended exchange and immediately opened journal (`037`): August 24, 1897, 0 lb food, $842 cash; the whipsaw is drawn on the right. This independently observes an $8 purchase, with unchanged date/food; no tickets, additional purchase, or travel intervened.

For the subsequent refusal preparation, bought the 2,400-lb outfit advertised at $420 (`042`), using the corresponding choice. Outfit description (`041`) lists cooking supplies, mining supplies, cold-weather clothing, sled, food. Postpurchase journal `051`: August 24, 1897, 2,400 lb food, $422 cash; whipsaw and outfit rendered. Seattle merchant then only offers additional sled (`043`), so no unaffordable attempt occurred in this Linda run.

Used original File → Save Game As (`045`–`046`). Inputting `seattle.gam` through System Events omitted the period, producing invalid `seattlegam` (`047`); this is an input-method issue, not a save-format failure. Dismissed error and replaced the selected name with basename `seattle`, which the original accepted as `C:\MECC\YUKON\SEATTLE.GAM` (`049`). Preserved byte-for-byte ignored evidence copy `SEATTLE-after-whipsaw-outfit.GAM`. No existing BLIND save was touched. Save identity is in the manifest; reload is pending.

Finalized native `001.avi`/`001.wav` after this bounded purchase/save case. Began a separate clean New Game via File, declined saving changes to SEATTLE.GAM (`053`–`054`, No then Return), entered `voices`, and captured clean August 23/$350/0 food initial journal (`056`). The old saved checkpoint remains available for later reload comparison. This new run has no accidental journal notes.

## Remaining partner interviews (separate clean voices run)

The separate `voices` run used initial journal `056`, then ordinary Wharf → Downtown → Ticket Office. No partner accepted while interviewing Sadie or Jake. Full introductions, why-partner replies and cash replies were preserved with native audiovisual recording `002`:

| Candidate | Native PNGs | Observed reply content |
| --- | --- | --- |
| Sadie, leftmost blue clothes | `060` intro, `061`–`062` why, `063` cash | Knows gold mining; says she is the best gold miner, struck rich in Colorado then lost it in poker; has $500 and proposes equal partnership. |
| Jake, standing center-right | `065` intro, `066` why, `067` cash | Master carpenter; building cabin, mining equipment and boat is his specialty; has $500. |
| Midas T. Golden, seated right | `069` intro, `070` why, `071` cash | Well-to-do businessman willing to share money; has $750 and would share equally. |
| Linda, seated red clothes | Earlier run `021`–`023`, `025`–`027` | Native of destination area, carries more supplies/covers more ground, has $500; actual acceptance journal independently checked above. |

These are observed introductions and selected questions, not exhaustive interviews. “Tell me more about yourself,” solo-trip replies, acceptance cancellation, and all other partner/game branches remain untested unless explicitly added later. Sadie and Jake were dismissed through “Nice talking to you. I'll let you know later.” Midas's higher cash contradicts the initial tentative idea that selecting him would make an unaffordable Seattle purchase easy; that idea was not used as game evidence.

## Save reload, menus, isolated date case and final state

Confirmed Midas in the separate `voices` run: `072` entrusts player with cash and asks for tickets; “OK. I'll be right back.” → `073`, Midas silhouette at bottom left. This acceptance lacks an immediate pre/post journal and is not presented as a validated monetary operation.

Ticket clerk `074` offers information, Skagway, Dyea and check-with-partner. Selected Dyea to inspect choices (`075`): Alliance $40 per person, Yosemite $30, Eliza Anderson $20. Chose the explicit decline/unsure option (`076`); **no ticket purchase**. No insufficient-funds response was reached. This does not prove the response unreachable in Seattle; it remains an uncaptured targeted case. No edited save, memory, or invented state/spending was used to manufacture it. Static PSND1 routing remains separate evidence; a later naturally low-cash Midas interaction is the next practical reference case.

Menu inventory only: Game native `017` (See Journal & Outfit, Sound Effects, Music, Reading Speed, Speech, Show Speech Balloons, Time Out, High Score List); File `045` (New Game, Load Game, Save Game, Save Game as, Close Game, Save Journal, Exit); Management `077` (About Management, Enable Management, disabled Set Preferences/Change Password). No management action or setting was selected.

Save reload: File → Load Game, declined saving separate `Untitled.gam` voices run (`079`–`080`), typed short basename `seattle` into Open and confirmed. Original restored Outfitters scene and Linda silhouette (`081`); journal `083` matches saved `051`: August 24, 1897, $422 cash, 2,400 lb food, Linda's $500 contribution entry, whipsaw and outfit visible. A second reload after the date case reproduced the same journal (`100`). The save and evidence copy remain byte-identical, SHA-256 `ac548222959f58c34fa8247ad308e16f4f0232ddbfb6374585334c5df2b00604`. This checks one original Seattle save/restore, not file-format recovery, all later saves or port persistence.

Isolated date check: started clean `clock` New Game, without saving over SEATTLE.GAM. Native `087` initial journal: August 23, 1897, $350, 0 lb food. Done → Wharf (`088`), then reopened journal via Game→Return with **no navigation or conversation**: `090` still August 23, $350, 0 lb. Closed Done, performed only Wharf→Downtown (`092`), reopened journal: `094` adds August 24, $350, 0 lb. Thus one first Downtown navigation advances displayed date in this case, whereas initial Done/journal reopening alone does not. This is a bounded observation, not a general recovered clock rule.

Final guest is the isolated original process 94413 / shell session 75582, restored SEATTLE.GAM with journal `100` open. Native recordings `000`, `001`, `002` AVI/WAV are finalized. `001.avi` probe: 1,041.936520 s, ZMBV 640×480 + PCM 48 kHz stereo; `002.avi`: 1,097.930805 s, same formats. Full decoding checks are recorded below when complete. No source media, prior guest, baseline archive, or BLIND save was altered. Native evidence contains 101 PNGs, three AVI/WAV pairs, and one preserved save; all exact identities are in the manifest. Many PNGs preserve input failures and menus rather than add game-content coverage.

The next substantive reference work is the uncaptured insufficient-funds speech and its exact live resource match. Other untested content includes solo-trip replies, Tell Me More branches, declined acceptance outcomes, actual destination/ship changes, other purchases and boundary cases, journey routes/events/minigames, later saves and complete-game paths. The original constrained Seattle checks cannot establish port fidelity or journey completion.

Reproducible mouse/capture command for the observed Done control (guest 160,429); substitute only coordinates from a fresh native observation. It fails explicitly if window dimensions differ. The user must authorize the alternate UI-control technology before using this fallback; it does not change OS permissions.

```sh
osascript -l JavaScript -e '
ObjC.import("ApplicationServices");
var proc=Application("System Events").processes.byName("dosbox-x");
proc.frontmost=true; delay(0.5);
var pos=proc.windows[0].position(), size=proc.windows[0].size();
if(size[0]!==640 || size[1]!==508) throw Error("Unexpected window geometry");
var point={x:pos[0]+160,y:pos[1]+28+429};
$.CGEventPost(0,$.CGEventCreateMouseEvent(null,5,point,0)); delay(0.2);
$.CGEventPost(0,$.CGEventCreateMouseEvent(null,1,point,0)); delay(0.5);
$.CGEventPost(0,$.CGEventCreateMouseEvent(null,2,point,0)); delay(2);
proc.menuBars[0].menuBarItems.byName("Capture").menus[0]
.menuItems.byName("Take screenshot [F12+P]").click();'
```

Wait for the asynchronously written native PNG to finish before reading it. Keyboard actions used AppleScript `tell application "System Events" to tell process "dosbox-x"`, `set frontmost to true`, `key code 36` (Return), `key code 53` (Escape), or individual `keystroke` characters with 0.1 s between them. Native mouse capture numbers are cumulative within the configured capture directory. Preserve prior captures and saved filenames.

Verification finished: FFmpeg 8.1.2 fully decoded both `001.avi` and `002.avi` with exit 0 and no error output. This validates media-stream integrity; it does not verify sound-resource identity or all animation frames. Python 3.14.5, macOS 14.8.3 build 23J220, DOSBox-X 2026.10.01 ARM SDL2 were used. Final original ISO and restored executable SHA-256 still match source identities; saved SEATTLE.GAM still matches its evidence copy. `git diff --check` passes. Source media, guest/config/captures and save copies remain ignored; only these reference documents/metadata belong to this subagent's patch.

```sh
ffmpeg -nostdin -v error -i local/evidence/seattle-reference-2026-10-13/krnl386_001.avi -f null -
ffmpeg -nostdin -v error -i local/evidence/seattle-reference-2026-10-13/krnl386_002.avi -f null -
ffprobe -v error -show_entries format=duration,size:stream=index,codec_name,width,height,sample_rate,channels \
  -of json local/evidence/seattle-reference-2026-10-13/krnl386_001.avi
```
