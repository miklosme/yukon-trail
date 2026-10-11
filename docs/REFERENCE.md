# Original-game reference environment

Updated: 2026-10-04. **Windows 3.1 and the original Yukon Trail now run locally in DOSBox-X.** The original opening, name entry, initial journal, and Seattle Wharf scene were observed, including journal dismissal with working guest mouse input. A clean Windows/DOSBox shutdown and fresh process launch reproduced the opening. Setup left the emulator at Seattle Wharf for the owner's first review.

This is an opening-reference check. It does not establish full gameplay, save/load behavior, historical hardware, timing, or audio fidelity. All media, guest files, backups, and native captures remain ignored under `local/`; the supplied ISO is unchanged. Small versioned [environment metadata](reference-environment.json) records exact artifact hashes, settings, installation choices, and validation scope.

This document and its manifest preserve the setup checkpoint. A subsequent
[blind playthrough](BLIND-PLAYTHROUGH.md) reached the return-home newspaper ending
and Claims of Fame; the live guest is now left at an unconfirmed fresh name
prompt. Its captures and later observations are separate from the setup evidence.

The owner's [game-disc Archive item](SOURCE-PROVENANCE.md) supplies the verified game ISO, but no Windows installation material. Windows and drivers were obtained separately during this authorized setup; their identities are distinct from the game source manifest.

## Inventory actually performed

The inventory checked executable names on `PATH`, installed Homebrew formulae/casks, application names in `/Applications` and `~/Applications`, and emulator-related names immediately under `~/Library/Application Support`, `~/Library/Preferences`, `~/Library/Containers`, and `~/.config`. Filename searches covered the project's `original/` and `local/` directories plus `~/Downloads`, `~/Desktop`, and `~/Documents`, including ignored/hidden files. Searches targeted emulator names, Windows 3.x installation names, disk-image extensions, and relevant compressed-archive names. This was a scoped inventory, not a claim about every disk or personal directory.

Observed before staging tools:

| Item | Actual result |
| --- | --- |
| Host | Apple Silicon `arm64`; macOS 14.8.3, build 23J220 |
| Homebrew | 7.0.1 at `/opt/homebrew/bin/brew` |
| `dosbox-x`, `dosbox`, `qemu-system-i386`, `qemu-img`, `wine`, `wine64`, `utm`, `vmrun`, `VBoxManage` | Absent from `PATH` |
| DOSBox-X/DOSBox, QEMU, Wine, UTM, VirtualBox, VMware Fusion, Parallels, Boxer, PCem, 86Box app/package names | None found in the checked app, package, and emulator-data locations |
| Windows 3.x installation images/files or emulator guest disks | None found in the checked locations |
| Relevant original media | `original/iso/YUKONCD.ISO`; no accompanying audio-track files found in the project inventory |
| Source-inspection tools used | Apple `bsdtar` 3.5.3 / libarchive 3.5.3; Python 3.14.5 |

Reproduction commands, from the repository root:

```sh
uname -m
sw_vers
brew --version
command -v dosbox-x dosbox qemu-system-i386 qemu-img wine wine64 utm vmrun VBoxManage
HOMEBREW_NO_AUTO_UPDATE=1 brew list --formula --versions
HOMEBREW_NO_AUTO_UPDATE=1 brew list --cask --versions
rg --files -uuu original local "$HOME/Downloads" "$HOME/Desktop" "$HOME/Documents" \
  | rg -i '(dosbox|qemu|win31|win3[._ -]?1|windows.?3|\.img$|\.ima$|\.qcow2$|\.vhd$|\.vmdk$|\.iso$)'
```

An absent directory may produce a diagnostic from `rg`; an empty match set is not an execution failure to investigate as game behavior. Package inventories and directory-name checks complemented the filename search.

## Emulator identity and host checks

