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
        {"1010:baae", "PackedSound_ReadHeader", "Observed NE3:baae. Storesheader size,flags,declaredpackedbits580,expandedsize14; algorithm3remainsdecoderguardnotreadhere. Flags0/header12skipsmetadata; flags2readpositivecount1..26 withsize14+8*count. Finalstreamcursor=start+headersize, palette256at24 zigzag128/127/etc, control124zero. All871actualheaders and27syntheticcases matchoriginalcount/copy/cursor/palette/ceilblocks with explicitplatformallocation/lockstubs. Blockloopbe0e boundsphysicalstreambytes andremainingblocks, notdeclared580. Pair/seekmeaningunknown. docs/formats/PSND.md."},
        {"1010:bfd8", "PackedSound_ReadOpaqueCheckpointPairs", "Observed NE3:bfd8. Readswordcount584; zero returnsimmediately, positiveadvances2, allocatescount*8buffer, copies2words+1dwordperentry unchanged andadvances8each. Boundedpositivecounts1..26provedall703actualindexedheaders+26synthetics; unindexedflags0nevercall. Pairvalue/seeksemanticsunknown; allocation/bufferconstructor/lock stubs explicit. docs/formats/PSND.md."},
        {"1010:be0e", "PackedSound_ReadBlocks", "Observed NE3:be0e. Calls63fe whole64byteblock, repeatcounter126/constantdword12a, advancesmemorystream windows; loopguardsrequestedcount, remainingblocks18 andphysicalavailablebytes, notdeclaredpackedbits580. Nineactualterminaldiscrepancies executeoriginalwholeblock/cursors/counts with boundedrelocatedsuffix, no blockbehaviorstubs; stop with0..7unusedphysicalbits. Wholeprocessor/hugeallocation/seek/playback excluded. docs/formats/PSND.md."},
        {"1010:bbee", "PackedSound_EmitExpandedBytes", "Observed NE3:bbee. Clampsrequestedbytes againstexpanded14-minus-emitted570; readswholeblocks viabe0e, retainsfinalpartialblockbytes56e, clampsreportedtotaltoexpanded14. Sourcecontrolflowcheckedagainstdisassembly; wholebbee notnative-emulated. Pythonsequentialdecoder emitsfirstexpandedbytes afterceil64blockdecode; partialpadding retained asmetadata. docs/formats/PSND.md."},
        {"1010:63fe", "Packed_Decode64ByteBlock", "Observed sharedNE3:63fe. Contextfar,streamfar,bitcursorDWORD,destinationfar,repeatfar. Type0ordinary6614,1hybrid6540,2recursiveabsolute24bitreference withoutercursorrestore/repeatdiscard,3constantbyte+optional16repeat. OriginalNE1:0000/0062/0129bithelpers. Nineactualsoundterminalblocks match64bytes/cursors underoriginalbe0e loop; broaderimage/localpalette/recursivecasesnotestablishedbythatproof. No guessedCsignature. docs/formats/PSND.md."},
        {"1010:9b34", "PSND_IntegrateSamples", "Observed NE3:9b34. BP06=fourstatebytesfar,0a=orderDWORD,0e=lengthDWORD,12=samplebufferfar. Order0returnsbytes/stateunchanged;1..4 integratebyte+80 intodeepeststate thenprecedingstate+80, overwritingwithstate0.47source-mappedSeattlevoices matchall7626207samples/119127integercalls;all13actualrareorder0/3/4voices matchnativeinteger/converter separately. Callerstatepersistsacrosschunks. No mixer/playback claim. docs/formats/PSND.md."},
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
