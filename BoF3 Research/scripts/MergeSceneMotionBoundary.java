import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.symbol.SourceType;
public class MergeSceneMotionBoundary extends GhidraScript {
 public void run() throws Exception {
  var start=toAddr(0x801a1384L);var middle=toAddr(0x801a138cL);var end=toAddr(0x801a179fL);
  var prefix=getFunctionAt(start);var tail=getFunctionAt(middle);
  if(prefix!=null && tail==null && prefix.getBody().getNumAddresses()==1052){println("SCENE_MOTION_BOUNDARY_ALREADY_MERGED=1");return;}
  if(prefix==null || tail==null || prefix.getBody().getNumAddresses()!=8 || !prefix.getBody().getMaxAddress().equals(middle.subtract(1)) || tail.getBody().getNumAddresses()!=1044 || !tail.getBody().getMaxAddress().equals(end))throw new IllegalStateException("Unexpected bodies; inspect manually");
  if(!prefix.getName().equals("FUN_801a1384") || !tail.getName().equals("FUN_801a138c"))throw new IllegalStateException("Do not replace named functions");
  if(getInt(start)!=0x3c031f80 || getInt(start.add(4))!=0x8c630044 || getInt(middle)!=0x27bdffd0)throw new IllegalStateException("Unexpected prefix instructions");
  for(var ref:getReferencesTo(middle))if(ref.getReferenceType().isCall())throw new IllegalStateException("Independent call to tail requires review");
  AddressSet body=new AddressSet(prefix.getBody());body.add(tail.getBody());
  currentProgram.getFunctionManager().removeFunction(middle);currentProgram.getFunctionManager().removeFunction(start);
  var merged=currentProgram.getFunctionManager().createFunction(null,start,body,SourceType.ANALYSIS);
  merged.setComment("Research boundary correction: direct calls target 0x801A1384; LUI/LW load the current scene-record pointer before the stack prologue. The eight-byte prefix falls through into the contiguous body. Retains all original instructions.");
  println("SCENE_MOTION_BOUNDARY_MERGED=1");
 }
}
