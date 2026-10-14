// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateSeattleConditions extends GhidraScript {
 private static final String SOURCE="9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
 private static final String[][] ITEMS={
  {"1000:a040","State_GetWord318","Observed NE1:a040 raw558becc45e06268b871803c9ca0400, read-only far-state getter318. Selectedkind7/index17 compares318 to17 only after indexedseen23a nonzero, then signedpositiveinventory300/302/306. Broader318meaningunknown. docs/SEATTLE-CONDITIONS.md;4995native predicates across selectedkind0/2/4/7/11/26/172. No guessed signature."},
  {"1010:5118","SceneCondition_Evaluate","Observed NE3:5118 condition dispatcher. Selected actualSeattle14TREE graphs use0/2/4/7(index17only)/11(values107/108/109)/26/172. Original4995full-sizedexplicitstate/settings cases matchPython/JS, no condition behavior stubs or statewrites. Kind4seengate then30c zero/nonzero; kind7marker318/currentindex17 and signedpositive300/302/306; kind172settings5314+30 selects1nonzero/2zero. Otherkinds/specialcontexts not recovered; full condition catalog, UI filtering and callerstate unknown. docs/SEATTLE-CONDITIONS.md."}
 };
 public void run() throws Exception {
  String[] a=getScriptArgs();if(a.length!=2||!(a[0].equals("apply")||a[0].equals("verify")))throw new IllegalArgumentException("apply|verify audit-path");
  if(!SOURCE.equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Source mismatch");
  boolean apply=a[0].equals("apply");ArrayList<String> out=new ArrayList<>();out.add("SOURCE_SHA256\t"+SOURCE);
  for(String[] it:ITEMS){Function f=currentProgram.getFunctionManager().getFunctionAt(toAddr(it[0]));if(f==null&&apply){new DisassembleCommand(toAddr(it[0]),null,true).applyTo(currentProgram,monitor);f=createFunction(toAddr(it[0]),null);}if(f==null)throw new IllegalStateException("Missing "+it[0]);if(apply){if(!f.getName().startsWith("FUN_")&&!f.getName().equals(it[1]))throw new IllegalStateException("Conflicting name "+it[0]);f.setName(it[1],SourceType.USER_DEFINED);f.setComment(it[2]);}if(!f.getName().equals(it[1])||!it[2].equals(f.getComment()))throw new IllegalStateException("Annotation mismatch "+it[0]);out.add("FUNCTION\t"+it[0]+"\t"+f.getName());out.add("COMMENT\t"+it[0]+"\t"+f.getComment());}
  Files.write(Path.of(a[1]),out,StandardCharsets.UTF_8);
 }
}
