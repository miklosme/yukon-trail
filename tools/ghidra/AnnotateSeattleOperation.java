// Observed bounded partner acceptance and money mutation; do not install guessed signatures.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateSeattleOperation extends GhidraScript {
    private static final String SOURCE = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
    private static final String[][] ITEMS = {
        {"1008:23c6", "Dialogue_AcceptPartner", "Observed NE0002:23c6. BP+0c partnerword, BP+0a amountword. Calls0001:9df8 to set partner, journal lead0001:c474 event7,0001:a652 flag344 (partners2/4=1,1/3=0), then signextends amountword and calls0001:a184 slot0. Further scene transition unimplemented. Selected TREE3400 partner4 amount500. docs/SEATTLE-RULES.md."},
        {"1000:9df8", "State_SetPartnerWord", "Observed NE0001:9df8. If state word334 is zero, copies BP+0a to state312 and marks separate DS52fc object word54=1. Meaning of334 remains unknown. Synthetic native verification passes partner4 and gated case."},
        {"1000:a652", "State_SetFlag344Word", "Observed NE0001:a652. Copies BP+0a to state344 without334 gate; marks separate DS52fc object word54=1. Partners2/4 caller passes1,1/3 passes0. Broader flag meaning unknown."},
        {"1000:a184", "State_ChangeMoneyWords", "Observed NE0001:a184. BP+06 statefar,+0a deltadword,+0e slotword. Word slots start2fa stride2. State334 nonzero returns1 without money mutation. Selected slot0 signedword delta subset recovered: lowword wrapping add, negative deficits use slot1, insufficient combined total returns0 unchanged, final negative signed slot clamped0. Optional display cache lookup at a1bd stubbednull only in native verifier; arithmetic executes original. docs/SEATTLE-RULES.md."}
    };    public void run() throws Exception {
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
