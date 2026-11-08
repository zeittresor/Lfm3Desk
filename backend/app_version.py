from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
try:VERSION=(ROOT/'version.txt').read_text(encoding='utf-8').strip()
except OSError:VERSION='1.5.1'
