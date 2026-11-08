using System.Diagnostics;
using System.Media;
using System.Text.Json;

namespace Lfm3Desk;

public sealed class MainForm : Form
{
    readonly Settings settings=Settings.Load();
    readonly Worker worker=new();
    readonly ChatStore chatStore=new(Paths.Root);
    readonly List<ChatSession> chatSessions=new();
    ChatSession activeChat=new();
    bool selectingChat;
    readonly ListBox chatList=new(){Dock=DockStyle.Fill,DrawMode=DrawMode.OwnerDrawFixed,ItemHeight=54,BorderStyle=BorderStyle.FixedSingle};
    readonly DeskButton newChat=new();
    readonly Recorder recorder=new();
    CancellationTokenSource? cancellation;
    bool recording,busy,localizing,failed;
    readonly MenuStrip menu=new(){Dock=DockStyle.Top};
    readonly TabControl tabs=new(){Dock=DockStyle.Fill,DrawMode=TabDrawMode.OwnerDrawFixed,ItemSize=new Size(180,34),SizeMode=TabSizeMode.Fixed};
    readonly TabPage chatPage=new(),settingsPage=new(),setupPage=new();
    readonly ComboBox ui=new(),theme=new(),inputLanguage=new(),outputLanguage=new(),speechLanguage=new(),format=new(),task=new(),voice=new(),device=new(),imageBackend=new();
    readonly NumericUpDown imageGpu=new(){Minimum=0,Maximum=31};
    readonly DeskButton imageGpuInstall=new();
    readonly CheckBox hideDestinations=new(),offlineMode=new(),save=new(),tools=new(),videoAudio=new(),autoplay=new();
    readonly CheckBox wikiEnabled=new(),wikiAuto=new(),wikiOnlineEnabled=new(),webEnabled=new(),weatherEnabled=new(),mcpEnabled=new();
    readonly Label wikiAvailability=new(){AutoSize=true,MaximumSize=new Size(430,0),UseMnemonic=false,Padding=new Padding(0,6,0,6)};
    readonly TextBox wikiPath=new(){Width=400};
    readonly ComboBox wikiFlavour=new();
    readonly DeskButton wikiBrowse=new(),wikiDownload=new(),mcpExport=new();
    readonly NumericUpDown tokens=new(){Minimum=32,Maximum=8192,Increment=128},fps=new(){Minimum=0.1m,Maximum=2,DecimalPlaces=1,Increment=0.1m};
    readonly TextBox prompt=new(){Multiline=true,ScrollBars=ScrollBars.Vertical,Dock=DockStyle.Fill,AcceptsReturn=true,BorderStyle=BorderStyle.FixedSingle};
    readonly TextBox system=new(){Multiline=true,ScrollBars=ScrollBars.Vertical,Dock=DockStyle.Fill,Height=84,BorderStyle=BorderStyle.FixedSingle};
    readonly RichTextBox answer=new(){ReadOnly=true,Dock=DockStyle.Fill,DetectUrls=false,BorderStyle=BorderStyle.None};
    readonly RichTextBox setupLog=new(){ReadOnly=true,Dock=DockStyle.Fill,DetectUrls=false,WordWrap=false,Font=new Font("Consolas",9.5f),BorderStyle=BorderStyle.None};
    readonly SplitContainer results=new(){Dock=DockStyle.Fill,Orientation=Orientation.Vertical,Panel2Collapsed=true,SplitterWidth=8};
    readonly PictureBox preview=new(){Dock=DockStyle.Fill,SizeMode=PictureBoxSizeMode.Zoom,Cursor=Cursors.Hand};
    readonly ListBox attachments=new(){Dock=DockStyle.Fill,HorizontalScrollbar=true,BorderStyle=BorderStyle.FixedSingle};
    readonly ProgressBar progress=new(){Dock=DockStyle.Fill,Style=ProgressBarStyle.Marquee,MarqueeAnimationSpeed=30,Visible=false,Margin=new Padding(12,6,2,6)};
    readonly TableLayoutPanel imageProgressPanel=new(){Dock=DockStyle.Fill,AutoSize=true,ColumnCount=3,RowCount=2,Visible=false,Padding=new Padding(8),Margin=new Padding(0,0,0,6)};
    readonly ImageActivityIndicator imageActivity=new(){Dock=DockStyle.Fill,Margin=new Padding(0,0,10,0)};
    readonly ProgressBar imageProgress=new(){Dock=DockStyle.Fill,Style=ProgressBarStyle.Marquee,MarqueeAnimationSpeed=30};
    readonly Label imageProgressText=new(){Dock=DockStyle.Fill,TextAlign=ContentAlignment.MiddleLeft,UseMnemonic=false};
    readonly Label imagePercent=new(){Dock=DockStyle.Fill,TextAlign=ContentAlignment.MiddleRight,UseMnemonic=false};
    bool imageActive;
    int speechIndex,speechTotal;
    readonly Label status=new(){Dock=DockStyle.Fill,AutoEllipsis=true,TextAlign=ContentAlignment.MiddleLeft,UseMnemonic=false};
    readonly Label setupSummary=new(){AutoSize=true,Dock=DockStyle.Fill,UseMnemonic=false,Padding=new Padding(0,0,0,8)};
    readonly Label errorText=new(){Dock=DockStyle.Fill,AutoEllipsis=true,TextAlign=ContentAlignment.MiddleLeft,UseMnemonic=false};
    readonly TableLayoutPanel errorBanner=new(){Dock=DockStyle.Top,ColumnCount=2,RowCount=1,Height=64,Visible=false,Padding=new Padding(12,8,8,8)};
    readonly DeskButton send=new(),stop=new(),mic=new(),attach=new(),remove=new(),setup=new(),download=new(),play=new(),openLog=new(),copyError=new(),details=new(),setupCancel=new();
    readonly Dictionary<Control,string> labels=new();
    readonly Dictionary<ToolStripItem,string> menuLabels=new();
    readonly Dictionary<ComboBox,string> choicePrefixes=new();
    readonly List<Attachment> media=new();
    readonly List<ToolStripItem> idleMenuItems=new();
    Dictionary<string,string> words=new();
    Dictionary<string,string> palette=new();
    string? lastImage,lastAudio,lastError;
    bool lastTemporary;
    SoundPlayer? player;

