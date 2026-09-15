"""Black-box regression test against the compiled stdio MCP, no third-party packages."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

binary = str(Path(sys.argv[1]).resolve())
original_hash = hashlib.sha256(Path(binary).read_bytes()).hexdigest()


def session(commands, setting):
    env = {**os.environ, "OFFICECLI_SKIP_UPDATE": "1", "OFFICECLI_NO_AUTO_RESIDENT": "1"}
    if setting is None:
        env.pop("OFFICECLI_MCP_ALLOWED_FORMATS", None)
    else:
        env["OFFICECLI_MCP_ALLOWED_FORMATS"] = setting
    requests = [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}]
    requests += [{"jsonrpc": "2.0", "id": i + 2, "method": "tools/call", "params": {"name": "officecli", "arguments": {"command": command}}} for i, command in enumerate(commands)]
    result = subprocess.run([binary, "mcp"], input="\n".join(map(json.dumps, requests))+"\n", text=True, capture_output=True, env=env, timeout=90)
    assert result.returncode == 0, result.stderr
    replies = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    assert all("result" in reply for reply in replies), {"replies": replies, "stderr": result.stderr}
    return [r["result"] for r in replies]


with tempfile.TemporaryDirectory(prefix="mcp formats ") as temp:
    original_cwd = os.getcwd()
    try:
        os.chdir(temp)
        commands = ["help", "help all --json", "skills list", "help docx", "help xlsx", "load_skill word", "load_skill excel",
                    "help pptx", "help powerpoint", "load_skill pptx", "load_skill morph-ppt", "load_skill pitch-deck",
                    'create "blocked deck.pptx"', ["officecli", "create", "BLOCKED.PPTX"], "view deck.pptx screenshot", "batch deck.pptx --commands []",
                    "merge report.docx output.pptx", "@unchecked.rsp", "plugins", "__resident-serve__ deck.pptx",
                    ["create", "report.docx"], ["create", "book.xlsx"], ["view", "report.docx", "text"], ["view", "book.xlsx", "text"]]
        replies = session(commands, "docx,xlsx")
        definition = json.dumps(replies[0]).lower()
        assert not any(word in definition for word in ["pptx", "powerpoint", "slide", "morph-ppt", "pitch-deck"]), definition
        for i in range(7):
            assert not replies[i+1].get("isError", False), (commands[i], replies[i+1])
        for i in range(3):
            text = json.dumps(replies[i+1]).lower()
            assert not any(word in text for word in ["pptx", "powerpoint", "morph-ppt", "pitch-deck"]), text
        for i in range(7, 20):
            assert replies[i+1].get("isError"), (commands[i], replies[i+1])
        for i in range(20, len(commands)):
            assert not replies[i+1].get("isError", False), (commands[i], replies[i+1])
        assert not Path("blocked deck.pptx").exists()
        assert not Path("BLOCKED.PPTX").exists()
        assert Path("report.docx").exists() and Path("book.xlsx").exists()
        # Default behavior, including the standalone CLI, stays compatible.
        default = session(["create default.pptx"], None)
        assert "pptx" in json.dumps(default[0])
        assert not default[1].get("isError", False) and Path("default.pptx").exists()
        env = {**os.environ, "OFFICECLI_MCP_ALLOWED_FORMATS": "docx,xlsx", "OFFICECLI_SKIP_UPDATE": "1", "OFFICECLI_NO_AUTO_RESIDENT": "1"}
        cli = subprocess.run([binary, "create", "internal.pptx"], env=env, capture_output=True, timeout=30)
        assert cli.returncode == 0 and Path("internal.pptx").exists(), cli.stderr
    finally:
        os.chdir(original_cwd)

assert hashlib.sha256(Path(binary).read_bytes()).hexdigest() == original_hash, "Tests must not update the pinned binary"
print("PASS: restricted discovery, help, skills, execution, Word/Excel, and unrestricted CLI")
