// Copyright 2026 OfficeCLI contributors
// SPDX-License-Identifier: Apache-2.0

namespace OfficeCli;

/// <summary>MCP-only format policy. The standalone CLI and preview handlers are unchanged.</summary>
internal sealed class McpFormatPolicy
{
    private readonly HashSet<string> allowed;
    private static readonly string[] Formats = ["docx", "xlsx", "pptx"];
    private static readonly Dictionary<string, string> Skills = new(StringComparer.OrdinalIgnoreCase)
    {
        ["word"] = "docx", ["word-form"] = "docx", ["academic-paper"] = "docx",
        ["excel"] = "xlsx", ["data-dashboard"] = "xlsx", ["financial-model"] = "xlsx",
        ["pptx"] = "pptx", ["morph-ppt"] = "pptx", ["morph-ppt-3d"] = "pptx", ["pitch-deck"] = "pptx",
    };
    private static readonly HashSet<string> FileCommands = new(StringComparer.Ordinal)
    {
        "create", "view", "get", "query", "set", "add", "remove", "move", "swap", "validate",
        "batch", "raw", "dump", "import", "merge", "open", "close", "save", "mark", "unmark", "goto",
    };

    public McpFormatPolicy(string? setting)
    {
        allowed = setting == null ? new(Formats) : new(setting.Split(',').Select(s => Normalize(s.Trim())));
        if (allowed.Count == 0 || allowed.Any(f => !Formats.Contains(f)))
            throw new ArgumentException("OFFICECLI_MCP_ALLOWED_FORMATS must be a nonempty comma-separated subset of docx,xlsx,pptx.");
    }

    public bool Restricted => allowed.Count != Formats.Length;
    public string FormatList => string.Join(", ", Formats.Where(allowed.Contains));
    public string SkillList => string.Join(", ", Skills.Where(pair => allowed.Contains(pair.Value)).Select(pair => pair.Key));
    public string Description => $"Create, inspect and edit documents in the enabled formats: {FormatList}. "
        + "Pass a command string or argv array. Use help first, then load_skill for the selected file type. "
        + $"Available skills: {SkillList}. Use validate and view issues before delivery; use view screenshot to inspect layout.";
    public string CommandDescription => "Command string or argv array. Syntax: <verb> <file> [arguments]. "
        + $"Enabled file formats: {FormatList}. Use help <format> <element> for schemas and load_skill for guides.";
    public string Help => $"Enabled formats: {FormatList}\nCommands: {string.Join(", ", FileCommands)}\n"
        + "Syntax: <verb> <file> [arguments]. The file must immediately follow the verb.\n"
        + "help <format> [verb] [element] — format-specific schemas.\n"
        + $"load_skill <name> [--path <relative-file>] — available guides: {SkillList}.\n"
        + "Use load_skill for examples, validate <file> and view <file> issues to check the document, "
        + "and view <file> screenshot for visual review. Append --json for structured results.";
    public string SkillCatalog => $"Available guides: {SkillList}.\nUse load_skill <name> or load_skill <name> --path <relative-file>.";

    private static string Normalize(string name) => name.ToLowerInvariant() switch
    {
        "word" => "docx", "excel" => "xlsx", "ppt" or "powerpoint" => "pptx", var value => value,
    };

    public void ValidateSkill(string name)
    {
        if (!Skills.TryGetValue(name, out var format) || !allowed.Contains(format))
            throw new ArgumentException($"This guide is not enabled. Available guides: {SkillList}.");
    }

    /// <returns>A scoped help response, or null to continue to the CLI dispatcher.</returns>
    public string? Validate(string[] argv)
    {
        if (!Restricted) return null;
        // System.CommandLine can expand response files. Do not let them replace
        // the validated argv with an unchecked command after this boundary.
        if (argv.Any(a => a.StartsWith('@')))
            throw new ArgumentException("Response files are not supported by the restricted MCP command interface.");
        if (argv.Length == 0) return Help;
        var verb = argv[0];
        if (verb is "help" or "--help" or "-h" or "/?")
        {
            if (argv.Length < 2 || argv[1] == "all" || FileCommands.Contains(argv[1])) return Help;
            if (!allowed.Contains(Normalize(argv[1])))
                throw new ArgumentException($"This help format is not enabled. Enabled formats: {FormatList}.");
            if (argv.Skip(2).Any(a => a is "--help" or "-h" or "/?")) return Help;
            return null;
        }
        if (verb is "load_skill" or "skill" or "skills") return null; // validated before loading the guide
        if (!FileCommands.Contains(verb))
            throw new ArgumentException($"This command is not enabled. Run help for available commands. Enabled formats: {FormatList}.");
        if (argv.Any(a => a is "--help" or "-h" or "/?")) return Help;
        if (argv.Length < 2) throw new ArgumentException("Provide the document path immediately after the command.");
        ValidateFile(argv[1]);
        if (verb == "merge")
        {
            if (argv.Length < 3) throw new ArgumentException("Provide the merge output path.");
            ValidateFile(argv[2]);
        }
        return null;
    }

    private void ValidateFile(string path)
    {
        var extension = Path.GetExtension(path).TrimStart('.').ToLowerInvariant();
        if (!allowed.Contains(extension))
            throw new ArgumentException($"This document format is not enabled. Enabled formats: {FormatList}.");
    }
}
