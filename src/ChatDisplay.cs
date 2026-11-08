using System.Text;
using System.Text.RegularExpressions;
namespace Lfm3Desk;
public static class ChatDisplay
{
    public sealed record BoldSpan(int Start,int Length);
    public sealed record FormattedText(string Text,List<BoldSpan> Bold);
    public static FormattedText FormatBold(string text)
    {
        text=text.Replace("\r\n","\n").Replace('\r','\n');
        var output=new StringBuilder();var spans=new List<BoldSpan>();int start=0;
        foreach(Match match in Regex.Matches(text,@"(?<code>```[\s\S]*?(?:```|\z)|~~~[\s\S]*?(?:~~~|\z)|`[^`\r\n]+`)|(?<![\*\\])\*\*(?!\*)(?=\S)([^\r\n]*?\S)\*\*(?!\*)|(?<![\*\\])\*\*(?!\*)([^\s*])\*\*(?!\*)")){
            if(match.Groups["code"].Success){output.Append(text[start..(match.Index+match.Length)]);start=match.Index+match.Length;continue;}
            output.Append(text[start..match.Index]);var value=match.Groups[1].Success?match.Groups[1].Value:match.Groups[2].Value;
            spans.Add(new BoldSpan(output.Length,value.Length));output.Append(value);start=match.Index+match.Length;
        }
        output.Append(text[start..]);return new FormattedText(output.ToString(),spans);
    }
    const string CodePattern=@"```[\s\S]*?(?:```|\z)|~~~[\s\S]*?(?:~~~|\z)|`[^`\r\n]+`";
    static string ProtectCode(string text,out List<string> saved)
    {
        var values=new List<string>();text=Regex.Replace(text,CodePattern,m=>{values.Add(m.Value);return "\uE100"+(values.Count-1)+"\uE101";});saved=values;return text;
    }
    static string RestoreCode(string text,List<string> saved)
    {
        for(int i=0;i<saved.Count;i++)text=text.Replace("\uE100"+i+"\uE101",saved[i]);return text;
    }
    public static string WrapSources(string text)=>string.IsNullOrEmpty(text)?"":"\n[[LFM3_SOURCES]]\n"+text+"\n[[/LFM3_SOURCES]]\n";
    public static string FilterMetadata(string text,bool showSources,bool showTools)
    {
        text=ProtectCode(text,out var code);
        text=Regex.Replace(text,@"(?s)\[\[LFM3_SOURCES\]\](.*?)\[\[/LFM3_SOURCES\]\]",m=>showSources?m.Groups[1].Value:"");
        if(!showSources)text=Regex.Replace(text,@"(?ms)^Sources / Quellen:[^\n]*\n.*?(?=^(?:Du|You|LFM3):|\z)","");
        if(!showTools)text=Regex.Replace(text,@"(?m)^(?:\[Tool: [A-Za-z0-9_.:-]+\]|Tool: [A-Za-z0-9_.:-]+)\r?$","");
        return RestoreCode(text,code);
    }
    public sealed record StyledTranscript(string Text,List<BoldSpan> Bold,List<BoldSpan> Tools);
    public static StyledTranscript FormatTranscript(string text,string? assistantName)
    {
        text=ProtectCode(text,out var code);
        var name=Settings.CleanAssistantName(assistantName);
        text=Regex.Replace(text,@"(?m)^LFM3:",_=>name+":");
        text=Regex.Replace(text,@"(?m)^\[Tool: ([A-Za-z0-9_.:-]+)\](?=\r?$)","Tool: $1");
        var formatted=FormatBold(RestoreCode(text,code));
        var codeRanges=Regex.Matches(formatted.Text,CodePattern).Cast<Match>().ToList();
        var tools=Regex.Matches(formatted.Text,@"(?m)^Tool: [A-Za-z0-9_.:-]+(?=\r?$)")
            .Where(m=>!codeRanges.Any(c=>m.Index>=c.Index&&m.Index<c.Index+c.Length)).Select(m=>new BoldSpan(m.Index,m.Length)).ToList();
        return new StyledTranscript(formatted.Text,formatted.Bold,tools);
    }
    public static string HideDestinations(string text)
    {
        text=ProtectCode(text,out var code);
        var output=new StringBuilder();int start=0;var pattern=new Regex(@"!?\[([^\]\r\n]*)\]\(");
        while(true){
            var match=pattern.Match(text,start);
            if(!match.Success){output.Append(text[start..]);break;}
            int depth=1,end=match.Index+match.Length;
            while(end<text.Length&&depth>0){if(text[end]=='\\'&&end+1<text.Length&&"()\\".Contains(text[end+1])){end+=2;continue;}if(text[end]=='(')depth++;else if(text[end]==')')depth--;end++;}
            if(depth>0){output.Append(text[start..(match.Index+match.Length)]);start=match.Index+match.Length;continue;}
            output.Append(text[start..match.Index]);output.Append(match.Groups[1].Value);start=end;
        }
        text=output.ToString();
        text=Regex.Replace(text,@"(?m)^\s*\[[^\]\r\n]+\]:\s*\S+[^\r\n]*","");
        text=Regex.Replace(text,@"!?\[([^\]\r\n]+)\]\[[^\]\r\n]*\]","$1");
        text=Regex.Replace(text,"""(["'`])(?:[A-Za-z]:[\\/]|\\\\|/|~[/\\]|\.\.?[/\\])[^\r\n]*?\1""","");
        text=Regex.Replace(text,"""(?i)<?\b(?:https?://|ftp://|file://|mailto:|www\.)[^\s<>\[\]"`]+>?""","");
        text=Regex.Replace(text,"""(?<!\w)[A-Za-z]:[\\/][^\s<>"\[\]`]+""","");
        text=Regex.Replace(text,"""(?<!\w)\\\\[^\s<>"\[\]`]+""","");
        text=Regex.Replace(text,"""(?<![\w:])(?:~|\.{1,2})?/(?:[^\s/<>"`]+/)*[^\s/<>"`]+""","");
        text=Regex.Replace(text,"""(?i)\b(?:[\w.-]+[\\/])+[\w.-]+\.(?:png|jpe?g|webp|gif|bmp|wav|mp3|flac|ogg|mp4|mkv|txt|json|pdf|zip)\b""","");
        text=Regex.Replace(text,"""(?i)\b(?:[a-z0-9-]+\.)+(?:org|com|net|de|io|edu|gov)(?:/[^\s<>"`]+)?\b""","");
        text=Regex.Replace(text,@"(?m)[ \t]*[—–][ \t]*(?=\r?$)","");
        text=Regex.Replace(text,@"[ \t]{2,}"," ");
        text=Regex.Replace(text,@"\(\s*\)|\[\s*\]|<\s*>","");
        return RestoreCode(text,code);
    }
}
