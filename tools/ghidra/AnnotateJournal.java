// Selected journal helpers and pending action; no guessed signatures or calendar defaults.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateJournal extends GhidraScript {
    private static final String SOURCE = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
    private static final String[][] ITEMS = {
        {"1008:0c72", "SeattleScene_HandleMessage", "Observed NE0002:0c72; table0006:6646 slot4.0465→0e1c refreshwindow1:607e/59dc and slot8→0f62 pauseanimation.046a→0e40 snapshots manager+48 to scene+54 and setscontrollerflag1.046b→0e98 restores snapshot/background, controllerflag0, relatedobjectflags0, cursor/resource1:47d8. Common pendingword+0e clears then dispatches8byteaction+10 throughslot10→0890; not safe to assume actionzero.0466 timer branch calls0740 only active top scene matchingtimer. No direct datewrite in465/46b. docs/SEATTLE-RULES.md."},
        {"1008:0740", "SeattleScene_ProcessAnimationTimer", "Observed NE0002:0740. When animationfar+18 nonnull and signedDS1188countdown>0, updatesanimation, calls1:a0c2 dateincrement at07a4, decrementscountdown thenreturns. Oncecountdown<=0 cancels timers and animation, queuesselectedscene4000 action(1,400,31000,0). Timer0466 invokes only ifsceneactive andtimeridmatches+1e. Do not equate allsceneleave with dayadvance."},
        {"1000:a0c2", "State_AdvanceOneDayWords", "Observed NE0001:a0c2. Gate334nonzero suppresses; otherwise wrappingINCstate30e/day28, fixedmonthlengths31,28,31,30,31,30,31,31,30,31,30,31; validdayoverflow setsday1, incrementsmonth2a/wrap12to1 and rawphase310; dirtyobjectDS52fcword54=1.2190 fullstate native comparisons match explicit DateWords model, no behaviorstubs. No initialdate/year defaults or Linda directcall inferred."},
        {"1010:2268", "SceneResourceController_Create", "Observed NE0003:2268. Installs table0006:78d2, ownerfar+1e, loads SCRP at caller supplied id into+1a, calls0003:2394. Linda0002:0f92 passes owner SCNE+6; selected SCNE4000 yieldsSCRP4000. This is a resource controller; no claim of general script VM."},
        {"1010:2394", "SceneResourceController_PopulateChildren", "Observed NE0003:2394. SCRP countword then18byte records. For each evaluates3fourbyte conditions via0003:5118, copies18byte record into child+0c when all succeed. Kind3 loads SPRT and creates targetobject; otherkind semantics and conditions not fully recovered. Selected SCRP4000 has16records. docs/SEATTLE-RULES.md."},
        {"1010:26f2", "SceneResourceController_SetKind3FlagWord", "Observed NE0003:26f2. Traverses linked childfar+0c, nextfar+8. Kindword+0c=3 writes targetfar+1e word+84=argument; if argument0 also targetword+82=1. Linda0002:0f92 passes1. Flag purpose unknown; no calendar mutation in this routine."},
        {"1000:cdae", "Journal_AppendDateHeading", "Observed NE0001:cdae. Reads day/month through0001:a68e state28/2a, appends source month and decimalday; signed state310 from0001:a850 <=5 selects data13:0f90 year1897 suffix, otherwise0f99 year1898. Component total must stay<255. No date writes.576 selected native model cases match. No calendar semantics inferred. docs/SEATTLE-RULES.md."},
        {"1000:cff8", "Journal_AppendPlaceHeading", "Observed NE0001:cff8. Reads location tuple state34/36/38 through0001:a6f4. Firstword200 selectsregiontable; secondword index<<5 atd1f2 selectsplace. Selectedindex0 appends data13:0fa2 Seattle string if total<255; thirdwordunused.48source/native thirdwordcases includeactualscene1000/3000/4000 andboundarywords. Otherregion/placeindices unrecovered. Historical200/0/0 fixture notactualsceneinitialization. No state writes."},
        {"1000:d364", "Journal_AppendEntrySeparator", "Observed NE0001:d364. If existing global journal DS5304 object text+0e strlen>0, append data13:1093 then1096 CRLF parts, capacity<255. Empty prior journal adds nothing."},
        {"1008:2040", "CSTR_GetStringAtIndex", "Observed NE0002:2040. Zero-based index in transformed CSTR string list; selected event7 partner4 requestsindex3, the fourth CSTR505 string. Internalentry relocation at205e targets0006:1f88 although sourceplaceholderoffset1b86. Raw CSTR505 countword postreadswap is separate."},
        {"1000:4dba", "SceneManager_QueueAction", "Observed NE0001:4dba. Copy8actionbytes to manager+4 via0006:28c0 then word+2=1. Selected Linda continuation(3,0,0,0) native verified against3sentinelbuffers; preserves other bytes. Queue does not itself advance date or draw scene."},
        {"1000:3e6a", "SceneManager_GetParent", "Observed NE0001:3e6a. Searches10farstackentries starting manager+16 for child pointer, returns nextentry onmatch. Linda caller climbs until objectkind+6=200 before0002:0f92 and queueaction3. Broader graph semantics unknown."}
    };
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2 || !(args[0].equals("apply") || args[0].equals("verify"))) throw new IllegalArgumentException("apply|verify audit-path");
        if (!SOURCE.equals(currentProgram.getExecutableSHA256())) throw new IllegalStateException("Source identity mismatch");
        if (args[0].equals("apply")) {
            ghidra.program.model.address.AddressSet range = new ghidra.program.model.address.AddressSet(toAddr("1000:cdae"), toAddr("1000:d363"));
            for (String value : new String[]{"1000:cdae", "1000:cff8"}) {
                ghidra.program.model.address.Address address = toAddr(value);
                byte[] prologue = new byte[4]; currentProgram.getMemory().getBytes(address, prologue);
                if ((prologue[0] & 255) != 0xc8 || prologue[3] != 0) throw new IllegalStateException("Unexpected ENTER prologue " + value);
                new ghidra.app.cmd.disassemble.DisassembleCommand(address, range, true).applyTo(currentProgram, monitor);
                if (getFunctionAt(address) == null) createFunction(address, null);
            }
        }
        if (args[0].equals("apply") && getFunctionAt(toAddr("1008:0c72")) == null) {
            byte[] prologue = new byte[4]; currentProgram.getMemory().getBytes(toAddr("1008:0c72"), prologue);
            if (!java.util.Arrays.equals(prologue, new byte[]{(byte)0xc8,0x28,0,0})) throw new IllegalStateException("Unexpected scene callback prologue");
            ghidra.program.model.address.AddressSet range = new ghidra.program.model.address.AddressSet(toAddr("1008:0c72"), toAddr("1008:0f61"));
            new ghidra.app.cmd.disassemble.DisassembleCommand(toAddr("1008:0c72"), range, true).applyTo(currentProgram, monitor);
            createFunction(toAddr("1008:0c72"), null);
        }
        ArrayList<String> audit = new ArrayList<>();
        audit.add("SOURCE_SHA256\t" + SOURCE);
        for (String[] item : ITEMS) {
            Function f = currentProgram.getFunctionManager().getFunctionAt(currentProgram.getAddressFactory().getAddress(item[0]));
            if (f == null) throw new IllegalStateException("Missing function " + item[0]);
            if (args[0].equals("apply")) {
                if (!f.getName().startsWith("FUN_") && !f.getName().equals(item[1])) throw new IllegalStateException("Conflicting name " + item[0]);
                f.setName(item[1], SourceType.USER_DEFINED);
                f.setComment(item[2]);
            }
            if (!f.getName().equals(item[1]) || !item[2].equals(f.getComment())) throw new IllegalStateException("Annotation missing " + item[0]);
            audit.add("FUNCTION\t" + item[0] + "\t" + f.getName());
            audit.add("COMMENT\t" + item[0] + "\t" + f.getComment());
        }
        Files.write(Path.of(args[1]), audit, StandardCharsets.UTF_8);
    }
}
