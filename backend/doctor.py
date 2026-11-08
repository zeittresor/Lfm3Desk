import os
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
if sys.prefix == sys.base_prefix or Path(sys.prefix).resolve() != (root/'.venv').resolve():
    raise SystemExit('Run this check using this application\'s .venv/Scripts/python.exe. Global Python packages are not used.')
handle=None
if os.name=='nt': handle=os.add_dll_directory(str(root/'tools'/'ffmpeg'/'bin'))
import torch
import torchvision
import torchcodec
from transformers import AutoModelForMultimodalLM, AutoProcessor
from libzim.reader import Archive
from mcp.server.fastmcp import FastMCP
from ddgs import DDGS
from secure_http import tls_context
context=tls_context()
print('HTTPS certificate and hostname verification enabled; native Windows trust + certifi')
print('ZIM / MCP / web client imports OK (no network connection started)')
print('Python / PyTorch / Transformers / TorchCodec imports OK')
print('PyTorch:',torch.__version__,'CUDA:',torch.cuda.is_available())
print('Shared FFmpeg directory:',root/'tools'/'ffmpeg'/'bin')
