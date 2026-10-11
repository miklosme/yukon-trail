# Original-game blind playthrough

Run date: 2026-10-04 (America/Los_Angeles). **Completed: reached the original game's ending and Claims of Fame score, 14,586 (Stampeder).**

The owner requested a subagent to play blind and see whether it could reach a finished game state. The player used only the running original game's scenes, dialogue, and menus. No walkthroughs, strategies, recovered behavior, binary/resource inspection, or prior gameplay findings were consulted. Emulator operation/capture instructions in `docs/REFERENCE.md` and provenance-only `docs/source-manifest.json` were allowed. This observation does not prove port fidelity or completeness of any milestone.

## Environment and evidence method

Original Windows game in DOSBox-X ARM SDL2 2026.10.01, Windows 3.1 Enhanced Mode, S3 640×480/256 colors, SB16, integrated guest mouse. Existing `local/emulator/win31.conf` remained unchanged (SHA-256 `a7944c47ac090d8a6081135d40f6988ed145628f10faede957422e626db22792`). The existing guest was already running at Seattle Wharf. Used File → New Game, declined saving the old `Untitled.gam` reference session, and replaced the selected name `reference` with `blind` using individual key presses. No optimization restart occurred.

Source identities copied from the provenance manifest:

- `original/iso/YUKONCD.ISO`: 370,939,904 bytes; SHA-256 `89f8eb97bd7d3afdbabbd05dce10854673eff5c5617825940994aba7a0360ed8`.
- Original/installed `YUKON.EXE`: 404,272 bytes; SHA-256 `9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06`.

All interaction used CUA native app controls; guest content was visually observed because accessibility exposes the emulator menus, not game text. Scene changes sometimes needed another observation to settle; dialogue choices appeared after speech or clicking the speech bubble. No runtime fault has been observed. Time and randomness were not artificially controlled; seeds and exact original timing are unknown.

Native DOSBox-X Capture → Take screenshot / Record video to AVI produces the evidence. Capture destination still points at `local/evidence/reference/`; new captures only are moved into `local/evidence/blind-playthrough-2026-10-04/`. Existing reference captures are preserved. Evidence is ignored, not committed. Raw captures are distinct from the observations below.

## Observed decisions and progress

1. Fresh journal named `blind`: August 23, 1897; arrived Seattle; 0 lb food; $350 cash. Native `01-starting-journal.png`.
2. Visited downtown Seattle → Pioneer Outfitters → merchant. Merchant would only sell an outfit for two travelers, and advised finding a partner at the ticket office.
3. Ticket office: spoke first with Linda, who introduced herself as born and raised in the destination area and able to lead to gold. Chose “OK! Great! Let's be partners!” → “OK. I'll go get the tickets.” Other partner candidates were not interviewed. A money animation appeared; contribution amount was not inspected at that moment.
4. Clerk: “Two tickets to Dyea, please.” → “The Yosemite, please.” → “OK, it's a deal.” Two tickets cost $60. Chose Dyea and the middle priced ship without an external strategy.
5. Outfitters: requested supplies → outfit → buy → outfit with 1,600 lb food ($370). Merchant described cooking supplies, mining supplies, cold-weather clothing, a sled, and food. Asked about whipsaw; merchant described a two-person saw for boards costing $8. Bought it. Did not buy an additional sled; outfit already described one.
6. Returned to Wharf and attempted boarding via gangway. Confirmed tickets and readiness. Told Yosemite was due back and departure would be in about a week. Chose “OK. We'll be ready.” Displayed calendar advanced; voyage map began. Bounded native AVI recording started before departure confirmation.
7. Aboard-ship news reported crowded Chilkoot and White Pass trails. Clicked the news panel to continue. Linda noted a bad storm and hoped the ship could weather it; chose OK. Voyage continued (September 10 shown at latest observation).

