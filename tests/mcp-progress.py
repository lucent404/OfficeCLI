"""Verify progress frames and subsequent requests over the real stdio transport."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

binary = str(Path(sys.argv[1]).resolve())
env = {**os.environ, 'OFFICECLI_SKIP_UPDATE': '1', 'OFFICECLI_NO_AUTO_RESIDENT': '1'}
with tempfile.TemporaryDirectory(prefix='officecli-progress-') as temp:
    book = str(Path(temp) / 'book.xlsx')
    source = Path(temp) / 'batch.json'
    source.write_text(json.dumps([{'command': 'get', 'path': '/'}] * 3))
    requests = []
    for index, (command, token) in enumerate([
        (['create', book], None),
        (['batch', book, '--input', str(source)], 'batch-1'),
        (['batch', book, '--input', str(source)], 0),
        (['batch', str(Path(temp) / 'missing.xlsx'), '--input', str(source)], 'failed'),
        (['help', 'xlsx'], None),
    ], 1):
        params = {'name': 'officecli', 'arguments': {'command': command}}
        if token is not None:
            params['_meta'] = {'progressToken': token}
        requests.append({'jsonrpc': '2.0', 'id': index, 'method': 'tools/call', 'params': params})
    run = subprocess.run([binary, 'mcp'], input='\n'.join(map(json.dumps, requests))+'\n',
                         capture_output=True, text=True, env=env, timeout=45)
    assert run.returncode == 0, run.stderr
    frames = [json.loads(line) for line in run.stdout.splitlines()]
    replies = [f for f in frames if 'id' in f]
    assert [f['id'] for f in replies] == [1, 2, 3, 4, 5], frames
    for reply in replies:
        assert reply['result'].get('isError', False) == (reply['id'] == 4), reply
    for token, count, response_id in [('batch-1', 5, 2), (0, 5, 3), ('failed', 2, 4)]:
        progress = [f for f in frames if f.get('method') == 'notifications/progress'
                    and f['params']['progressToken'] == token]
        assert len(progress) == count, progress
        assert [p['params']['progress'] for p in progress] == list(range(count)), progress
        assert all(p['params']['message'] for p in progress)
        assert frames.index(progress[-1]) < next(i for i, f in enumerate(frames) if f.get('id') == response_id)
    assert len(frames) == 17, frames  # no notifications without a token or after a request ends
print('PASS: batch progress, string/zero tokens, error completion, no-token calls, subsequent requests')
