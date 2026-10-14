// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.data.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class AnnotateSprite extends GhidraScript {
 private static final String SOURCE="9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06";
 private static final String[][] ITEMS={
 {"1010:274a","Sprite_CreateFromSPRT","Observed NE3:274a: copies normalized SPRT header38+schedulecount*8; header0 CBMP,2 ACEL/ASEQ ID,4/6 signed anchorXY; sets82=1,84=0. See docs/SEATTLE-SPRITES.md; unknown header words preserved."},
 {"1010:2a52","Sprite_UpdateScheduleAndSuspension","Observed NE3:2a52: word84 suspends update; with82=1 returns without hiding; with82=0 and visible28 nonzero invokes hide slot10. Clock and schedule timing not independently validated."},
 {"1008:d556","Sprite_StartSequence","Observed NE2:d556: ASEQ count then8-byte descriptors(startstep,successorsequence,defaultduration,stepcount). Object6a=start,6e=successor,66=duration,74=count; sequence index negative handled separately."},
 {"1008:d61e","Sprite_AdvanceSequence","Observed NE2:d61e:12-byte ASEQ steps(frame,dx,dy,unknown,durationoverride,fliptoggle). Zero duration uses default66; exhausted counter uses successor6e. Movement calls slot20; actual timer/successor execution unvalidated."},
 {"1008:e62a","Sprite_SetAnchorYX","Observed NE2:e62a: sets anchor24=Y,26=X; derives rectangle from frame offset1c=Y,1e=X and dimensions. Original execution checked selected SPRT403 geometry."},
 {"1008:e5e4","Sprite_MoveYX","Observed NE2:e5e4: adds signed Y delta to10/14/24 and X delta to12/16/26; marks dirty54 on nonzero movement. Original selected sequence5 four upward10 moves independently executed."},
 {"1008:e6ba","Sprite_SetFrameAndOffsetYX","Observed NE2:e6ba: frame selection and signed frame offsets feed current rectangle/anchor; ACEL400 offsets are XY pairs,3 entries. Frame-size producer455e stores height first,width second."},
 {"1008:d53a","Sprite_SetAnimationResources","Observed NE2:d53a: installs animation resource pointers used by sequence routines. No guessed segmented-pointer parameter signature installed."}
 };
 private StructureDataType structure(String name,String[] fields,DataType[] types){
  StructureDataType s=new StructureDataType(new CategoryPath("/YukonTrail/Selected"),name,0);
  for(int i=0;i<fields.length;i++)s.add(types[i],fields[i],"Observed normalized resource field; see docs/SEATTLE-SPRITES.md");return s;
 }
 public void run() throws Exception {
  String[] a=getScriptArgs();if(a.length!=2||!(a[0].equals("apply")||a[0].equals("verify")))throw new IllegalArgumentException("apply|verify audit-path");
  if(!SOURCE.equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Source mismatch");
  boolean apply=a[0].equals("apply");ArrayList<String> out=new ArrayList<>();out.add("SOURCE_SHA256\t"+SOURCE);
  for(String[] it:ITEMS){Function f=currentProgram.getFunctionManager().getFunctionAt(toAddr(it[0]));if(f==null)throw new IllegalStateException("Missing "+it[0]);if(apply){if(!f.getName().startsWith("FUN_")&&!f.getName().equals(it[1]))throw new IllegalStateException("Conflicting name "+it[0]);f.setName(it[1],SourceType.USER_DEFINED);f.setComment(it[2]);}if(!f.getName().equals(it[1])||!it[2].equals(f.getComment()))throw new IllegalStateException("Annotation mismatch "+it[0]);out.add("FUNCTION\t"+it[0]+"\t"+f.getName());out.add("COMMENT\t"+it[0]+"\t"+f.getComment());}
  DataType u=UnsignedShortDataType.dataType,h=ShortDataType.dataType,b=Undefined1DataType.dataType;
  StructureDataType[] expected={
   structure("SPRT_ObservedHeader",new String[]{"bitmap_id","animation_id","anchor_x","anchor_y","unknown8","initial_sequence","unknown18","click_sequence","unknown32","unknown34","schedule_count"},new DataType[]{u,u,h,h,new ArrayDataType(b,8,1),h,new ArrayDataType(b,12,1),h,u,u,u}),
   structure("SPRT_ScheduleEntry",new String[]{"sequence","interval","unknown_word2","unknown_word3"},new DataType[]{h,h,h,h}),
   structure("ACEL_FrameOffsetXY",new String[]{"offset_x","offset_y"},new DataType[]{h,h}),
   structure("ASEQ_ObservedSequence",new String[]{"start_step","successor_sequence","default_duration","step_count"},new DataType[]{u,h,u,u}),
   structure("ASEQ_ObservedStep",new String[]{"bitmap_frame","delta_x","delta_y","unknown_word","duration_override","flip_toggle"},new DataType[]{u,h,h,u,u,u}),
   structure("HSPT_ObservedRecord",new String[]{"left","right","top","bottom","action_word0","action_word1","action_dword"},new DataType[]{h,h,h,h,u,u,DWordDataType.dataType})
  };
  for(StructureDataType s:expected){DataType dt=apply?currentProgram.getDataTypeManager().resolve(s,DataTypeConflictHandler.REPLACE_HANDLER):currentProgram.getDataTypeManager().getDataType(s.getCategoryPath(),s.getName());if(!(dt instanceof Structure)||dt.getLength()!=s.getLength())throw new IllegalStateException("Missing type "+s.getName());Structure got=(Structure)dt;if(got.getNumComponents()!=s.getNumComponents())throw new IllegalStateException("Field count "+s.getName()+" got="+got.getNumComponents()+" expected="+s.getNumComponents());out.add("TYPE\t"+dt.getPathName()+"\t"+dt.getLength());for(int i=0;i<s.getNumComponents();i++){DataTypeComponent x=got.getComponent(i),y=s.getComponent(i);if(x.getOffset()!=y.getOffset()||!x.getFieldName().equals(y.getFieldName())||!x.getDataType().isEquivalent(y.getDataType()))throw new IllegalStateException("Field mismatch "+s.getName());out.add("FIELD\t"+s.getName()+"\t"+x.getOffset()+"\t"+x.getFieldName()+"\t"+x.getDataType().getName());}}
  Files.write(Path.of(a[1]),out,StandardCharsets.UTF_8);
 }
}
