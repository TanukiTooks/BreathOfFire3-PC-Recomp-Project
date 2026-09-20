import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.symbol.SourceType;
public class MergeGameplayUpdateBoundary extends GhidraScript {
 public void run() throws Exception {
  var start=toAddr(0x801a06d8L);var middle=toAddr(0x801a06e0L);var end=toAddr(0x801a0ae3L);
  var prefix=getFunctionAt(start);var tail=getFunctionAt(middle);
  if(prefix!=null && tail==null && prefix.getBody().getNumAddresses()==1036){println("GAMEPLAY_BOUNDARY_ALREADY_MERGED=1");return;}
  if(prefix==null || tail==null || prefix.getBody().getNumAddresses()!=8 || !prefix.getBody().getMaxAddress().equals(middle.subtract(1)) || tail.getBody().getNumAddresses()!=1028 || !tail.getBody().getMaxAddress().equals(end))throw new IllegalStateException("Unexpected bodies; inspect manually");
  if(!prefix.getName().equals("FUN_801a06d8") || !tail.getName().equals("FUN_801a06e0"))throw new IllegalStateException("Do not replace named functions");
  if(getInt(start)!=0x3c028014 || getInt(start.add(4))!=0x9442625a || getInt(middle)!=0x27bdffd8)throw new IllegalStateException("Unexpected prefix instructions");
  for(var ref:getReferencesTo(middle))if(ref.getReferenceType().isCall())throw new IllegalStateException("Independent call to tail requires review");
  AddressSet body=new AddressSet(prefix.getBody());body.add(tail.getBody());
  currentProgram.getFunctionManager().removeFunction(middle);currentProgram.getFunctionManager().removeFunction(start);
  var merged=currentProgram.getFunctionManager().createFunction(null,start,body,SourceType.ANALYSIS);
  merged.setComment("Research boundary correction: direct calls target 0x801A06D8; LUI/LHU load the control flag before the stack prologue. The eight-byte prefix falls through into the contiguous body. Retains all original instructions.");
  println("GAMEPLAY_BOUNDARY_MERGED=1");
 }
}
