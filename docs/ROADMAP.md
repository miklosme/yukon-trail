# Execution roadmap

The target is a faithful game that plays well on the web. Milestones are ordered by what they establish. Static analysis and reference-runtime setup can advance independently; an unavailable runtime does not prevent all progress, but it does prevent claiming behavioral fidelity.

## M0 — Reproducible source and reference environment

Verify source hashes; extract Windows files into a durable local location; inventory the Mac partition without discarding resource forks. Record the Internet Archive item and track inventory when available. Establish a working original Windows installation in an emulator, starting with evaluation of DOSBox-X plus Windows 3.1.

**Exit evidence:** repeatable extraction commands and verified hashes; documented reference environment and opening-scene capture; explicit remaining media gaps. A machine-local emulator disk is accompanied by setup notes so the next agent can reproduce it.

## M1 — Small proof of recovery and runtime decision

1. Implement a bounded archive reader from the documented index. Produce a manifest keyed by type and ID, preserving offsets, sizes, and source identity. Check group boundaries, duplicate keys, truncation, arithmetic bounds, and unsupported inputs. Use synthetic fixtures for automated failure cases.
2. Import the executable into a persistent Ghidra project. Find archive lookup and image/audio consumers. Record address mappings and the evidence for types and structures.
3. Decode at least one actual `CBMP` image, including its palette/transparency as applicable, and one `PSND` sound with established playback parameters. `YLOGO.BMP` alone does not demonstrate resource decoding.
4. Recover one small gameplay operation visible in the original, preferably a purchase or dialogue choice with measurable state effects. Capture before/after state and repeatable actions.
5. Decide TypeScript versus C++/WebAssembly based on native-logic volume, data-driven behavior, platform coupling, debugging, and maintenance. Record the reasons, uncertainties, and chosen rendering approach.

**Exit evidence:** reproducible extraction/decoding; image and sound comparison to the original; one independently checked state transition; durable analysis notes; an explicit architecture decision. If any part fails, retain the useful results and document the specific gap rather than extrapolating success.

## M2 — Playable opening slice

Implement the actual opening sequence through a bounded Seattle interaction loop and a verified transition out of it. Confirm the exact sequence by observing the original. Include the required scene backgrounds, hit regions, dialogue, inventory/money state, audio, and navigation. Provide a basic browser save/load path and controlled time/randomness where the recovered rules require them.

Keep import/conversion tools independent from runtime assets; keep state transitions independent from rendering and browser services. Add build/run instructions and focused CI when those commands exist.

**Exit evidence:** playable browser slice; documented original-versus-port comparisons; a save/load round trip that preserves relevant state; a list of unsupported resources and behavior. A visual mockup is not this milestone.

## M3 — Full journey and behavior coverage

Expand scene and rule support from the observed game: preparation, travel, route decisions, health and events, activities/minigames, arrival, mining/claims, and ending/scoring as applicable. Treat this as an initial coverage outline, not a verified complete game specification. Recover conditions and transitions from original evidence.

Maintain a coverage matrix connecting scenes, resource types, important rules, and replay cases. Cover alternate paths, invalid actions, boundary values, loss/end conditions, and save restoration. Investigate remaining Mac/demo differences only when they resolve uncertainty or supply missing evidence.

**Exit evidence:** at least one complete journey compared with the original, plus targeted alternate-route and edge-case checks. Record untested paths explicitly; a single successful journey does not establish complete fidelity.

## M4 — Browser experience and preservation release

Polish responsive scaling, touch and keyboard interaction, readable text, volume controls, browser audio activation, pause/resume, autosave, and save export/import. Address loading progress, asset caching/lazy loading, and memory use based on measured needs. For a native-code port, validate event-loop yielding and persistence across reloads. Verify desktop and mobile browser behavior, including Safari, rather than assuming a successful Chromium run is sufficient.

Document intentional differences from the original. Resolve missing-media handling, project-code licensing, and the asset distribution model before deployment packaging. Possible packaging approaches include a separately provisioned asset set or local user import; selection is still open.

**Exit evidence:** reproducible static build/deployment instructions; measured loading and runtime behavior; save recovery checks; documented browser coverage and known issues; a complete-playthrough report and asset provenance. Public deployment is a separate requested action.

## Decision policy

Do not choose React Three Fiber solely because earlier projects used it. It remains an option if it offers concrete reuse or rendering benefits. Do not pursue byte-identical native recompilation as a prerequisite for a browser port; use disassembly/compilation comparisons selectively when they answer behavioral questions. Do not replace unimplemented original behavior with guessed rules to accelerate an apparent completion date.
