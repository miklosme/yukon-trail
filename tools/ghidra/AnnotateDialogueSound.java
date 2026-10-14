// Observed dialogue-to-PSND routing; do not install guessed signatures.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateDialogueSound extends GhidraScript {
    private static final String SOURCE = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
    private static final String[][] ITEMS = {
        {"1000:1f02", "Dialogue_LoadTree", "Observed NE0001:1f02. Reads TREE resource, scans up to five 0x112-byte initial records by text at+16, sets response cursor to payload+116+n*112, calls0001:1c56. Selected TREE1 has no initial text and first response at+116. Full TREE schema/conditions unknown."},
        {"1000:1c56", "Dialogue_CopyResponseNode", "Observed NE0001:1c56. Copies response words0,2 and byte ranges4..f into allocated node, response word10 into node+10, and response string+12 into node far pointer+12. Advances response cursor112. Word10 reaches PSND ID via0001:2bc2 and0001:0724. Full tree traversal unvalidated."},
        {"1000:2bc2", "Dialogue_SelectTextAndVoice", "Observed NE0001:2bc2. Selects eligible initial text or active response; response node+12 text far pointer goes conversation+10, node word10 goes conversation+24. At0001:0d15..0d25, +24 supplied as ID with kind3ed to0002:9cd6. Conditions and side effects not recovered."},
        {"1008:9cd6", "ResourceCache_GetByIdAndKind", "Observed NE0002:9cd6. Cache key is dword BP+0a: low word resource ID, high word kind. Cache miss at9e04..9e10 calls virtual slot+4 with original key and cache far pointer. Sound server DS009c created at0001:6c7a via0003:e1ae, table0006:883a slot+4 maps to0003:e1ee. Cached lifetime branches remain unvalidated."}
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
