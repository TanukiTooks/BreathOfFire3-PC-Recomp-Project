import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;

public class ExportLoaderCandidates extends GhidraScript {
    public void run() throws Exception {
        Path output = Path.of(getScriptArgs()[0]);
        Files.createDirectories(output);
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        int exported = 0;
        try {
            var functions = currentProgram.getFunctionManager().getFunctions(true);
            while (functions.hasNext() && !monitor.isCancelled()) {
                var fn = functions.next();
                long entry = fn.getEntryPoint().getOffset();
                if (entry < 0x8014AA00L || entry >= 0x80167000L) continue;
                var result = decompiler.decompileFunction(fn, 5, monitor);
                String text = "// Original entry: " + fn.getEntryPoint() + " Name: " + fn.getName() + "\n";
                if (result.decompileCompleted()) text += result.getDecompiledFunction().getC();
                else text += "// Decompile incomplete: " + result.getErrorMessage();
                Files.writeString(output.resolve(fn.getEntryPoint() + ".c"), text, StandardCharsets.UTF_8);
                exported++;
            }
        } finally { decompiler.dispose(); }
        println("LOADER_CANDIDATES_EXPORTED=" + exported);
    }
}
