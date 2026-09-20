import ghidra.app.script.GhidraScript;
import java.nio.file.*;
public class SeedOverlayAnalysis extends GhidraScript {
 public void run() throws Exception {
  for(String line:Files.readAllLines(Path.of(getScriptArgs()[0]))) {
   if(line.isBlank())continue;
   var addr=toAddr(Long.parseLong(line.split("\t")[0],16));
   disassemble(addr);
   if(getFunctionContaining(addr)==null)createFunction(addr,null);
  }
 }
}
