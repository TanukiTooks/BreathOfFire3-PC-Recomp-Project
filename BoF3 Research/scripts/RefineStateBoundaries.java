import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.symbol.SourceType;
public class RefineStateBoundaries extends GhidraScript {
 public void run() throws Exception {
  var start=toAddr(0x801a782cL);var middle=toAddr(0x801a7834L);var end=toAddr(0x801a7877L);
  var prefix=getFunctionAt(start);var tail=getFunctionAt(middle);
  boolean merged=prefix!=null && tail==null && prefix.getBody().getNumAddresses()==76 && prefix.getBody().getMaxAddress().equals(end);
  if(!merged) {
   if(prefix==null || tail==null || prefix.getBody().getNumAddresses()!=8 || !prefix.getBody().getMaxAddress().equals(middle.subtract(1)) || tail.getBody().getNumAddresses()!=68 || !tail.getBody().getMaxAddress().equals(end))throw new IllegalStateException("Unexpected dispatcher bodies");
   if(!prefix.getName().equals("FUN_801a782c") || !tail.getName().equals("FUN_801a7834"))throw new IllegalStateException("Do not replace named functions");
   for(var ref:getReferencesTo(middle))if(ref.getReferenceType().isCall())throw new IllegalStateException("Independent tail call");
  }
  if(getInt(start)!=0x3c028014 || getInt(start.add(4))!=0x80426870 || getInt(middle)!=0x27bdffe8)throw new IllegalStateException("Unexpected mode-loading prefix");
  var leafStart=toAddr(0x801a1a24L);var leafEnd=toAddr(0x801a1a57L);var leaf=getFunctionAt(leafStart);
  int[] words={0x3c021f80,0x8c420044,0x00000000,0x90430006,0x24020008,0x10620005,0x00000000,0x90820074,0x00000000,0x34420010,0xa0820074,0x03e00008,0x00000000};
  for(int i=0;i<words.length;i++)if(getInt(leafStart.add(i*4))!=words[i])throw new IllegalStateException("Unexpected leaf instructions");
  if(getInt(leafStart.subtract(8))!=0x03e00008 || getInt(toAddr(0x801c83f0L))!=0x801a1a24)throw new IllegalStateException("Missing leaf boundary/table evidence");
  if(leaf!=null && (leaf.getBody().getNumAddresses()!=52 || !leaf.getBody().getMaxAddress().equals(leafEnd)))throw new IllegalStateException("Unexpected existing leaf body");
  if(leaf==null)for(int i=0;i<52;i+=4)if(getFunctionContaining(leafStart.add(i))!=null || getInstructionAt(leafStart.add(i))==null)throw new IllegalStateException("Leaf overlaps function or missing instructions");
  if(!merged) {
   AddressSet body=new AddressSet(prefix.getBody());body.add(tail.getBody());
   currentProgram.getFunctionManager().removeFunction(middle);currentProgram.getFunctionManager().removeFunction(start);
   var fn=currentProgram.getFunctionManager().createFunction(null,start,body,SourceType.ANALYSIS);
   fn.setComment("Research boundary correction: includes signed mode-byte load at 0x80146870 before stack prologue. Original two-stage callback lookup retained.");
   println("STATE_DISPATCH_BOUNDARY_MERGED=1");
  }else println("STATE_DISPATCH_BOUNDARY_ALREADY_MERGED=1");
  if(leaf==null) {
   var fn=currentProgram.getFunctionManager().createFunction(null,leafStart,new AddressSet(leafStart,leafEnd),SourceType.ANALYSIS);
   fn.setComment("Research identification: complete 52-byte leaf, original table pointer at 0x801C83F0 and observed fallback entry; preceding return and full own delay slot verified.");
   println("RECORD_FLAG_LEAF_CREATED=1");
  }else println("RECORD_FLAG_LEAF_ALREADY_EXISTS=1");
 }
}
