// Observed bounded partner acceptance and money mutation; do not install guessed signatures.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateTree extends GhidraScript {
    private static final String SOURCE = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
    private static final String[][] ITEMS = {
        {"1000:1d88","TREE_CopyChoiceAndChild","Observed NE0001:1d88. Copies18byte metadata plus independently allocatedNULtext into22bytechoice record, advances274bytes, recursivelycalls1c56 if nexttextnonempty, otherwise skips empty nochildrecord. Runtime88bytenode has10choicefar+4, parentfar+2c,10childnodefar+30. SelectedTREE3400/2100 graphs matchoriginalparser withboundedallocator only. docs/formats/TREE.md."},
        {"1000:2468","Dialogue_HandleMessage","Observed NE0001:2468; actualtable0006:609a slot4 (base608a slot4 isruntimepurevirtualthunk). Inmenu phasewordce=3, click/keyboard0464/0467 mapsvisibleindex throughb6, storesselectedchoice actionfar+26, callsvirtualslot10 first, passesitsreturn0/1 to2fec. Afterwards f0/3 suppressselectedplayeroption. Otheraudio/timer/UIeffects notfullyported. docs/formats/TREE.md."},
        {"1000:2fec","Dialogue_ApplyChoiceLinks","Observed NE0001:2fec. Marksresponse/choiceword0=1. Calleractionreturn1 exposeschildresponse text/voice andinvokeschildresponseaction. Choiceword2 isabsolutelevel vsdepthb4. Backward<=depth popsparent2c untildepth<link; unvisitedtextoptions controladditionalrewind. Forward32a6 descends onlyifchildnodefirstoptionresponsepointer+30 nonnull, returningbeforeauto-rewind.176 native selectedchoicecases match model, actioncallbackobservation/UIrefreshboundary explicit. docs/formats/TREE.md."},
        {"1008:248c","MerchantDialogue_Create","Observed NE0002:248c. Calls0001:0724 theninstalls0006:66d6; table+10 points0002:2884. Fullscene/resourcecreatorbinding notnative-emulated."},
        {"1008:2884","MerchantDialogue_ExecuteAction","Observed NE0002:2884; methodtable0006:66d6 slot10. Selectedopcode220 passescount1,costactionword4,itemactionword2 to24d0. Otheropcodes unsupported inboundedpurchase model. TREE2100confirmation+4d14 action220/109/8/0; originaldispatch executes in112case nativeproof."},
        {"1008:24d0","MerchantDialogue_PurchaseSelectedItem","Observed NE0002:24d0. Affordguard signedwrappingcash+bank>=cost; elsepartner4 opensTREE600/type300 andreturns0. Success9e40(CONVfirstword),a184(-cost,slot0),optionalcache927d dirty, item109→a184(+1,slot6),returns1. Slot6word306 whipsaw; native112source states match boundedmodel. No directdate/journalcalls; GUI/refusalcreation excluded. docs/SEATTLE-RULES.md."},
        {"1000:9e40","State_SetWord318","Observed NE0001:9e40. Gate334zero copiesargumentword tostate318 anddirtyDS52fcobject54=1. SelectedmerchantcallerpassesCONVfirstword17. Broaderword318meaningunknown."},
        {"1000:a2e4","State_MarkConversationSeen","Observed NE1:a2e4. If gate334zero and index!=ffff, writes1 atstate218+2*index thenDS52fcobject54dirty. LindaCONV3400firstword4 maps220. Dialogueconstructor0724 callsinitialselector2bc2 at0883 BEFOREmarka2e4 at0937; selected18nativecases confirmpreviousflagselectsvoice3401/3400 thenmark. Otherindicesunsupported inselectedmodel. docs/SEATTLE-RULES.md."},
        {"1000:a7bc","State_GetSceneVisitWord","Observed NE1:a7bc readsstate2aa+2*index. Sceneconstructor2:04f0 divides signedsceneID by1000; 0503 readsvisitword, skipsSCNE+8dateiterations ifnonzero. ActualSCNE1000+8=1,4000+8=0.96native selectedconstructorbranchcases matchexplicitvisit/date model; wholeconstructor/UI excluded. docs/SEATTLE-RULES.md."},
        {"1000:a368","State_MarkSceneVisit","Observed NE1:a368 gate334zero writes1 atstate2aa+2*index; nodirectdirtynotification. Sceneconstructor0592 passes signedsceneID/1000 afterfirstvisitdatebranch. Selected1000index1→2ac;4000index4→2b2. Native96cases comparefullsentinelstate. docs/SEATTLE-RULES.md."},
        {"1008:1036","SeattleScene_StartCountdownAnimation","Observed NE2:1036. Signedrequestedcount<=0 coerced1, storesDS1188. Allocatesanimation18bytes onlyifscene18far null; sets scene1e timer from120/count+30 (or+5 sceneID4a38), scene1c from2. Constructor057c invokesonlypositiveexistingDS1188; explicitaction140 invokeswithnonzeroactionword2. Separate fromSCNEfirstvisit+8 datebranch. OSanimation/timerallocation notnativevalidated. docs/SEATTLE-RULES.md."},
        {"1000:a774","State_GetIndexedWord218","Observed NE0001:a774. Returnsunsignedwordstate218+2*index. Selectedcondition2/1 via3:5a34 passesCONVfirstword4, thusstate220 nonzero selectsLinda initialoverride. Broaderarraymeaningunknown;12 selectedconditionnativecases executeactualgetters."}
    };
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2 || !(args[0].equals("apply") || args[0].equals("verify"))) throw new IllegalArgumentException("apply|verify audit-path");
        if (!SOURCE.equals(currentProgram.getExecutableSHA256())) throw new IllegalStateException("Source identity mismatch");
        byte[] slot=new byte[4]; currentProgram.getMemory().getBytes(toAddr("1028:66e6"),slot);
        if(!java.util.Arrays.equals(slot,new byte[]{(byte)0x84,0x28,0x08,0x10}))throw new IllegalStateException("Merchantactionslotbindingdiffers");
        if(args[0].equals("apply")){
            for(String[] pair:new String[][]{{"1000:2468","1000:29d1"},{"1008:248c","1008:24b1"},{"1008:24d0","1008:262f"},{"1008:2884","1008:29e9"}}){
                ghidra.program.model.address.Address a=toAddr(pair[0]);
                ghidra.program.model.address.AddressSet r=new ghidra.program.model.address.AddressSet(a,toAddr(pair[1]));
                new ghidra.app.cmd.disassemble.DisassembleCommand(a,r,true).applyTo(currentProgram,monitor);
                if(getFunctionAt(a)==null)createFunction(a,null);
            }
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