8. Clicked Fast/near-right speed indicator while sailing. The game explained: ship already chosen, nothing more can affect its speed. Acknowledged OK; no emulator speed change was made. Ship struck rocks during storm; Linda reported taking on a little water and possible cargo damage. Chose OK. September 18 displayed afterward. Totem-pole educational scene was acknowledged earlier.
9. Arrived Dyea town. Journal recorded September 27 arrival; September 28: 1,309 lb food, $412 cash. It also recorded Linda's $500 contribution on August 24 and August 31 boarding. Captured town and journal; stopped/moved voyage AVI. No shore unloading fee choice was presented in the observed sequence.
10. Chose displayed Chilkoot sign → “Let's start up the trail.” Walking route began without a packing dialog in the observed sequence. A thief took some food; acknowledged OK. October 3 shown on route. Corduroy Road educational scene appeared; acknowledged it. Briefly inspected Management menu, saw administrative options, dismissed without enabling anything.
11. More crowds/rock-slide delays and blizzard presented only OK; acknowledged. Saved checkpoint through File → Save (`C:\MECC\YUKON\BLIND.GAM`, host `local/emulator/windows/MECC/YUKON/BLIND.GAM`) during a crowd event, no reload. Arrived Sheep Camp October 27; October 28 journal: 993 lb food, $412. Theft entry said 112 lb lost. Journal also displayed an October 3 Chilkoot Trail entry about a ship hitting an iceberg, despite the walking scene; recorded as displayed, cause unknown. Native `05-sheep-camp-journal.png`.
12. At Sheep Camp chose Trail sign → “Yes, let's go.” No camp purchases or dog-team hire made.
13. Linda caught her foot between rocks and sprained her ankle just after leaving Sheep Camp. Chose “OK, let's stop and rest!” rather than continuing immediately. The trail resumed afterward, with November 4 displayed at Summit–Scales. Acknowledged the Scales and Golden Stairs educational scenes.

14. Customs officer welcomed us to Canada; asked “Can we pass?” Refused: total 2,000 lb food and $100 tax required; officer would guard current supplies, told us to go back for more. Chose OK; automatic return trail began, with further crowd delays and Golden Stairs scene. Native `06-customs-refusal.png`.

15. Returning from customs: player fell; chose “Yes, let's stop” to rest. Blizzard delays acknowledged. Back at Sheep Camp December 2: journal 861 lb food, $412 cash. Native `07-return-sheep-camp-journal.png`. Entered outfitter tent and bought 1,600 lb food for $240 (“Here you are”). Merchant explained 400 lb/$60 packages, about 100 lb per person per month, customs 1,000 lb/person.

16. Chose Trail → “Yes, let's go.” Scales/Golden Stairs acknowledged on second uphill journey. Asked customs “Can we pass?” Officer said supplies enough and requested $100 tax. Chose OK; money animation and onward Lake Bennett route followed. December 15 displayed; crowd delay acknowledged.

17. Bennett route winter delays: repeated blizzards and mule train only offered OK; acknowledged. Player ankle sprain → “Yes, let's stop and rest!” January 3, 1898 displayed afterward. Lake Lindeman educational scene acknowledged; journey continued, January 22 displayed.

18. Lake Bennett arrival conversation: told wait until spring and build boat. Asked how → logs/whipsaw and plans sign; asked where logs → use abandoned logs by lake. “I see” → “Thanks for information.” Journal arrived January 27; January 28: 2,077 lb food, $72; native `08-lake-bennett-journal.png`. Boat Plans sign → Plan 1 (first illustrated boat) → Build. No comparative plan specifications were shown. Calendar animation; officer said spring here, ice broken, boat examined and fit, late arrival requires four-day departure wait. Chose OK.

19. Departed automatically after spring wait. Acknowledged Caribou Crossing and Fifty Mile River educational scenes. Miles Canyon image → click to continue → rafting. Consulted only running Help → Game actions → Rafting; popup says move pointer on water, maneuverability affected by boat type. Closed help. Used pointer clicks on visible clear water to steer; course advanced. Boat damaged; chose “Let's try to repair it” (dialogue described two days, compared with week to build new boat).
20. Started bounded native AVI late in Miles Canyon transition, so recording begins at its aftermath, not complete first rafting. White Horse Rapids followed; clicked image and steered via visible water clicks. Boat damaged again; chose repair again. June 16, 1898 displayed in the first post-repair observation; later capture-menu housekeeping allowed travel to advance, and the AVI also includes a June 24 river map. Native `09-white-horse-rafting.avi` contains this second course and outcomes; recording stopped. No reload or minigame retry. Native-tool round trips and sparse observations limit precise collision attribution; damage observed in dialogue, individual collision cause unknown.

