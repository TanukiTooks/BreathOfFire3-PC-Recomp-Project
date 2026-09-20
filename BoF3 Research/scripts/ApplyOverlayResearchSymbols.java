import ghidra.app.script.GhidraScript;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.data.ByteDataType;
import java.nio.file.*;
public class ApplyOverlayResearchSymbols extends GhidraScript {
 public void run() throws Exception {
  int count=0;
  for(String line:Files.readAllLines(Path.of(getScriptArgs()[0]))) {
   if(line.isBlank())continue;String[] p=line.split("\t",4);var addr=toAddr(Long.parseLong(p[0],16));
   if(p[1].equals("function")) {
    var fn=getFunctionAt(addr);if(fn==null)throw new IllegalStateException("Missing identified function "+addr);
    fn.setName(p[2],SourceType.USER_DEFINED);fn.setComment("Research descriptive name, not original source symbol. "+p[3]);
   }else{
    if(getInstructionContaining(addr)!=null)throw new IllegalStateException("Data label overlaps code "+addr);
    clearListing(addr,addr);createData(addr,ByteDataType.dataType);createLabel(addr,p[2],true,SourceType.USER_DEFINED);setPlateComment(addr,"Research byte variable. "+p[3]);
   }
   count++;
  }
  println("RESEARCH_SYMBOLS_APPLIED="+count);
 }
}
