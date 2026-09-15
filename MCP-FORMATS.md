# MCP format policy (TeaBuddy fork)

Based on upstream v1.0.148. Apache-2.0 notices remain unchanged.

Set `OFFICECLI_MCP_ALLOWED_FORMATS=docx,xlsx` in the environment of `officecli mcp`
to expose only Word and Excel. Omitting it preserves all upstream formats.
Invalid or empty values fail closed; supported values are a comma-separated
subset of `docx,xlsx,pptx` (aliases word/excel/ppt/powerpoint are accepted).

The policy changes tool metadata, generic help, skill discovery and command
execution. Disabled-format commands are rejected before a document is opened
or a screenshot is rendered, including string and argv-array forms. Guides for
disabled formats cannot be loaded. Restricted calls use `<verb> <file>` ordering;
response files and process/plugin management commands are not exposed. `help
<enabled-format> ...` retains the upstream schema reference. Generic command
help directs callers to enabled guides rather than returning all-format examples.

This is an MCP capability restriction, not an operating-system sandbox. The
standalone executable retains all formats for application-managed preview and
other internal use. A separate shell tool can still invoke that executable.
Clients must also remove all-format OfficeCLI instructions from their own system
prompts. Restart the MCP process after changing the setting. Restricted MCP mode also
skips the periodic upstream update check so it cannot replace the fork binary.

Validation: `dotnet publish src/officecli/officecli.csproj -c Release -r linux-x64
-o publish`, then `python3 tests/mcp-formats.py publish/officecli`. GitHub workflow
`MCP format policy` performs the same black-box tests on every fork branch push.
