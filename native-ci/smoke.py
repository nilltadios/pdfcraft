#!/usr/bin/env python3
"""Native runtime compatibility checks for a single published Craft binary."""
import json
import os
from pathlib import Path
import subprocess

app = os.environ['APP']
qa = Path('qa').resolve()
qa.mkdir(exist_ok=True)
def cli(*args):
    cmd = ['flatpak', 'build', '--runtime', f'--bind-mount=/qa={qa}', 'build', f'/app/bin/{app}-cli', *args]
    print('$', *cmd, flush=True)
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
    print(p.stdout, flush=True)
    p.check_returncode()
    return p.stdout

cli('--version')
if app == 'gridcraft':
    assert cli('eval', '=SUM(1,2,3)').strip() == '6'
    cli('run', '--sample', 'sales', '--cmd', 'cell.set={"cell":"A1","input":"Runtime compatibility"}', '--out', '/qa/book.xlsx')
    cli('info', '/qa/book.xlsx', '--json')
    assert 'Runtime compatibility' in cli('cat', '/qa/book.xlsx', '--range', 'A1:A1')
    cli('convert', '/qa/book.xlsx', '/qa/book.csv')
    cli('convert', '/qa/book.xlsx', '/qa/book.pdf')
elif app == 'wordcraft':
    (qa / 'input.txt').write_text('Runtime compatibility\nThe quick brown fox jumps over 123 lazy dogs.\n')
    cli('convert', '/qa/input.txt', '/qa/document.docx')
    cli('info', '/qa/document.docx')
    assert 'Runtime compatibility' in cli('text', '/qa/document.docx')
    cli('convert', '/qa/document.docx', '/qa/document.pdf')
    cli('render', '/qa/document.docx', '/qa/document.png', '--scale', '1')
elif app == 'deckcraft':
    cli('run', '--sample', '--save', '/qa/deck.deckcraft')
    cli('convert', '/qa/deck.deckcraft', '/qa/deck.pptx')
    cli('info', '/qa/deck.pptx')
    cli('convert', '/qa/deck.pptx', '/qa/deck-roundtrip.deckcraft')
    cli('convert', '/qa/deck.pptx', '/qa/deck.pdf')
    cli('render', '/qa/deck.pptx', '--scale', '1', '/qa/deck.png')
elif app == 'pdfcraft':
    # Minimal contributor-original vector PDF, with no external asset or font.
    stream = b'0.2 0.4 0.8 rg 20 20 80 80 re f\n'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << >> /Contents 4 0 R >>',
               f'<< /Length {len(stream)} >>\nstream\n'.encode() + stream + b'endstream']
    data = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data += f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n'
    start = len(data)
    data += b'xref\n0 5\n0000000000 65535 f \n'
    for offset in offsets[1:]:
        data += f'{offset:010d} 00000 n \n'.encode()
    data += f'trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode()
    (qa / 'input.pdf').write_bytes(data)
    cli('info', '/qa/input.pdf')
    cli('edit', '/qa/input.pdf', '--out', '/qa/edited.pdf', '--rotate', '1:90', '--title', 'Flatpak compatibility')
    cli('info', '/qa/edited.pdf')
    cli('render', '/qa/edited.pdf', '--page', '1', '--dpi', '72', '--out', '/qa/page.png')
    cli('check', '/qa/edited.pdf', '--dpi', '36', '--json', '/qa/check.json')
else:
    raise ValueError(app)
print(app, 'PASS: native release binary under Platform 26.08')
