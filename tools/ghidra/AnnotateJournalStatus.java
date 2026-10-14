// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateJournalStatus extends GhidraScript {
 private static final String SOURCE="9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
 private static final String[][] ITEMS={
 {"1000:c474","Journal_AppendEventWithStatusGate","Observed NE1:c474 event4 compares cachedday, foodindex2,cashindex0,goldindex1 and dirtyword0a exactly1. Always refreshes cachedday/month/food/cash/gold; clearsdirtyonlywhenappending. Calls dbe2 then original full journal append. Original147 full-buffer cases; no source state writes. Other event consumers/overflow prompts not all recovered."},
 {"1000:dbe2","Journal_CreateStatusEntry","Observed NE1:dbe2: builds capacity255 entry; source date/place heading and We have prefix; signed food/cash decimal; nonzero settings5314word30 converts food trunc(signedfood*45/100), otherwise pounds; signedpositive gold appends dollar/in gold line. Each component accepted only combinedlength<255. Original formatter/full-buffer oracle docs/JOURNAL-STATUS.md."},
 {"1000:a744","State_GetInventoryWord","Observed NE1:a744: returns rawword state+2fa+2*index. Currentjournal usesindexes0cash,1gold,2food. Inventory selectorbb4c uses indexes0..8 from complete source table. No setter or dirty mutation."},
 {"1000:b25a","Journal_HandleMessage","Observed NE1:b25a table6:61a0 slot4. Constructor setsEditlimit27ff; Done467/id10 returns to managerparent orqueues scene4000. Source469 nonclipboard branch and itemclick copyEditWMGETTEXT before journalappend. Longtext prompt/retention path not implemented."},
 {"1000:b1ca","Journal_DestroyPresentation","Observed NE1:b1ca nondeleting presentation destructor: whenDS0df2==0 sends EditWMGETTEXT capacity2800 directlyto journaltext+0e, then destroysDone/Edit/font/resources. API execution outside source-only harness; raw buffer retention request supported."},
 {"1028:60fc","Journal_DeletePresentation","Observed NE6:60fc table61a0 deletionentry. SameDS0df2==0 EditWMGETTEXT request capacity2800 into journaltext+0e; skipsrequestwhenflag nonzero. Native request-boundary cases0/1/ffff recorded; actualWindowsEdit engine not executed. Optionaldeallocationflag thenfreesobject."},
 {"1000:c2c2","Journal_CreateTextState","Observed NE1:c2c2 allocates/locks2800-byte journalbuffer; writesNUL anddirty0a=1; cachesCSTR500/501/502/503. Clearscachedfood/cash/gold, butcachedinitialday/month are not initialized by thisfunction. Do not invent snapshot defaults."}
 };
 public void run() throws Exception {
  String[] a=getScriptArgs();if(a.length!=2||!(a[0].equals("apply")||a[0].equals("verify")))throw new IllegalArgumentException("apply|verify audit-path");
  if(!SOURCE.equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Source mismatch");
  boolean apply=a[0].equals("apply");ArrayList<String> out=new ArrayList<>();out.add("SOURCE_SHA256\t"+SOURCE);
  for(String[] it:ITEMS){Function f=currentProgram.getFunctionManager().getFunctionAt(toAddr(it[0]));if(f==null&&apply){new DisassembleCommand(toAddr(it[0]),null,true).applyTo(currentProgram,monitor);f=createFunction(toAddr(it[0]),null);}if(f==null)throw new IllegalStateException("Missing "+it[0]);if(apply){if(!f.getName().startsWith("FUN_")&&!f.getName().equals(it[1]))throw new IllegalStateException("Conflicting name "+it[0]);f.setName(it[1],SourceType.USER_DEFINED);f.setComment(it[2]);}if(!f.getName().equals(it[1])||!it[2].equals(f.getComment()))throw new IllegalStateException("Annotation mismatch "+it[0]);out.add("FUNCTION\t"+it[0]+"\t"+f.getName());out.add("COMMENT\t"+it[0]+"\t"+f.getComment());}
  Files.write(Path.of(a[1]),out,StandardCharsets.UTF_8);
 }
}