The [official DOSBox-X homepage](https://dosbox-x.com/) links the arm64 macOS package for [release 2026.10.01](https://github.com/joncampbell123/dosbox-x/releases/tag/dosbox-x-v2026.10.01). It was downloaded into the ignored tool directory and extracted there, with no system-wide installation.

| Artifact | Identity |
| --- | --- |
| Download | `https://github.com/joncampbell123/dosbox-x/releases/download/dosbox-x-v2026.10.01/dosbox-x-macosx-arm64-2026.10.01.zip` |
| Local ZIP | `local/tools/dosbox-x/dosbox-x-macosx-arm64-2026.10.01.zip` |
| ZIP size | 94,369,585 bytes |
| ZIP SHA-256 | `8514ab856e8ac2611fbdac7adf334c34085c1e00d700a88711f842adec50240f` — matches the digest published on the release page |
| SDL2 executable | `local/tools/dosbox-x/dosbox-x-sdl2/dosbox-x.app/Contents/MacOS/dosbox-x` |
| SDL2 executable SHA-256 | `bad60deaa4cfbe9ce3ed391f3ebc30e3d62f1008abf4cc7663d0143ba60d8f37` |
| SDL1 executable | `local/tools/dosbox-x/dosbox-x/dosbox-x.app/Contents/MacOS/dosbox-x` |
| SDL1 executable SHA-256 | `57b26ee723a738298331e70d39020e7b22e2a2da69fc8eddc47ed3b1cff78ac8` |
| Bundle version metadata | `2026.10.01 Commit b6abbd5`; `ARM SDL2` / `ARM SDL1` |

Checks actually performed: ZIP path traversal/symlink review and all-entry CRC verification passed for 320 entries; the SDL2 executable is Mach-O arm64; `codesign --verify --deep --strict` passed for its app bundle; `otool -L` showed bundled relative library paths and macOS libraries/frameworks. The bundled README describes both SDL variants. The SDL2 variant was subsequently launched and used for the observed Windows and game checks below; the SDL1 variant was not evaluated.

The initial sandboxed `curl` attempt failed DNS resolution (`curl: (6) Could not resolve host: github.com`). An approved network-escalated retry succeeded. There was no automatic approval-review rejection. No quarantine attributes or host security settings were changed.

To repeat staging into a **fresh** tool directory:

```sh
mkdir -p local/tools/dosbox-x
curl --fail --location --retry 2 \
  --output local/tools/dosbox-x/dosbox-x-macosx-arm64-2026.10.01.zip \
  https://github.com/joncampbell123/dosbox-x/releases/download/dosbox-x-v2026.10.01/dosbox-x-macosx-arm64-2026.10.01.zip
shasum -a 256 local/tools/dosbox-x/dosbox-x-macosx-arm64-2026.10.01.zip
bsdtar -tf local/tools/dosbox-x/dosbox-x-macosx-arm64-2026.10.01.zip
# Verify the published hash and inspect archive paths before extraction.
bsdtar -xf local/tools/dosbox-x/dosbox-x-macosx-arm64-2026.10.01.zip -C local/tools/dosbox-x
file local/tools/dosbox-x/dosbox-x-sdl2/dosbox-x.app/Contents/MacOS/dosbox-x
codesign --verify --deep --strict local/tools/dosbox-x/dosbox-x-sdl2/dosbox-x.app
git check-ignore local/tools/dosbox-x/dosbox-x-macosx-arm64-2026.10.01.zip
```

## Requirements observed in the supplied installer

**Source identity:** ISO SHA-256 `89f8eb97bd7d3afdbabbd05dce10854673eff5c5617825940994aba7a0360ed8`; `YUKONCD.INF`, 16,285 bytes, SHA-256 `5717b561682bb430e5ca3dae3f6440e8710a2ea5af033c0c39e66ba67cdcd1ab`. Offsets below refer to original bytes of that file, including its CRLF line endings. These are observed installer declarations/checks, not measurements from a running game.

| Observation | Byte offset |
| --- | --- |
| Default installation directory is `C:\MECC\YUKON` | `0x71` |
| Declares the Yukon `.FOT` font file, alongside `.TTF` | `0xf1` |
| Sets `ColorsNeeded` to 256; lower depth calls the warning procedure | `0x261` |
| Rejects horizontal resolution below 640 | `0x13a9` |
| Rejects vertical resolution below 480 | `0x13e7` |
| Rejects Windows version below 3.1 | `0x16cb` |
| Checks extended memory against 3000; its message states 4 MB installed memory | `0x17c9`; message `0x3d74` |
| Writes installation directory into `YUKON.INI` as `Game Dir` | `0x31f3` |
| Rejects 808x, 8018x, and 80286 CPUs | `0x14af`, `0x14e0`, `0x1512` |
| Checks Enhanced mode and warns when it is absent | `0x15e1` |
| Offers Yukon font installation | `0x1ef3` |
| Sets music/sound/voice flags according to the sound-card answer | `0x2562` |

The script supplies setup evidence beyond the generic disc README's requirements. The installer ran successfully with these requirements satisfied. Individual rejection branches were not tested.

The ISO root contains `SETUP.EXE`, `PRODUCT.PF`, `YUKON.ICO`, `YUF_____.FOT`, and `YUF_____.TTF`. The selected-file extraction procedure alone is not a complete installer directory; mount the verified full ISO for installation.

Reproduce the installer-source inspection without executing it:

```sh
bsdtar -xOf original/iso/YUKONCD.ISO YUKONCD.INF
bsdtar -xOf original/iso/YUKONCD.ISO YUKONCD.INF | shasum -a 256
bsdtar -tf original/iso/YUKONCD.ISO \
  | rg '^(SETUP\.EXE|PRODUCT\.PF|YUKON\.ICO|YUF_____\.FOT|YUF_____\.TTF)$'
```

## Installation sources and actual setup

The [official DOSBox-X Windows guide](https://dosbox-x.com/wiki/Guide:Installing-Windows-3.1x) provided the mounted-folder installation route and driver recommendations. The guest uses DOSBox-X's internal DOS; separate MS-DOS media was unnecessary. The table identifies the exact packages used. Complete local sizes/hashes, raw downloaded metadata, and six floppy-image hashes are in [reference-environment.json](reference-environment.json).

| Component | Source and identity | Actual checks |
| --- | --- | --- |
| Windows | [English Windows 3.1 OEM](https://archive.org/details/win31-oem), `Windows 3.1 (OEM).rar`, six 1.44 MB disk images | Archive size/MD5/SHA-1/CRC matched published metadata; UNRAR test passed all six images; independent source check passed |
| Display | [S3 Trio64V+ 1.70.04](https://vogonsdrivers.com/getfile.php?fileid=275&menustate=0), 626,292-byte ZIP | 52-entry ZIP CRC/path review passed; no published digest was available for comparison |
| Sound | [Creative Labs Sound Blaster 16AWE](https://archive.org/details/creativelabssoundblaster16awe), `Creative Labs Sound Blaster 16AWE.zip` | Archive size/MD5/SHA-1/CRC matched metadata; 47-entry ZIP CRC/path review passed; all 15 selected INSTALL files matched archive bytes |
| Mouse | [Official doslib release 20250729](https://github.com/joncampbell123/doslib/releases/tag/doslib-20250729), commit `473980b3f58d2dc4a6e614b843aba1cec4c03df1` | TAR.XZ size/SHA-256 matched published release; selected regular Win31 driver/INF members matched extracted files independently |
| RAR extractor | [Official RARLAB UNRAR 7.23 arm64](https://www.rarlab.com/download.htm), staged portable binary | Archive path review; six-image RAR integrity test passed; no host-wide installation |

Two download/extraction corrections matter for reproduction. WinWorld's retail mirrors returned 404, so the actual Windows source is the separately identified Archive OEM package. The guide's SierraHelp `SB16W3X.ZIP` link returned 404; the Archive sound fallback identifies itself as **Sound Blaster Basic Disk for DOS/Windows 3.1, SDR-31STD-1-US (Revision 1)**, distributed as `SBBASIC.EXE`. It is not identified as the missing Sierra ZIP. Apple `bsdtar` 3.5.3 could list the Windows RAR but could not extract its filters; incomplete output under `local/emulator/media/windows31-disks/` was not used. Portable UNRAR successfully extracted the six installation images under `windows31-images/`.

After checking the source identity and listing, the actual RAR extraction was:

```sh
local/tools/unrar/rar/unrar t local/emulator/media/windows31-oem.rar
local/tools/unrar/rar/unrar x -o- local/emulator/media/windows31-oem.rar \
  local/emulator/media/windows31-images/
```

DOSBox-X copied all six floppies into a fresh mounted `C:\INSTALL`. For each disk, use the following pattern, replacing `Disk01.img` through `Disk06.img`:

```dos
IMGMOUNT A /Users/miklosme/github/yukon-trail/local/emulator/media/windows31-images/Disk01.img -t floppy
COPY A:\*.* C:\INSTALL
IMGMOUNT A -U
```

The guide's `IMGMOUNT A DISK01.IMG -U` example did not mount an image in the installed emulator version. Explicit `-t floppy` mounting followed by a separate unmount worked. The combined directory contained 465 files. Run `CD \INSTALL` then `SETUP`; Express installation used `C:\WINDOWS`, name `Yukon Reference`, no attached printer, and skipped the tutorial. Initial display was VGA. Actual `WINVER` subsequently showed **386 Enhanced Mode Windows Version 3.10**, rather than relying on the download label.

Driver files were selected into ignored guest directories:

```sh
LC_ALL=C bsdtar -xf local/emulator/media/s3-trio64-win31.zip \
  --strip-components 1 -C local/emulator/windows/DRIVERS/S3
LC_ALL=C bsdtar -xf local/emulator/media/sb16awe.zip \
  --strip-components 2 -C local/emulator/windows/DRIVERS/SB16 \
  'Creative Labs Sound Blaster 16AWE/INSTALL/'
```

With Windows closed, run `C:\WINDOWS\SETUP`, choose Display → Other, supply `C:\DRIVERS\S3`, and select `S3 Trio64V 1.70.04 640x480 256`; repeat that driver path if prompted. Actual `SYSTEM.INI` selects `s3trio.drv`, `vdds3764.386`, display width 640 and color format 8. The S3 driver requires Enhanced Mode. No Win32s, WinG, QuickTime, VFW, AWE, or PnP extras were installed.

Run `C:\DRIVERS\SB16\INSTALL` from DOS. Use `C:\SB16`, explicitly set Windows path `C:\WINDOWS`, and change installer IRQ 5 to **7**, matching the emulator. Ports are 220/330, low DMA 1 and high DMA 5. Preserve the existing MIDI map using the installer Backup option. Installed wave/aux/mixer/MIDI-port entries use `sb16snd.drv`; the music synthesizer uses `sb16fm.drv`. MIDI Mapper remained `SB16 Ext Synth`, routing channels 1–10 to Creative Music Synthesizer and 11–16 to None. External host MIDI is disabled. OPL3 is a recorded reference choice, not evidence of the original physical machine's sound.

The standard Microsoft/IBM PS/2 Windows driver exposed relative movement: CUA's host pointer and guest pointer diverged, so apparent journal Done clicks missed the button. Keyboard menus continued working. The [official mouse guide](https://dosbox-x.com/wiki/Guide:Mouse-support-in-DOSBox%E2%80%90X) explains this limitation. The DOSBox-X integration driver fixed the observed mismatch. Only `doslib/windrv/dosboxpi/bin/win31/dboxmpi.drv` and `oemsetup.inf` were selected from the verified TAR.XZ and copied to `C:\DRIVERS\MOUSE` as `DBOXMPI.DRV`/`OEMSETUP.INF`. From DOS Windows SETUP, select Mouse → Other → that folder → DOSBox-X Mouse Pointer Integration. Actual `SYSTEM.INI` now uses `mouse.drv=dboxmpi.drv`, with `*vmd`. The final emulator config enables `mouse emulation=integration` and `integration device=true`. The vendor guide calls this integration experimental; it is an environment input adjustment, with no game executable/resource patch.

## Final configuration and launch

The exact 708-byte `local/emulator/win31.conf` has SHA-256 `a7944c47ac090d8a6081135d40f6988ed145628f10faede957422e626db22792`. Its full text is versioned in [reference-environment.json](reference-environment.json). Settings are S3, 16 MB RAM, normal Pentium core, fixed 20,000 cycles, SB16 port 220/IRQ 7/DMA 1/high DMA 5, external MIDI disabled, and integrated guest mouse. These are reconstruction parameters; hardware/timing equivalence has not been established.

C: mounts only `local/emulator/windows/`. D: mounts the full unchanged ISO before Windows starts. Autoexec sets BLASTER/SOUND/MIDI, runs `DIAGNOSE /S` and `MIXERSET /P /Q`, sets Windows PATH/TEMP, and starts WIN. Host networking or host command execution was not enabled.

From the repository root:

```sh
local/tools/dosbox-x/dosbox-x-sdl2/dosbox-x.app/Contents/MacOS/dosbox-x \
  -nopromptfolder -conf /Users/miklosme/github/yukon-trail/local/emulator/win31.conf
```

Paths are specific to this checkout; update mount/capture paths when reproducing elsewhere. The initial sandboxed GUI launch aborted before showing a window; approved GUI execution outside the shell sandbox was necessary for macOS WindowServer. Network downloads similarly needed approved network execution. No automatic approval-review rejection, quarantine removal, or host security change occurred. UI actions used CUA. Rapid text/paste was unreliable at the DOS prompt; individual key presses worked. This is an automation-input constraint, not a game behavior finding.

## Game installation and opening check

In Program Manager use File → Run → `D:\SETUP.EXE`. The actual choices were default `C:\MECC\YUKON`, copy executable Yes, program group MECC, Yukon font Yes, sound card Yes. The installer completed and requested a Windows restart; Windows was exited cleanly and DOSBox restarted before game execution. `C:\MECC\YUKON\YUKON.EXE` is 404,272 bytes and SHA-256 `9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`, exactly matching the original full-game executable. `YUKONRES` was not copied to C:; resources remain on D:. No explicit resource pathname appears in `YUKON.INI`.

The installer generated `C:\WINDOWS\YUKON.INI` with `Game Dir=C:\MECC\YUKON` and music/sound/voice flags all 1. A captured copy and exact initial text are in the environment manifest. The original ISO hash was independently rechecked after installation and remained unchanged.

Observed action sequence:

1. Launch the selected The Yukon Trail icon in the MECC group with Enter. Observe animated title/opening and Seattle Wharf name prompt.
2. Enter lowercase `reference`, confirm with Enter. Observe initial journal: August 23, 1897, arrived Seattle; 0 pounds of food and $350 cash.
3. Exit game and Windows, install the mouse integration driver from DOS, close DOSBox, and start a fresh process using the final config. The same blank name prompt and journal values recur; the earlier name was not persisted. No game save was requested.
4. Click journal Done with aligned guest mouse. Observe Seattle Wharf with animated Dyea, Skagway and Pioneer Outfitters characters and the Downtown Seattle sign. Stop here; no travel, purchases, or further decisions were performed.

There was no observed runtime error. A click in the repeated animated introduction was also recorded; whether it skipped a portion of the opening was not established. The first run's uninterrupted opening is preserved separately. The guest was left at Seattle Wharf at the setup checkpoint; this is a review checkpoint, not a completed fidelity milestone.

## Native evidence and backups

Captures use DOSBox-X's **Capture** menu, rather than host screenshots: Take screenshot produces native 640×480 PNG; Record video to AVI produces ZMBV video plus PCM; Record audio to WAV produces stereo 48 kHz/16-bit PCM. The menu toggles finalize recordings. The official macOS shortcuts are F12+P/I/W; CUA could not submit the dual nonmodifier chord, so menu actions were used. Full artifact sizes/SHA-256 values are versioned in the environment manifest.

| Local evidence under `local/evidence/reference/` | Scope |
| --- | --- |
| `krnl386_000.png`, `krnl386_001.png` | Actual Windows WINVER and MIDI Mapper |
| `krnl386_000.wav` | Windows TADA.WAV test; 36.861 s, nonzero captured PCM |
| `krnl386_000.avi`, `krnl386_001.wav`, `krnl386_002.png` | First game launch/opening/name/journal before mouse integration |
| `krnl386_001.avi`, `krnl386_002.wav` | Fresh integrated-mouse run through opening and journal dismissal to Wharf |
| `krnl386_003.png`, `004.png`, `005.png`, `006.png` | Repeated opening frame, blank name prompt, journal, and first playable Wharf scene (full filenames use `krnl386_` prefix) |

Both Windows and game WAV captures contain nonzero PCM. This verifies recorded emulator signal, not host audible listening or identification of individual sound/music/voice resources. Both AVI metadata probes and full FFmpeg decodes passed independently. Independent review reports live alongside the evidence; the manifest lists their exact scope. PSND decoding equivalence, audio balance, MIDI timbre, historical timing, later gameplay, save/load, and scoring were untested at this setup checkpoint; the later blind-run report adds one observed journey and ending.

With Windows closed, guest folder archives were made using `LC_ALL=C bsdtar -czf <baseline>.tar.gz -C local/emulator/windows .`, with a config copy alongside each. They are distinguished explicitly:

| Baseline under `local/emulator/baselines/` | State |
| --- | --- |
| `windows31-drivers` | S3/SB16 installed, before first Windows boot; no game |
| `windows31-clean-pregame` | After clean boot/WINVER/TADA/MIDI inspection, before game install; standard relative mouse |
| `yukon-installed-prelaunch` | Game installed, before first game execution; standard relative mouse |
| `yukon-mouse-integrated-pre-relaunch` | After first journal run and mouse-driver install, before fresh integrated-mouse game run; no save requested |

All are `.tar.gz` plus matching `.conf`, with identities in the manifest. The preboot archive's 1,630 member paths/types and critical Windows/driver files were independently reviewed. Backup restoration/boot has not been tested; the successful repeat check used the same installed guest folder after a fresh process launch.

To restore safely into a new ignored folder without replacing the current guest, first verify archive SHA-256 and paths against the manifest, then:

```sh
mkdir -p local/emulator/restored-yukon
LC_ALL=C bsdtar -xf local/emulator/baselines/yukon-mouse-integrated-pre-relaunch.tar.gz \
  -C local/emulator/restored-yukon
cp local/emulator/baselines/yukon-mouse-integrated-pre-relaunch.conf \
  local/emulator/restored-yukon.conf
```

Edit only the copied config's C: mount to the absolute `local/emulator/restored-yukon/` path, keep the verified ISO D: mount, and launch with that copied config. Baselines are local reference backups, not redistributable repository assets. Do not extract a baseline over a running guest. For normal replay, use the final launch command above, select MECC/The Yukon Trail, and repeat the recorded name/Done sequence. Compare against the native evidence before interpreting later recovered behavior.
