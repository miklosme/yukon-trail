// Read-only discovery of previously unanalyzed image buffer routines.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.nio.file.*;
public class ProbeImageGap extends GhidraScript {
 public void run() throws Exception {
  String[] args=getScriptArgs();
  if(!"9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06".equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Source identity mismatch");
  Address a=toAddr("1008:5158"), z=toAddr("1008:5707");
  AddressSet range=new AddressSet(a,z);
  for(Address at=a;at.compareTo(z)<=0;at=at.add(1)) {
   if(getInstructionAt(at)==null && getDataAt(at)==null) new DisassembleCommand(at,range,true).applyTo(currentProgram,monitor);
  }
  createFunction(toAddr("1008:515a"),null); createFunction(toAddr("1008:5300"),null);
  new DisassembleCommand(toAddr("1010:0c56"),null,true).applyTo(currentProgram,monitor); if(getFunctionAt(toAddr("1010:0c56"))==null)createFunction(toAddr("1010:0c56"),null);
  StringBuilder out=new StringBuilder();
  for(String table:new String[]{"1028:67ea","1028:71e8","1028:69ca","1028:7b02","1028:706a"}){Address t=toAddr(table);for(int n=0;n<0x40;n+=4)out.append("TABLE\t").append(t.add(n)).append("\t").append(String.format("%08x",getInt(t.add(n)))).append("\n");}
  if(args.length>1)for(String name:args[1].split(",")){Address at=toAddr(name);new DisassembleCommand(at,null,true).applyTo(currentProgram,monitor);if(getFunctionAt(at)==null)createFunction(at,null);}

  InstructionIterator it=currentProgram.getListing().getInstructions(range,true);
  while(it.hasNext()){Instruction i=it.next();out.append(i.getAddress()).append("\t"); for(byte b:i.getBytes())out.append(String.format("%02x",b&255));out.append("\t").append(i).append("\n");}
  Files.writeString(Path.of(args[0]),out.toString());
 }
}
