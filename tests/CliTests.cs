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
            AppLog.Append("runtime.log","first",true);AppLog.Append("runtime.log","second",true);var log=File.ReadAllText(Path.Combine(chatRoot,"output","logs","runtime.log"));Check(log.Split("LFM3 Desk 1.5.1").Length==3,"runtime version per session");
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
        var formatted=ChatDisplay.FormatBold("Vorher **Wind**: 9 km/h und **Temperatur**: 8 °C.");
        Check(formatted.Text=="Vorher Wind: 9 km/h und Temperatur: 8 °C.","bold Markdown removed from visible text");
        Check(formatted.Bold.Count==2&&formatted.Text.Substring(formatted.Bold[0].Start,formatted.Bold[0].Length)=="Wind","correct first bold span");
        Check(formatted.Text.Substring(formatted.Bold[1].Start,formatted.Bold[1].Length)=="Temperatur","correct second bold span");
        Check(ChatDisplay.FormatBold("**offen").Text=="**offen","unmatched Markdown preserved");
        Check(ChatDisplay.FormatBold("**x**").Bold.Single().Length==1,"single character emphasis");
        var multiline=ChatDisplay.FormatBold("Zeile\r\n**Wind**");Check(multiline.Text.Substring(multiline.Bold[0].Start,multiline.Bold[0].Length)=="Wind","Windows newline offsets");
        var hidden=ChatDisplay.FormatBold(ChatDisplay.HideDestinations("**[Bild](E:\\output\\bild.png)**"));Check(hidden.Text=="Bild"&&hidden.Bold.Count==1,"hidden path and bold caption compose");
        Check(Settings.CleanAssistantName("  Mira ")=="Mira","assistant name trimmed");
        Check(Settings.CleanAssistantName("\r\n : ")=="LFM3","empty assistant name falls back");
        Check(Settings.CleanAssistantName("Mira\nNova")=="Mira Nova","assistant name single line");
        Check(Settings.CleanAssistantName(new string('a',80)).Length==64,"assistant name bounded");
        Check(Request.From(new Settings{AssistantName="Mira"}).assistant_name=="Mira","assistant name forwarded");
        Check(Cli.Parse(new[]{"-input","x","-name","Mira"}).Request.assistant_name=="Mira","CLI assistant name");
        var rawTranscript="Du: LFM3 bleibt als Begriff.\n[Tool: current_weather]\nLFM3: **Wind** aus Norden.";
        var styled=ChatDisplay.FormatTranscript(rawTranscript,"Mira");
        Check(styled.Text=="Du: LFM3 bleibt als Begriff.\nTool: current_weather\nMira: Wind aus Norden.","assistant label and tool marker rendering");
        Check(styled.Tools.Count==1&&styled.Text.Substring(styled.Tools[0].Start,styled.Tools[0].Length)=="Tool: current_weather","tool color range");
        Check(styled.Text.Substring(styled.Bold[0].Start,styled.Bold[0].Length)=="Wind","bold offsets after name and tool rendering");
        Check(rawTranscript.Contains("[Tool:")&&rawTranscript.Contains("LFM3: **"),"raw transcript preserved");
        Check(ChatDisplay.FormatTranscript(rawTranscript,"A much longer name").Text.Contains("A much longer name: Wind"),"renaming old transcript is reversible");
        Check(ChatDisplay.FormatTranscript("Tool: current_weather\r\nLFM3: Text.","").Tools.Count==1,"new and legacy tool formats supported");
        Check(ChatDisplay.FormatTranscript("Ein [Tool: current_weather] Beispiel.","Mira").Tools.Count==0,"inline tool mention is not a tool row");
        Check(!new Settings().ShowSources&&new Settings().ShowToolCalls,"source/tool display defaults");
        var sources="LFM3: Antwort."+ChatDisplay.WrapSources("Sources / Quellen:\n• Wetter Hamburg — https://example.org");
        Check(!ChatDisplay.FilterMetadata(sources,false,true).Contains("Wetter Hamburg"),"wrapped sources hidden");
        Check(ChatDisplay.FilterMetadata(sources,true,true).Contains("Wetter Hamburg"),"wrapped sources restored");
        Check(!ChatDisplay.FilterMetadata(sources,true,true).Contains("LFM3_SOURCES"),"source markers never displayed");
        Check(!ChatDisplay.FilterMetadata("[Tool: current_weather]\nLFM3: Antwort.",false,false).Contains("current_weather"),"tool row hidden");
        Check(ChatDisplay.FilterMetadata("[Tool: current_weather]\nLFM3: Antwort.",false,true).Contains("current_weather"),"tool row restored");
        Check(ChatDisplay.FilterMetadata("Sources / Quellen:\n• Wetter\nDu: Weiter.\nLFM3: Ja.",false,true).Contains("Du: Weiter."),"legacy sources preserve next turn");
        Check(!ChatDisplay.FilterMetadata("Sources / Quellen:\n• Wetter",false,true).Contains("Wetter"),"legacy sources hidden");
        Check(ChatDisplay.FilterMetadata("Fehler: offline!",false,false)=="Fehler: offline!","hiding tools preserves errors");
        Check(Cli.Parse(new[]{"-input","x","-sources"}).Request.show_sources,"CLI source opt-in");
        var codeText="```python\nx=2**3; y=2**4\nTool: example\nLFM3: literal\n```";
        Check(ChatDisplay.FormatBold(codeText).Text==codeText,"bold rendering preserves code operators");
        Check(ChatDisplay.FilterMetadata(codeText,false,false)==codeText,"metadata filtering preserves code");
        var codeStyled=ChatDisplay.FormatTranscript(codeText,"Mira");Check(codeStyled.Text==codeText&&codeStyled.Tools.Count==0,"code roles and tool strings remain literal");
        var imageChat=new ChatSession{GeneratedImages=new(){"one.png","two.png"}};Check(System.Text.Json.JsonSerializer.Deserialize<ChatSession>(System.Text.Json.JsonSerializer.Serialize(imageChat))!.GeneratedImages.Count==2,"per-chat image list roundtrip");
        var codeUrl="```python\nurl='https://example.org/test'\npath='C:/data/input.json'\n```";Check(ChatDisplay.HideDestinations(codeUrl)==codeUrl,"destination hiding preserves code literals");
        Console.WriteLine($"{count} CLI assertions passed.");return 0;
    }
}
