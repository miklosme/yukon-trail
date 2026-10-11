# Persistent Windows binary analysis

Checked on 2026-10-04. **Observed:** the verified Yukon 1.1 executable imports into a persistent Ghidra NE project, survives a fresh-process reopen, and can be decompiled with locally built macOS native components. This establishes an analysis environment, not recovered gameplay or reliable default function types.

This document records the initial tool setup and baseline audits. Later archive
consumer recovery and persisted names/types are recorded in
[ARCHIVE-CONSUMERS.md](ARCHIVE-CONSUMERS.md); preserve the original audit files
when exporting the annotated project again.

## Source and local artifacts

- Source: `original/extracted/windows/YUKON.EXE`, 404,272 bytes, SHA-256 `9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`.
- Project: `local/ghidra/YukonTrail.gpr` plus `local/ghidra/YukonTrail.rep/`; active program `/YUKON.EXE`.
- Tool installations and downloads: `local/tools/`.
- Settings, launcher Java selection, caches, temporary files, and Java preferences: `local/ghidra/`.
- Exports and logs: `local/ghidra/ne-header.json`, `import-audit.tsv`, `reopen-audit.tsv`, `leads-audit.tsv`, `leads-reopen-audit.tsv`, `entry-smoke.c`, `entry-smoke.asm.txt`, and corresponding `import`, `reopen`, `leads-reopen`, and `smoke` logs.

These directories are ignored. The versioned scripts in `tools/ghidra/` reproduce the inspection and exports without committing the project or binary contents.

## Pinned toolchain and provenance

The initial read-only inventory found no Ghidra, functioning Java runtime, Ghidra/ReVa MCP integration, radare2/rizin, or NASM disassembler in PATH, `/Applications`, standard Java locations, or Homebrew packages. The existing `/usr/bin/java` launcher reported no runtime. Existing build tools were Apple clang 16.0.0 (`clang-1600.0.26.6`) and Python 3.14.5. No system-wide software was installed.

