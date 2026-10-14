// Observed dialogue-to-PSND routing; do not install guessed signatures.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateImageCompositing extends GhidraScript {
    private static final String SOURCE = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
    private static final String[][] ITEMS = {
        {"1000:0344", "Image_CopyExceptKey", "Observed NE0001:0344. Source DS:ESI and destination ES:EDI; width/height dwords BP+0e/+12; row strides BP+16/+1a; excluded source byte BP+1e into AH. Writes only source bytes unequal to AH. Caller NE0003:0d90 supplies zero. Rendering-mode and scene dispatch not fully traced."},
        {"1000:04fc", "Image_CopyReverseExceptKey", "Observed NE0001:04fc. Equivalent excluded-byte copy with source traversal decrementing ESI, destination incrementing EDI. Caller NE0003:0e4c supplies zero. Flipped frame/table semantics remain unvalidated."},
        {"1000:042a", "Image_CopyRectangle", "Observed NE0001:042a. Unconditional byte rectangle copy through REP MOVSD/MOVSB with source/destination strides. Caller NE0003:0c56 demonstrates a separate path from excluded-byte rendering."},
        {"1010:0d90", "Image_CopyZeroKeyWrapper", "Observed NE0003:0d90. Checks nonzero width/height then pushes byte-key word zero at0d9f and calls NE0001:0344 at0dc5. Input caller/scene mapping incomplete."},
        {"1010:0e4c", "Image_CopyReverseZeroKeyWrapper", "Observed NE0003:0e4c. Checks nonzero width/height then pushes byte-key word zero at0e5b and calls NE0001:04fc at0e81. Input caller/scene mapping incomplete."},
        {"1008:5c54", "Image_ComposeZeroKeyClipped", "Observed NE0002:5c54. Clips source/destination rectangles, branches on flip byte BP+0a; at5e93/5eaa calls NE3:0e4c/0d90 which supply index-zero key. Buffer table NE6:69ca slot34 resolves here. Bubble spritee554 reaches it through CBMP table67ea slot30->7eb0 and manager4290 destination+4 buffer from38d4/4e4e. Full live pixel comparison pending."},
        {"1008:4290", "SpriteManager_RedrawChanged", "Observed NE0002:4290. Changed visible sprites: if manager+8 absent, pushes manager+4 image buffer at430e and calls sprite slot0c at431b. Original startup manager constructor da7c passes zero,38d4 omits+8. Sprite table71e8 slot0c is e554. If+8 exists, uses sprite slot8 instead; that separate path unvalidated."},
        {"1008:7eb0", "CBMP_ComposeFrame", "Observed NE0002:7eb0. CBMP table NE6:67ea slot30. Selects frame via slot3c, arranges source/destination rectangles, forwards flip byte BP+0a and original destination BP+14 to virtual slot34 at7f79. Selected destination buffer table69ca slot34->5c54, explicit zero-key compositor."},
        {"1008:4e4e", "ImageBuffer_Create", "Observed NE0002:4e4e. Installs far table NE6:69ca (Ghidra1028:69ca) at4e79/4e7e and calls5708. Manager38d4 creates+4 via this at39b6; table slot34->5c54. Existing parser image indices remain separate from display normalization."},
        {"1008:3ee2", "SceneManager_CopyBackground", "Observed NE0002:3ee2. Manager slot20, table NE6:706a. Stores supplied CBMP in+0c, gets frame via resource slot3c, then at3f70 calls image buffer(manager+4) slot20. Table69ca slot20->515a, unconditional rectangle copy, preserving source index0. Scene loader0002:0002 at0353 reads SCNE first word, CBMP server56d4 at0364, then manager slot20 at03a0."},
        {"1008:515a", "Image_CopyRectangleClipped", "Observed NE0002:515a. Image buffer table69ca slot20. Locks source/destination buffers and supplies clipped rectangles to NE3:0c56 at528e, whose0d84 calls unconditional NE1:042a. This background path copies index0; it is distinct from bubble slot34 zero-key composition."},
        {"1008:6a66", "Display_InitializeIndexedContext", "Observed NE0002:6a66. Copies palette wrapper param+06 handle into context+1a at6af1, SELECTPALETTE at6b02/6b42. Constructs8bit BITMAPINFO and identity256word logical-color table at6cbd. Startup NE1:7005 passes final system-adjusted DS00ac palette wrapper via530c and NE3:0c28. Does not use embedded palette0 unmodified."},
        {"1008:3dc8", "SceneManager_BlitRegions", "Observed NE0002:3dc8. Iterates dirty regions; at3e8a calls NE3:0b92 with manager+4 indexed image buffer and display context; wrapper calls NE2:6112. Startup final palette passed via530c to indexed context6a66. Live GDI mode branch/native API returns untraced."}
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
