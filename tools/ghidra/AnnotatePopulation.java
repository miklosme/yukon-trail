// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotatePopulation extends GhidraScript {
 private static final String SOURCE="9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
 private static final String[][] ITEMS={
 {"1008:ddd0", "SpriteContext_CreateList", "Observed NE2:ddd0 initializes source context list head/tail. Executed unchanged in96 selected initial Seattle population cases; see docs/SEATTLE-POPULATION.md."},
 {"1008:dece", "SpriteContext_AppendTail", "Observed NE2:dece links an actor at context tail. Original generic and global constructors register through manager slot34. Native96cases preserve actual context order."},
 {"1008:e06a", "SpriteContext_InsertAfter", "Observed NE2:e06a removes target node from its old list position and inserts after specified node. Scene0002 moves primary37500 then secondary37501 after controller actors. Original list instructions executed, not a z-sort."},
 {"1008:404c", "SpriteManager_RegisterContextNode", "Observed NE2:404c manager table706a slot34 forwards context48 and sprite to list appenddece. Native population fixtures use that actual source method/table."},
 {"1010:61f6", "Animation_GetTickCountDiv17", "Observed NE3:61f6 calls USER ordinal13 GetTickCount then unsigned32 divides by17. Separate sprite scheduler uses MMSYSTEM607 TimeGetTime>>4. Clocks are explicit constant fixture inputs in population proof."},
 {"1008:4466", "SpriteManager_InvalidateVisibleHeadToNext", "Observed NE2:4466 traverses context48 head0c next08; for visible and not dirty54 nodes, rectangle collision virtualmethod marks dirty55. Source source order confirmed; invalidation path excluded from initial constructor oracle."},
 {"1008:3c8e", "SpriteManager_UpdateDrawAndPresent", "Observed NE2:3c8e invokes manager virtualslot14 after buffer40 setup, with slot0c prior invalidation path. Static caller of dirty head-to-next drawing4290; whole background/present not executed."}
 };
 public void run() throws Exception {
  String[] a=getScriptArgs();if(a.length!=2||!(a[0].equals("apply")||a[0].equals("verify")))throw new IllegalArgumentException("apply|verify audit-path");
  if(!SOURCE.equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Source mismatch");
  boolean apply=a[0].equals("apply");ArrayList<String> out=new ArrayList<>();out.add("SOURCE_SHA256\t"+SOURCE);
  for(String[] it:ITEMS){Function f=currentProgram.getFunctionManager().getFunctionAt(toAddr(it[0]));if(f==null&&apply){new DisassembleCommand(toAddr(it[0]),null,true).applyTo(currentProgram,monitor);f=createFunction(toAddr(it[0]),null);}if(f==null)throw new IllegalStateException("Missing "+it[0]);if(apply){if(!f.getName().startsWith("FUN_")&&!f.getName().equals(it[1]))throw new IllegalStateException("Conflicting name "+it[0]);f.setName(it[1],SourceType.USER_DEFINED);f.setComment(it[2]);}if(!f.getName().equals(it[1])||!it[2].equals(f.getComment()))throw new IllegalStateException("Annotation mismatch "+it[0]);out.add("FUNCTION\t"+it[0]+"\t"+f.getName());out.add("COMMENT\t"+it[0]+"\t"+f.getComment());}
  Files.write(Path.of(a[1]),out,StandardCharsets.UTF_8);
 }
}