| Component | Pinned distribution | Published SHA-256, matched locally |
| --- | --- | --- |
| Ghidra | [12.1.4, released 2026-09-21](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build), `ghidra_12.1.4_PUBLIC_20260921.zip` | `ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db` |
| Temurin JDK | [21.0.12.1+1, macOS aarch64 HotSpot JDK](https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.12.1%2B1), `OpenJDK21U-jdk_aarch64_mac_hotspot_21.0.12.1_1.tar.gz` | `3623232f33a9c3baadf304480b2535f9a3cba8a58d42ecbb438ba267315d9998` |
| Gradle | [9.7.1 official binary distribution](https://services.gradle.org/distributions/gradle-9.7.1-bin.zip), the version selected by Ghidra's bundled wrapper | `acd53f1edaf02f1a8ff99879f8a34b302661a057d9b063ae9e35b552f804d20a` |

Ghidra's [release-tag README](https://github.com/NationalSecurityAgency/ghidra/blob/Ghidra_12.1.4_build/README.md) requires JDK 21; development master had moved to JDK 25 when checked. Use the release requirement. The installed `Ghidra/application.properties` records compiler/minimum Java 21 and Ghidra source revision `8b6bbb857accdfa20dc5b2f5dea471178c2e9fbc`.

The Temurin checksum came from the [official Adoptium assets API](https://api.adoptium.net/v3/assets/feature_releases/21/ga?architecture=aarch64&heap_size=normal&image_type=jdk&jvm_impl=hotspot&os=mac&vendor=eclipse&page_size=1); the Ghidra checksum also appears in its release page and GitHub release metadata. Gradle's checksum came from its [official checksum file](https://services.gradle.org/distributions/gradle-9.7.1-bin.zip.sha256). Release JSON and the Gradle checksum file are retained under `local/tools/downloads/`.

The supplied `support/gradle/gradle-wrapper.jar` has SHA-256 `cb0da6751c2b753a16ac168bb354870ebb1e162e9083f116729cec9c781156b8`; its integrity is covered by the verified Ghidra archive. The wrapper properties select `https://services.gradle.org/distributions/gradle-9.7.1-bin.zip`. The build used the independently downloaded and verified Gradle executable rather than allowing the wrapper to download an unchecked archive.

### Recreate the isolated tools

Run from the repository root, into new destinations. Do not extract over an existing installation. Download URLs are pinned, rather than aliases to latest releases.

```sh
mkdir -p local/tools/downloads local/tools/jdk local/ghidra
curl --fail --location --output local/tools/downloads/ghidra_12.1.4_PUBLIC_20260921.zip \
  'https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.4_build/ghidra_12.1.4_PUBLIC_20260921.zip'
curl --fail --location --output local/tools/downloads/OpenJDK21U-jdk_aarch64_mac_hotspot_21.0.12.1_1.tar.gz \
  'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jdk_aarch64_mac_hotspot_21.0.12.1_1.tar.gz'
curl --fail --location --output local/tools/downloads/gradle-9.7.1-bin.zip \
  'https://services.gradle.org/distributions/gradle-9.7.1-bin.zip'
```

Verify all downloads before extracting or executing them:

```sh
python3 - <<'PY'
import hashlib
from pathlib import Path
expected = {
    'ghidra_12.1.4_PUBLIC_20260921.zip': 'ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db',
    'OpenJDK21U-jdk_aarch64_mac_hotspot_21.0.12.1_1.tar.gz': '3623232f33a9c3baadf304480b2535f9a3cba8a58d42ecbb438ba267315d9998',
    'gradle-9.7.1-bin.zip': 'acd53f1edaf02f1a8ff99879f8a34b302661a057d9b063ae9e35b552f804d20a',
}
for name, wanted in expected.items():
    path = Path('local/tools/downloads') / name
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != wanted:
        raise SystemExit(f'Checksum mismatch: {name}: {actual}')
    print(name, actual)
PY
bsdtar -xf local/tools/downloads/ghidra_12.1.4_PUBLIC_20260921.zip -C local/tools
bsdtar -xf local/tools/downloads/OpenJDK21U-jdk_aarch64_mac_hotspot_21.0.12.1_1.tar.gz -C local/tools/jdk
bsdtar -xf local/tools/downloads/gradle-9.7.1-bin.zip -C local/tools
local/tools/jdk/jdk-21.0.12.1+1/Contents/Home/bin/java -version
```

The session initially extracted with Python's ZIP/TAR libraries after checksum verification and preserved ZIP executable permission bits. The `bsdtar` equivalents above avoid depending on that one-off extraction code.

### Build macOS native components

The official 12.1.4 ZIP lacks native macOS binaries. Initial analysis logged `os/mac_arm_64/decompile does not exist`, while NE import/disassembly still completed. Ghidra's [Getting Started, Building Native Components](https://github.com/NationalSecurityAgency/ghidra/blob/Ghidra_12.1.4_build/GhidraDocs/GettingStarted.md#building-native-components) directs `buildNatives` for macOS. Existing Apple command-line tools were sufficient:

```sh
yukon_root="$PWD"
yukon_jdk="$yukon_root/local/tools/jdk/jdk-21.0.12.1+1/Contents/Home"
env JAVA_HOME="$yukon_jdk" PATH="$yukon_jdk/bin:$PATH" \
  GRADLE_USER_HOME="$yukon_root/local/tools/gradle-home" \
  JAVA_TOOL_OPTIONS="-Duser.home=$yukon_root/local/ghidra/home -Djava.util.prefs.userRoot=$yukon_root/local/ghidra/preferences" \
  local/tools/gradle-9.7.1/bin/gradle --offline --no-daemon --max-workers=2 \
  -p local/tools/ghidra_12.1.4_PUBLIC/support/gradle buildNatives
```

**Observed result:** `BUILD SUCCESSFUL in 1m 1s`, 14 executed tasks. Decompiler, Sleigh, GNU demanglers, and LZFSE native binaries were built under the isolated Ghidra installation. The built `Ghidra/Features/Decompiler/build/os/mac_arm_64/decompile` has local SHA-256 `1d4338ce6a0742b4ff34ceb3764e41fd3a0cb825133b619ef2b9730316bbc21d`; this is a local artifact identity, not a promise of reproducible compilation across machines.

In Codex's sandbox the offline Gradle build initially failed opening a local coordination socket (`java.net.SocketException: Operation not permitted`). Automatic approval review allowed the same isolated command outside the sandbox. Downloads similarly needed network escalation. No review rejected an action. A Python downloader failed because its local TLS certificate chain was unavailable; native `curl` succeeded with certificate verification enabled.

## NE import and address mapping

The original file's NE header is at file offset `0x80`; its 13-entry segment table starts at `0xc0`. The alignment shift field is 4. The raw startup CS:IP fields at NE header `+0x14` are **NE segment index 0006, offset 001a**. Ghidra selected `New Executable (NE)` with `x86:LE:16:Protected Mode` and compiler specification `default`, image base `0000:0000`.

The following mapping was exported from this actual import and checked against the raw segment table. Ghidra's selectors are analysis addresses, not original runtime selectors or invented flat addresses.

| NE segment index | Ghidra block/start | Original initialized file offset | Ghidra size (bytes) | Initialized |
| --- | --- | --- | ---: | --- |
| 0001 | `Code1`, `1000:0000` | `0x460` | 60,176 | Yes |
| 0002 | `Code2`, `1008:0000` | `0xf2c0` | 59,610 | Yes |
| 0003 | `Code3`, `1010:0000` | `0x1dde0` | 59,278 | Yes |
| 0004 | `Code4`, `1018:0000` | `0x2cac0` | 60,252 | Yes |
| 0005 | `Code5`, `1020:0000` | `0x3b800` | 37,748 | Yes |
| 0006 | `Code6`, `1028:0000` | `0x44fc0` | 39,822 | Yes |
| 0007 | `Data7`, `1030:0000` | — | 32 | No |
| 0008 | `Data8`, `1038:0000` | — | 144 | No |
| 0009 | `Data9`, `1040:0000` | `0x4f3e0` | 8 | Yes |
| 000a | `Data10`, `1048:0000` | — | 8 | No |
| 000b | `Data11`, `1050:0000` | `0x4f400` | 8 | Yes |
| 000c | `Data12`, `1058:0000` | — | 8 | No |
| 000d | `Data13`, `1060:0000` | `0x4f420` | 29,314 | Yes |

For this import the selector sequence is `0x1000 + 8 × (NE segment index − 1)`. Preserve both NE index:offset and Ghidra selector:offset in later findings. Uninitialized segment table sector/length words are zero; their Ghidra sizes match their minimum allocation words. The loader also created 44 `Rsrc` blocks and one `EXTERNAL` block, for 58 blocks total.

Startup maps to **NE 0006:001a → Ghidra 1028:001a → original file offset 0x44fda**. The first three source bytes `33 ed 55` agree with Ghidra's `XOR BP,BP; PUSH BP`. Loader relocations change in-memory operands: the next call's source bytes at file `0x44fdd` are `9a ff ff 00 00`, while Ghidra exports `9a 70 00 c8 11` / `CALLF 0x11c8:0070`. Do not compare relocated bytes to source bytes without accounting for fixups. The source hash remained unchanged after import/build/reopen.

### Imports and analysis scope

Raw module-reference/name tables and Ghidra agree on six modules: `KERNEL`, `GDI`, `USER`, `WIN87EM`, `COMMDLG`, and `MMSYSTEM`. Their length-prefixed names start at file offsets `0x3e3`, `0x3ea`, `0x3ee`, `0x3f3`, `0x3fb`, and `0x403`, respectively. Ghidra applied bundled Win16 export tables and created 187 external import symbols. No original DLL bodies were present or imported.

Default autoanalysis reported 1,645 functions and completed without timeout. These are tool-created function boundaries and default types, not independently verified recovered functions. The first run lacked the native decompiler, so its decompiler-dependent analysis must not be treated as fully exercised. The smoke reopen used `-noanalysis -readOnly` and did not silently rerun that analysis or change annotations.

## Reproduce import, reopen, and smoke export

`inspect_ne.py` checks the exact executable SHA-256 before exporting raw header fields and file occurrences of `YUKONRES`. It is an inventory helper for this source, not a general NE loader.

`headless.sh` uses the pinned local JDK/Ghidra and redirects Java's `user.home`, Ghidra settings/cache/temp paths, and Java preferences under `local/ghidra/`. Redirecting Java's home is necessary because the Ghidra launch-support process saves Java selection before the main application's settings override takes effect. The shell's `HOME` is unchanged.

For a fresh project, the following uses new export filenames to preserve the session's original audits. This session imported before building native components; importing after the native build exercises more analyzers and may produce a different initial inventory.

```sh
python3 tools/ghidra/inspect_ne.py original/extracted/windows/YUKON.EXE \
  > local/ghidra/ne-header.json
yukon_root="$PWD"
tools/ghidra/headless.sh "$yukon_root/local/ghidra" YukonTrail \
  -import "$yukon_root/original/extracted/windows/YUKON.EXE" \
  -analysisTimeoutPerFile 300 -max-cpu 2 \
  -scriptPath "$yukon_root/tools/ghidra" \
  -postScript AuditNE.java "$yukon_root/local/ghidra/fresh-import-audit.tsv" stamp \
  -log "$yukon_root/local/ghidra/fresh-import.log" \
  -scriptlog "$yukon_root/local/ghidra/fresh-import-script.log"
```

Do not re-import over the existing project for routine queries. Reopen the existing saved program in a new process, exporting the current script's records to a new query file:

```sh
yukon_root="$PWD"
tools/ghidra/headless.sh "$yukon_root/local/ghidra" YukonTrail \
  -process YUKON.EXE -noanalysis -readOnly \
  -scriptPath "$yukon_root/tools/ghidra" \
  -postScript AuditNE.java "$yukon_root/local/ghidra/query-audit.tsv" \
  -postScript DecompileSmoke.java 1028:001a "$yukon_root/local/ghidra/query-entry-smoke" \
  -log "$yukon_root/local/ghidra/query.log" \
  -scriptlog "$yukon_root/local/ghidra/query-script.log"
# Compare to leads-audit.tsv only for the original, unannotated baseline.
# The current annotated project has additional function boundaries; verify its
# saved names/types with the commands in ARCHIVE-CONSUMERS.md instead.
```

For a newly created project, compare `fresh-import-audit.tsv` to `query-audit.tsv` instead of the existing session's `leads-audit.tsv`.

**Actual persistence check:** the initial audit script stamped source identity in program options, then exported 261 metadata/block/import/entry records. A second JVM reopened the saved program read-only and verified that stamp. Import and reopen exports were byte-identical, SHA-256 `3409aff9de70666643c368faf4e3c9d0eb11fc4cd3ea33326fce6e7a9402ea93` each. Thirteen segment sizes, initialized flags, mapped starts, six module names, and the startup entry mapping were also checked against the independently read raw header.

The versioned audit subsequently gained string/xref inventory. Two additional fresh-process, read-only runs produced `leads-audit.tsv` and `leads-reopen-audit.tsv`, each with 263 records and SHA-256 `b4e1eecf3bdb6733616ce895200004312a1ebc35d1c66e323e3625392b3656e2`. `cmp` passed. Removing the two `STRING` records from either baseline export yields the original 261-record audit byte-for-byte; the original import/reopen exports remain preserved. At that baseline, no recovered semantic names/types had been assigned; the proven persisted annotation was the source-identity option. The later names/types and bounded function additions have their own reopen audit in `ARCHIVE-CONSUMERS.md`; their current inventory must not be expected to match the pre-annotation function count.

**Actual native decompiler smoke:** `DecompileSmoke.java` completed at `1028:001a` without a returned error message. It exported C (SHA-256 `05224cdd9dc379887d44225c7946c5ea98108d6c5552cc2c67cdbf9d64d6bb8d`) and the function's disassembly/relocated bytes (SHA-256 `0782c3f1f57598b88ca2c9a5a2ead7e760cc1a4aca5439dc50e78137b696f998`). The C output warns that globals overlap and contains unresolved incoming registers and a `char *` representation of incoming CS. It also prints guessed call arguments; for example, the generated `GETVERSION(0x11c8)` must be checked against `CALLF` at `1028:0051` and the surrounding stack/register use. No rule, calling convention, return type, or argument list was validated by this smoke test.

## Observed archive-string leads and next question

| Original `YUKON.EXE` string file offset | Ghidra address | Current exact-address xrefs |
| --- | --- | ---: |
| `0x4f62d` | `Data13`, `1060:020d` (NE segment 000d:020d) | 0 |
| `0x605c7` | `Rsrc22`, `1118:0057` | 0 |

The zero counts describe the current autoanalysis result. They do not establish that the archive name is unused; segmented pointer analysis and indirect references remain unverified. No caller address can currently be claimed from these exact string xrefs. Imported `KERNEL::_LOPEN`, `_LREAD`, `_HREAD`, and `_LLSEEK` symbols provide other observed starting points, without yet identifying the game's archive reader.

**Follow-up:** the file-API and archive-name trace has now identified the original
open/index/lookup/read routines; their names/types and exact evidence are in
[ARCHIVE-CONSUMERS.md](ARCHIVE-CONSUMERS.md). The next static question is its
postread transformation at NE `0001:8462`, followed by image/audio consumers.
Integration setup, full decompiler-dependent reanalysis, and
original-versus-recovered behavior checks remain open.
