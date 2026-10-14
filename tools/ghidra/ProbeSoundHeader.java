// Read-only selected variable sound header and memory stream bindings.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import java.nio.file.*;
public class ProbeSoundHeader extends GhidraScript {
 public void run() throws Exception {
  if(!"9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06".equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Identity mismatch");
  StringBuilder out=new StringBuilder();
  for(String table:new String[]{"1028:89fc"})for(int offset=0x18;offset<=0x24;offset+=4){byte[] b=new byte[4];currentProgram.getMemory().getBytes(toAddr(table).add(offset),b);out.append(table).append('+').append(Integer.toHexString(offset)).append('\t');for(byte x:b)out.append(String.format("%02x",x&255));out.append('\n');}
  Files.writeString(Path.of(getScriptArgs()[0]),out.toString());
 }
}
