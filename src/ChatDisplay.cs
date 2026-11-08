using System.Text;
using System.Text.RegularExpressions;
namespace Lfm3Desk;
public static class ChatDisplay
{
    public static string HideDestinations(string text)
    {
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
        return text;
    }
}
