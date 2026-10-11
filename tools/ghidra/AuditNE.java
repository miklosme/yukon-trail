// Export loader observations and optionally stamp source identity for reopen verification.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.framework.options.Options;
import ghidra.program.model.address.AddressIterator;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

public class AuditNE extends GhidraScript {
    @Override
    public void run() throws Exception {
        String expected = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
        if (!expected.equals(currentProgram.getExecutableSHA256())) {
            throw new IllegalStateException("Unexpected source identity");
        }
        String[] args = getScriptArgs();
        if (args.length < 1) throw new IllegalArgumentException("Output path required");
        Options provenance = currentProgram.getOptions("Yukon Trail Verification");
        if (args.length == 2 && args[1].equals("stamp")) {
            provenance.setString("Source SHA256", expected);
        }
        String stamp = provenance.getString("Source SHA256", "MISSING");
        if (!expected.equals(stamp)) throw new IllegalStateException("Missing saved source stamp");
        List<String> lines = new ArrayList<>();
        lines.add("NAME\t" + currentProgram.getName());
        lines.add("SOURCE_SHA256\t" + currentProgram.getExecutableSHA256());
        lines.add("SAVED_SOURCE_STAMP\t" + stamp);
        lines.add("FORMAT\t" + currentProgram.getExecutableFormat());
        lines.add("LANGUAGE\t" + currentProgram.getLanguageID());
        lines.add("COMPILER\t" + currentProgram.getCompilerSpec().getCompilerSpecID());
        lines.add("IMAGE_BASE\t" + currentProgram.getImageBase());
        lines.add("FUNCTION_COUNT\t" + currentProgram.getFunctionManager().getFunctionCount());
        for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
            lines.add("BLOCK\t" + block.getName() + "\t" + block.getStart() + "\t" +
                block.getEnd() + "\t" + block.getSize() + "\tinitialized=" +
                block.isInitialized() + "\texecute=" + block.isExecute());
        }
        String[] libraries = currentProgram.getExternalManager().getExternalLibraryNames();
        Arrays.sort(libraries);
        for (String library : libraries) lines.add("LIBRARY\t" + library);
        List<String> imports = new ArrayList<>();
        SymbolIterator symbols = currentProgram.getSymbolTable().getExternalSymbols();
        while (symbols.hasNext()) {
            Symbol symbol = symbols.next();
            imports.add("IMPORT\t" + symbol.getName(true) + "\t" + symbol.getAddress());
        }
        Collections.sort(imports);
        lines.addAll(imports);
        AddressIterator entries = currentProgram.getSymbolTable().getExternalEntryPointIterator();
        while (entries.hasNext()) lines.add("ENTRY\t" + entries.next());
        byte[] needle = "YUKONRES".getBytes(StandardCharsets.US_ASCII);
        for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
            if (!block.isInitialized() || block.getSize() > Integer.MAX_VALUE) continue;
            byte[] bytes = new byte[(int) block.getSize()];
            block.getBytes(block.getStart(), bytes);
            for (int pos = 0; pos <= bytes.length - needle.length; pos++) {
                boolean match = true;
                for (int n = 0; n < needle.length; n++) {
                    if (bytes[pos + n] != needle[n]) { match = false; break; }
                }
                if (!match) continue;
                Address address = block.getStart().add(pos);
                ReferenceIterator refIterator = currentProgram.getReferenceManager().getReferencesTo(address);
                List<Reference> refs = new ArrayList<>();
                while (refIterator.hasNext()) refs.add(refIterator.next());
                lines.add("STRING\tYUKONRES\t" + address + "\txrefs=" + refs.size());
                for (Reference ref : refs) {
                    Function caller = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                    lines.add("STRING_XREF\t" + ref.getFromAddress() + "\t" + address +
                        "\t" + ref.getReferenceType() + "\tfunction=" +
                        (caller == null ? "NONE" : caller.getEntryPoint() + ":" + caller.getName()));
                }
            }
        }
        Files.write(Path.of(args[0]), lines, StandardCharsets.UTF_8);
        println("Audit wrote " + lines.size() + " records; source stamp verified.");
    }
}
