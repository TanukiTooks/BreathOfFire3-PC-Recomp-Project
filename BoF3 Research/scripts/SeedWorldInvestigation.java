import ghidra.app.script.GhidraScript;
public class SeedWorldInvestigation extends GhidraScript {
 public void run() throws Exception {
  // 4904 and 4968 are call-return continuations inside the renderer, not starts.
  for(String pc : new String[]{"801f4968","801f4904"})
   if(getFunctionAt(toAddr(pc))!=null) removeFunction(toAddr(pc));
  for (String pc : new String[]{"801f469c","801f397c","801f3a14"}) {
   var addr=toAddr(pc);
   disassemble(addr);
   if(getFunctionAt(addr)==null) createFunction(addr,null);
  }
 }
}
