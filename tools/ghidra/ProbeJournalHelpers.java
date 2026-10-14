// Decode bounded original journal switch targets in a read-only probe.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.nio.file.*;

public class ProbeJournalHelpers extends GhidraScript {
 public void run() throws Exception {
  if (!"9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06".equals(currentProgram.getExecutableSHA256())) throw new IllegalStateException("Source identity mismatch");
  AddressSet range = new AddressSet(toAddr("1000:cdae"), toAddr("1000:d363"));
  StringBuilder out = new StringBuilder();
  for(String value : new String[]{"1000:cdae","1000:cff8"}) {
   Address target=toAddr(value);
   new DisassembleCommand(target,range,true).applyTo(currentProgram,monitor);
   if(getFunctionAt(target)==null)createFunction(target,null);
  }
  InstructionIterator it=currentProgram.getListing().getInstructions(range,true);
  while(it.hasNext()){Instruction i=it.next();out.append(i.getAddress()).append("\t");for(byte b:i.getBytes())out.append(String.format("%02x",b&255));out.append("\t").append(i).append("\n");}
  Files.writeString(Path.of(getScriptArgs()[0]),out.toString());
 }
}
