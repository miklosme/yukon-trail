// Read-only independent NE loader audit; generated source images stay ignored.
// @category YukonTrail.Evidence
import ghidra.app.script.GhidraScript;
import java.nio.file.*;
public class ExportLoadedSegments extends GhidraScript {
 public void run() throws Exception {
  if(!"9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06".equals(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Source mismatch");
  Path out=Path.of(getScriptArgs()[0]);Files.createDirectories(out);
  int[][] rows={{1,60176},{2,59610},{3,59278},{4,60252},{5,37748},{6,39822},{9,8},{11,8},{13,29314}};
  for(int[] row:rows){String address=String.format("%04x:0000",0x1000+8*(row[0]-1));byte[] data=new byte[row[1]];currentProgram.getMemory().getBytes(toAddr(address),data);Files.write(out.resolve("NE"+row[0]+".bin"),data);}
 }
}
