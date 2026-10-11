// Apply or verify narrowly supported archive annotations for this exact NE import.
// Does not modify original bytes, invent flat far pointers, or install guessed
// parameter signatures. See docs/ARCHIVE-CONSUMERS.md for disassembly evidence.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.data.ArrayDataType;
import ghidra.program.model.data.ByteDataType;
import ghidra.program.model.data.CategoryPath;
import ghidra.program.model.data.DataType;
import ghidra.program.model.data.DataTypeComponent;
import ghidra.program.model.data.DataTypeConflictHandler;
import ghidra.program.model.data.Structure;
import ghidra.program.model.data.StructureDataType;
import ghidra.program.model.data.DWordDataType;
import ghidra.program.model.data.UnsignedShortDataType;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public class AnnotateArchive extends GhidraScript {
    private static final String SOURCE = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
    private static final CategoryPath CATEGORY = new CategoryPath("/YukonTrail/ObservedArchive");
    private static final String[][] FUNCTIONS = {
        {"1000:673a", "YukonArchive_Initialize", "Observed NE 0001:673a. Allocates 0x70c context; passes DS:020d YUKONRES and DS:0204 Resource to 0001:722c; stores far return at Data13:52f4. Further registration semantics unresolved."},
        {"1000:722c", "YukonArchive_OpenContext", "Observed NE 0001:722c. BP+06=context far pair, +0a=directory far pair, +0e=filename far pair, +12=mode word; RETF 0x0e. Copies strings, opens via 0001:8278, reads header/index via 0001:73fa. Default Ghidra function signature is not verified."},
        {"1000:73fa", "YukonArchive_ReadHeaderAndIndex", "Observed NE 0001:73fa. BP+06=context far pair; RETF 4. Reads 0x58 bytes to context+16, group_count*8 to far table+72, record_count*14 to far table+76. Swaps header words 0,2,54,56; group words4,6; record word4/dwords6,10. Counts and loop bounds use signed 16-bit comparisons."},
        {"1000:75fe", "YukonArchive_FindRecordIndex", "Observed NE 0001:75fe. BP+06=context far pair,+0a=u16 ID,+0c=raw unswapped tag dword; RETF 0x0a. Linear group-tag search, bounded midpoint ID search. ID ordering uses unsigned JBE; bounds/counts use signed branches. AX=index or 0xffff. Callers byteswap logical numeric tag before this call."},
        {"1000:7818", "YukonArchive_ReadRecord", "Observed NE 0001:7818. BP+06=context far pair,+0a=destination far pair,+0e=ID word,+10=logical numeric tag dword; RETF 0x0e. Swaps tag, finds index, seeks record+0a absolute offset, _HREAD length record+06. Mode1 separate-file fallback precedes archive path; postread transformation 0001:8462 remains unresolved."},
        {"1000:7c88", "YukonArchive_GetRecordLength", "Observed NE 0001:7c88. Archive branch swaps logical tag and finds record, returns entry+06 length in DX:AX. Mode1 separate-file fallback checks file length. BP+06=context far pair,+0a=ID word,+0c=logical tag dword; RETF 0x0a."},
        {"1000:7dd2", "YukonArchive_GetRecordFileSlice", "Observed NE 0001:7dd2. BP+06=context far,+0a=output length far,+0e=output offset far,+12=output handle far,+16=ID word,+18=logical tag dword; RETF 0x16. Archive path writes context+12 handle, record+0a offset and record+06 length; returns AX1. Mode1 separate-file fallback can return handle, offset0, file length. Output object ownership and playback callers remain unresolved."},
        {"1000:8278", "YukonArchive_OpenFileWithFallback", "Observed NE 0001:8278. Opens context+00 far filename with _LOPEN mode0; retries via 0001:8314 and a user-dialog path. Full drive/dialog behavior not recovered."},
        {"1028:60ae", "ByteSwap16_InPlace", "Observed NE 0006:60ae. LES BX,[BP+06]; swaps AL/AH in pointed word; RETF without argument cleanup. No guessed Ghidra pointer signature installed."},
        {"1028:60c2", "ByteSwap32_InPlace", "Observed NE 0006:60c2. LES BX,[BP+06]; swaps bytes in two words and stores words in reverse order; RETF without argument cleanup. No guessed Ghidra pointer signature installed."},
        {"1010:e1ee", "PSND_ConsumerLead", "Observed NE 0003:e1ee; referenced by relocated far method-table slot NE0006:883e. Bounded disassembly adds previously undefined routine. Pushes logical PSND at e24c/e332/e35f; e340 calls length, e370 generic resource buffer loader. Branches by values0x3ea/0x3ed/0x3ee; their meaning and playback formats remain unresolved. Runtime method dispatch has not been observed."}
    };

    private Address address(String text) {
        return currentProgram.getAddressFactory().getAddress(text);
    }

    private void decode(String start, String end, byte[] prologue) throws Exception {
        Address entry = address(start);
        byte[] actual = new byte[prologue.length];
        currentProgram.getMemory().getBytes(entry, actual);
        if (!java.util.Arrays.equals(actual, prologue)) throw new IllegalStateException("Unexpected bytes at " + start);
        if (currentProgram.getListing().getInstructionAt(entry) == null) {
            DisassembleCommand command = new DisassembleCommand(entry, new AddressSet(entry, address(end)), true);
            if (!command.applyTo(currentProgram, monitor)) throw new IllegalStateException(command.getStatusMsg());
        }
        if (currentProgram.getFunctionManager().getFunctionAt(entry) == null && createFunction(entry, null) == null) {
            throw new IllegalStateException("Cannot create function at " + entry);
        }
    }

    private StructureDataType structure(String name, int length) {
        return new StructureDataType(CATEGORY, name, length);
    }

    private void field(StructureDataType type, int offset, DataType field, String name) {
        type.replaceAtOffset(offset, field, field.getLength(), name, null);
    }

    private DataType bytes(int count) {
        return new ArrayDataType(ByteDataType.dataType, count, 1);
    }

    private List<StructureDataType> structures() {
        List<StructureDataType> result = new ArrayList<>();
        StructureDataType far = structure("OffsetSelector16", 4);
        field(far, 0, UnsignedShortDataType.dataType, "offset");
        field(far, 2, UnsignedShortDataType.dataType, "selector");
        result.add(far);
        StructureDataType group = structure("ArchiveGroupInMemory", 8);
        field(group, 0, bytes(4), "tag_bytes_unswapped");
        field(group, 4, UnsignedShortDataType.dataType, "record_count");
        field(group, 6, UnsignedShortDataType.dataType, "first_record_index");
        result.add(group);
        StructureDataType record = structure("ArchiveRecordInMemory", 14);
        field(record, 0, bytes(4), "tag_bytes_unswapped");
        field(record, 4, UnsignedShortDataType.dataType, "resource_id");
        field(record, 6, DWordDataType.dataType, "payload_length");
        field(record, 10, DWordDataType.dataType, "absolute_payload_offset");
        result.add(record);
        StructureDataType context = structure("ArchiveContextObserved", 0x70c);
        field(context, 0, far, "filename_far");
        field(context, 4, far, "directory_far");
        field(context, 8, UnsignedShortDataType.dataType, "mode_word");
        field(context, 10, UnsignedShortDataType.dataType, "status_word");
        field(context, 0x12, UnsignedShortDataType.dataType, "file_handle_word");
        field(context, 0x16, bytes(0x54), "header_prefix_partly_swapped");
        field(context, 0x6a, UnsignedShortDataType.dataType, "type_group_count");
        field(context, 0x6c, UnsignedShortDataType.dataType, "record_count");
        field(context, 0x72, far, "type_groups_far");
        field(context, 0x76, far, "records_far");
        result.add(context);
        return result;
    }

    @Override
    public void run() throws Exception {
        if (!SOURCE.equals(currentProgram.getExecutableSHA256())) throw new IllegalStateException("Unexpected executable identity");
        String[] args = getScriptArgs();
        if (args.length != 2 || !(args[0].equals("apply") || args[0].equals("verify"))) {
            throw new IllegalArgumentException("apply|verify and output audit path required");
        }
        boolean apply = args[0].equals("apply");
        if (apply) {
            // Selectors in this imported method table are analysis mappings.
            byte[] slot = new byte[4];
            currentProgram.getMemory().getBytes(address("1028:883e"), slot);
            if (!java.util.Arrays.equals(slot, new byte[]{(byte)0xee,(byte)0xe1,0x10,0x10})) {
                throw new IllegalStateException("Unexpected relocated PSND method slot");
            }
            decode("1010:e1ee", "1010:e463", new byte[]{(byte)0xc8,0x4c,0,0});
            // Direct call from the newly decoded e1ee routine, bounded before next known function.
            decode("1000:7dd2", "1000:8011", new byte[]{(byte)0xc8,0x5c,0,0});
        }
        List<String> audit = new ArrayList<>();
        audit.add("SOURCE_SHA256\t" + SOURCE);
        for (String[] item : FUNCTIONS) {
            Function function = currentProgram.getFunctionManager().getFunctionAt(address(item[0]));
            if (function == null) throw new IllegalStateException("Missing function " + item[0]);
            if (apply) {
                if (!function.getName().startsWith("FUN_") && !function.getName().equals(item[1])) {
                    throw new IllegalStateException("Refusing to replace another annotation at " + item[0]);
                }
                function.setName(item[1], SourceType.USER_DEFINED);
                function.setComment(item[2]);
            }
            if (!function.getName().equals(item[1]) || !item[2].equals(function.getComment())) {
                throw new IllegalStateException("Missing saved annotation at " + item[0]);
            }
            audit.add("FUNCTION\t" + item[0] + "\t" + function.getName() + "\t" + function.getBody().getNumAddresses());
            audit.add("COMMENT\t" + item[0] + "\t" + function.getComment());
        }
        for (StructureDataType wanted : structures()) {
            DataType stored = currentProgram.getDataTypeManager().getDataType(CATEGORY, wanted.getName());
            if (stored == null && apply) stored = currentProgram.getDataTypeManager().addDataType(wanted, DataTypeConflictHandler.KEEP_HANDLER);
            if (!(stored instanceof Structure) || !stored.isEquivalent(wanted)) {
                throw new IllegalStateException("Missing/conflicting type " + wanted.getName());
            }
            // Machine-sized C integers can shrink in the 16-bit data organization.
            // Assert actual saved field widths, not just datatype equivalence.
            for (DataTypeComponent wantedField : wanted.getDefinedComponents()) {
                DataTypeComponent actualField = ((Structure)stored).getComponentAt(wantedField.getOffset());
                if (actualField.getLength() != wantedField.getLength()) {
                    throw new IllegalStateException("Wrong saved width in " + wanted.getName() + ":" + wantedField.getFieldName());
                }
            }
            audit.add("TYPE\t" + stored.getPathName() + "\t" + stored.getLength());
            for (DataTypeComponent component : ((Structure)stored).getDefinedComponents()) {
                audit.add("FIELD\t" + stored.getName() + "\t" + component.getOffset() + "\t" +
                    component.getLength() + "\t" + component.getFieldName() + "\t" + component.getDataType().getName());
            }
        }
        Function recovered = currentProgram.getFunctionManager().getFunctionAt(address("1000:7dd2"));
        if (recovered == null) throw new IllegalStateException("Missing saved direct-call target");
        audit.add("RECOVERED_BOUNDARY\t" + recovered.getEntryPoint() + "\t" + recovered.getBody().getNumAddresses());
        Files.write(Path.of(args[1]), audit, StandardCharsets.UTF_8);
        println("Archive annotations " + args[0] + " checked; " + audit.size() + " audit records.");
    }
}
