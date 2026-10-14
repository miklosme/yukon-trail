// Read-only relocated dialogue tables and selected missing consumers.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.nio.file.*;
public class ProbeDialogueSlots extends GhidraScript {
 public void run() throws Exception {
  if(!"9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06".equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Identity mismatch");
  StringBuilder out=new StringBuilder();
  for(String table:new String[]{"1028:608a","1028:609a"}){
   for(int slot=0;slot<=0x18;slot+=4){byte[] b=new byte[4];currentProgram.getMemory().getBytes(toAddr(table).add(slot),b);out.append(table).append('+').append(Integer.toHexString(slot)).append('\t');for(byte q:b)out.append(String.format("%02x",q&255));out.append('\n');}
  }
  Address a=toAddr("1008:2884");AddressSet set=new AddressSet(a,toAddr("1008:2b50"));new DisassembleCommand(a,set,true).applyTo(currentProgram,monitor);if(getFunctionAt(a)==null)createFunction(a,null);
  InstructionIterator it=currentProgram.getListing().getInstructions(set,true);while(it.hasNext()){Instruction i=it.next();out.append(i.getAddress()).append('\t');for(byte b:i.getBytes())out.append(String.format("%02x",b&255));out.append('\t').append(i).append('\n');}
  for(String[] pair:new String[][]{{"1000:2468","1000:29d1"},{"1008:24d0","1008:262f"}}){Address q=toAddr(pair[0]);AddressSet r=new AddressSet(q,toAddr(pair[1]));new DisassembleCommand(q,r,true).applyTo(currentProgram,monitor);if(getFunctionAt(q)==null)createFunction(q,null);}
  Files.writeString(Path.of(getScriptArgs()[0]),out.toString());
 }
}
