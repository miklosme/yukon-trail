// Observed raw sound stream accessors; do not install guessed signatures.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateSoundStreams extends GhidraScript {
    private static final String SOURCE = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
    private static final String[][] ITEMS = {
        {"1018:0ef0", "MemoryStream_Create", "Observed NE0004:0ef0. Constructor calls0003:b56a then installs table0006:89fc. Stores bufferfar at+0e,lengthdword+12,cursordword+16=0. Table+18 points0004:0f4c. Selected PSND kind3ed buffer path uses this stream."},
        {"1018:0f4c", "MemoryStream_GetPointerAndRemaining", "Observed NE0004:0f4c. BP+06 streamfar,+0a outputlengthfar,+0e outputpointerfar. Returns buffer+cursor and length-cursor; when remaining<=0 writes length0 and returns1, otherwise0. Does not read payload. All256 byte1 values and cursor0/end match original native execution with zero payload reads. PSND byte1 not interpreted by this stream or0003:acea selected header path."},
        {"1018:0fd8", "MemoryStream_SetCursor", "Observed NE0004:0fd8. Sets cursor+16 to requested dword BP+0a if <=length+12, otherwise clamps tolength and returns1. No sound-record byte parsing."},
        {"1020:8eaa", "FileStream_GetBufferedPointerAndRemaining", "Observed NE0005:8eaa. Calls0005:9168 buffer refill then returns current buffer pointer and remaining bytes. Checks buffer-control bytes+10/+11, not PSND record byte1. File I/O/refill semantics not fully recovered or executed by sound stream verifier."}
    };    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2 || !(args[0].equals("apply") || args[0].equals("verify"))) throw new IllegalArgumentException("apply|verify audit-path");
        if (!SOURCE.equals(currentProgram.getExecutableSHA256())) throw new IllegalStateException("Source identity mismatch");
        byte[] memorySlot = new byte[4], fileSlot = new byte[4];
        currentProgram.getMemory().getBytes(currentProgram.getAddressFactory().getAddress("1028:8a14"), memorySlot);
        currentProgram.getMemory().getBytes(currentProgram.getAddressFactory().getAddress("1028:9b16"), fileSlot);
        if (!java.util.Arrays.equals(memorySlot, new byte[]{0x4c,0x0f,0x18,0x10}) ||
            !java.util.Arrays.equals(fileSlot, new byte[]{(byte)0xaa,(byte)0x8e,0x20,0x10})) throw new IllegalStateException("Unexpected stream slot18 bindings");
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
