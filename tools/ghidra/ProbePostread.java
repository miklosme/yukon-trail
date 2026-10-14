// Read-only recovery of postread switch branches and registration code.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public class ProbePostread extends GhidraScript {
    public void run() throws Exception {
        if (!"9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06".equals(currentProgram.getExecutableSHA256()))
            throw new IllegalStateException("Source identity mismatch");
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("Output path required; run read-only");
        for (int offset : new int[]{0x850e, 0x851e, 0x8530, 0x8542, 0x8560, 0x8572, 0x8578})
            disassemble(currentProgram.getAddressFactory().getAddress(String.format("1000:%04x", offset)));
        StringBuilder out = new StringBuilder("SOURCE_SHA256\t" + currentProgram.getExecutableSHA256() + "\n");
        for (int[] range : new int[][]{{0x83e4,0x85e5},{0x673a,0x6a25}}) {
            for (int offset = range[0]; offset <= range[1];) {
                Address address = currentProgram.getAddressFactory().getAddress(String.format("1000:%04x", offset));
                Instruction instruction = getInstructionAt(address);
                if (instruction == null) { offset++; continue; }
                out.append(address).append("\t");
                for (byte value : instruction.getBytes()) out.append(String.format("%02x", value & 255));
                out.append("\t").append(instruction).append("\n");
                offset += instruction.getLength();
            }
        }
        Files.writeString(Path.of(args[0]), out.toString(), StandardCharsets.UTF_8);
    }
}
