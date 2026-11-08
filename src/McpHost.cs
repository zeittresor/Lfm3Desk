using System.Diagnostics;
using System.Text.Json;
namespace Lfm3Desk;
public static class McpHost
{
    public static string Configuration()
    {
        var entry=new Dictionary<string,object>{{"command",Path.Combine(Paths.Root,"lfm3gui.exe")},{"args",new[]{"-mcp"}}};
        var runtime=Path.Combine(Paths.Root,"tools","dotnet-runtime");
        if(Directory.Exists(runtime))entry["env"]=new Dictionary<string,string>{{"DOTNET_ROOT",runtime}};
        return JsonSerializer.Serialize(new{mcpServers=new Dictionary<string,object>{{"lfm3desk",entry}}},new JsonSerializerOptions{WriteIndented=true});
    }
    public static int Run()
    {
        try{
            if(!Settings.Load().McpEnabled)throw new InvalidOperationException("MCP is disabled. Enable it in Settings first.");
            if(!Paths.RuntimeReady)throw new InvalidOperationException("Run Setup.cmd before starting MCP.");
            var si=new ProcessStartInfo(Paths.Python){WorkingDirectory=Paths.Root,UseShellExecute=false,CreateNoWindow=true};
            si.ArgumentList.Add("-u");si.ArgumentList.Add(Path.Combine(Paths.Root,"backend","mcp_server.py"));
            si.Environment["PYTHONIOENCODING"]="utf-8";
            using var process=Process.Start(si)??throw new IOException("Could not start MCP.");
            Console.CancelKeyPress+=(_,e)=>{e.Cancel=true;try{process.Kill(true);}catch{}};
            process.WaitForExit();return process.ExitCode;
        }catch(Exception e){Console.Error.WriteLine(e.Message);return 1;}
    }
}
