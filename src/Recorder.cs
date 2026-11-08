using System.Runtime.InteropServices;
using System.Text;
namespace Lfm3Desk;
public sealed class Recorder : IDisposable
{
    [DllImport("winmm.dll",CharSet=CharSet.Unicode)] static extern int mciSendString(string command,StringBuilder? result,int length,IntPtr window);
    [DllImport("winmm.dll",CharSet=CharSet.Unicode)] static extern int mciGetErrorString(int error,StringBuilder result,int length);
    bool active;
    static void Command(string text)
    {
        int code=mciSendString(text,null,0,IntPtr.Zero);
        if(code!=0) {var message=new StringBuilder(512);mciGetErrorString(code,message,512);throw new IOException(message.ToString());}
    }
    public void Start()
    {
        Command("open new type waveaudio alias lfmmic");active=true;
        try {Command("set lfmmic time format milliseconds");Command("set lfmmic channels 1 samplespersec 16000 bitspersample 16");Command("record lfmmic");}
        catch {Dispose();throw;}
    }
    public string Stop()
    {
        Directory.CreateDirectory(Path.Combine(Paths.Root,"output","recordings"));
        string file=Path.Combine(Paths.Root,"output","recordings",DateTime.Now.ToString("yyyyMMdd_HHmmss_")+Guid.NewGuid().ToString("N")[..8]+".wav");
        try {Command("stop lfmmic");Command("save lfmmic \""+file+"\"");return file;}
        finally {Dispose();}
    }
    public void Dispose() {if(active) {mciSendString("close lfmmic",null,0,IntPtr.Zero);active=false;}}
}
