// Observed bounded partner acceptance and money mutation; do not install guessed signatures.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateInitialState extends GhidraScript {
    private static final String SOURCE = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
    private static final String[][] ITEMS = {
        {"1000:9900","State_ResetOriginalRawWords","Observed NE1:9900..9bb8. Resetsnamesfirstbytes0/14; Aug23/month8,partner312ffff,elapsed30e1,phase3101,cash350/bank0,inventoryslots2fe..30a0,conversationarray218/61words0,visits2aa/40words0,gate334/flag3440. Writesextendthroughword384; holespreserved, notwholebuffermemset. Randomwordfrom6:2a28 selects314/316 pair7/10,8/11,9/12. Fullreset+originalRNG/multiply/memset36nativecases match sentinelmodels withoutbehaviorstubs; seedexplicit, alloc/sceneexcluded. docs/SEATTLE-RULES.md."},
        {"1000:9ffa","State_SetLocationTuple","Observed NE1:9ffa. Gate334zero copies3wordsfromfarargumenttostate34/36/38 thendirtyDS52fcobject54. ActualSeattleconstructor2:00e6..0214 sets(200,0,sceneID) forselected1000/2000/3000/4000,8nativecases provefullsentinelstate/gate. Journalcff8 firstword200 checkssecondwordindex<<5; selectedindex0 appendsSeattleliteral whilethirdunused.48nativejournal thirdwordcases includeactual1000/3000/4000 andboundaries. Othersecondindices unsupported. docs/SEATTLE-RULES.md."},
        {"1000:98ea","State_ResetOriginalWrapper","Observed NE1:98ea..98ff. Passesexplicitfarstateargumentto9900 thenreturns samefar pointer. Newsessionconstructor929e9394 andloadroutine9698970e alsocall9900; loadcanoverwrite defaults later, soresetaloneisnotloaded-save state."},
        {"1028:2a28","Random_NextOriginal15Bits","Observed NE6:2a28. Originalmultiply2c48 computesDS483eDWORDseed*214013, adds2531011 withu32wrap, storesseed, returnsupperword&7fff. Originalinstructionsrunin36resetproofcases with12controlledseeds; noRNGstub. OSseedinitializationunknown; nofixedseeddefault. docs/SEATTLE-RULES.md."}
    };
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2 || !(args[0].equals("apply") || args[0].equals("verify"))) throw new IllegalArgumentException("apply|verify audit-path");
        if (!SOURCE.equals(currentProgram.getExecutableSHA256())) throw new IllegalStateException("Source identity mismatch");
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
