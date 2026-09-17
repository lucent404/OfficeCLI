namespace OfficeCli.Core;

/// <summary>Request-scoped progress; ordinary CLI and resident calls have no sink.</summary>
internal static class CommandProgress
{
    internal static readonly AsyncLocal<Action<string>?> Sink = new();
    internal static void Report(string message) => Sink.Value?.Invoke(message);
}