    public MainForm()
    {
        Text="LFM3 Desk 1.4.0";Font=new Font("Segoe UI",10);AutoScaleMode=AutoScaleMode.Dpi;
        MinimumSize=new Size(900,680);Size=new Size(1180,850);StartPosition=FormStartPosition.CenterScreen;
        var body=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=3,Padding=new Padding(12,8,12,8)};
        body.RowStyles.Add(new RowStyle(SizeType.AutoSize));body.RowStyles.Add(new RowStyle(SizeType.Percent,100));body.RowStyles.Add(new RowStyle(SizeType.Absolute,32));
        errorBanner.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));errorBanner.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,150));
        errorBanner.RowStyles.Add(new RowStyle(SizeType.Percent,100));
        details.Dock=DockStyle.None;details.Anchor=AnchorStyles.Top|AnchorStyles.Right;details.Margin=Padding.Empty;details.Size=new Size(140,36);details.MinimumSize=new Size(110,34);
        SetLabel(details,"show_details");errorBanner.Controls.Add(errorText,0,0);errorBanner.Controls.Add(details,1,0);body.Controls.Add(errorBanner,0,0);
        tabs.TabPages.AddRange(new[]{chatPage,settingsPage,setupPage});SetLabel(chatPage,"tab_chat");SetLabel(settingsPage,"tab_settings");SetLabel(setupPage,"tab_setup");
        foreach(var page in new[]{chatPage,settingsPage,setupPage})page.Padding=new Padding(12);
        body.Controls.Add(tabs,0,1);
        var statusRow=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=2,Margin=Padding.Empty};statusRow.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));statusRow.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,250));statusRow.Controls.Add(status,0,0);statusRow.Controls.Add(progress,1,0);body.Controls.Add(statusRow,0,2);
        Controls.Add(body);Controls.Add(menu);MainMenuStrip=menu;
        InitializeChoices();BuildChat();BuildSettings();BuildSetup();BuildMenu();
        tabs.DrawItem+=(_,e)=>{var selected=tabs.SelectedIndex==e.Index;using var brush=new SolidBrush(C(selected?"accent":"background"));e.Graphics.FillRectangle(brush,e.Bounds);TextRenderer.DrawText(e.Graphics,tabs.TabPages[e.Index].Text,Font,e.Bounds,selected?Contrast(C("accent")):C("foreground"),TextFormatFlags.HorizontalCenter|TextFormatFlags.VerticalCenter|TextFormatFlags.NoPrefix);};
        ui.SelectedIndexChanged+=(_,_)=>{if(!localizing){Localize();ApplyTheme();}};
        theme.SelectedIndexChanged+=(_,_)=>{if(!localizing)ApplyTheme();};
        send.Click+=async(_,_)=>await Send();stop.Click+=(_,_)=>cancellation?.Cancel();setupCancel.Click+=(_,_)=>cancellation?.Cancel();mic.Click+=(_,_)=>Record();attach.Click+=(_,_)=>AttachFiles();
        remove.Click+=(_,_)=>{int i=attachments.SelectedIndex;if(i>=0){media.RemoveAt(i);attachments.Items.RemoveAt(i);}};
        setup.Click+=async(_,_)=>await Setup();download.Click+=async(_,_)=>await Download();
        wikiBrowse.Click+=(_,_)=>{using var dialog=new OpenFileDialog{Filter="Wikipedia ZIM|*.zim"};if(dialog.ShowDialog()==DialogResult.OK){wikiPath.Text=dialog.FileName;ReadSettings().Save();}};
        imageGpuInstall.Click+=async(_,_)=>await InstallImageGpu();
        wikiDownload.Click+=async(_,_)=>await DownloadWikipedia();
        mcpExport.Click+=(_,_)=>{try{ReadSettings().Save();using var dialog=new SaveFileDialog{Filter="JSON|*.json",FileName="lfm3desk-mcp.json"};if(dialog.ShowDialog()==DialogResult.OK)File.WriteAllText(dialog.FileName,McpHost.Configuration());}catch(Exception e){ReportError(e);}};
        foreach(var check in new[]{wikiEnabled,wikiAuto,wikiOnlineEnabled,webEnabled,weatherEnabled,mcpEnabled})check.CheckedChanged+=(_,_)=>{if(!localizing)try{ReadSettings().Save();}catch(Exception e){ReportError(e);}};
        hideDestinations.CheckedChanged+=(_,_)=>{if(!localizing){RenderTranscript();ReadSettings().Save();}};
        offlineMode.CheckedChanged+=(_,_)=>{if(!localizing)ReadSettings().Save();};
        play.Click+=(_,_)=>PlayLast();
        openLog.Click+=(_,_)=>OpenSetupLog();copyError.Click+=(_,_)=>{if(!string.IsNullOrEmpty(lastError))Clipboard.SetText(lastError);else if(setupLog.TextLength>0)Clipboard.SetText(setupLog.Text);};
        details.Click+=(_,_)=>ShowErrorDetails();
        preview.Click+=(_,_)=>{if(lastImage!=null&&File.Exists(lastImage))OpenFile(lastImage);};
        worker.Event+=e=>QueueUi(()=>HandleEvent(e));
        prompt.KeyDown+=async(_,e)=>{if(e.Control&&e.KeyCode==Keys.Enter){e.SuppressKeyPress=true;await Send();}};
        FormClosing+=(_,_)=>{try{SaveCurrentChat();}catch(Exception e){AppLog.Append("chat-store.log",e.ToString());}cancellation?.Cancel();recorder.Dispose();worker.Dispose();player?.Stop();player?.Dispose();preview.Image?.Dispose();DeleteTemporary();try{ReadSettings().Save();}catch{}};
        Localize();InitializeChats();ApplyTheme();UpdateAvailability();
        ResizeEnd+=(_,_)=>{SizeToolbarButtons();RecordButtonLayout();};
        Shown+=async(_,_)=>{SizeToolbarButtons();BeginInvoke(new Action(RecordButtonLayout));var work=Screen.FromControl(this).WorkingArea;if(Width>work.Width||Height>work.Height)Bounds=work;if(!Paths.RuntimeReady)await Setup();else await Download();};
    }

    void InitializeChoices()
    {
        Fill(ui,new[]{"DE","EN","PIH"},settings.UiLanguage,"ui");
        Fill(theme,Directory.GetFiles(Path.Combine(Paths.Root,"themes"),"*.json").Select(Path.GetFileNameWithoutExtension).OfType<string>().OrderBy(x=>x).ToArray(),settings.Theme,"theme");
        var languages=new[]{"AUTO","DE","EN","FR","RU","ES","IT","JA","KO","ZH","AR","PL","PT","DA","EL","FI","HE","NL","SV","TR","VI","TH","ID","HI"};
        var speechLanguages=new[]{"DE","EN","FR","ES","IT","JA","KO","ZH","AR","PL","PT","DA","EL","FI","HE","NL","SV","TR"};
        Fill(inputLanguage,languages,settings.InputLanguage,"language");Fill(outputLanguage,languages,settings.OutputLanguage,"language");Fill(speechLanguage,speechLanguages,settings.SpeechLanguage,"language");
        Fill(format,new[]{"txt","tts","txt,tts"},settings.Output,"output");Fill(task,new[]{"chat","asr","translate","tts"},"chat","task");Fill(voice,new[]{"female","male"},settings.Voice,"voice");Fill(device,new[]{"auto","cuda","cpu"},settings.Device,"device");
        Fill(imageBackend,new[]{"cpu","directml"},settings.ImageBackend,"image_backend");imageGpu.Value=Math.Clamp(settings.ImageGpu,0,31);
        tokens.Value=Math.Clamp(settings.MaxTokens,32,8192);fps.Value=Math.Clamp((decimal)settings.Fps,0.1m,2);system.Text=settings.SystemPrompt;
        Fill(wikiFlavour,new[]{"mini","nopic"},settings.WikiFlavour,"wiki");
        wikiOnlineEnabled.Checked=settings.WikiOnlineEnabled;wikiPath.Text=settings.WikiPath;wikiEnabled.Checked=settings.WikiEnabled;wikiAuto.Checked=settings.WikiAuto;webEnabled.Checked=settings.WebEnabled;weatherEnabled.Checked=settings.WeatherEnabled;mcpEnabled.Checked=settings.McpEnabled;
        hideDestinations.Checked=settings.HideChatDestinations;offlineMode.Checked=settings.OfflineMode;save.Checked=settings.SaveAudio;tools.Checked=settings.Tools;videoAudio.Checked=settings.VideoAudio;autoplay.Checked=settings.PlayAudio;
    }
    void BuildChat()
    {
        var shell=new SplitContainer{Width=1050,Dock=DockStyle.Fill,FixedPanel=FixedPanel.Panel1,SplitterDistance=210,Panel1MinSize=170,Panel2MinSize=400,SplitterWidth=8};chatPage.Controls.Add(shell);
        var sidebar=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=2,Padding=new Padding(0,0,8,0)};sidebar.RowStyles.Add(new RowStyle(SizeType.Absolute,50));sidebar.RowStyles.Add(new RowStyle(SizeType.Percent,100));shell.Panel1.Controls.Add(sidebar);
        SetLabel(newChat,"new_chat");newChat.Dock=DockStyle.Top;newChat.Height=38;sidebar.Controls.Add(newChat,0,0);sidebar.Controls.Add(chatList,0,1);
        newChat.Click+=(_,_)=>{if(!busy&&!recording)CreateChat();};
        chatList.SelectedIndexChanged+=(_,_)=>{if(!selectingChat&&!busy&&!recording&&chatList.SelectedItem is ChatSession chat&&chat.Id!=activeChat.Id){SaveCurrentChat();RestoreChat(chat);}};
        chatList.DrawItem+=(_,e)=>{if(e.Index<0)return;var item=(ChatSession)chatList.Items[e.Index];bool selected=(e.State&DrawItemState.Selected)!=0;var back=C(selected?"accent":"surface");using var brush=new SolidBrush(back);e.Graphics.FillRectangle(brush,e.Bounds);var rectangle=new Rectangle(e.Bounds.X+8,e.Bounds.Y+5,e.Bounds.Width-16,Font.Height+4);TextRenderer.DrawText(e.Graphics,item.Title,Font,rectangle,selected?Contrast(back):C("foreground"),TextFormatFlags.SingleLine|TextFormatFlags.EndEllipsis|TextFormatFlags.NoPrefix);rectangle.Y+=Font.Height+6;rectangle.Height=Font.Height+2;TextRenderer.DrawText(e.Graphics,item.Updated.LocalDateTime.ToString("g"),Font,rectangle,selected?Contrast(back):C("muted"),TextFormatFlags.SingleLine|TextFormatFlags.EndEllipsis);};
        var grid=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=4,Margin=Padding.Empty};grid.RowStyles.Add(new RowStyle(SizeType.Percent,100));grid.RowStyles.Add(new RowStyle(SizeType.AutoSize));grid.RowStyles.Add(new RowStyle(SizeType.Absolute,210));grid.RowStyles.Add(new RowStyle(SizeType.Absolute,48));shell.Panel2.Controls.Add(grid);
        imageProgressPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,58));imageProgressPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));imageProgressPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,90));
        imageProgressPanel.RowStyles.Add(new RowStyle(SizeType.Absolute,28));imageProgressPanel.RowStyles.Add(new RowStyle(SizeType.Absolute,22));
        imageProgressPanel.Controls.Add(imageActivity,0,0);imageProgressPanel.SetRowSpan(imageActivity,2);imageProgressPanel.Controls.Add(imageProgressText,1,0);imageProgressPanel.SetColumnSpan(imageProgressText,2);imageProgressPanel.Controls.Add(imageProgress,1,1);imageProgressPanel.Controls.Add(imagePercent,2,1);grid.Controls.Add(imageProgressPanel,0,1);
        var conversation=Group("conversation");results.Panel1.Padding=new Padding(6);results.Panel1.Controls.Add(answer);results.Panel2.Controls.Add(preview);conversation.Controls.Add(results);grid.Controls.Add(conversation,0,0);
        var input=Group("message");var composer=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=2,RowCount=2,Margin=Padding.Empty};composer.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,70));composer.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,30));composer.RowStyles.Add(new RowStyle(SizeType.Absolute,25));composer.RowStyles.Add(new RowStyle(SizeType.Percent,100));
        composer.Controls.Add(LabelFor("prompt_hint"),0,0);composer.Controls.Add(LabelFor("attachments"),1,0);prompt.Margin=new Padding(0,0,10,0);composer.Controls.Add(prompt,0,1);
        var mediaBox=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=2,Margin=Padding.Empty};mediaBox.RowStyles.Add(new RowStyle(SizeType.Percent,100));mediaBox.RowStyles.Add(new RowStyle(SizeType.Absolute,48));mediaBox.Controls.Add(attachments,0,0);SetLabel(remove,"remove");remove.Dock=DockStyle.None;remove.Anchor=AnchorStyles.Top|AnchorStyles.Right;remove.Margin=new Padding(0,5,0,2);remove.Size=new Size(140,38);toolbarButtons.Add(remove);mediaBox.Controls.Add(remove,0,1);composer.Controls.Add(mediaBox,1,1);input.Controls.Add(composer);grid.Controls.Add(input,0,2);
        grid.Controls.Add(ButtonRow(new[]{(send,"send"),(stop,"stop"),(mic,"record"),(attach,"attach"),(play,"play")}),0,3);
    }
    void BuildSettings()
    {
        var scroll=new Panel{Dock=DockStyle.Fill,AutoScroll=true};settingsPage.Controls.Add(scroll);
        var grid=new TableLayoutPanel{Dock=DockStyle.Top,AutoSize=true,ColumnCount=2,Padding=new Padding(0,0,6,0)};grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,50));grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,50));scroll.Controls.Add(grid);
        var language=SettingsGroup("language_voice",new[]{("input_language",(Control)inputLanguage),("output_language",outputLanguage),("speech_language",speechLanguage),("voice",voice)});grid.Controls.Add(language,0,0);
        var model=SettingsGroup("model_output",new[]{("task",(Control)task),("output",format),("device",device),("tokens",tokens),("fps",fps),("image_backend",imageBackend),("image_gpu",imageGpu),("image_gpu_runtime",imageGpuInstall)});grid.Controls.Add(model,1,0);
        SetLabel(imageGpuInstall,"image_gpu_install");
        grid.Controls.Add(SettingsGroup("appearance",new[]{("interface",(Control)ui),("theme",theme)}),0,1);
        var behavior=Group("behavior");behavior.AutoSize=true;var checks=new TableLayoutPanel{Dock=DockStyle.Top,AutoSize=true,ColumnCount=1,Padding=new Padding(4)};
        foreach(var (check,key) in new[]{(hideDestinations,"hide_chat_destinations"),(save,"save_audio"),(autoplay,"autoplay"),(tools,"tools"),(videoAudio,"video_audio")}){SetLabel(check,key);check.AutoSize=true;check.UseMnemonic=false;check.Margin=new Padding(0,5,0,5);checks.Controls.Add(check);}
        behavior.Controls.Add(checks);grid.Controls.Add(behavior,1,1);
        var knowledge=Group("knowledge");knowledge.AutoSize=true;
        var knowledgeGrid=new TableLayoutPanel{Dock=DockStyle.Top,AutoSize=true,ColumnCount=1};
        foreach(var (check,key) in new[]{(wikiEnabled,"wiki_enabled"),(wikiAuto,"wiki_auto")}){SetLabel(check,key);check.AutoSize=true;check.UseMnemonic=false;knowledgeGrid.Controls.Add(check);}
        var pathLabel=LabelFor("wiki_path");pathLabel.AutoSize=true;knowledgeGrid.Controls.Add(pathLabel);wikiPath.Dock=DockStyle.Top;knowledgeGrid.Controls.Add(wikiPath);
        SetLabel(wikiBrowse,"wiki_browse");wikiBrowse.Size=new Size(240,36);knowledgeGrid.Controls.Add(wikiBrowse);
        var edition=LabelFor("wiki_edition");edition.AutoSize=true;knowledgeGrid.Controls.Add(edition);wikiFlavour.Width=400;knowledgeGrid.Controls.Add(wikiFlavour);
        SetLabel(wikiDownload,"wiki_download");wikiDownload.Size=new Size(400,40);knowledgeGrid.Controls.Add(wikiDownload);
        var wikiHint=LabelFor("wiki_hint");wikiHint.AutoSize=true;wikiHint.MaximumSize=new Size(430,0);wikiHint.Padding=new Padding(0,8,0,0);knowledgeGrid.Controls.Add(wikiHint);knowledgeGrid.Controls.Add(wikiAvailability);knowledge.Controls.Add(knowledgeGrid);grid.Controls.Add(knowledge,0,2);
        var connections=Group("connections");connections.AutoSize=true;var connectionGrid=new TableLayoutPanel{Dock=DockStyle.Top,AutoSize=true,ColumnCount=1};
        foreach(var (check,key) in new[]{(offlineMode,"offline_mode"),(wikiOnlineEnabled,"wiki_online_enabled"),(webEnabled,"web_enabled"),(weatherEnabled,"weather_enabled"),(mcpEnabled,"mcp_enabled")}){SetLabel(check,key);check.AutoSize=true;check.UseMnemonic=false;check.Margin=new Padding(0,6,0,6);connectionGrid.Controls.Add(check);}
        SetLabel(mcpExport,"mcp_export");mcpExport.Size=new Size(400,40);connectionGrid.Controls.Add(mcpExport);
        var networkHint=LabelFor("connections_hint");networkHint.AutoSize=true;networkHint.MaximumSize=new Size(430,0);networkHint.Padding=new Padding(0,10,0,0);connectionGrid.Controls.Add(networkHint);connections.Controls.Add(connectionGrid);grid.Controls.Add(connections,1,2);
        var instruction=Group("system");instruction.Height=130;instruction.Controls.Add(system);grid.Controls.Add(instruction,0,3);grid.SetColumnSpan(instruction,2);
        var help=LabelFor("settings_hint");help.AutoSize=true;help.MaximumSize=new Size(950,0);help.Padding=new Padding(8);grid.Controls.Add(help,0,4);grid.SetColumnSpan(help,2);
    }
    void BuildSetup()
    {
        var grid=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=3};grid.RowStyles.Add(new RowStyle(SizeType.AutoSize));grid.RowStyles.Add(new RowStyle(SizeType.Absolute,48));grid.RowStyles.Add(new RowStyle(SizeType.Percent,100));setupPage.Controls.Add(grid);
        grid.Controls.Add(setupSummary,0,0);grid.Controls.Add(ButtonRow(new[]{(setup,"setup"),(download,"download"),(setupCancel,"stop"),(openLog,"open_log"),(copyError,"copy_error")}),0,1);
        var logBox=Group("live_log");logBox.Controls.Add(setupLog);grid.Controls.Add(logBox,0,2);
    }
    void BuildMenu()
    {
        ToolStripMenuItem Parent(string key){var item=new ToolStripMenuItem();menuLabels[item]=key;menu.Items.Add(item);return item;}
        ToolStripMenuItem Action(ToolStripMenuItem parent,string key,Action action,bool needsIdle=false,Keys shortcut=Keys.None){var item=new ToolStripMenuItem{ShortcutKeys=shortcut};menuLabels[item]=key;item.Click+=(_,_)=>action();parent.DropDownItems.Add(item);if(needsIdle)idleMenuItems.Add(item);return item;}
        var file=Parent("menu_file");Action(file,"new_chat",async()=>await ClearChat(),true,Keys.Control|Keys.N);Action(file,"export",()=>Export());Action(file,"folder",()=>OpenOutput());file.DropDownItems.Add(new ToolStripSeparator());Action(file,"quit",()=>Close());
        var model=Parent("menu_model");Action(model,"setup",async()=>await Setup(),true);Action(model,"download",async()=>await Download(),true);Action(model,"play",()=>PlayLast());
        var view=Parent("menu_view");Action(view,"tab_chat",()=>tabs.SelectedTab=chatPage);Action(view,"tab_settings",()=>tabs.SelectedTab=settingsPage);Action(view,"tab_setup",()=>tabs.SelectedTab=setupPage);
        var help=Parent("menu_help");Action(help,"readme",()=>OpenFile(Path.Combine(Paths.Root,"README.md")));Action(help,"about",()=>MessageBox.Show(this,"LFM3 Desk 1.4.0\nC# / local LFM3 Omni + Tiny-SD\ngithub.com/zeittresor",T("about"),MessageBoxButtons.OK,MessageBoxIcon.Information));
    }
    GroupBox Group(string key){var group=new GroupBox{Dock=DockStyle.Fill,Padding=new Padding(10,24,10,10),Margin=new Padding(0,0,10,10)};SetLabel(group,key);return group;}
    GroupBox SettingsGroup(string key,(string Key,Control Control)[] fields)
    {
        var group=Group(key);group.AutoSize=true;group.AutoSizeMode=AutoSizeMode.GrowAndShrink;
        var grid=new TableLayoutPanel{Dock=DockStyle.Top,AutoSize=true,ColumnCount=2,Padding=Padding.Empty};grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,45));grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,55));
        foreach(var (name,control) in fields){int row=grid.RowCount++;grid.RowStyles.Add(new RowStyle(SizeType.Absolute,control is DeskButton?48:40));var label=LabelFor(name);label.TextAlign=ContentAlignment.MiddleLeft;label.Dock=DockStyle.Fill;grid.Controls.Add(label,0,row);control.Dock=DockStyle.Fill;control.Margin=new Padding(4,6,2,4);grid.Controls.Add(control,1,row);}
        group.Controls.Add(grid);return group;
    }
    readonly List<DeskButton> toolbarButtons=new();
    TableLayoutPanel ButtonRow((DeskButton Button,string Key)[] buttons)
    {
        var row=new TableLayoutPanel{Dock=DockStyle.Fill,AutoSize=false,ColumnCount=buttons.Length+1,RowCount=1,Margin=Padding.Empty,Padding=Padding.Empty,GrowStyle=TableLayoutPanelGrowStyle.FixedSize};
        row.RowStyles.Add(new RowStyle(SizeType.Percent,100));
        int i=0;
        foreach(var (button,key) in buttons)
        {
            SetLabel(button,key);button.AutoSize=false;button.MinimumSize=Size.Empty;
            button.Dock=DockStyle.None;button.Anchor=AnchorStyles.Top|AnchorStyles.Left;
            button.Size=new Size(150,34);button.Margin=new Padding(0,3,8,3);
            row.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));row.Controls.Add(button,i++,0);
            toolbarButtons.Add(button);
        }
        row.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        return row;
    }
    void SizeToolbarButtons()
    {
        chatList.ItemHeight=Math.Max(54,Font.Height*2+12);
        details.Size=new Size(Math.Max(140,TextRenderer.MeasureText(details.Text,details.Font).Width+50),Math.Max(36,(int)Math.Ceiling(36*DeviceDpi/96.0)));
        errorBanner.ColumnStyles[1].Width=details.Width+8;errorBanner.Height=Math.Max(64,details.Height+errorBanner.Padding.Vertical);
        int height=Math.Max(34,(int)Math.Ceiling(34*DeviceDpi/96.0));
        foreach(var button in toolbarButtons)
        {
            int width=TextRenderer.MeasureText(button.Text,button.Font,new Size(int.MaxValue,height),TextFormatFlags.SingleLine|TextFormatFlags.NoPrefix).Width+(int)Math.Ceiling(50*DeviceDpi/96.0);
            button.Size=new Size(Math.Max((int)Math.Ceiling(110*DeviceDpi/96.0),width),height);
        }
    }
    void RecordButtonLayout()
    {
        if(IsDisposed||Disposing)return;
        try
        {
            var lines=toolbarButtons.Concat(new[]{details,newChat,wikiBrowse,wikiDownload,mcpExport}).Select(button=>$"{button.Text}: Bounds={button.Bounds}; Client={button.ClientSize}; ParentClient={button.Parent?.ClientSize}; FontHeight={button.Font.Height}; DPI={button.DeviceDpi}; Enabled={button.Enabled}");
            var directory=Path.Combine(Paths.Root,"output","logs");Directory.CreateDirectory(directory);
            File.WriteAllLines(Path.Combine(directory,"ui-layout.log"),new[]{$"LFM3 Desk 1.4.0 | ui-layout | {DateTimeOffset.Now:O}"}.Concat(lines));
        }
        catch{}
    }
    Label LabelFor(string key){var label=new Label{Dock=DockStyle.Fill,TextAlign=ContentAlignment.MiddleLeft,AutoEllipsis=true,UseMnemonic=false};SetLabel(label,key);return label;}
    void SetLabel(Control control,string key){labels[control]=key;control.Text=key;if(control is DeskButton button)button.IconKey=key;}
    void Fill(ComboBox combo,string[] values,string selected,string prefix)
    {
        combo.DropDownStyle=ComboBoxStyle.DropDownList;combo.DrawMode=DrawMode.OwnerDrawFixed;combo.ItemHeight=24;combo.FormattingEnabled=true;combo.Items.AddRange(values);combo.SelectedItem=values.Contains(selected)?selected:values.FirstOrDefault();choicePrefixes[combo]=prefix;
        combo.DrawItem+=(_,e)=>{if(e.Index<0)return;bool selectedItem=(e.State&DrawItemState.Selected)!=0;var back=C(selectedItem?"accent":"surface");using var brush=new SolidBrush(back);e.Graphics.FillRectangle(brush,e.Bounds);var value=combo.Items[e.Index]?.ToString()??"";var key=prefix+"_"+value;TextRenderer.DrawText(e.Graphics,words.GetValueOrDefault(key,value),Font,e.Bounds,combo.Enabled?(selectedItem?Contrast(back):C("foreground")):C("muted"),TextFormatFlags.Left|TextFormatFlags.VerticalCenter|TextFormatFlags.EndEllipsis|TextFormatFlags.NoPrefix);};
    }
    static string Value(ComboBox combo)=>combo.SelectedItem?.ToString()??"";
    string T(string key)=>words.GetValueOrDefault(key,key);
    void Localize()
    {
        localizing=true;
        try{
            words=JsonSerializer.Deserialize<Dictionary<string,string>>(File.ReadAllText(Path.Combine(Paths.Root,"lang","EN.json")))!;
            var path=Path.Combine(Paths.Root,"lang",Value(ui)+".json");if(File.Exists(path))foreach(var pair in JsonSerializer.Deserialize<Dictionary<string,string>>(File.ReadAllText(path))!)words[pair.Key]=pair.Value;
            foreach(var pair in labels)pair.Key.Text=pair.Key is DeskButton?System.Text.RegularExpressions.Regex.Replace(T(pair.Value),@"\s+"," ").Trim():pair.Key is GroupBox?T(pair.Value).Replace("&","&&"):T(pair.Value);foreach(var pair in menuLabels)pair.Key.Text=T(pair.Value);foreach(var combo in choicePrefixes.Keys)combo.Invalidate();SizeToolbarButtons();
            if(recording)mic.Text=T("stop_recording");if(!busy&&!failed)status.Text=T(Paths.RuntimeReady?"ready":"setup_required");UpdateSummary();tabs.Invalidate();
        }catch(Exception e){status.Text=e.Message;}finally{localizing=false;}
    }
    Color C(string key)
    {
        string fallback=key switch{"background"=>"#151922","surface"=>"#232a36","accent"=>"#31517b","muted"=>"#b2bdcc","border"=>"#536073","error"=>"#6b252b",_=>"#f0f3fa"};
        return ColorTranslator.FromHtml(palette.GetValueOrDefault(key,fallback));
    }
    static Color Contrast(Color color)=>color.GetBrightness()>.62f?Color.FromArgb(20,25,32):Color.White;
    void ApplyTheme()
    {
        try{
            palette=JsonSerializer.Deserialize<Dictionary<string,string>>(File.ReadAllText(Path.Combine(Paths.Root,"themes",Value(theme)+".json")))!;
            void Paint(Control control){var surface=control is TextBoxBase||control is ListBox||control is ComboBox||control is NumericUpDown;control.BackColor=C(surface?"surface":"background");control.ForeColor=C("foreground");
                if(control is ImageActivityIndicator)control.ForeColor=C("accent");
                if(control is DeskButton button)button.ConfigureTheme(C("accent"),Contrast(C("accent")),C("border"));
                foreach(Control child in control.Controls)Paint(child);control.Invalidate();}
            Paint(this);menu.Renderer=new DeskMenuRenderer(C("background"),C("surface"),C("accent"),C("foreground"),C("muted"));
            errorBanner.BackColor=C("error");errorText.BackColor=C("error");errorText.ForeColor=Contrast(C("error"));
        }catch(Exception e){status.Text=e.Message;}
    }
    Settings ReadSettings(){settings.ImageBackend=Value(imageBackend);settings.ImageGpu=(int)imageGpu.Value;settings.HideChatDestinations=hideDestinations.Checked;settings.OfflineMode=offlineMode.Checked;settings.WikiOnlineEnabled=wikiOnlineEnabled.Checked;settings.WikiEnabled=wikiEnabled.Checked;settings.WikiAuto=wikiAuto.Checked;settings.WikiPath=wikiPath.Text.Trim();settings.WikiFlavour=Value(wikiFlavour);settings.WebEnabled=webEnabled.Checked;settings.WeatherEnabled=weatherEnabled.Checked;settings.McpEnabled=mcpEnabled.Checked;settings.UiLanguage=Value(ui);settings.Theme=Value(theme);settings.InputLanguage=Value(inputLanguage);settings.OutputLanguage=Value(outputLanguage);settings.SpeechLanguage=Value(speechLanguage);settings.Output=Value(format);settings.Voice=Value(voice);settings.Device=Value(device);settings.SaveAudio=save.Checked;settings.Tools=tools.Checked;settings.VideoAudio=videoAudio.Checked;settings.PlayAudio=autoplay.Checked;settings.MaxTokens=(int)tokens.Value;settings.Fps=(double)fps.Value;settings.SystemPrompt=system.Text;return settings;}
    void UpdateAvailability(){chatList.Enabled=newChat.Enabled=!busy&&!recording;wikiDownload.Enabled=!busy&&!recording;wikiBrowse.Enabled=!busy;wikiFlavour.Enabled=!busy;send.Enabled=!busy&&!recording&&Paths.RuntimeReady;mic.Enabled=!busy;attach.Enabled=remove.Enabled=!busy;setup.Enabled=download.Enabled=!busy&&!recording;imageGpuInstall.Enabled=!busy&&!recording&&Paths.RuntimeReady;imageBackend.Enabled=imageGpu.Enabled=!busy;device.Enabled=!busy;stop.Enabled=setupCancel.Enabled=busy;foreach(var item in idleMenuItems)item.Enabled=!busy&&!recording;}
    void UpdateSummary()
    {
        var available=Paths.HasWikipedia(wikiPath.Text.Trim());
        wikiAvailability.Text=T(!wikiEnabled.Checked?"wiki_disabled":available?"wiki_ready":"wiki_unavailable");
        if(wikiEnabled.Checked&&!available){try{using var document=JsonDocument.Parse(File.ReadAllText(Path.Combine(Paths.Root,"data","wikipedia","status.json")));if(document.RootElement.TryGetProperty("error",out var error)&&!string.IsNullOrWhiteSpace(error.GetString()))wikiAvailability.Text+="\n"+error.GetString();}catch{}}
        setupSummary.Text=T(Paths.RuntimeReady?"runtime_prepared":"setup_required")+Environment.NewLine+T("setup_explanation");
        if(Paths.RuntimeReady&&wikiEnabled.Checked&&!available)setupSummary.Text+="\n"+T("wiki_unavailable");
    }
    void QueueUi(Action action){if(IsDisposed||Disposing||!IsHandleCreated)return;try{BeginInvoke(new Action(()=>{if(!IsDisposed&&!Disposing)action();}));}catch(InvalidOperationException){}}
    void Log(string line){if(IsDisposed||Disposing)return;setupLog.AppendText(line+Environment.NewLine);if(setupLog.TextLength>250000)setupLog.Text=setupLog.Text[^180000..];setupLog.SelectionStart=setupLog.TextLength;setupLog.ScrollToCaret();}
    void SetupLine(string line){if(IsDisposed||Disposing)return;Log(line);if(busy&&line.StartsWith("[STEP]"))status.Text=line[6..].Trim();
        if(busy&&line.StartsWith("[WIKI]")&&line.Contains('%')&&double.TryParse(line[6..line.IndexOf('%')].Trim(),System.Globalization.NumberStyles.Float,System.Globalization.CultureInfo.InvariantCulture,out var percent)){progress.Style=ProgressBarStyle.Continuous;progress.Value=Math.Clamp((int)percent,0,100);status.Text=line[6..].Trim();}}
    async Task<bool> Execute(Func<CancellationToken,Task> action,string message)
    {
        if(busy)return false;speechTotal=0;imageActivity.Animating=false;imageProgressPanel.Visible=false;imageActive=false;failed=false;errorBanner.Visible=false;busy=true;cancellation=new CancellationTokenSource();progress.Style=ProgressBarStyle.Marquee;progress.MarqueeAnimationSpeed=30;progress.Visible=true;status.Text=message;UpdateAvailability();
        bool success=false;
        try{await action(cancellation.Token);success=true;}
        catch(OperationCanceledException){if(imageActive)FinishImageProgress("cancelled",false);status.Text=T("cancelled");Log(T("cancelled"));}
        catch(Exception e){if(imageActive)FinishImageProgress("image_failed",false);ReportError(e);}
        finally{busy=false;cancellation.Dispose();cancellation=null;if(!IsDisposed&&!Disposing){progress.MarqueeAnimationSpeed=0;progress.Visible=false;UpdateSummary();UpdateAvailability();if(success)status.Text=T(Paths.RuntimeReady&&wikiEnabled.Checked&&!Paths.HasWikipedia(wikiPath.Text.Trim())?"ready_without_wiki":"ready");}}
        return success;
    }
    void ShowErrorDetails()
    {
        using var dialog=new Form{Text=T("error_details"),StartPosition=FormStartPosition.CenterParent,Size=new Size(940,580),MinimumSize=new Size(600,360),Font=Font,AutoScaleMode=AutoScaleMode.Dpi,BackColor=C("background"),ForeColor=C("foreground"),MinimizeBox=false,ShowInTaskbar=false};
        var area=Screen.FromControl(this).WorkingArea;dialog.Size=new Size(Math.Min(dialog.Width,area.Width),Math.Min(dialog.Height,area.Height));
        var grid=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=2,Padding=new Padding(12)};grid.RowStyles.Add(new RowStyle(SizeType.Percent,100));grid.RowStyles.Add(new RowStyle(SizeType.Absolute,52));dialog.Controls.Add(grid);
        var text=new RichTextBox{Dock=DockStyle.Fill,ReadOnly=true,WordWrap=false,DetectUrls=false,Font=new Font("Consolas",10),BackColor=C("surface"),ForeColor=C("foreground"),Text=lastError??setupLog.Text};grid.Controls.Add(text,0,0);
        var actions=new FlowLayoutPanel{Dock=DockStyle.Fill,WrapContents=false,AutoScroll=true,Padding=new Padding(0,6,0,0)};grid.Controls.Add(actions,0,1);
        DeskButton Add(string key,Action action){var button=new DeskButton{Text=T(key),IconKey=key,Size=new Size(Math.Max(160,TextRenderer.MeasureText(T(key),Font).Width+52),36),Margin=new Padding(0,0,10,0)};button.ConfigureTheme(C("accent"),Contrast(C("accent")),C("border"));button.Click+=(_,_)=>action();actions.Controls.Add(button);return button;}
        Add("copy_error",()=>{try{Clipboard.SetText(text.Text);}catch(Exception e){MessageBox.Show(dialog,e.Message,T("error_details"));}});
        Add("open_log",()=>OpenSetupLog());
        var close=Add("close",()=>dialog.Close());dialog.CancelButton=close;
        dialog.ShowDialog(this);
    }
    void ReportError(Exception error){failed=true;lastError=error.ToString();var lines=error.Message.Split(new[]{'\r','\n'},StringSplitOptions.RemoveEmptyEntries);var summary=lines.LastOrDefault(line=>line.StartsWith("[ERR]"))??lines.FirstOrDefault()??error.Message;errorText.Text=T("operation_failed")+" "+summary;errorBanner.Visible=true;status.Text=T("operation_failed");Log(Environment.NewLine+"[ERR] "+lastError);tabs.SelectedTab=setupPage;}
    void ImagePhase(string phase)
    {
        if(!busy)return;
        imageProgressPanel.Visible=true;imageActive=true;imageActivity.Animating=true;
        imageProgressText.Text=T("image_"+phase);imagePercent.Text="";
        imageProgress.Style=ProgressBarStyle.Marquee;imageProgress.MarqueeAnimationSpeed=30;
    }
    void FinishImageProgress(string key,bool complete)
    {
        imageActive=false;imageActivity.Animating=false;imageProgress.MarqueeAnimationSpeed=0;imageProgress.Style=ProgressBarStyle.Continuous;
        if(complete)imageProgress.Value=100;
        imageProgressText.Text=T(key);imagePercent.Text=complete?"100 %":"";
    }
    void HandleEvent(JsonElement e)
    {
        switch(e.GetProperty("type").GetString()){
            case "status":var message=e.GetProperty("message").GetString()??"";Log(message);if(busy){progress.Style=ProgressBarStyle.Marquee;progress.MarqueeAnimationSpeed=30;status.Text=speechTotal>0?$"{T("speech_fragments")} {speechIndex} / {speechTotal}: {message}":message;}break;
            case "image_phase":
                var phase=e.GetProperty("phase").GetString()??"preparing";
                if(phase=="failed"){if(imageActive)FinishImageProgress("image_failed",false);}else ImagePhase(phase);
                break;
            case "image_progress":if(busy){
                var step=e.GetProperty("step").GetInt32();var steps=Math.Max(1,e.GetProperty("steps").GetInt32());
                imageProgressPanel.Visible=true;imageActive=true;imageActivity.Animating=true;imageProgress.MarqueeAnimationSpeed=0;imageProgress.Style=ProgressBarStyle.Continuous;imageProgress.Value=Math.Clamp((int)(step*100L/steps),0,100);
                imageProgressText.Text=$"{T("image_sampling")}: {step} / {steps}";imagePercent.Text=$"{imageProgress.Value} %";
                status.Text=imageProgressText.Text;
            }break;
            case "download_progress":if(busy){progress.Style=ProgressBarStyle.Continuous;progress.Value=Math.Clamp((int)(e.GetProperty("bytes").GetInt64()*100/e.GetProperty("total").GetInt64()),0,100);status.Text=$"Tiny-SD: {progress.Value}%";}break;
            case "speech_progress":if(busy){var stage=e.GetProperty("stage").GetString();var part=e.GetProperty("part").GetInt32();var total=Math.Max(1,e.GetProperty("total").GetInt32());speechIndex=part;speechTotal=stage=="complete"?0:total;progress.Style=ProgressBarStyle.Continuous;progress.Value=stage=="complete"?100:Math.Clamp((part-1)*100/total,0,99);status.Text=stage=="normalizing"?T("speech_normalizing"):$"{T("speech_fragments")}: {part} / {total}";}break;
            case "progress":if(busy)status.Text=$"{(speechTotal>0?$"{T("speech_fragments")} {speechIndex} / {speechTotal}":T("generating"))}: {e.GetProperty("tokens")} / {e.GetProperty("limit")} {e.GetProperty("unit")}";break;
            case "tool":
                Log(e.GetRawText());AppendTranscript($"\n[Tool: {e.GetProperty("name")}]\n");
                if(e.GetProperty("name").GetString()=="current_weather"&&e.GetProperty("result").TryGetProperty("online_available",out var onlineAvailable)&&onlineAvailable.ValueKind==JsonValueKind.False){
                    var cache=e.GetProperty("result");AppendTranscript(T("weather_offline")+"\n");if(cache.TryGetProperty("cache_retrieved_at",out var date))AppendTranscript(T("weather_cached_asof")+" "+date.GetString()+"\n");else AppendTranscript(T("weather_no_cache")+"\n");
                }
                if(e.GetProperty("result").TryGetProperty("error",out var toolError))AppendTranscript(T("tool_failed")+" "+toolError.GetString()+"\n");
                break;
            case "image":if(imageProgressPanel.Visible)FinishImageProgress("image_completed",true);lastImage=e.GetProperty("path").GetString();if(lastImage!=null&&File.Exists(lastImage)){using var source=Image.FromFile(lastImage);var copy=new Bitmap(source);preview.Image?.Dispose();preview.Image=copy;results.Panel2Collapsed=false;results.SplitterDistance=Math.Max(100,results.Width*2/3);}break;
        }
    }
    async Task Send()
    {
        if(busy||recording||(string.IsNullOrWhiteSpace(prompt.Text)&&media.Count==0))return;
        if(!Paths.RuntimeReady){if(!await Setup())return;}
        var request=Request.From(ReadSettings());request.history=activeChat.History.ToList();request.task=Value(task);request.input=prompt.Text;request.attachments=media.ToList();if(request.task=="tts")request.output="tts";
        if(string.IsNullOrWhiteSpace(activeChat.Transcript)){activeChat.Title=string.IsNullOrWhiteSpace(request.input)?T("media_chat"):request.input.Replace("\r"," ").Replace("\n"," ").Trim();if(activeChat.Title.Length>48)activeChat.Title=activeChat.Title[..48]+"…";}
        AppendTranscript("\n"+T("you")+": "+request.input+"\n");
        SaveCurrentChat();RefreshChats();
        await Execute(async ct=>{var reply=await worker.SendAsync(request,ct);if(reply==null)return;if(reply.History!=null)activeChat.History=reply.History;AppendTranscript("\nLFM3: "+reply.Text+reply.SourceText+"\n");answer.SelectionStart=answer.TextLength;answer.ScrollToCaret();player?.Stop();player?.Dispose();DeleteTemporary();lastAudio=reply.Audio;lastTemporary=reply.Temporary;if(lastAudio!=null&&autoplay.Checked){player=new SoundPlayer(lastAudio);player.Play();}prompt.Clear();media.Clear();attachments.Items.Clear();SaveCurrentChat();RefreshChats();},T("generating"));
    }
    async Task<bool> Setup()
    {
        if(busy||recording)return false;worker.Stop();tabs.SelectedTab=setupPage;Log("\n=== LFM3 Desk 1.4.0 / Setup ===");
        var reporter=new Progress<string>(SetupLine);var ok=await Execute(ct=>SetupRunner.RunAsync(Value(device),reporter,ct,ReadSettings()),T("setup_running"));
        if(ok&&tabs.SelectedTab==setupPage)tabs.SelectedTab=chatPage;return ok;
    }
    async Task DownloadWikipedia()
    {
        if(busy||recording)return;
        if(!Paths.RuntimeReady){await Setup();return;}
        ReadSettings().Save();tabs.SelectedTab=setupPage;
        var reporter=new Progress<string>(SetupLine);
        var ok=await Execute(ct=>SetupRunner.RunAsync(Value(device),reporter,ct,ReadSettings(),true),T("wiki_download"));
        if(ok){var folder=Path.Combine(Paths.Root,"data","wikipedia");var file=Directory.GetFiles(folder,"wikipedia_de_all_"+Value(wikiFlavour)+"_*.zim").OrderByDescending(p=>p).FirstOrDefault();if(file!=null){wikiPath.Text=file;ReadSettings().Save();}}
    }
    async Task InstallImageGpu()
    {
        if(busy||recording)return;ReadSettings().Save();worker.Stop();tabs.SelectedTab=setupPage;
        var reporter=new Progress<string>(SetupLine);
        var ok=await Execute(ct=>SetupRunner.RunAsync(Value(device),reporter,ct,ReadSettings(),imageGpuOnly:true),T("image_gpu_install"));
        if(ok){imageBackend.SelectedIndex=1;ReadSettings().Save();Log(T("image_gpu_ready"));}
    }
    async Task Download(){if(busy||recording)return;if(!Paths.RuntimeReady){await Setup();return;}await Execute(async ct=>{await worker.SendAsync(new Request{command="download",offline=offlineMode.Checked},ct);},T("checking_models"));}
    Task ClearChat(){if(!busy&&!recording)CreateChat();return Task.CompletedTask;}
    void InitializeChats(){chatSessions.AddRange(chatStore.Load());if(chatSessions.Count==0){activeChat=new ChatSession{Title=T("new_chat")};chatSessions.Add(activeChat);chatStore.Save(activeChat);}RestoreChat(chatSessions[0]);RefreshChats();}
    void AppendTranscript(string text){activeChat.Transcript+=text;RenderTranscript();}
    void RenderTranscript(){answer.Text=hideDestinations.Checked?ChatDisplay.HideDestinations(activeChat.Transcript):activeChat.Transcript;answer.SelectionStart=answer.TextLength;answer.ScrollToCaret();}
    void SaveCurrentChat(){activeChat.Draft=prompt.Text;activeChat.Attachments=media.ToList();activeChat.Image=lastImage;activeChat.Audio=lastTemporary?null:lastAudio;activeChat.Updated=DateTimeOffset.Now;chatStore.Save(activeChat);}
    void RefreshChats(){selectingChat=true;try{chatList.BeginUpdate();chatList.Items.Clear();foreach(var chat in chatSessions.OrderByDescending(c=>c.Updated))chatList.Items.Add(chat);chatList.SelectedItem=activeChat;chatList.EndUpdate();}finally{selectingChat=false;}}
    void CreateChat(){SaveCurrentChat();var chat=new ChatSession{Title=T("new_chat")};chatSessions.Add(chat);RestoreChat(chat);chatStore.Save(chat);RefreshChats();tabs.SelectedTab=chatPage;prompt.Focus();}
    void RestoreChat(ChatSession chat)
    {
        player?.Stop();player?.Dispose();player=null;DeleteTemporary();activeChat=chat;RenderTranscript();prompt.Text=chat.Draft;media.Clear();media.AddRange(chat.Attachments);attachments.Items.Clear();foreach(var item in media)attachments.Items.Add(item.kind+": "+Path.GetFileName(item.path));
        preview.Image?.Dispose();preview.Image=null;results.Panel2Collapsed=true;lastImage=chat.Image;lastAudio=chat.Audio;lastTemporary=false;imageActivity.Animating=false;imageProgressPanel.Visible=false;
        if(lastImage!=null&&File.Exists(lastImage)){using var source=Image.FromFile(lastImage);preview.Image=new Bitmap(source);results.Panel2Collapsed=false;}
        answer.SelectionStart=answer.TextLength;answer.ScrollToCaret();
    }
    void AttachFiles(){using var dialog=new OpenFileDialog{Multiselect=true,Filter="Media|*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.wav;*.mp3;*.flac;*.ogg;*.m4a;*.mp4;*.mkv;*.webm;*.mov|All|*.*"};if(dialog.ShowDialog()!=DialogResult.OK)return;foreach(var file in dialog.FileNames){string ext=Path.GetExtension(file).ToLowerInvariant();string kind=new[]{".png",".jpg",".jpeg",".webp",".bmp"}.Contains(ext)?"image":new[]{".mp4",".mkv",".webm",".mov"}.Contains(ext)?"video":"audio";media.Add(new Attachment(kind,file));attachments.Items.Add(kind+": "+Path.GetFileName(file));}}
    void Record(){try{if(!recording){recorder.Start();recording=true;mic.Text=T("stop_recording");status.Text=T("recording");}else{string file=recorder.Stop();recording=false;media.Add(new Attachment("audio",file));attachments.Items.Add("audio: "+Path.GetFileName(file));mic.Text=T("record");status.Text=T("ready");}UpdateAvailability();}catch(Exception e){recording=false;recorder.Dispose();mic.Text=T("record");UpdateAvailability();ReportError(e);}}
    void PlayLast(){try{if(lastAudio!=null&&File.Exists(lastAudio)){player?.Dispose();player=new SoundPlayer(lastAudio);player.Play();}}catch(Exception e){ReportError(e);}}
    void Export(){try{using var dialog=new SaveFileDialog{Filter="Text|*.txt",FileName="chat.txt"};if(dialog.ShowDialog()==DialogResult.OK)File.WriteAllText(dialog.FileName,answer.Text);}catch(Exception e){ReportError(e);}}
    void OpenOutput(){Directory.CreateDirectory(Path.Combine(Paths.Root,"output"));OpenFile(Path.Combine(Paths.Root,"output"));}
    void OpenSetupLog(){var file=Path.Combine(Paths.Root,"output","logs","setup.log");if(File.Exists(file))OpenFile(file);else tabs.SelectedTab=setupPage;}
    void OpenFile(string path){try{Process.Start(new ProcessStartInfo(path){UseShellExecute=true});}catch(Exception e){ReportError(e);}}
    void DeleteTemporary(){if(lastTemporary&&lastAudio!=null)try{File.Delete(lastAudio);}catch{}lastAudio=null;}
}
