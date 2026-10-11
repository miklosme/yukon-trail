// Export segmented disassembly and archive/file-API leads from the saved NE import.
// Read-only evidence export. Names and signatures in this output are Ghidra's
// current annotations; callers and operand widths still require human review.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public class TraceArchive extends GhidraScript {
    private String owner(Address address) {
        Function function = currentProgram.getFunctionManager().getFunctionContaining(address);
        return function == null ? "NONE" : function.getEntryPoint() + ":" + function.getName();
    }

    @Override
    public void run() throws Exception {
        String expected = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
        if (!expected.equals(currentProgram.getExecutableSHA256())) {
            throw new IllegalStateException("Unexpected source identity");
        }
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("Output prefix required");
        List<String> leads = new ArrayList<>();
        List<String> assembly = new ArrayList<>();
        leads.add("SOURCE_SHA256\t" + expected);
        Set<String> imports = Set.of("_LOPEN", "_LREAD", "_HREAD", "_LLSEEK", "_LCLOSE");
        SymbolIterator symbols = currentProgram.getSymbolTable().getAllSymbols(true);
        while (symbols.hasNext()) {
            Symbol symbol = symbols.next();
            if (!imports.contains(symbol.getName())) continue;
            leads.add("SYMBOL\t" + symbol.getName(true) + "\t" + symbol.getAddress());
            ReferenceIterator references = currentProgram.getReferenceManager().getReferencesTo(symbol.getAddress());
            while (references.hasNext()) {
                Reference reference = references.next();
                leads.add("API_XREF\t" + symbol.getName(true) + "\t" + reference.getFromAddress() +
                    "\t" + reference.getReferenceType() + "\t" + owner(reference.getFromAddress()));
            }
        }
        for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
            if (!block.isExecute()) continue;
            InstructionIterator instructions = currentProgram.getListing().getInstructions(block.getStart(), true);
            while (instructions.hasNext()) {
                Instruction instruction = instructions.next();
                if (!block.contains(instruction.getAddress())) break;
                StringBuilder line = new StringBuilder(instruction.getAddress().toString()).append("\t");
                for (byte b : instruction.getBytes()) line.append(String.format("%02x", b & 0xff));
                line.append("\t").append(instruction).append("\tfunction=").append(owner(instruction.getAddress()));
                for (Reference reference : instruction.getReferencesFrom()) {
                    line.append("\tref=").append(reference.getToAddress()).append(":").append(reference.getReferenceType());
                }
                assembly.add(line.toString());
                for (int operand = 0; operand < instruction.getNumOperands(); operand++) {
                    for (Object object : instruction.getOpObjects(operand)) {
                        if (object instanceof Scalar && ((Scalar) object).getUnsignedValue() == 0x20d) {
                            leads.add("STRING_OFFSET_OPERAND\t" + line);
                        }
                    }
                }
            }
        }
        Files.write(Path.of(args[0] + ".leads.tsv"), leads, StandardCharsets.UTF_8);
        Files.write(Path.of(args[0] + ".asm.tsv"), assembly, StandardCharsets.UTF_8);
        println("Exported " + leads.size() + " lead records and " + assembly.size() + " instructions.");
    }
}
