import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.*;
public class RefineOverlayBoundaries extends GhidraScript {
 public void run() throws Exception {
  int done=0;
  for(String line:Files.readAllLines(Path.of(getScriptArgs()[0]))) {
   if(line.isBlank())continue;String[] p=line.split("\t");var old=toAddr(Long.parseLong(p[0],16));var start=toAddr(Long.parseLong(p[1],16));var fn=getFunctionAt(old);
   if(fn==null){println("SKIP missing old entry "+old);continue;}
   boolean free=true;
   for(var a=start;a.compareTo(old)<0;a=a.add(4))if(getFunctionContaining(a)!=null)free=false;
   if(!free){println("SKIP occupied prefix "+start);continue;}
   AddressSet body=new AddressSet(fn.getBody());body.addRange(start,old.subtract(1));
   currentProgram.getFunctionManager().removeFunction(old);
   var created=currentProgram.getFunctionManager().createFunction(null,start,body,SourceType.ANALYSIS);
   created.setComment("Research boundary refinement: includes pre-stack argument setup. Prefix follows prior return/delay slot and has pointer or call-target evidence. Not an original source symbol.");done++;
  }
  println("BOUNDARIES_REFINED="+done);
 }
}