21. Five Finger Rapids image → rafting; steered by pointer clicks on visible water. Boat damaged; chose repair for the third time. July 2 displayed on the river afterward. Dawson arrival July 6; July 7 journal: 1,837 lb food, $72 cash, June 2 first boat trip. Native `10-dawson-journal.png`. Arrival is an intermediate town, not an ending.
22. Dawson Claims board → claim map → first selected available marker by Bonanza Creek label, No. 5 Below Bonanza Creek. Linda instructed picking a spot and digging. First spot by creek yielded gold dust; chose “Let's test this claim some more.” Second spot farther upriver selected; it left a plain mound and no new dialogue. Clicking the player silhouette opened the journal; clicking the prospector/gold mound did not show another conversation. Trail sign prompted whether to stake before leaving. Chose “Yes. Let's stake this claim!”

23. Staking entered an automatic mining scene: miners working, gold counter increasing, calendar pages turning. Native `11-mining-ending.avi` starts after this animation was already underway, not at the initial staking click. Counter reached 14,514. Notice said winter was coming, to cash in and head home using Trail. Acknowledged notice; November 2, 1898 displayed. Clicked Trail.
24. Explicit closing dialogue congratulated reaching Dawson and said a little more luck might have meant striking it rich. Native `12-ending-dialogue.png`; chose Thanks. Newspaper headline: “Klondike Pair Reaches Dawson”; subheadline: “They Find Enough Gold to Pay for Passage Home.” Native `13-ending-newspaper.png`; clicked it to continue.
25. Claims of Fame listed `blind`, `Stampeder`, `14586`, `Jul 6, 1898`. Native `14-final-score.png`. This is the displayed final score; the preceding gold counter was 14,514 and cash at Dawson was $72. Their sum equals the displayed score, but its calculation is an inference, not a recovered rule. Date on score board is Dawson arrival, not the November mining date.
26. Clicked Claims of Fame Done to check continuation. Game automatically returned to Seattle Wharf and Enter Your Name with `blind` selected. Native `15-new-run-prompt.png`. This is a fresh-run prompt, not continued mining/travel. Left it unconfirmed; did not play another run. Stopped AVI recording.

## Outcome and verification

**Observed terminal outcome:** reached Dawson, mined the first selected claim, finished when winter/homeward instruction appeared, received an ending newspaper and final score/rank. No death, failure dialog, crash, or softlock was observed. Customs rejection, injuries, and boat damage were recoverable ordinary game obstacles. The claim score screen followed the ending; Done began fresh-run setup. This is evidence of a completed original-game run, not completion of a port or exhaustive game validation.

Run wall duration was approximately **89 minutes** from the first journal capture (2026-10-05 03:40:27.613 UTC) to score capture (05:09:34.061 UTC), including UI/capture overhead and an agent capacity interruption. Exact New Game start was not timestamped. First explicit clock reading during Seattle supply purchase was 03:45:29 UTC; ending newspaper/score observation was about 05:08:40 UTC. Native ending clip duration is 268.858275 seconds (ffprobe). In-game dates: August 23, 1897 opening; July 6, 1898 Dawson arrival; November 2, 1898 before ending.

The agent turn stopped once with a model-capacity error while prospecting. Resumed the same live emulator and run after root follow-up, with the journal open. Closed it and continued; no restart, reload, emulator reset, patch, or invented state was needed. The interruption was outside the game, not a game terminal outcome. Root independently inspected arrival/rafting evidence; its reports are separate ignored files (`independent-arrival-review.json`, `independent-rafting-review.json`). After gameplay ended, root also independently inspected the ending dialogue, newspaper, score and new-run prompt. It reported a full error-free decode of the 268.858275-second ending AVI (ZMBV 640×480, PCM 48 kHz stereo) and matching ISO/archive/installed executable/configuration hashes. These are independent verification reports, separate from the player's observations.

Root's `independent-ending-review.json` records terminal observations, artifact
identities and source/configuration checks. All 16 capture-manifest identities
(15 native captures and the checkpoint save) match local bytes. FFmpeg 8.1.2
fully decoded all three AVIs without errors. The ending check used:

```sh
ffmpeg -nostdin -v error \
  -i local/evidence/blind-playthrough-2026-10-04/11-mining-ending.avi -f null -
ffprobe -v error \
  -show_entries format=duration,size:stream=index,codec_name,width,height,sample_rate,channels \
  -of json local/evidence/blind-playthrough-2026-10-04/11-mining-ending.avi
```

