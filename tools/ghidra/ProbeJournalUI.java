// Read-only source investigation; no interpretation is saved by this probe.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.nio.file.*;
public class ProbeJournalUI extends GhidraScript {
 public void run() throws Exception {
  if(!"9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06".equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Source mismatch");
  String[] a=getScriptArgs();AddressSet range=new AddressSet(toAddr(a[1]),toAddr(a[2]));
  for(String value:a[3].split(",")){Address at=toAddr(value);new DisassembleCommand(at,null,true).applyTo(currentProgram,monitor);if(getFunctionAt(at)==null)createFunction(at,null);}
  StringBuilder out=new StringBuilder();InstructionIterator it=currentProgram.getListing().getInstructions(range,true);
  while(it.hasNext()){Instruction i=it.next();out.append(i.getAddress()).append("\t");for(byte b:i.getBytes())out.append(String.format("%02x",b&255));out.append("\t").append(i).append("\n");}
  Files.writeString(Path.of(a[0]),out.toString());
 }
}
