// Exercise the native decompiler on a specified Ghidra segmented address.
// The output is evidence of tooling operation, not a recovered behavior claim.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public class DecompileSmoke extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) throw new IllegalArgumentException("Ghidra segment:offset and output prefix required");
        Address address = currentProgram.getAddressFactory().getAddress(args[0]);
        Function function = currentProgram.getFunctionManager().getFunctionAt(address);
        if (function == null) throw new IllegalStateException("No function starts at " + address);
        DecompInterface decompiler = new DecompInterface();
        try {
            if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException(decompiler.getLastMessage());
            DecompileResults result = decompiler.decompileFunction(function, 60, monitor);
            if (!result.decompileCompleted()) throw new IllegalStateException(result.getErrorMessage());
            String header = "// Source SHA256: " + currentProgram.getExecutableSHA256() + "\n" +
                "// Ghidra address: " + function.getEntryPoint() + "\n" +
                "// Tool smoke output; types and behavior are unverified.\n";
            Files.writeString(Path.of(args[1] + ".c"), header + result.getDecompiledFunction().getC(), StandardCharsets.UTF_8);
            StringBuilder asm = new StringBuilder(header);
            InstructionIterator instructions = currentProgram.getListing().getInstructions(function.getBody(), true);
            while (instructions.hasNext()) {
                Instruction instruction = instructions.next();
                asm.append(instruction.getAddress()).append("\t");
                for (byte b : instruction.getBytes()) asm.append(String.format("%02x", b & 0xff));
                asm.append("\t").append(instruction).append("\n");
            }
            Files.writeString(Path.of(args[1] + ".asm.txt"), asm.toString(), StandardCharsets.UTF_8);
            println("Decompiler completed for " + function.getEntryPoint() + "; warnings: " + result.getErrorMessage());
        } finally { decompiler.dispose(); }
    }
}
