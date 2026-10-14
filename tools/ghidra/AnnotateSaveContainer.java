// Observed fixed save transfer layout; do not install guessed signatures.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateSaveContainer extends GhidraScript {
    private static final String SOURCE = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
    private static final String[][] ITEMS = {
        {"1000:94e6","Save_LoadReadThenCheckHeader","Observed NE1:94e6..9697. Check8854 then clear selected globals, open8afe(0), read five raw save blocks through8d88, close8d70, and only then header-check95a9 onward via6:2004. Signature compare4 ignores fifth byte; title bound64/version10 stop at loaded NUL inclusive. Status -1 signature,-2 title,1 lexical lower version,-3 higher,0 equal; nonzero UI message indices5/6/4/7. Original header decision branch and constructor header-global copies match246 synthetic mutations; full cancellation/error UI/rollback/scene reconstruction not native validated. docs/formats/GAM.md."},
        {"1028:2004","String_CompareLoadedBoundedBytes","Observed NE6:2004..203f. Determines length up to bound/firstNUL inclusive of first far argument viaREPNE SCASB, compares unsigned bytes with second far argument viaREPE CMPSB; returns signed -1/0/1. Original helper plus save95a9 branch matches246 header mutations, including post-NUL ignored bytes and lexical version0.10 greater than0.1. No guessed signature installed. docs/formats/GAM.md."},
        {"1000:974a","Save_ReadFiveFixedBlocks","Observed NE1:974a..97eb. Opens selected file via8afe(0), reads five buffers through8d88 in order length5/64/10/386h/2800h: object+4/+9/+49, DS5308state, DS5304journalobject far+0e. Calls8d70 close and returns1 when open succeeded. Successful native instruction path including8d88 transfer-count comparisons matches five captured original saves; only dialog/open and KERNEL I/O substituted. Header validation, short reads, full load/scene rebuild excluded. docs/formats/GAM.md."},
        {"1000:97ec","Save_WriteFiveFixedBlocks","Observed NE1:97ec..988e. Opens selected file via8afe(1), writes same five raw buffers/lengths through8e24; close8d70; returns1 on opened successful path. Original source saves11221bytes; byte-preserving read/write on five evidence saves has zero differences. No endian normalization or guessed state defaults. OS failures, save dialog/cancellation and full session persistence excluded. docs/formats/GAM.md."},
        {"1000:8d88","File_ReadCheckedCount","Observed NE1:8d88..8e23. Passes handle/far buffer/word count to KERNEL::_LREAD at8d9a, stores result inDS563c with highword0, compares against requestedDWORD length. Error UI path separately unrecovered. Successful branch executed unchanged in five original save comparisons, KERNEL I/O supplied in-memory. No guessed signature."},
        {"1000:8e24","File_WriteCheckedCount","Observed NE1:8e24..8ebf. Passes handle/far buffer/word count to file write import at8e36, stores result inDS563c with highword0, compares against requestedDWORD length. Error UI path separately unrecovered. Successful branch executed unchanged in five original save comparisons, KERNEL I/O supplied in-memory. Import identity follows saved loader metadata; no guessed signature."},
        {"1000:8d70","File_CloseHandleWrapper","Observed NE1:8d70..8d87. Passes handle to KERNEL::_LCLOSE at8d79. Successful save read/write harness supplies in-memory close; actual Windows handle lifetime and errors excluded. No guessed signature."}
    };
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2 || !(args[0].equals("apply") || args[0].equals("verify"))) throw new IllegalArgumentException("apply|verify audit-path");
        if (!SOURCE.equals(currentProgram.getExecutableSHA256())) throw new IllegalStateException("Source identity mismatch");
        ArrayList<String> audit = new ArrayList<>();
        audit.add("SOURCE_SHA256\t" + SOURCE);
        for (String[] item : ITEMS) {
            Function f = currentProgram.getFunctionManager().getFunctionAt(currentProgram.getAddressFactory().getAddress(item[0]));
            if (f == null && args[0].equals("apply")) {
                new DisassembleCommand(currentProgram.getAddressFactory().getAddress(item[0]),null,true).applyTo(currentProgram,monitor);
                f = createFunction(currentProgram.getAddressFactory().getAddress(item[0]),null);
            }
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
