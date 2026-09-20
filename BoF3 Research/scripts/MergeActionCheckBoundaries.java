import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.symbol.SourceType;
public class MergeActionCheckBoundaries extends GhidraScript {
 public void run() throws Exception {
  long[][] specs={{0x801c364cL,0x801c3654L,0x801c378fL,316,0x3c021f80L,0x8c420044L},{0x801b544cL,0x801b5454L,0x801b55bfL,364,0x3c048014L,0x8c846250L}};
  for(long[] s:specs) {
   var start=toAddr(s[0]);var mid=toAddr(s[1]);var end=toAddr(s[2]);var pre=getFunctionAt(start);var tail=getFunctionAt(mid);
   if(pre!=null && tail==null && pre.getBody().getNumAddresses()==s[3]+8 && pre.getBody().getMaxAddress().equals(end))continue;
   if(pre==null || tail==null || pre.getBody().getNumAddresses()!=8 || tail.getBody().getNumAddresses()!=s[3] || !pre.getBody().getMaxAddress().equals(mid.subtract(1)) || !tail.getBody().getMaxAddress().equals(end))throw new IllegalStateException("Unexpected function bounds "+start);
   if(!pre.getName().equals("FUN_"+start) || !tail.getName().equals("FUN_"+mid))throw new IllegalStateException("Named function conflict");
   if(getInt(start)!=(int)s[4] || getInt(start.add(4))!=(int)s[5] || getInt(mid)!=(s[0]==0x801c364cL?0x27bdffd8:0x27bdffe8) || getInt(start.subtract(8))!=0x03e00008)throw new IllegalStateException("Prefix mismatch");
   for(var ref:getReferencesTo(mid))if(ref.getReferenceType().isCall())throw new IllegalStateException("Independent tail call");
  }
  int count=0;
  for(long[] s:specs) {
   var start=toAddr(s[0]);var mid=toAddr(s[1]);var pre=getFunctionAt(start);var tail=getFunctionAt(mid);if(tail==null)continue;
   AddressSet body=new AddressSet(pre.getBody());body.add(tail.getBody());currentProgram.getFunctionManager().removeFunction(mid);currentProgram.getFunctionManager().removeFunction(start);
   var fn=currentProgram.getFunctionManager().createFunction(null,start,body,SourceType.ANALYSIS);fn.setComment("Research boundary correction: includes original eight-byte setup before stack prologue; exact contiguous bodies and prefix verified; all instructions retained.");count++;
  }
  println("ACTION_CHECK_BOUNDARIES_MERGED="+count);
 }
}
