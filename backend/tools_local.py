"""Bounded offline tools. No shell, network, or arbitrary file access."""
import ast
import datetime
import json
import math
import operator
import re
from pathlib import Path

CALL = re.compile(r'<tool_call>\s*<function=([^>\n]+)>(.*?)</function>\s*</tool_call>', re.S)
PARAM = re.compile(r'<parameter=([^>\n]+)>\n?(.*?)\n?</parameter>', re.S)

def parse_calls(text):
    calls = []
    for name, body in CALL.findall(text):
        args = {}
        for k, value in PARAM.findall(body):
            try: args[k] = json.loads(value)
            except json.JSONDecodeError: args[k] = value.strip()
        calls.append({'type':'function','function':{'name':name.strip(),'arguments':args}})
    return calls

def schema(name, description, properties, required):
    return {'type':'function','function':{'name':name,'description':description,'parameters':{'type':'object','properties':properties,'required':required}}}

TOOLS = [
    schema('generate_image','Generate an image using the offline Tiny-SD model when the user requests a picture. Translate the visual prompt to English. Output is a saved PNG. Width/height 256,384,512; default 512; steps 1..50, default20; guidance1..15,default7; seed=-1 random.',{'prompt':{'type':'string','description':'Detailed English image prompt'},'negative_prompt':{'type':'string'},'width':{'type':'integer','enum':[256,384,512]},'height':{'type':'integer','enum':[256,384,512]},'steps':{'type':'integer'},'guidance':{'type':'number'},'seed':{'type':'integer'}},['prompt']),
    schema('convert_units','Convert temperatures C/F/K, speed km/h or m/s, length m/km/cm/mm, or mass kg/g. Offline deterministic conversion. Never invent conversions between different physical quantities.',{'value':{'type':'number'},'from_unit':{'type':'string'},'to_unit':{'type':'string'}},['value','from_unit','to_unit']),
    schema('current_time','Get the current local date and time, including UTC offset.',{},[]),
    schema('calculate','Evaluate arithmetic. Operators + - * / // % **; functions sqrt, sin, cos, log, abs, round. Constants pi, e.',{'expression':{'type':'string'}},['expression']),
    schema('list_notes','List UTF-8 text files in the application workspace.',{},[]),
    schema('read_note','Read a UTF-8 text file from the application workspace.',{'name':{'type':'string'}},['name']),
    schema('save_note','Save a NEW UTF-8 text note in the application workspace. Cannot overwrite.',{'name':{'type':'string'},'text':{'type':'string'}},['name','text'])
]

def calculate(expression):
    if len(expression)>256: raise ValueError('Expression too long')
    tree = ast.parse(expression, mode='eval')
    if len(list(ast.walk(tree)))>80: raise ValueError('Expression too complex')
    ops={ast.Add:operator.add, ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,ast.Pow:operator.pow}
    funcs={'sqrt':math.sqrt,'sin':math.sin,'cos':math.cos,'log':math.log,'abs':abs,'round':round}
    def run(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float): value=n.value
        elif isinstance(n,ast.Name) and n.id in ('pi','e'): value=getattr(math,n.id)
        elif isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.USub,ast.UAdd)): value=(-1 if isinstance(n.op,ast.USub) else 1)*run(n.operand)
        elif isinstance(n,ast.BinOp) and type(n.op) in ops:
            a,b=run(n.left),run(n.right)
            if isinstance(n.op,ast.Pow) and (abs(b)>100 or abs(a)>1e10): raise ValueError('Exponent limit')
            value=ops[type(n.op)](a,b)
        elif isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in funcs and not n.keywords and len(n.args)<=2:
            value=funcs[n.func.id](*[run(a) for a in n.args])
        else: raise ValueError('Unsupported expression')
        if isinstance(value,complex) or not math.isfinite(value) or abs(value)>1e100: raise ValueError('Numeric limit')
        return value
    return run(tree.body)

def convert_units(value,from_unit,to_unit):
    value=float(value)
    if not math.isfinite(value):raise ValueError('Finite value required')
    aliases={'°c':'c','celsius':'c','°f':'f','fahrenheit':'f','kelvin':'k','kph':'km/h'}
    a=aliases.get(from_unit.lower(),from_unit.lower());b=aliases.get(to_unit.lower(),to_unit.lower())
    temperatures={'c','f','k'}
    if a in temperatures and b in temperatures:
        k=value+273.15 if a=='c' else (value-32)*5/9+273.15 if a=='f' else value
        if k<0:raise ValueError('Temperature below absolute zero')
        result=k-273.15 if b=='c' else (k-273.15)*9/5+32 if b=='f' else k
    else:
        groups=[{'m':1,'km':1000,'cm':.01,'mm':.001},{'kg':1,'g':.001},{'m/s':1,'km/h':1/3.6}]
        group=next((g for g in groups if a in g and b in g),None)
        if group is None:raise ValueError('Unsupported or incompatible units')
        result=value*group[a]/group[b]
    if not math.isfinite(result):raise ValueError('Conversion overflow')
    return {'value':round(result,10),'unit':to_unit,'from_value':value,'from_unit':from_unit}

def dispatch(name, args, workspace):
    workspace=Path(workspace).resolve(); workspace.mkdir(parents=True,exist_ok=True)
    if name=='convert_units':return convert_units(**args)
    if name=='current_time': return {'time':datetime.datetime.now().astimezone().isoformat()}
    if name=='calculate': return {'result':calculate(**args)}
    if name=='list_notes': return {'files':sorted(p.name for p in workspace.glob('*.txt') if p.is_file() and not p.is_symlink())[:200]}
    if name in ('read_note','save_note'):
        filename=args.get('name','')
        if not re.fullmatch(r'[\w -]{1,80}\.txt',filename): raise ValueError('Use a simple filename ending in .txt')
        if filename.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}:raise ValueError('Reserved filename')
        path=workspace/filename
        if path.is_symlink() or path.resolve().parent!=workspace: raise ValueError('Path outside workspace')
        if name=='read_note':
            if path.stat().st_size>65536: raise ValueError('Note too large')
            return {'text':path.read_text(encoding='utf-8')}
        data=args['text']
        if len(data.encode('utf-8'))>65536: raise ValueError('Note too large')
        with path.open('x',encoding='utf-8') as f: f.write(data)
        return {'saved':filename}
    raise ValueError('Unknown tool: '+name)
