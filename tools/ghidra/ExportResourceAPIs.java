// Read-only export of palette/waveform import thunks and their callers.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public class ExportResourceAPIs extends GhidraScript {
    public void run() throws Exception {
        String expected = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
        if (!expected.equals(currentProgram.getExecutableSHA256()))
            throw new IllegalStateException("Unexpected executable identity");
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("Output path required");
        List<String> lines = new ArrayList<>();
        lines.add("SOURCE_SHA256\t" + expected);
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            Function f = functions.next();
            if (!f.isThunk()) continue;
            Function target = f.getThunkedFunction(true);
            String name = target.getName(true);
            if (!(name.contains("PALETTE") || name.contains("DIB") || name.contains("WAVEOUT"))) continue;
            lines.add("THUNK\t" + f.getEntryPoint() + "\t" + name);
            ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(f.getEntryPoint());
            while (refs.hasNext()) {
                Reference r = refs.next();
                Function caller = currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
                lines.add("XREF\t" + r.getFromAddress() + "\t" + name + "\t" +
                    (caller == null ? "NONE" : caller.getEntryPoint()) + "\t" + r.getReferenceType());
            }
        }
        Files.write(Path.of(args[0]), lines, StandardCharsets.UTF_8);
        println("Exported " + lines.size() + " records");
    }
}