The same decode/probe commands were applied to `02-seattle-to-dyea.avi` and
`09-white-horse-rafting.avi`. Full decoding checks stream integrity; root's visual
inspection covered selected journal/rafting frames and the four terminal PNGs.

## Save/reload and limits

One normal game save `BLIND.GAM` was made before Sheep Camp. No reload or emulator-state load has been used. Only the initial fresh New Game was started. The completed run is preserved by ending captures and its Claims of Fame entry; after Done the live guest is at unconfirmed new-run setup, so no final save was made. A byte-for-byte copy of the earlier checkpoint is retained as `local/evidence/blind-playthrough-2026-10-04/BLIND-before-sheep-camp.GAM` (11,221 bytes), SHA-256 `f082939ff627671c1a09a166409fcf2195eeb0809f0b3204c884d05f2573bf6f`. No save content was decoded or changed.


## Evidence handoff

All paths below are relative to `local/evidence/blind-playthrough-2026-10-04/`. Native PNGs are guest captures; AVIs are bounded original emulator recordings. `capture-manifest.json` stores exact paths, sizes, and SHA-256 values, including the preserved checkpoint. Reference captures were not replaced. Original ISO, executable/resources, and reference configuration were not modified. No artificial random seed, simulation clock, or emulator speed control was used.

| Capture | SHA-256 |
| --- | --- |
| `01-starting-journal.png` | `f19fe874f03c9bf8b75670496468dddc5c0dce9eb2b42fc9a804bdb3de8e149e` |
| `02-seattle-to-dyea.avi` | `9f9474e3efd04f2e80cb562250bf86bcf25ce49635d37c012c9562ca7d661966` |
| `03-dyea-town.png` | `87ec5a9306a1ddcb20308d0ce84fe0cc5adbdf04dd490801007425d025ef4834` |
| `04-dyea-journal.png` | `42c8e24b0c6c5fa0e55de87181d9e8f7a951967f0819b88a5e67307cfc401988` |
| `05-sheep-camp-journal.png` | `82877467346cbb5c853f0f4f272f587828be37b63016f456ffedb04d99d87821` |
| `06-customs-refusal.png` | `b106a165ad5c11b071e27d2e4885e148dc104429ca59c4c3eafe004de782d432` |
| `07-return-sheep-camp-journal.png` | `c73d6f8e9c68c8c19128e11818026e74db9d3272c588e1964d1eaf8bca4bca97` |
| `08-lake-bennett-journal.png` | `e16777708c081b6823d1b114dc4f98428d4b07c33a35dd28fa385c2f55f8bd1c` |
| `09-white-horse-rafting.avi` | `3421950000c0b15e76a29930c82ac165c2cc826749069919069bf311eaa5d88f` |
| `10-dawson-journal.png` | `661f3a891142c04c55704f41f6b59096806f610b6bb4adbe5632966bf52ded87` |
| `11-mining-ending.avi` | `3b84bd867b6383cf438b8f4d3fecd8004fac1df67019044e3e8eb0d8d1b973c2` |
| `12-ending-dialogue.png` | `5817f35362f2ddced25f9ec93952c9a11ac89a587a9c4945b1c682baa605c6ec` |
| `13-ending-newspaper.png` | `cecde54131ce2d57d0985d6b9ba0e7b8e293d16558fb6ad017ec97fc29bfacb7` |
| `14-final-score.png` | `dc29799f288ab9e3a2afd3a121ca348003884bdeb084978f0fdd5b7a5e75c902` |
| `15-new-run-prompt.png` | `1c3b5764d02734b0787a1f23da9de66d906103986d1f1fd39661933207662282` |

Reproduce observation using the preserved reference environment and ordinary game choices above; do not expect identical random events/timing. Capture through native DOSBox-X Capture menu, then move only newly created `krnl386` outputs to a new run folder. Inspect PNGs directly and decode AVIs using ffmpeg/ffprobe. No continuous full-run video exists; journal captures, two travel clips and one mining/ending clip anchor the recorded path. Sparse observations and host input latency limit exact event timing and collision attribution. Other routes, partners, ships, boat plans, claim sites, intentional failure, and score rules were not tested.
