namespace Lfm3Desk;

// Lightweight UI animation; no additional assets or inference work.
public sealed class ImageActivityIndicator : Control
{
    readonly System.Windows.Forms.Timer timer=new(){Interval=60};
    bool animating;
    double phase;
    public bool Animating
    {
        get=>animating;
        set{animating=value;timer.Enabled=animating&&Visible;if(!value)phase=0;Invalidate();}
    }
    public ImageActivityIndicator()
    {
        SetStyle(ControlStyles.AllPaintingInWmPaint|ControlStyles.UserPaint|ControlStyles.OptimizedDoubleBuffer,true);
        timer.Tick+=(_,_)=>{phase+=0.18;Invalidate();};
        AccessibleName="Image generation activity";
        TabStop=false;
    }
    protected override void OnVisibleChanged(EventArgs e){base.OnVisibleChanged(e);timer.Enabled=animating&&Visible;}
    protected override void OnHandleDestroyed(EventArgs e){timer.Stop();base.OnHandleDestroyed(e);}
    protected override void Dispose(bool disposing){if(disposing)timer.Dispose();base.Dispose(disposing);}
    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        int side=Math.Max(3,Math.Min(Width,Height)/4),gap=Math.Max(2,side/4);
        int size=3*side+2*gap,left=(Width-size)/2,top=(Height-size)/2;
        for(int y=0;y<3;y++)for(int x=0;x<3;x++)
        {
            int alpha=animating?(int)(65+185*(0.5+0.5*Math.Sin(phase-x*.9-y*.65))):130;
            using var brush=new SolidBrush(Color.FromArgb(alpha,ForeColor));
            e.Graphics.FillRectangle(brush,left+x*(side+gap),top+y*(side+gap),side,side);
        }
    }
}
