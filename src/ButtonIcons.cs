using System.Drawing.Drawing2D;
namespace Lfm3Desk;

// Small code-native vector glyphs; no font, network, or image model dependency.
public static class ButtonIcons
{
    public static Bitmap Create(string key,Color color,int size)
    {
        var bitmap=new Bitmap(size,size);using var g=Graphics.FromImage(bitmap);
        g.SmoothingMode=SmoothingMode.AntiAlias;g.ScaleTransform(size/24f,size/24f);
        using var pen=new Pen(color,1.8f){StartCap=LineCap.Round,EndCap=LineCap.Round,LineJoin=LineJoin.Round};
        using var brush=new SolidBrush(color);
        void Line(float a,float b,float c,float d)=>g.DrawLine(pen,a,b,c,d);
        switch(key)
        {
            case "send":g.DrawPolygon(pen,new[]{new PointF(3,3),new PointF(22,12),new PointF(3,21),new PointF(7,12)});Line(7,12,16,12);break;
            case "stop":g.FillRectangle(brush,5,5,14,14);break;
            case "record":g.DrawRectangle(pen,9,3,6,12);g.DrawArc(pen,6,7,12,12,0,180);Line(12,19,12,22);Line(8,22,16,22);break;
            case "attach":g.DrawArc(pen,6,3,12,14,180,270);g.DrawArc(pen,9,5,6,11,180,270);Line(6,10,6,18);g.DrawArc(pen,6,14,12,8,0,180);Line(18,11,18,18);break;
            case "play":g.FillPolygon(brush,new[]{new PointF(7,4),new PointF(20,12),new PointF(7,20)});break;
            case "new_chat":g.DrawRectangle(pen,3,3,18,18);Line(12,7,12,17);Line(7,12,17,12);break;
            case "remove":Line(6,6,18,18);Line(18,6,6,18);break;
            case "download":Line(12,3,12,15);Line(7,10,12,15);Line(12,15,17,10);Line(4,16,4,21);Line(4,21,20,21);Line(20,16,20,21);break;
            case "setup":
                g.DrawEllipse(pen,7,7,10,10);g.DrawEllipse(pen,10,10,4,4);
                for(int i=0;i<8;i++){double angle=i*Math.PI/4;Line(12+(float)Math.Cos(angle)*7,12+(float)Math.Sin(angle)*7,12+(float)Math.Cos(angle)*10,12+(float)Math.Sin(angle)*10);}break;
            case "copy_error":g.DrawRectangle(pen,8,7,12,14);Line(4,17,4,3);Line(4,3,16,3);break;
            case "open_log":g.DrawRectangle(pen,5,3,14,18);Line(8,8,16,8);Line(8,12,16,12);Line(8,16,14,16);break;
            default:g.DrawEllipse(pen,3,3,18,18);g.FillEllipse(brush,11,6,2,2);Line(12,11,12,17);break;
        }
        return bitmap;
    }
}
