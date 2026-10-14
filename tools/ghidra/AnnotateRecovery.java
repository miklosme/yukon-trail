// Persist bounded image/palette recovery names and observed on-disk layouts.
// No guessed parameter signatures, runtime selectors, or general PSND decoder.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.*;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public class AnnotateRecovery extends GhidraScript {
    private static final String SOURCE = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
    private static final CategoryPath CATEGORY = new CategoryPath("/YukonTrail/ObservedImage");
    private static final String[][] FUNCTIONS = {
        {"1000:0000", "Packed_ReadMSBBits", "Observed NE0001:0000. MSB-first reader. Independent bounded original-code probe: bytes12345678, offset4, length8 returns0x23. Default decompiler signature is unverified."},
        {"1000:0062", "Packed_ReadEscapeBytes", "Observed NE0001:0062. Base-bit symbols; all-ones escape adds extension chunks with 8-bit wrapping until maximum or nonescape extension. Returns absolute bit position in DX:AX. BP after saved registers: input far+1c, bitpos dword+20, base word+24, extension word+26, maximum word+28, count word+2a, output far+2c. 679 combined reader comparisons for CBMP1/2 match original code; see docs/formats/CBMP.md."},
        {"1000:0129", "Packed_ReadHybridBytes", "Observed NE0001:0129. Falls back to0001:0062 when maximum>>base is zero. Otherwise small-value prefix and bounded unary groups, preserving byte masks/results and signed16 group arithmetic. Same stack layout after full register save. No guessed C signature installed."},
        {"1000:83e4", "YukonArchive_RegisterPostreadPattern", "Observed NE0001:83e4. Adds logical tag and zero-terminated signed-word pattern to context registry, stride0x54. Startup0001:677f..6a25 registers17 patterns; original isolated registration execution matches raw push-sequence extraction. Actual tags include ACTS, ANMS, SPRT (correcting earlier transcription). CBMP/PSND absent. Runtime guest DS unobserved. See docs/formats/POSTREAD.md."},
        {"1000:8462", "YukonArchive_ApplyPostreadPattern", "Observed NE0001:8462. Context+70a count, registry+7a stride54; absent tag unchanged. Opcodes -1 skip1,-2 swap16,-3 swap32,-4 swap16 count/set single loop slot,-5 decrement signed16/repeat,-6 skip256,-7 first-op whole-word swap,-8 signed skip operand. Checks end after each operation. Full original routine plus swap helpers match bounded synthetic/source buffers; huge selector and malformed behavior excluded. BP+06=context far,+0a=length dword,+0e=buffer far,+12=tag dword; RETF10. See tools/yukontransform.py and docs/formats/POSTREAD.md."},
        {"1008:455e", "CBMP_ReadFrameTable", "Observed NE0002:455e. Count word at payload+0; frame records12 bytes at+2: width word+0,height word+2,offset dword+4,length dword+8. Supported positive-dimension proof in tools/yukonbmp.py; signed/flipped paths not validated."},
        {"1008:464e", "CBMP_ExtractFrame", "Observed NE0002:464e. Reads frame geometry/offset and calls0003:698e for packed image expansion. Default decompiler pointer types and full clipping/transparency behavior remain unverified."},
        {"1010:698e", "CBMP_UnpackTiledImage", "Observed NE0003:698e. Initializes pixel-writer context then invokes0003:62e2. Uses0003:6a28 callback to place64-byte blocks as8x8 tiles."},
        {"1010:62e2", "Packed_ExpandBlocks", "Observed NE0003:62e2. Header fields: u16 header_size,+2 algorithm byte,+3 flags byte,+4 packed bit count dword,+8 expanded size dword. Block control2bits:0 escape values,1 hybrid values,2 absolute24-bit bitstream reference,3 constant byte with optional16-bit repeat. Algorithm3 flags1 CBMP1/2 exact sizes and bit consumption verified; audio flags2 not decoded."},
        {"1010:66e8", "Packed_SelectLocalPalette", "Observed NE0003:66e8. For global palette flag, 2bit selector:0 global,1 cumulative-increasing subset via0003:679e,2 delta/reset subset via0003:687c. Selector3 unsupported by recovery tool. Do not infer semantics from resource names."},
        {"1010:679e", "Packed_ReadCumulativePalette", "Observed NE0003:679e. Reads6-bit token count and two3-bit width-minus-one fields. Hybrid tokens select global indices cumulative_sum(tokens)+entry_index."},
        {"1010:687c", "Packed_ReadDeltaResetPalette", "Observed NE0003:687c. Reads token count/widths. First token absolute index; nonzero tokens add, zero consumes next token as absolute reset. Token count differs from emitted palette length."},
        {"1010:6a28", "CBMP_WriteColumnMajorTile", "Observed NE0003:6a28. Writes8x8 pixel blocks, advancing tile y first then x. Partial bottom/right crop required for visible geometry. CBMP2 border matches6230 native capture pixels at50,234 after6-bit DAC conversion; exterior/fill excluded."},
        {"1000:5eb4", "Display_CreateEmbeddedPalette", "Observed NE0001:5eb4. FINDRESOURCE type2000 ID100, then LOAD/LOCKRESOURCE. Count at+16, RGB entries at+18 stride4 copied into LOGPALETTE with flags4. Source custom NE resource at file0x618e0 length1056: RIFF PAL data,256 entries. Calls GDI CREATEPALETTE at5f8e; system-palette path also follows."}
    };

    private Address address(String value) { return currentProgram.getAddressFactory().getAddress(value); }
    private void field(StructureDataType type, int offset, DataType value, String name) {
        type.replaceAtOffset(offset, value, value.getLength(), name, null);
    }
    private List<StructureDataType> layouts() {
        List<StructureDataType> result = new ArrayList<>();
        StructureDataType frame = new StructureDataType(CATEGORY, "CBMPFrameRecord", 12);
        field(frame, 0, UnsignedShortDataType.dataType, "width");
        field(frame, 2, UnsignedShortDataType.dataType, "height_raw");
        field(frame, 4, DWordDataType.dataType, "payload_relative_offset");
        field(frame, 8, DWordDataType.dataType, "compressed_length");
        result.add(frame);
        StructureDataType header = new StructureDataType(CATEGORY, "PackedChunkHeader", 12);
        field(header, 0, UnsignedShortDataType.dataType, "header_size");
        field(header, 2, ByteDataType.dataType, "algorithm");
        field(header, 3, ByteDataType.dataType, "flags");
        field(header, 4, DWordDataType.dataType, "packed_bit_count");
        field(header, 8, DWordDataType.dataType, "expanded_byte_count");
        result.add(header);
        return result;
    }
    @Override public void run() throws Exception {
        if (!SOURCE.equals(currentProgram.getExecutableSHA256())) throw new IllegalStateException("Unexpected source identity");
        String[] args = getScriptArgs();
        if (args.length != 2 || !(args[0].equals("apply") || args[0].equals("verify"))) throw new IllegalArgumentException("apply|verify and audit path required");
        boolean apply = args[0].equals("apply");
        List<String> audit = new ArrayList<>();
        audit.add("SOURCE_SHA256\t" + SOURCE);
        for (String[] item : FUNCTIONS) {
            Function function = currentProgram.getFunctionManager().getFunctionAt(address(item[0]));
            if (function == null) throw new IllegalStateException("Missing function " + item[0]);
            if (apply) {
                if (!function.getName().startsWith("FUN_") && !function.getName().equals(item[1])) throw new IllegalStateException("Refusing conflicting name " + item[0]);
                function.setName(item[1], SourceType.USER_DEFINED);
                function.setComment(item[2]);
            }
            if (!function.getName().equals(item[1]) || !item[2].equals(function.getComment())) throw new IllegalStateException("Missing annotation " + item[0]);
            audit.add("FUNCTION\t" + item[0] + "\t" + function.getName());
            audit.add("COMMENT\t" + item[0] + "\t" + function.getComment());
        }
        for (StructureDataType wanted : layouts()) {
            DataType stored = currentProgram.getDataTypeManager().getDataType(CATEGORY, wanted.getName());
            if (stored == null && apply) stored = currentProgram.getDataTypeManager().addDataType(wanted, DataTypeConflictHandler.KEEP_HANDLER);
            if (!(stored instanceof Structure) || !stored.isEquivalent(wanted)) throw new IllegalStateException("Missing/conflicting structure " + wanted.getName());
            audit.add("TYPE\t" + stored.getPathName() + "\t" + stored.getLength());
            for (DataTypeComponent expected : wanted.getDefinedComponents()) {
                DataTypeComponent actual = ((Structure)stored).getComponentAt(expected.getOffset());
                if (actual.getLength() != expected.getLength()) throw new IllegalStateException("Wrong field width");
                audit.add("FIELD\t" + stored.getName() + "\t" + actual.getOffset() + "\t" + actual.getLength() + "\t" + actual.getFieldName());
            }
        }
        Files.write(Path.of(args[1]), audit, StandardCharsets.UTF_8);
        println("Recovery annotations " + args[0] + ": " + audit.size() + " records");
    }
}
