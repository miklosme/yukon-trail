// Read-only map scene virtual bindings and selected missing factory branch.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.nio.file.*;
public class ProbeVoyage extends GhidraScript {
 public void run() throws Exception {
  if(!"9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06".equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Source mismatch");
  StringBuilder out=new StringBuilder("SOURCE_SHA256\t"+currentProgram.getExecutableSHA256()+"\n");
  for(String table:new String[]{"1028:8afe","1028:8b54"})for(int slot=0;slot<0x30;slot+=4){byte[] b=new byte[4];currentProgram.getMemory().getBytes(toAddr(table).add(slot),b);out.append("TABLE\t").append(table).append('+').append(Integer.toHexString(slot)).append('\t');for(byte q:b)out.append(String.format("%02x",q&255));out.append('\n');}
  for(String[] pair:new String[][]{{"1000:427a","1000:42a9"},{"1000:a8d0","1000:a902"}}){disassemble(toAddr(pair[0]));InstructionIterator it=currentProgram.getListing().getInstructions(new AddressSet(toAddr(pair[0]),toAddr(pair[1])),true);while(it.hasNext()){Instruction i=it.next();out.append(i.getAddress()).append('\t');for(byte b:i.getBytes())out.append(String.format("%02x",b&255));out.append('\t').append(i).append('\n');}}
  Files.writeString(Path.of(getScriptArgs()[0]),out.toString());
 }
}
