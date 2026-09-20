import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import java.nio.file.*;
public class ExportOverlayAnalysis extends GhidraScript {
 public void run() throws Exception {
  Path out=Path.of(getScriptArgs()[0]);Files.createDirectories(out.resolve("decompiled"));
  try(var old=Files.newDirectoryStream(out.resolve("decompiled"),"*.c")){for(var file:old)Files.delete(file);}
  StringBuilder fns=new StringBuilder("address\tname\tbody_bytes\tmin_address\tmax_address\tdecompiled\n");
  StringBuilder refs=new StringBuilder("from\tto\ttype\tfunction\n");
  StringBuilder insns=new StringBuilder();
  var dec=new DecompInterface();dec.openProgram(currentProgram);
  var fs=currentProgram.getFunctionManager().getFunctions(true);
  while(fs.hasNext()&&!monitor.isCancelled()) {
   var fn=fs.next();var block=currentProgram.getMemory().getBlock(fn.getEntryPoint());if(block==null || !block.isInitialized())continue;var res=dec.decompileFunction(fn,5,monitor);
   fns.append(fn.getEntryPoint()).append("\t").append(fn.getName()).append("\t").append(fn.getBody().getNumAddresses()).append("\t").append(fn.getBody().getMinAddress()).append("\t").append(fn.getBody().getMaxAddress()).append("\t").append(res.decompileCompleted()).append("\n");
   if(res.decompileCompleted())Files.writeString(out.resolve("decompiled").resolve(fn.getEntryPoint()+".c"),"// Original section address: "+fn.getEntryPoint()+"\n"+res.getDecompiledFunction().getC());
  }
  dec.dispose();
  var ii=currentProgram.getListing().getInstructions(true);
  while(ii.hasNext()) {
   var i=ii.next();insns.append(i.getAddress()).append(" ").append(i).append("\n");
   var fn=getFunctionContaining(i.getAddress());
   for(var ref:i.getReferencesFrom())refs.append(ref.getFromAddress()).append("\t").append(ref.getToAddress()).append("\t").append(ref.getReferenceType()).append("\t").append(fn==null?"":fn.getEntryPoint()).append("\n");
  }
  Files.writeString(out.resolve("functions.tsv"),fns.toString());Files.writeString(out.resolve("references.tsv"),refs.toString());Files.writeString(out.resolve("disassembly.txt"),insns.toString());
  println("OVERLAY_FUNCTIONS="+currentProgram.getFunctionManager().getFunctionCount());
 }
}
