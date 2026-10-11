// Narrow source-verified sequential PSND recovery. No guessed C signatures.
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

public class AnnotateSound extends GhidraScript {
    private static final String SOURCE = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
    private static final CategoryPath CATEGORY = new CategoryPath("/YukonTrail/ObservedSound");
    private static final String[][] FUNCTIONS = {
        {"1010:acea", "PSND_CreateProcessor", "Observed NE0003:acea. Reads type1/type2/type0 records from stream. Header bytes6,7,8,10 copied to words1c,1e,20,1a. State2c initialized80808080. Installs method table NE0006:82c0, mapped1028:82c0. Selected sequential PSND1 recovery in docs/formats/PSND.md; seeking/other variants unvalidated."},
        {"1010:b636", "PackedSound_CreateReader", "Observed NE0003:b636. Creates packed stream reader and calls0003:baae for compression header initialization. Default decompiler parameter types remain unverified."},
        {"1010:baae", "PackedSound_ReadHeader", "Observed NE0003:baae. Reads chunk fields header_size,algorithm,flags,packed_bit_count,expanded_size. Flags2 calls0003:bfd8. Initializes256-entry byte palette128,127,129,126,... at+24 and clears local palette control byte+124. Selected PSND1 header_size54,algorithm3,flags2."},
        {"1010:be0e", "PackedSound_ReadBlocks", "Observed NE0003:be0e. Reads64-byte blocks through0003:63fe, retains repeat counter and constant dword, and advances stream windows. Whole stream/seek semantics not emulated by native verifier."},
        {"1010:9b34", "PSND_IntegrateSamples", "Observed NE0003:9b34. BP+06=four-byte state far,+0a=order dword,+0e=length dword,+12=sample buffer far. Orders1..4 integrate byte+80 into deepest active state then each preceding state+80, overwriting sample with state0. Caller retains state across chunks. All81792 PSND1 bytes and final state match original bounded x86 execution; no Windows calls."},
        {"1010:92dc", "PSND_CreateWaveFormat", "Observed NE0003:92dc. Processor getter slots34/38/3c yield channels/bits/ratecode. Ratecode11 maps11025,22 maps22050. Writes format tag1 at object44,channels46,rate48,alignment50,bits52. Caller0003:978a passes format+44 to WAVEOUTOPEN at9826. Source PSND1=>mono8bit22050; live resource mapping not established."},
        {"1010:b20a", "PSND_GetChannels", "Observed NE0003:b20a. Returns object word1c derived from type1 record byte6. Method slot NE0006:82c0+34, Ghidra1028:82f4 points here."},
        {"1010:b218", "PSND_GetSampleBits", "Observed NE0003:b218. Returns object word1e derived from type1 record byte7. Method slot NE0006:82c0+38, Ghidra1028:82f8 points here."},
        {"1010:b226", "PSND_GetRateCode", "Observed NE0003:b226. Returns object word20 derived from type1 record byte8. Method slot NE0006:82c0+3c, Ghidra1028:82fc points here."}
    };
    private Address address(String value) { return currentProgram.getAddressFactory().getAddress(value); }
    private void field(StructureDataType type, int offset, DataType value, String name) {
        type.replaceAtOffset(offset, value, value.getLength(), name, null);
    }
    @Override public void run() throws Exception {
        if (!SOURCE.equals(currentProgram.getExecutableSHA256())) throw new IllegalStateException("Unexpected source identity");
        String[] args = getScriptArgs();
        if (args.length != 2 || !(args[0].equals("apply") || args[0].equals("verify"))) throw new IllegalArgumentException("apply|verify and audit path required");
        boolean apply = args[0].equals("apply");
        byte[] slots = new byte[12];
        currentProgram.getMemory().getBytes(address("1028:82f4"), slots);
        byte[] expected = {(byte)0x0a,(byte)0xb2,0x10,0x10,0x18,(byte)0xb2,0x10,0x10,0x26,(byte)0xb2,0x10,0x10};
        if (!java.util.Arrays.equals(slots, expected)) throw new IllegalStateException("Unexpected relocated getter bindings");
        List<String> audit = new ArrayList<>();
        audit.add("SOURCE_SHA256\t" + SOURCE);
        audit.add("GETTER_BINDINGS\t1028:82f4\t1010:b20a,1010:b218,1010:b226");
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
        StructureDataType wanted = new StructureDataType(CATEGORY, "PSNDHeaderRecord", 12);
        field(wanted, 0, ByteDataType.dataType, "record_type");
        field(wanted, 1, ByteDataType.dataType, "record_flags_raw");
        field(wanted, 2, DWordDataType.dataType, "record_length");
        field(wanted, 6, ByteDataType.dataType, "channels");
        field(wanted, 7, ByteDataType.dataType, "sample_bits");
        field(wanted, 8, ByteDataType.dataType, "rate_code");
        field(wanted, 9, ByteDataType.dataType, "byte9_unknown");
        field(wanted, 10, ByteDataType.dataType, "integration_order");
        field(wanted, 11, ByteDataType.dataType, "byte11_unknown");
        DataType stored = currentProgram.getDataTypeManager().getDataType(CATEGORY, wanted.getName());
        if (stored == null && apply) stored = currentProgram.getDataTypeManager().addDataType(wanted, DataTypeConflictHandler.KEEP_HANDLER);
        if (!(stored instanceof Structure) || !stored.isEquivalent(wanted)) throw new IllegalStateException("Missing/conflicting sound structure");
        audit.add("TYPE\t" + stored.getPathName() + "\t" + stored.getLength());
        for (DataTypeComponent expectedField : wanted.getDefinedComponents()) {
            DataTypeComponent actual = ((Structure)stored).getComponentAt(expectedField.getOffset());
            if (actual.getLength() != expectedField.getLength()) throw new IllegalStateException("Wrong field width");
            audit.add("FIELD\t" + actual.getOffset() + "\t" + actual.getLength() + "\t" + actual.getFieldName());
        }
        Files.write(Path.of(args[1]), audit, StandardCharsets.UTF_8);
        println("Sound annotations " + args[0] + ": " + audit.size() + " records");
    }
}
