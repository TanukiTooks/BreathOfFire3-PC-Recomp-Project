import ghidra.app.script.GhidraScript;
public class IdentifyWorldTerrain extends GhidraScript {
 public void run() throws Exception {
  var manager=currentProgram.getFunctionManager();
  manager.removeFunction(toAddr("801f4968"));
  manager.removeFunction(toAddr("801f4904"));
  var addr=toAddr("801f469c");
  disassemble(addr);
  createFunction(addr,"bof3_draw_area033_terrain_tiles");
 }
}
