using System.Diagnostics;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Lfm3Desk;
public sealed class Settings
{
    public string UiLanguage { get; set; } = "DE";
    public string Theme { get; set; } = "Dark";
    public string InputLanguage { get; set; } = "DE";
    public string OutputLanguage { get; set; } = "DE";
    public string SpeechLanguage { get; set; } = "DE";
    public string Output { get; set; } = "txt,tts";
    public string Voice { get; set; } = "female";
    public bool WikiEnabled { get; set; } = true;
    public bool WikiAuto { get; set; } = true;
    public string WikiPath { get; set; } = "";
    public string WikiFlavour { get; set; } = "mini";
    public bool WikiOnlineEnabled { get; set; } = false;
    public bool WebEnabled { get; set; } = false;
    public bool WeatherEnabled { get; set; } = true;
    public bool OfflineMode {get;set;} = false;
    public bool HideChatDestinations {get;set;} = true;
    public bool McpEnabled { get; set; } = false;
    public bool SaveAudio { get; set; } = true;
    public bool Tools { get; set; } = true;
    public bool VideoAudio { get; set; } = true;
    public bool PlayAudio { get; set; } = true;
    public int MaxTokens { get; set; } = 1024;
    public string Device { get; set; } = "auto";
    public string ImageBackend {get;set;} = "cpu";
    public int ImageGpu {get;set;} = 0;
    public double Fps { get; set; } = 1;
    public string SystemPrompt { get; set; } = "";
    public static Settings Load()
    {
        try { return JsonSerializer.Deserialize<Settings>(File.ReadAllText(Paths.Settings)) ?? new(); }
        catch { return new(); }
    }
    public void Save()
    {
        var temporary=Paths.Settings+".tmp";
        File.WriteAllText(temporary,JsonSerializer.Serialize(this,new JsonSerializerOptions{WriteIndented=true}));
        File.Move(temporary,Paths.Settings,true);
    }
}
public static class Paths
{
    public static string Root = AppContext.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
    public static string Settings => Path.Combine(Root, "settings.json");
    public static bool RuntimeReady
    {
        get
        {
            try { if(!File.Exists(Python))return false;var hash=Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(Path.Combine(Root,"backend","requirements.txt"))));return Directory.GetFiles(Path.Combine(Root,".venv"),"lfm-runtime-*.ready").Any(p=>File.ReadAllText(p)==hash); }
            catch{return false;}
        }
    }
    public static bool HasWikipedia(string path="")
    {
        try{if(!string.IsNullOrWhiteSpace(path))return File.Exists(path);var folder=Path.Combine(Root,"data","wikipedia");return Directory.Exists(folder)&&Directory.GetFiles(folder,"wikipedia_de*.zim").Length>0;}catch{return false;}
    }
    public static string Python => Path.Combine(Root,".venv","Scripts","python.exe");
}
public record Attachment(string kind, string path);
public sealed class Request
{
    public string command { get; set; } = "chat";
    public string input { get; set; } = "";
    public string task { get; set; } = "chat";
    public string output { get; set; } = "txt";
    public string input_language { get; set; } = "DE";
    public string output_language { get; set; } = "DE";
    public string speech_language { get; set; } = "DE";
    public string voice { get; set; } = "female";
    public string device { get; set; } = "auto";
    public string image_backend {get;set;} = "cpu";
    public int image_gpu {get;set;} = 0;
    public bool wiki_enabled { get; set; } = true;
    public bool wiki_auto { get; set; } = true;
    public string wiki_path { get; set; } = "";
    public bool wiki_online_enabled { get; set; } = false;
    public bool web_enabled { get; set; } = false;
    public bool weather_enabled { get; set; } = true;
    public bool offline {get;set;} = false;
    public bool save_audio { get; set; } = true;
    public bool tools { get; set; } = true;
    public bool video_audio { get; set; } = true;
    public int max_tokens { get; set; } = 1024;
    public double fps { get; set; } = 1;
    public string system { get; set; } = "";
    [JsonIgnore(Condition=JsonIgnoreCondition.WhenWritingNull)]
    public List<JsonElement>? history {get;set;}
    public List<Attachment> attachments { get; set; } = new();
    public static Request From(Settings s) => new() { image_backend=s.ImageBackend,image_gpu=s.ImageGpu,offline=s.OfflineMode,wiki_online_enabled=s.WikiOnlineEnabled,wiki_enabled=s.WikiEnabled,wiki_auto=s.WikiAuto,wiki_path=s.WikiPath,web_enabled=s.WebEnabled,weather_enabled=s.WeatherEnabled,output=s.Output,input_language=s.InputLanguage,output_language=s.OutputLanguage,speech_language=s.SpeechLanguage,voice=s.Voice,device=s.Device,save_audio=s.SaveAudio,tools=s.Tools,video_audio=s.VideoAudio,max_tokens=s.MaxTokens,fps=s.Fps,system=s.SystemPrompt };
}
public sealed record SourceInfo(string title,string url,string? kind=null,string? archive=null);
public sealed record Reply(string Text, string? Audio, bool Temporary, List<SourceInfo>? Sources=null,List<JsonElement>? History=null)
{
    public string SourceText => Sources is {Count:>0} ? "\nSources / Quellen:\n"+string.Join("\n",Sources.Select(s=>$"• {s.title} ({s.kind}) — {s.url}")) : "";
}
public sealed class Worker : IDisposable
{
    Process? process;
    readonly SemaphoreSlim gate = new(1);
    public event Action<JsonElement>? Event;
    public async Task<Reply?> SendAsync(Request request, CancellationToken ct)
    {
        await gate.WaitAsync(ct);
        try
        {
            if (!File.Exists(Paths.Python)) throw new InvalidOperationException("Runtime missing. Run Setup.cmd first. / Bitte zuerst Setup.cmd starten.");
            if (process == null || process.HasExited)
            {
                var si=new ProcessStartInfo(Paths.Python) { WorkingDirectory=Paths.Root,UseShellExecute=false,CreateNoWindow=true,RedirectStandardInput=true,RedirectStandardOutput=true,RedirectStandardError=true,StandardOutputEncoding=Encoding.UTF8,StandardErrorEncoding=Encoding.UTF8,StandardInputEncoding=new UTF8Encoding(false) };
                si.ArgumentList.Add("-u"); si.ArgumentList.Add(Path.Combine(Paths.Root,"backend","engine.py"));
                si.Environment["PYTHONIOENCODING"]="utf-8";
                var ff=Path.Combine(Paths.Root,"tools","ffmpeg","bin");
                if(Directory.Exists(ff)) si.Environment["PATH"]=ff+Path.PathSeparator+Environment.GetEnvironmentVariable("PATH");
                process?.Dispose();
                process=new Process {StartInfo=si};
                Directory.CreateDirectory(Path.Combine(Paths.Root,"output","logs"));
                process.ErrorDataReceived+=(_,e)=> { if(e.Data!=null) { try { AppLog.Append("runtime.log",e.Data); } catch {} } };
                AppLog.Append("runtime.log","Starting local Python worker: "+Paths.Python,true);
                process.Start(); process.BeginErrorReadLine();
            }
            using var registration=ct.Register(()=> { try { process?.Kill(true); } catch {} });
            await process.StandardInput.WriteLineAsync(JsonSerializer.Serialize(request));
            await process.StandardInput.FlushAsync(ct);
            while(true)
            {
                string? line=await process.StandardOutput.ReadLineAsync(ct);
                if(line==null) throw new IOException("Runtime stopped. See output/logs/runtime.log.");
                using var document=JsonDocument.Parse(line);
                var data=document.RootElement.Clone(); Event?.Invoke(data);
                switch(data.GetProperty("type").GetString())
                {
                    case "error": throw new InvalidOperationException(data.GetProperty("message").GetString());
                    case "done": return null;
                    case "result": return new(data.GetProperty("text").GetString()??"",data.GetProperty("audio").GetString(),data.GetProperty("temporary").GetBoolean(),data.TryGetProperty("sources",out var sources)?sources.Deserialize<List<SourceInfo>>():null,data.TryGetProperty("history",out var history)&&history.ValueKind==JsonValueKind.Array?history.Deserialize<List<JsonElement>>():null);
                }
            }
        }
        catch when(ct.IsCancellationRequested) { throw new OperationCanceledException(ct); }
        finally { gate.Release(); }
    }
    public void Stop() { var old=process;process=null;try { if(old is { HasExited:false }) old.Kill(true); } catch {} old?.Dispose(); }
    public void Dispose()=>Stop();
}
public static class SetupRunner
{
    public static async Task RunAsync(string device,IProgress<string> progress,CancellationToken ct,Settings? settings=null,bool wikipediaOnly=false,bool imageGpuOnly=false)
    {
        var info=new ProcessStartInfo("powershell.exe"){WorkingDirectory=Paths.Root,UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true,StandardOutputEncoding=Encoding.UTF8,StandardErrorEncoding=Encoding.UTF8};
        foreach(var arg in new[]{"-NoProfile","-ExecutionPolicy","Bypass","-File",Path.Combine(Paths.Root,"Setup.ps1"),"-NoLaunch","-Device",device})info.ArgumentList.Add(arg);
        if(settings!=null){
            if(settings.OfflineMode)info.ArgumentList.Add("-Offline");
            if(!settings.WikiEnabled)info.ArgumentList.Add("-SkipWikipedia");
            info.ArgumentList.Add("-WikipediaFlavour");info.ArgumentList.Add(settings.WikiFlavour=="nopic"?"nopic":"mini");
            if(!string.IsNullOrWhiteSpace(settings.WikiPath)&&!wikipediaOnly){info.ArgumentList.Add("-WikipediaPath");info.ArgumentList.Add(settings.WikiPath);}
        }
        if(wikipediaOnly)info.ArgumentList.Add("-WikipediaOnly");
        if(imageGpuOnly)info.ArgumentList.Add("-ImageGpuOnly");
        info.Environment["PYTHONIOENCODING"]="utf-8";
        using var process=new Process{StartInfo=info};
        var tail=new System.Collections.Concurrent.ConcurrentQueue<string>();
        process.Start();
        using var registration=ct.Register(()=>{try{process.Kill(true);}catch{}});
        async Task Pump(StreamReader reader)
        {
            while(await reader.ReadLineAsync() is string line){tail.Enqueue(line);while(tail.Count>40)tail.TryDequeue(out _);progress.Report(line);}
        }
        var output=Pump(process.StandardOutput);var error=Pump(process.StandardError);
        try{await process.WaitForExitAsync(ct);}
        finally{await Task.WhenAll(output,error);}
        ct.ThrowIfCancellationRequested();
        if(process.ExitCode!=0)
        {
            var lines=tail.ToArray();var last=Array.FindLastIndex(lines,line=>line.StartsWith("[ERR]"));
            string detail=string.Join(Environment.NewLine,last>=0?lines.Skip(last):lines.TakeLast(12));
            throw new IOException("Setup failed (exit "+process.ExitCode+")."+Environment.NewLine+detail);
        }
    }
}
public static class Cli
{
    public static (Request Request,bool Play,string? File,bool Help) Parse(string[] args)
    {
        var r=Request.From(Settings.Load()); r.output="txt"; r.save_audio=true;r.web_enabled=false;r.wiki_online_enabled=false;
        bool play=true,help=false; string? file=null; string? speechOverride=null;
        for(int i=0;i<args.Length;i++)
        {
            string key=args[i].TrimStart('-').ToLowerInvariant();
            string Value() { if(++i>=args.Length) throw new ArgumentException("Missing value for -"+key); return args[i]; }
            switch(key)
            {
                case "wiki": r.wiki_path=Path.GetFullPath(Value());r.wiki_enabled=true;break;
                case "no-wiki":r.wiki_enabled=false;break;
                case "no-wiki-auto":r.wiki_auto=false;break;
                case "wiki-online":r.wiki_online_enabled=true;break;
                case "web":r.web_enabled=true;break;
                case "offline":r.offline=true;break;
                case "no-weather":r.weather_enabled=false;break;
                case "weather":r.weather_enabled=true;break;
                case "nogui": break;
                case "help": case "h": case "?": help=true; break;
                case "language": r.input_language=r.output_language=r.speech_language=Value().ToUpperInvariant(); break;
                case "input-language": r.input_language=Value().ToUpperInvariant(); break;
                case "output-language": r.output_language=r.speech_language=Value().ToUpperInvariant(); break;
                case "speech-language": speechOverride=Value().ToUpperInvariant(); break;
                case "input": r.input=Value(); break;
                case "output": r.output=Value().ToLowerInvariant(); break;
                case "task": r.task=Value().ToLowerInvariant(); break;
                case "image": case "audio": case "video": r.attachments.Add(new(key,Path.GetFullPath(Value()))); break;
                case "voice": r.voice=Value().ToLowerInvariant(); break;
                case "device": r.device=Value().ToLowerInvariant(); break;
                case "image-backend":r.image_backend=Value().ToLowerInvariant();break;
                case "image-gpu":r.image_gpu=int.Parse(Value());break;
                case "max-tokens": r.max_tokens=int.Parse(Value()); break;
                case "fps": r.fps=double.Parse(Value(),System.Globalization.CultureInfo.InvariantCulture); break;
                case "system": r.system=Value(); break;
                case "out-file": file=Path.GetFullPath(Value()); break;
                case "no-play": play=false; break;
                case "no-save-audio": r.save_audio=false; break;
                case "no-tools": r.tools=false; break;
                case "no-video-audio": r.video_audio=false; break;
                case "download": r.command="download"; break;
                default: throw new ArgumentException("Unknown option: "+args[i]);
            }
        }
        if(speechOverride!=null)r.speech_language=speechOverride;
        if(!new[]{"female","male"}.Contains(r.voice))throw new ArgumentException("Voice: female | male");
        if(r.output=="tts,txt") r.output="txt,tts";
        if(!new[]{"txt","tts","txt,tts"}.Contains(r.output)) throw new ArgumentException("Output: txt | tts | txt,tts");
        if(!new[]{"chat","asr","tts","translate"}.Contains(r.task)) throw new ArgumentException("Task: chat | asr | tts | translate");
        if(r.task=="tts") r.output="tts";
        if(!new[]{"cpu","directml"}.Contains(r.image_backend))throw new ArgumentException("Image backend: cpu | directml");
        if(r.image_gpu<0||r.image_gpu>31)throw new ArgumentException("Image GPU index: 0..31");
        if(!new[]{"auto","cpu","cuda"}.Contains(r.device)) throw new ArgumentException("Device: auto | cpu | cuda");
        if(r.max_tokens<32 || r.max_tokens>8192 || r.fps<=0 || r.fps>2) throw new ArgumentException("max-tokens: 32..8192; fps: >0..2");
        if(!help && r.command!="download" && string.IsNullOrWhiteSpace(r.input) && r.attachments.Count==0) throw new ArgumentException("Provide -input or media.");
        return(r,play,file,help);
    }
    public const string Help="""
LFM3 Desk 1.4.0 — local C# GUI / CLI
lfm3gui -nogui -language DE -input "Erkläre die Gezeiten" -output txt,tts
  -output txt|tts|txt,tts     -task chat|asr|translate|tts
  -input-language DE        -output-language EN        -speech-language DE
  -image FILE               -audio FILE                -video FILE (repeatable)
  -image-backend cpu|directml  -image-gpu 0 (DXGI adapter index, 0..31)
  Optional DirectML runtime: Settings > Install image GPU runtime; CPU fallback on failure.
  -voice female|male        -device auto|cpu|cuda       -max-tokens 1024
  -no-tools                 -no-video-audio            -fps 1
  -no-play                  -no-save-audio             -out-file FILE.txt
  -download                 -system "Additional instruction"
  -wiki FILE.zim            -no-wiki                   -no-wiki-auto
  -web                      -weather (weather ON by default; web OFF)
  -wiki-online              Online Wikipedia only (OFF by default)
  -offline                  No online tools; weather may use recent cache
  -no-weather               Disable weather, including its cache
  -mcp                      MCP stdio server (requires GUI setting enabled)
  -mcp-config               Print MCP client configuration JSON
  -help                     Show this parameter list (no model loading).
Languages (ISO codes): DE EN FR RU ES IT JA KO ZH AR PL PT DA EL FI HE NL SV TR
Text additionally: VI TH ID HI. AUTO lets the prompt request language detection.
Speech requires an explicit supported speech language (not AUTO / RU / VI / TH / ID / HI).
Tasks: chat = answer questions; asr = transcribe; translate = translate;
       tts = read the input verbatim (male/female), rather than answer it.
-language sets input, text-output and speech language together.
-output-language sets text + speech; -speech-language overrides speech independently.
Audio: WAV, 24 kHz. Saved by default; -no-save-audio uses a temporary WAV.
GUI launch: lfm3gui (no arguments). CLI: -nogui and the options above.
Default CLI: txt output, female voice, playback ON, audio saving ON, tools from settings.
Run Setup.cmd once. Models stay in models/LFM3-Omni-2B beside the executable.
Exit codes: 0 success; 1 runtime error; 2 invalid arguments; 130 cancelled.
""";
}
