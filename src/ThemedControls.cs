namespace Lfm3Desk;

// Let WinForms lay out and draw button captions. No custom paint coordinates.
public sealed class DeskButton : Button
{
    string iconKey="show_details";
    public string IconKey{get=>iconKey;set{iconKey=value;RefreshIcon();}}
    void RefreshIcon()
    {
        var old=Image;Image=ButtonIcons.Create(iconKey,Enabled?normalFore:SystemColors.GrayText,Math.Max(16,(int)Math.Ceiling(20*DeviceDpi/96.0)));old?.Dispose();
    }
    protected override void Dispose(bool disposing){if(disposing){var old=Image;Image=null;old?.Dispose();}base.Dispose(disposing);}
    protected override void OnDpiChangedAfterParent(EventArgs e){base.OnDpiChangedAfterParent(e);RefreshIcon();}
    Color normalBack=Color.FromArgb(49,81,123),normalFore=Color.White;
    Color disabledBack=Color.FromArgb(218,225,235);
    public void ConfigureTheme(Color background,Color foreground,Color border)
    {
        normalBack=background;normalFore=foreground;
        disabledBack=Color.FromArgb((background.R+1020)/5,(background.G+1020)/5,(background.B+1020)/5);
        FlatAppearance.BorderColor=border;RefreshColors();
    }
    void RefreshColors(){BackColor=Enabled?normalBack:disabledBack;ForeColor=Enabled?normalFore:SystemColors.GrayText;RefreshIcon();Invalidate();}
    protected override void OnEnabledChanged(EventArgs e){base.OnEnabledChanged(e);RefreshColors();}
    public DeskButton()
    {
        AutoSize=false;Size=new Size(140,38);MinimumSize=new Size(80,36);FlatStyle=FlatStyle.Flat;FlatAppearance.BorderSize=1;
        Padding=new Padding(6,2,6,2);UseVisualStyleBackColor=false;UseMnemonic=false;
        TextAlign=ContentAlignment.MiddleCenter;UseCompatibleTextRendering=false;
        ImageAlign=ContentAlignment.MiddleLeft;TextImageRelation=TextImageRelation.ImageBeforeText;
    }
}
public sealed class DeskMenuRenderer : ToolStripProfessionalRenderer
{
    readonly Color foreground,muted;
    public DeskMenuRenderer(Color background,Color surface,Color accent,Color foreground,Color muted):base(new MenuColors(background,surface,accent)){this.foreground=foreground;this.muted=muted;RoundedEdges=false;}
    protected override void OnRenderItemText(ToolStripItemTextRenderEventArgs e){e.TextColor=e.Item.Enabled?foreground:muted;base.OnRenderItemText(e);}
    sealed class MenuColors : ProfessionalColorTable
    {
        readonly Color background,surface,accent;
        public MenuColors(Color background,Color surface,Color accent){this.background=background;this.surface=surface;this.accent=accent;UseSystemColors=false;}
        public override Color MenuStripGradientBegin=>background;public override Color MenuStripGradientEnd=>background;
        public override Color ToolStripDropDownBackground=>surface;public override Color ImageMarginGradientBegin=>surface;public override Color ImageMarginGradientMiddle=>surface;public override Color ImageMarginGradientEnd=>surface;
        public override Color MenuItemSelected=>accent;public override Color MenuItemBorder=>accent;public override Color MenuBorder=>accent;
        public override Color MenuItemSelectedGradientBegin=>accent;public override Color MenuItemSelectedGradientEnd=>accent;
        public override Color MenuItemPressedGradientBegin=>surface;public override Color MenuItemPressedGradientMiddle=>surface;public override Color MenuItemPressedGradientEnd=>surface;
    }
}
