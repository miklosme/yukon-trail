// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateNavigation extends GhidraScript {
 private static final String SOURCE="9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
 private static final String[][] ITEMS={
 {"1000:61b8","GameWindow_DispatchClientButtons","Observed NE1:61b8: Win16 button down201/204/207 maps464, up202/205/208 maps46e; client LPARAM signed x/y pass unchanged. DS5330 activation consumes/resets. See docs/SEATTLE-NAVIGATION.md and original1231-case oracle."},
 {"1000:3c28","SceneManager_ForwardEvent","Observed NE1:3c28: manager busyword/currentScene gates; forwards event through current scene virtualslot4. Source client coordinates unchanged."},
 {"1008:3bea","SpriteManager_HitTestContext","Observed NE2:3bea: context list tail-to-previous; signed inclusive node bbox; virtualslot28 pixel hit. Visibility flag is not filtered here."},
 {"1008:e78a","Sprite_HitTestFramePixel","Observed NE2:e78a: cached frame/buffer getters; signed16 linear pixel index using buffer stride, compared to frame width*height; nonzero byte hit. No visibilityword28 or flipbyte2c read. Bounded initialized-frame oracle only."},
 {"1000:4238","SceneManager_CreateByCategory","Observed NE1:4238 category dispatch; category200 jumps4258 and calls4a10. Full allocation/scene lifecycle not in navigation oracle."},
 {"1000:4a10","SceneManager_CreateSceneCategory200","Observed NE1:4a10: category200 selects scene3000 constructor NE1:bf82; scenes1000/2000/4000 NE2:0002. Other scene kinds remain separate."},
 {"1000:bf82","TicketOffice_CreateScene","Observed NE1:bf82 calls Seattle constructor NE2:0002 then installs table NE6:624a, message slot4 NE1:bfe0. Full construction lifecycle not in navigation instruction oracle."},
 {"1000:bfe0","TicketOffice_HandleMessage","Observed NE1:bfe0: message464 repeats sprite hit and strict HSPT fallback with inherited action0890; unlike common0c72 it does not read DS1188 countdown on this branch. Up46e delegates0c72. Original302-case bounded oracle; modal46b/schedule remain unsupported."},
 {"1028:7b0a","BubblePrimary_AdvanceIfEnabled","Observed NE6:7b0a: object word8a nonzero suppresses; otherwise calls NE2:d61e. No separate anchor mutation in wrapper."},
 {"1028:7b24","BubbleSecondary_AdvanceIfEnabled","Observed NE6:7b24: object word8a nonzero suppresses; otherwise calls NE2:d61e. No separate anchor mutation in wrapper."},
 {"1000:3c7a","SceneManager_ConsumeQueuedAction","Observed NE1:3c7a: pending action consumer reads opcode/category/destination; opcode1 category200 reaches factory4238. Complete teardown/construction and message pumping not executed in bounded navigation oracle."}
 };
 public void run() throws Exception {
  String[] a=getScriptArgs();if(a.length!=2||!(a[0].equals("apply")||a[0].equals("verify")))throw new IllegalArgumentException("apply|verify audit-path");
  if(!SOURCE.equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Source mismatch");
  boolean apply=a[0].equals("apply");ArrayList<String> out=new ArrayList<>();out.add("SOURCE_SHA256\t"+SOURCE);
  for(String[] it:ITEMS){Function f=currentProgram.getFunctionManager().getFunctionAt(toAddr(it[0]));if(f==null&&apply){new DisassembleCommand(toAddr(it[0]),null,true).applyTo(currentProgram,monitor);f=createFunction(toAddr(it[0]),null);}if(f==null)throw new IllegalStateException("Missing "+it[0]);if(apply){if(!f.getName().startsWith("FUN_")&&!f.getName().equals(it[1]))throw new IllegalStateException("Conflicting name "+it[0]);f.setName(it[1],SourceType.USER_DEFINED);f.setComment(it[2]);}if(!f.getName().equals(it[1])||!it[2].equals(f.getComment()))throw new IllegalStateException("Annotation mismatch "+it[0]);out.add("FUNCTION\t"+it[0]+"\t"+f.getName());out.add("COMMENT\t"+it[0]+"\t"+f.getComment());}
  Files.write(Path.of(a[1]),out,StandardCharsets.UTF_8);
 }
}
