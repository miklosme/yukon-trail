// Selected original Seattle ticket and boarding consumers; no guessed signatures.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.*;
import java.util.*;
public class AnnotateTicket extends GhidraScript {
 private static final String SOURCE="9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
 private static final String[][] ITEMS={
  {"1000:4148","SceneManager_CreateDialogueByResource","Observed NE1:4148. Type300 factory4238/426c calls here. Base resource3500 compare416c branches41ae; allocator256bytes then2:216a at41c8. Merchant2100/2101 choose248c, other dialogs may use0724. OSallocation notnative-emulated. docs/TICKETS.md."},
  {"1008:216a","SeattleDialogue_Create","Observed NE2:216a. Calls generic1:0724 then installs NE6:668e methodtable; slot10 is2:22c6. Actual HSPT3000 firstaction2/300/3500 leads clerk CONV3500 and this class. Whole constructor/UI excluded fromnativeproof."},
  {"1008:22c6","SeattleDialogue_ExecuteAction","Observed NE2:22c6; table6:668e slot10. Opcode240 calls23c6 partneroperation; opcode250 passesactionword4 fare andword2 shipchoice to21ae at2388; handledbranchesreturn1. Opcode320 delegates1:1250. Selected3960fare/36boardingnativefullbuffercases match. docs/TICKETS.md."},
  {"1008:21ae","SeattleDialogue_PurchaseTicket","Observed NE2:21ae. Original switch251..256 maps state320=3/2/1 and322=5000 for251..253/Dyea or9000 for254..256/Skagway; gatedsetters a3bc/a3e0. Optional displaycache927d target8a=0. Callsa184(-fare,slot0), ignoresfailure, thena184(+1,slot5/state304), returns1. No affordabilityguard/date/journalcall here.3960nativefullsentinelstates match. docs/TICKETS.md."},
  {"1000:2c9e","Dialogue_SelectConversationTree","Observed NE1:2c9e. CONVfarobject30; rowresourceword+10hex, stride14bytes, conditionpairs+12hex up to3. Zero resource sentinel stops; firstalltrue rowselected. Actual CONV3500 firstword16 rows3500 cond3/2;3550 cond3/1+8/2;3570 cond8/1.42nativecases preservefullstate. docs/TICKETS.md."},
  {"1000:a3bc","State_SetShipWord320","Observed NE1:a3bc. Gate334zero copiesargumentword tostate320 anddirtyDS52fcobject54=1. Original fare251/254 sets3,252/255 sets2,253/256 sets1. Broader reservationmeaningnotinferred."},
  {"1000:a3e0","State_SetDestinationWord322","Observed NE1:a3e0. Gate334zero copiesargumentword tostate322; no dirtywrite. Fare251..253 passes5000;254..256 passes9000. SourceTREE3550 labelsDyea/Skagway independentlybind values."},
  {"1000:a7f4","State_GetShipWord320","Observed NE1:a7f4 returns rawstate320. Condition8 testsnonzero/zero; condition26 matches3→0,2→1,1→2.40nativeconditions includeinvalid/boundarywords, no statewrites."},
  {"1000:a642","State_GetWord30c","Observed NE1:a642 raw558becc45e06268b870c03c9ca0400 returnsstate30c. Selectedboarding initialoverridecondition4/2 firstrequiresindexedconversationseenword nonzero then30c==0; override2/1 follows. CONV4300 index12→230;4400 index11→22e.64originalfullstatecontexts/128conditionchecks/64marks match. Broader30cmeaningunknown. docs/TICKETS.md."},
  {"1000:a530","State_SetWord33a","Observed NE1:a530 gate334zero copiesargument tostate33a anddirtyDS52fcobject54=1. Selectedboardingopcode320 delay0 passes0; broadermeaningunknown."},
  {"1008:100e","SeattleScene_QueueLocalAction","Observed NE2:100e. Setsparent+0e=1 andcopies8 originalactionbytes toparent+10. Raw8eda is MOV DS,DX despite misleadingGhidraassemblyrendering. Opcode320 generic1:1250 getsactualparent via3e6a, calls100e, queuesmanager1/400/31000/0 fordelay0 or3/0/0/0 fordelay7/14.36nativefullstate/parent/managercomparisons. No elapseddateadvanceinthisoperation. docs/TICKETS.md."}
 };
 public void run() throws Exception {
  String[] a=getScriptArgs();if(a.length!=2||!(a[0].equals("apply")||a[0].equals("verify")))throw new IllegalArgumentException("apply|verify auditpath");
  if(!SOURCE.equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Source identity mismatch");
  byte[] slot=new byte[4];currentProgram.getMemory().getBytes(toAddr("1028:669e"),slot);
  if(!Arrays.equals(slot,new byte[]{(byte)0xc6,0x22,0x08,0x10}))throw new IllegalStateException("Selected dispatchtablebinding differs");
  if(a[0].equals("apply")){
   for(String at:new String[]{"1000:4148","1008:216a","1000:a3bc","1000:a3e0"}){disassemble(toAddr(at));if(getFunctionAt(toAddr(at))==null)createFunction(toAddr(at),null);}
   clearListing(toAddr("1008:21b7"),toAddr("1008:21f5"));
   for(String at:new String[]{"1008:21b8","1008:21d4","1008:21d8","1008:21dc","1008:21ee","1008:21f2"})disassemble(toAddr(at));
   Function purchase=getFunctionAt(toAddr("1008:21ae"));AddressSet body=new AddressSet(purchase.getBody());body.add(toAddr("1008:21b8"),toAddr("1008:21f5"));purchase.setBody(body);
  }
  List<String> audit=new ArrayList<>();audit.add("SOURCE_SHA256\t"+SOURCE);
  for(String[] row:ITEMS){Function f=getFunctionAt(toAddr(row[0]));if(f==null)throw new IllegalStateException("Missingfunction"+row[0]);
   if(a[0].equals("apply")){if(!f.getName().startsWith("FUN_")&&!f.getName().equals(row[1]))throw new IllegalStateException("Conflictingname"+row[0]+f.getName());f.setName(row[1],SourceType.USER_DEFINED);f.setComment(row[2]);}
   if(!f.getName().equals(row[1])||!row[2].equals(f.getComment()))throw new IllegalStateException("Annotationlost"+row[0]);audit.add("FUNCTION\t"+row[0]+"\t"+f.getName());audit.add("COMMENT\t"+row[0]+"\t"+f.getComment());
  }
  Files.write(Path.of(a[1]),audit);
 }
}
