import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
public class VerifyLoaderCode extends GhidraScript {
 public void run() throws Exception {
  Path out=Path.of(getScriptArgs()[0]);
  for(String line:Files.readAllLines(Path.of(getScriptArgs()[1]))) {
   if(!line.startsWith("F ")) continue;
   long pc=Long.parseLong(line.substring(2).trim(),16);
   if(pc<0x80161f58L || pc>=0x80163300L) continue;
   var addr=toAddr(pc);
   if(getFunctionAt(addr)==null) { disassemble(addr); createFunction(addr,null); }
  }
  var dec=new DecompInterface();dec.openProgram(currentProgram);
  var fs=currentProgram.getFunctionManager().getFunctions(toAddr(0x80161f58L),true);
  while(fs.hasNext()) {
   var fn=fs.next();if(fn.getEntryPoint().getOffset()>=0x80163300L)break;
   var result=dec.decompileFunction(fn,10,monitor);
   if(result.decompileCompleted())Files.writeString(out.resolve(fn.getEntryPoint()+".c"),"// Original entry: "+fn.getEntryPoint()+"\n"+result.getDecompiledFunction().getC());
  }
  dec.dispose();
  StringBuilder listing=new StringBuilder();
  var instructions=currentProgram.getListing().getInstructions(toAddr(0x80161f58L),true);
  while(instructions.hasNext()) {var ins=instructions.next();if(ins.getAddress().getOffset()>=0x80163300L)break;listing.append(ins.getAddress()).append(" ").append(ins).append("\n");}
  Files.writeString(out.resolve("loader-disassembly.txt"),listing.toString(),StandardCharsets.UTF_8);
 }
}
