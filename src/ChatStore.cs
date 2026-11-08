using System.Text.Json;
namespace Lfm3Desk;
public sealed class ChatSession
{
    public string Id {get;set;}=Guid.NewGuid().ToString("N");
    public string Title {get;set;}="";
    public DateTimeOffset Updated {get;set;}=DateTimeOffset.Now;
    public string Transcript {get;set;}="";
    public string Draft {get;set;}="";
    public List<Attachment> Attachments {get;set;}=new();
    public List<JsonElement> History {get;set;}=new();
    public string? Image {get;set;}
    public string? Audio {get;set;}
}
public sealed class ChatStore
{
    readonly string directory;
    public ChatStore(string root){directory=Path.Combine(root,"output","chats");}
    public List<ChatSession> Load()
    {
        var sessions=new List<ChatSession>();
        if(!Directory.Exists(directory))return sessions;
        foreach(var path in Directory.GetFiles(directory,"*.json")){
            try{var value=JsonSerializer.Deserialize<ChatSession>(File.ReadAllText(path));if(value!=null&&Guid.TryParseExact(value.Id,"N",out _))sessions.Add(value);}
            catch(Exception error){AppLog.Append("chat-store.log",$"Could not read {Path.GetFileName(path)}: {error}");}
        }
        return sessions.OrderByDescending(s=>s.Updated).ToList();
    }
    public void Save(ChatSession value)
    {
        if(!Guid.TryParseExact(value.Id,"N",out _))throw new ArgumentException("Invalid chat id");
        Directory.CreateDirectory(directory);var path=Path.Combine(directory,value.Id+".json");
        File.WriteAllText(path+".tmp",JsonSerializer.Serialize(value,new JsonSerializerOptions{WriteIndented=true}));File.Move(path+".tmp",path,true);
    }
}
public static class AppLog
{
    public const string Version="1.4.0";
    public static void Append(string filename,string text,bool newSession=false)
    {
        var directory=Path.Combine(Paths.Root,"output","logs");Directory.CreateDirectory(directory);var path=Path.Combine(directory,filename);
        if(newSession||!File.Exists(path))File.AppendAllText(path,$"\n=== LFM3 Desk {Version} | {filename} | {DateTimeOffset.Now:O} ===\n");
        File.AppendAllText(path,text+Environment.NewLine);
    }
}
