#!/usr/bin/env bash
# Launch the pinned project-local Ghidra and isolate its settings/caches.
set -euo pipefail
yukon_root="$(cd "$(dirname "$0")/../.." && pwd)"
yukon_jdk="$yukon_root/local/tools/jdk/jdk-21.0.12.1+1/Contents/Home"
yukon_ghidra="$yukon_root/local/tools/ghidra_12.1.4_PUBLIC"
if [[ ! -x "$yukon_jdk/bin/java" || ! -x "$yukon_ghidra/support/analyzeHeadless" ]]; then
    echo "Pinned local toolchain is missing; see docs/ANALYSIS.md." >&2
    exit 1
fi
cd "$yukon_root"
mkdir -p local/ghidra/home local/ghidra/settings local/ghidra/cache local/ghidra/tmp local/ghidra/preferences
exec env JAVA_HOME="$yukon_jdk" PATH="$yukon_jdk/bin:$PATH" \
    JAVA_TOOL_OPTIONS="-Duser.home=$yukon_root/local/ghidra/home -Dapplication.settingsdir=$yukon_root/local/ghidra/settings -Dapplication.cachedir=$yukon_root/local/ghidra/cache -Dapplication.tempdir=$yukon_root/local/ghidra/tmp -Djava.util.prefs.userRoot=$yukon_root/local/ghidra/preferences" \
    "$yukon_ghidra/support/analyzeHeadless" "$@"
