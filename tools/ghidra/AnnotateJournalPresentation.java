// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.data.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateJournalPresentation extends GhidraScript {
 private static final String SOURCE="9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
 private static final String[][] ITEMS={
 {"1000:aea4","Journal_CreatePresentation","Observed NE1:aea4: original journal controls Done105,355,70,30 and Edit rectNE9:0000=0,0,302,340; loadsCBMP37000/37001 and16 conditional sprites fromNE13:0df4 stride10. Requests YukonFont10points through DPI-based negativeheight. See docs/JOURNAL-PRESENTATION.md; native/browser textmetrics pending."},
 {"1000:be32","Journal_EnumeratedFontCallback","Observed NE1:be32: compares enumerated LOGFONT face at+18 withNE13:0dee YukonFont; sets caller foundbyte and stores pointerDS568a. Other runtime LOGFONT fields not captured."},
 {"1000:bb4c","Journal_InventoryEntryEnabled","Observed NE1:bb4c: tableNE13:0df4 stride10 signedstateindex; -1 unconditional,7/8 equality withcomparisonword,otherwise nonzero state-reader result. Source frame/anchor words atentry+4/+6/+8."}
 };
 private StructureDataType structure(String name,String[] fields,DataType[] types){
  StructureDataType s=new StructureDataType(new CategoryPath("/YukonTrail/Selected"),name,0);
  for(int i=0;i<fields.length;i++)s.add(types[i],fields[i],"Observed normalized resource field; see docs/JOURNAL-PRESENTATION.md");return s;
 }
 public void run() throws Exception {
  String[] a=getScriptArgs();if(a.length!=2||!(a[0].equals("apply")||a[0].equals("verify")))throw new IllegalArgumentException("apply|verify audit-path");
  if(!SOURCE.equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Source mismatch");
  boolean apply=a[0].equals("apply");ArrayList<String> out=new ArrayList<>();out.add("SOURCE_SHA256\t"+SOURCE);
  for(String[] it:ITEMS){Function f=currentProgram.getFunctionManager().getFunctionAt(toAddr(it[0]));if(f==null&&apply){new DisassembleCommand(toAddr(it[0]),null,true).applyTo(currentProgram,monitor);f=createFunction(toAddr(it[0]),null);}if(f==null)throw new IllegalStateException("Missing "+it[0]);if(apply){if(!f.getName().startsWith("FUN_")&&!f.getName().equals(it[1]))throw new IllegalStateException("Conflicting name "+it[0]);f.setName(it[1],SourceType.USER_DEFINED);f.setComment(it[2]);}if(!f.getName().equals(it[1])||!it[2].equals(f.getComment()))throw new IllegalStateException("Annotation mismatch "+it[0]);out.add("FUNCTION\t"+it[0]+"\t"+f.getName());out.add("COMMENT\t"+it[0]+"\t"+f.getComment());}
  DataType u=UnsignedShortDataType.dataType,h=ShortDataType.dataType,b=Undefined1DataType.dataType;
  StructureDataType[] expected={
   structure("JournalInventoryEntry",new String[]{"state_index","state_compare","bitmap_frame","anchor_y","anchor_x"},new DataType[]{h,h,h,h,h}),
   structure("JournalControlRectXYWH",new String[]{"x","y","width","height"},new DataType[]{h,h,h,h})
  };
  for(StructureDataType s:expected){DataType dt=apply?currentProgram.getDataTypeManager().resolve(s,DataTypeConflictHandler.REPLACE_HANDLER):currentProgram.getDataTypeManager().getDataType(s.getCategoryPath(),s.getName());if(!(dt instanceof Structure)||dt.getLength()!=s.getLength())throw new IllegalStateException("Missing type "+s.getName());Structure got=(Structure)dt;if(got.getNumComponents()!=s.getNumComponents())throw new IllegalStateException("Field count "+s.getName()+" got="+got.getNumComponents()+" expected="+s.getNumComponents());out.add("TYPE\t"+dt.getPathName()+"\t"+dt.getLength());for(int i=0;i<s.getNumComponents();i++){DataTypeComponent x=got.getComponent(i),y=s.getComponent(i);if(x.getOffset()!=y.getOffset()||!x.getFieldName().equals(y.getFieldName())||!x.getDataType().isEquivalent(y.getDataType()))throw new IllegalStateException("Field mismatch "+s.getName());out.add("FIELD\t"+s.getName()+"\t"+x.getOffset()+"\t"+x.getFieldName()+"\t"+x.getDataType().getName());}}
  Files.write(Path.of(a[1]),out,StandardCharsets.UTF_8);
 }
}
