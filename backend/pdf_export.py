"""Offline chat PDF export. Unicode system fonts, paginated text/code and images."""
import argparse
import datetime
import html
import json
import os
from pathlib import Path
import re
import sys
import textwrap
import uuid
from app_version import VERSION

ROOT=Path(__file__).resolve().parents[1]

def export(payload,destination):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,XPreformatted
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    candidates=[Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts',Path('/usr/share/fonts/truetype/dejavu')]
    for folder in candidates:
        regular=next((folder/n for n in ('arial.ttf','DejaVuSans.ttf') if (folder/n).is_file()),None)
        bold=next((folder/n for n in ('arialbd.ttf','DejaVuSans-Bold.ttf') if (folder/n).is_file()),None)
        mono=next((folder/n for n in ('consola.ttf','DejaVuSansMono.ttf') if (folder/n).is_file()),None)
        if regular and bold and mono:break
    else:raise FileNotFoundError('Unicode PDF fonts not found (Windows Arial/Consolas).')
    for name,file in [('Chat',regular),('ChatBold',bold),('ChatMono',mono)]:pdfmetrics.registerFont(TTFont(name,str(file)))
    pdfmetrics.registerFontFamily('Chat',normal='Chat',bold='ChatBold',italic='Chat',boldItalic='ChatBold')
    body=ParagraphStyle('body',fontName='Chat',fontSize=10,leading=14,spaceAfter=5,textColor=colors.HexColor('#202b3c'),splitLongWords=True)
    heading=ParagraphStyle('heading',parent=body,fontName='ChatBold',fontSize=18,leading=23,spaceAfter=10)
    image_heading=ParagraphStyle('imageheading',parent=body,fontName='ChatBold',spaceBefore=12,keepWithNext=True)
    meta=ParagraphStyle('meta',parent=body,fontSize=8,leading=12,textColor=colors.HexColor('#64748b'),spaceAfter=12)
    code_style=ParagraphStyle('code',parent=body,fontName='ChatMono',fontSize=8,leading=11,backColor=colors.HexColor('#f1f4f8'),borderPadding=6,spaceBefore=6,spaceAfter=10)
    role=ParagraphStyle('role',parent=body,fontName='ChatBold',textColor=colors.HexColor('#244c74'),spaceBefore=9)
    tool=ParagraphStyle('tool',parent=body,fontSize=9,textColor=colors.HexColor('#805600'))
    title=str(payload.get('title') or 'Chat')[:300]
    story=[Paragraph(html.escape(title),heading),Paragraph(html.escape(f'LFM3 Desk {VERSION} · '+datetime.datetime.now().astimezone().strftime('%d.%m.%Y %H:%M %Z')),meta)]
    lines=str(payload.get('text','')).splitlines();in_code=False;code=[]
    def flush():
        if code:
            wrapped=[]
            for line in code:wrapped.extend(textwrap.wrap(line.expandtabs(4),width=88,replace_whitespace=False,drop_whitespace=False) or [''])
            story.append(XPreformatted(html.escape('\n'.join(wrapped)),code_style));code.clear()
    for line in lines:
        if re.match(r'^\s*(?:`{3,}|~{3,})',line):
            if in_code:flush()
            in_code=not in_code;continue
        if in_code:code.append(line);continue
        if not line.strip():story.append(Spacer(1,6));continue
        style=tool if line.startswith('Tool: ') else role if re.match(r'^(?:Du|You|'+re.escape(str(payload.get('assistant_name','LFM3')))+r'):',line) else body
        story.append(Paragraph(html.escape(line),style))
    flush()
    images=list(dict.fromkeys(str(p) for p in payload.get('images',[]) if p))
    if images:story.extend([Spacer(1,12),Paragraph('Bilder / Images',image_heading)])
    for item in images:
        path=Path(item)
        if not path.is_file():story.append(Paragraph('Bild nicht mehr vorhanden / Image unavailable.',meta));continue
        try:
            img=Image(str(path));scale=min(1,465/img.imageWidth,320/img.imageHeight);img.drawWidth=img.imageWidth*scale;img.drawHeight=img.imageHeight*scale;img.hAlign='LEFT';story.extend([img,Spacer(1,12)])
        except Exception:story.append(Paragraph('Bild konnte nicht eingebettet werden / Image could not be embedded.',meta))
    output=Path(destination);output.parent.mkdir(parents=True,exist_ok=True);temporary=output.with_name(output.name+'.'+uuid.uuid4().hex+'.part')
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Chat',8);canvas.setFillColor(colors.HexColor('#64748b'));canvas.drawString(44,24,'LFM3 Desk '+VERSION);canvas.drawRightString(A4[0]-44,24,str(doc.page));canvas.restoreState()
    try:
        document=SimpleDocTemplate(str(temporary),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=40,bottomMargin=42,title=title,author=str(payload.get('assistant_name','LFM3')))
        document.build(story,onFirstPage=footer,onLaterPages=footer);os.replace(temporary,output)
    finally:
        if temporary.exists():temporary.unlink()
    return str(output)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    if sys.prefix==sys.base_prefix or Path(sys.prefix).resolve()!=(ROOT/'.venv').resolve():raise RuntimeError('Use this app\'s own .venv interpreter.')
    print(f'LFM3 Desk {VERSION} | PDF export',flush=True)
    print(export(json.loads(Path(args.input).read_text(encoding='utf-8-sig')),args.output),flush=True)

if __name__=='__main__':
    try:main()
    except Exception as error:print('[ERR] '+str(error),file=sys.stderr);sys.exit(1)
