using Lfm3Desk;
static class Tests
{
    static int Main()
    {
        int count=0;
        void Check(bool ok,string message){if(!ok)throw new Exception(message);count++;}
        var o=Cli.Parse(new[]{"-nogui","-language","DE","-input","Erkläre bitte etwas","-output","txt,tts"});
        Check(o.Request.input_language=="DE"&&o.Request.output_language=="DE","paired languages");
        Check(o.Request.input=="Erkläre bitte etwas","unicode input");Check(o.Request.output=="txt,tts","combined output");
        o=Cli.Parse(new[]{"-input","x","-input-language","DE","-output-language","EN","-image","photo.jpg","-audio","mic.wav","-no-tools","-no-play"});
        Check(o.Request.output_language=="EN"&&o.Request.input_language=="DE","separate languages");
        Check(o.Request.attachments.Count==2&&Path.IsPathRooted(o.Request.attachments[0].path),"media paths");Check(!o.Request.tools&&!o.Play,"switches");
        o=Cli.Parse(new[]{"-input","x","-task","tts"});Check(o.Request.output=="tts","pure tts");
        o=Cli.Parse(new[]{"-input","x","-voice","male","-speech-language","FR","-output-language","EN"});Check(o.Request.voice=="male"&&o.Request.speech_language=="FR","male voice and explicit speech override");
        o=Cli.Parse(new[]{"-input","x","-voice","female"});Check(o.Request.voice=="female","female voice");
        Check(Cli.Parse(new[]{"-help"}).Help,"help without input");Check(Cli.Parse(new[]{"-download"}).Request.command=="download","download without input");
        foreach(var args in new[]{new[]{"-input"},new[]{"-input","x","-output","bad"},new[]{"-input","x","-unknown"},new[]{"-input","x","-max-tokens","99999"},new[]{"-input","x","-device","fake"},new[]{"-input","x","-voice","invalid"}})
        {bool rejected=false;try{Cli.Parse(args);}catch(ArgumentException){rejected=true;}Check(rejected,"invalid option rejection");}
        Check(new Settings().WikiFlavour=="mini"&&new Settings().WikiEnabled,"mini default");
        Check(!new Settings().McpEnabled&&!new Settings().WebEnabled&&new Settings().WeatherEnabled,"weather enabled, other connections default off");
        o=Cli.Parse(new[]{"-input","x","-web","-weather","-wiki","lexikon.zim"});
        Check(o.Request.web_enabled&&o.Request.weather_enabled&&Path.IsPathRooted(o.Request.wiki_path),"explicit connections and ZIM");
        Check(!Cli.Parse(new[]{"-input","x"}).Request.web_enabled,"CLI web default off");
        o=Cli.Parse(new[]{"-input","x","-no-wiki","-no-wiki-auto"});Check(!o.Request.wiki_enabled&&!o.Request.wiki_auto,"wiki switches");
        Check(!new Settings().WikiOnlineEnabled,"online Wikipedia off by default");
        Check(Cli.Parse(new[]{"-input","x","-wiki-online"}).Request.wiki_online_enabled,"explicit online Wikipedia");
        Check(!Cli.Parse(new[]{"-input","x","-web"}).Request.wiki_online_enabled,"web does not enable online Wikipedia");
        var priorRoot=Paths.Root;var chatRoot=Path.Combine(Path.GetTempPath(),"lfm-chats-"+Guid.NewGuid().ToString("N"));
        try{
            Paths.Root=chatRoot;var store=new ChatStore(chatRoot);
            var alice=new ChatSession{Title="Alice",Transcript="Erster Chat",History=new(){System.Text.Json.JsonSerializer.SerializeToElement(new{role="user",content="Nur Alice"})}};
            var bob=new ChatSession{Title="Bob",Transcript="Zweiter Chat"};store.Save(alice);store.Save(bob);
            var sessions=store.Load();Check(sessions.Count==2,"two persisted chats");Check(sessions.Single(c=>c.Id==alice.Id).History[0].GetProperty("content").GetString()=="Nur Alice","history roundtrip");
            Check(sessions.Single(c=>c.Id==bob.Id).History.Count==0,"history isolation");
            alice.Transcript+=" ergänzt";store.Save(alice);Check(store.Load().Single(c=>c.Id==alice.Id).Transcript.EndsWith("ergänzt"),"atomic chat update");
            bool rejected=false;try{store.Save(new ChatSession{Id="../escape"});}catch(ArgumentException){rejected=true;}Check(rejected,"chat id traversal rejected");
            AppLog.Append("runtime.log","first",true);AppLog.Append("runtime.log","second",true);var log=File.ReadAllText(Path.Combine(chatRoot,"output","logs","runtime.log"));Check(log.Split("LFM3 Desk 1.4.0").Length==3,"runtime version per session");
        }finally{Paths.Root=priorRoot;if(Directory.Exists(chatRoot))Directory.Delete(chatRoot,true);}
        Check(new Settings().HideChatDestinations,"hide destinations default on");
        var raw=@"Bild: ![Norderstedt](E:\Debug Enviroment\output\bild (1).png)";
        Check(ChatDisplay.HideDestinations(raw)=="Bild: Norderstedt","image caption retained without path");
        Check(raw.Contains("Debug Enviroment"),"original transcript unchanged");
        var urls=ChatDisplay.HideDestinations("Quelle — https://api.open-meteo.com/v1/forecast?x=1\nMehr: [Wikipedia](https://de.wikipedia.org/wiki/Test)");
        Check(!urls.Contains("https")&&!urls.Contains("open-meteo"),"source URLs hidden");
        Check(urls.Contains("Wikipedia"),"link labels retained");
        Check(ChatDisplay.HideDestinations("7,1 °C, 5 km/h, 1/2 und 10:30 Uhr.")=="7,1 °C, 5 km/h, 1/2 und 10:30 Uhr.","units intact");
        Check(Cli.Parse(new[]{"-input","x"}).Request.weather_enabled,"CLI weather on by default");
        Check(!Cli.Parse(new[]{"-input","x","-no-weather"}).Request.weather_enabled,"CLI weather disabled explicitly");
        Check(Cli.Parse(new[]{"-input","x","-offline"}).Request.offline,"CLI offline mode");
        Check(new Settings().ImageBackend=="cpu","image default CPU");
        Check(Request.From(new Settings{ImageBackend="directml",ImageGpu=1}).image_gpu==1,"image GPU settings forwarded");
        Check(Cli.Parse(new[]{"-input","x","-image-backend","directml","-image-gpu","1"}).Request.image_backend=="directml","CLI DirectML backend");
        Check(Cli.Parse(new[]{"-input","x","-image-backend","cpu"}).Request.image_backend=="cpu","CLI explicit image CPU");
        bool badImage=false;try{Cli.Parse(new[]{"-input","x","-image-backend","cuda"});}catch(ArgumentException){badImage=true;}Check(badImage,"unsupported image backend rejected");
        bool badGpu=false;try{Cli.Parse(new[]{"-input","x","-image-gpu","-1"});}catch(ArgumentException){badGpu=true;}Check(badGpu,"negative image GPU rejected");
        Console.WriteLine($"{count} CLI assertions passed.");return 0;
    }
}
