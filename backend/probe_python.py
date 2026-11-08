"""File-based interpreter probe: no Python -c quoting across PowerShell 5.1."""
import json
import struct
import sys

print(json.dumps({
    'version': str(sys.version_info[0]) + '.' + str(sys.version_info[1]),
    'executable': sys.executable,
    'bits': struct.calcsize('P') * 8,
    'is_venv': sys.prefix != sys.base_prefix,
    'prefix': sys.prefix,
}))
