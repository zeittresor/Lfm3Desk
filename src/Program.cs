using System.Media;
using System.Runtime.InteropServices;
using System.Text;
namespace Lfm3Desk;
internal static class Program
{
    [DllImport("kernel32.dll")] static extern bool FreeConsole();
    [STAThread]
    static int Main(string[] args)
    {
        if(args.Length==1 && args[0]=="-mcp-config"){Console.WriteLine(McpHost.Configuration());return 0;}
        if(args.Length==1 && args[0]=="-mcp")return McpHost.Run();
        if(args.Length>0) return RunCli(args).GetAwaiter().GetResult();
        FreeConsole();
        ApplicationConfiguration.Initialize();
        Application.ThreadException+=(_,e)=>MessageBox.Show(e.Exception.Message,"LFM3 Desk");
        Application.Run(new MainForm()); return 0;
    }
    static async Task<int> RunCli(string[] args)
    {
        Console.OutputEncoding=new UTF8Encoding(false);
        using var worker=new Worker(); using var cancel=new CancellationTokenSource();
        Console.CancelKeyPress+=(_,e)=>{e.Cancel=true;cancel.Cancel();};
        try
        {
            var options=Cli.Parse(args);
            if(options.Help) {Console.WriteLine(Cli.Help);return 0;}
            worker.Event+=e=> { if(e.GetProperty("type").GetString()=="tool" && e.GetProperty("result").TryGetProperty("error",out var toolError))Console.Error.WriteLine("Tool "+e.GetProperty("name").GetString()+": "+toolError.GetString()); else if(e.GetProperty("type").GetString()=="status") Console.Error.WriteLine(e.GetProperty("message").GetString()); else if(e.GetProperty("type").GetString()=="image")Console.Error.WriteLine(e.GetProperty("path").GetString()); };
            if(!Paths.RuntimeReady)
            {
                var reporter=new Progress<string>(line=>Console.Error.WriteLine(line));
                await SetupRunner.RunAsync(options.Request.device,reporter,cancel.Token, new Settings{OfflineMode=options.Request.offline,WikiEnabled=options.Request.wiki_enabled,WikiPath=options.Request.wiki_path});
            }
            var reply=await worker.SendAsync(options.Request,cancel.Token);
            if(reply==null) return 0;
            if(options.Request.output.Contains("txt")) Console.WriteLine(reply.Text+(options.Request.show_sources?reply.SourceText:""));
            if(options.File!=null) await File.WriteAllTextAsync(options.File,reply.Text+(options.Request.show_sources?reply.SourceText:""),new UTF8Encoding(false),cancel.Token);
            if(reply.Audio!=null)
            {
                try { Console.Error.WriteLine(reply.Audio); if(options.Play) {using var player=new SoundPlayer(reply.Audio);player.PlaySync();} }
                finally {if(reply.Temporary) File.Delete(reply.Audio);}
            }
            return 0;
        }
        catch(ArgumentException e) {Console.Error.WriteLine(e.Message+"\nUse -help.");return 2;}
        catch(OperationCanceledException) {Console.Error.WriteLine("Cancelled.");return 130;}
        catch(Exception e) {Console.Error.WriteLine(e.Message);return 1;}
    }
}
