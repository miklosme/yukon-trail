// Read-only ticket switch branches, factory binding and state setters.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.nio.file.*;
public class ProbeTicket extends GhidraScript {
 public void run() throws Exception {
  if(!"9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06".equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Source identity mismatch");
  clearListing(toAddr("1008:21b7"),toAddr("1008:21f5"));
  for(String a:new String[]{"1008:21b8","1008:21d4","1008:21d8","1008:21dc","1008:21ee","1008:21f2"})disassemble(toAddr(a));
  StringBuilder out=new StringBuilder("SOURCE_SHA256\t"+currentProgram.getExecutableSHA256()+"\n");
  for(String[] pair:new String[][]{{"1008:2098","1008:2263"},{"1000:a3bc","1000:a40a"},{"1000:4238","1000:45f8"}}){
   AddressSet set=new AddressSet(toAddr(pair[0]),toAddr(pair[1]));InstructionIterator it=currentProgram.getListing().getInstructions(set,true);
   while(it.hasNext()){Instruction i=it.next();out.append(i.getAddress()).append('\t');for(byte b:i.getBytes())out.append(String.format("%02x",b&255));out.append('\t').append(i).append('\n');}
  }
  for(String t:new String[]{"1028:668e"}){byte[] b=new byte[48];currentProgram.getMemory().getBytes(toAddr(t),b);out.append("TABLE\t").append(t).append('\t');for(byte q:b)out.append(String.format("%02x",q&255));out.append('\n');}
  Files.writeString(Path.of(getScriptArgs()[0]),out.toString());
 }
}
