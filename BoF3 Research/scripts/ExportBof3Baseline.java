import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Program;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;

public class ExportBof3Baseline extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path output = Path.of(getScriptArgs()[0]);
        StringBuilder report = new StringBuilder();
        report.append("program=").append(currentProgram.getName()).append("\n");
        report.append("format=").append(currentProgram.getExecutableFormat()).append("\n");
        report.append("language=").append(currentProgram.getLanguageID()).append("\n");
        report.append("compiler=").append(currentProgram.getCompilerSpec().getCompilerSpecID()).append("\n");
        report.append("psyq_version=").append(currentProgram.getOptions(Program.PROGRAM_INFO).getString("PsyQ Version", "undetected")).append("\n");
        report.append("function_count=").append(currentProgram.getFunctionManager().getFunctionCount()).append("\n");
        var entries = currentProgram.getSymbolTable().getExternalEntryPointIterator();
        while (entries.hasNext()) report.append("entry=").append(entries.next()).append("\n");
        for (var block : currentProgram.getMemory().getBlocks()) {
            report.append("memory=").append(block.getName()).append(" ").append(block.getStart()).append("-").append(block.getEnd()).append(" initialized=").append(block.isInitialized()).append("\n");
        }
        Files.writeString(output.resolve("ghidra-baseline.txt"), report.toString(), StandardCharsets.UTF_8);
        try (var writer = Files.newBufferedWriter(output.resolve("ghidra-functions.tsv"), StandardCharsets.UTF_8)) {
            writer.write("address\tname\tbyte_count\n");
            var functions = currentProgram.getFunctionManager().getFunctions(true);
            while (functions.hasNext()) {
                var function = functions.next();
                writer.write(function.getEntryPoint() + "\t" + function.getName() + "\t" + function.getBody().getNumAddresses() + "\n");
            }
        }
        println("BOF3_BASELINE_EXPORT_OK\n" + report);
    }
}
