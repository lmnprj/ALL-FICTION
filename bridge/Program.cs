using System.Diagnostics;
using System.Net;
using System.Text;
using System.Text.Json;

static void Log(string message) {
    try {
        string directory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ALL-FICTION", "MuMuBridge");
        Directory.CreateDirectory(directory);
        File.AppendAllText(Path.Combine(directory, "bridge.log"), $"{DateTime.Now:s} {message}\n");
    } catch { }
}

static async Task<(int ExitCode, string Output)> RunAdb(string adb, params string[] args) {
    var info = new ProcessStartInfo(adb) {
        UseShellExecute = false, CreateNoWindow = true,
        RedirectStandardOutput = true, RedirectStandardError = true
    };
    foreach (string arg in args) info.ArgumentList.Add(arg);
    using var process = Process.Start(info) ?? throw new IOException("Could not start adb");
    var stdout = process.StandardOutput.ReadToEndAsync();
    var stderr = process.StandardError.ReadToEndAsync();
    using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(8));
    try { await process.WaitForExitAsync(timeout.Token); }
    catch (OperationCanceledException) { try { process.Kill(); } catch { } throw new IOException("adb timed out"); }
    return (process.ExitCode, (await stdout) + (await stderr));
}

const string token = "REPLACE_WITH_SHARED_BRIDGE_TOKEN";
string root = Path.GetFullPath(File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "mumu-root.txt")).Trim(), AppContext.BaseDirectory);
string adb = Path.Combine(root, "nx_main", "adb.exe");
string cli = Path.Combine(root, "nx_main", "mumu-cli.exe");
Log("bridge started");
using var mutex = new Mutex(true, "Local\\AllFictionWindowsLinkBridge", out bool first);
if (!first) return;

if (args.Contains("--device-lifetime")) {
    _ = Task.Run(async () => {
        while (true) {
            await Task.Delay(5000);
            var processes = Process.GetProcessesByName("MuMuNxDevice");
            bool running = false;
            foreach (var process in processes) {
                try {
                    var path = process.MainModule?.FileName;
                    if (path != null && Path.GetFullPath(path).StartsWith(root.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) running = true;
                } catch { }
                finally { process.Dispose(); }
            }
            if (!running) Environment.Exit(0);
        }
    });
}

using var listener = new HttpListener();
listener.Prefixes.Add("http://127.0.0.1:38471/");
listener.Start();

_ = Task.Run(async () => {
    var connected = new Dictionary<string, DateTime>();
    var processIds = new Dictionary<string, int>();
    var initialized = new HashSet<int>();
    var startedAt = DateTime.UtcNow;
    while (true) {
        bool ready = false;
        try {
            var info = new ProcessStartInfo(cli) {
                UseShellExecute = false, CreateNoWindow = true,
                RedirectStandardOutput = true, RedirectStandardError = true
            };
            foreach (string arg in new[] { "info", "-v", "all" }) info.ArgumentList.Add(arg);
            using var process = Process.Start(info)!;
            string output = await process.StandardOutput.ReadToEndAsync();
            await process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();
            using var document = JsonDocument.Parse(output);
            foreach (var instance in document.RootElement.EnumerateObject()) {
                var item = instance.Value;
                if (!item.TryGetProperty("is_android_started", out var started) || !started.GetBoolean() ||
                    !item.TryGetProperty("adb_host_ip", out var host) || host.GetString() != "127.0.0.1" ||
                    !item.TryGetProperty("adb_port", out var port) || !port.TryGetInt32(out int number) || number < 1 || number > 65535) continue;
                string serial = $"127.0.0.1:{number}";
                ready = true;
                if (item.TryGetProperty("pid", out var pidValue) && pidValue.TryGetInt32(out int pid)) {
                    if (processIds.TryGetValue(serial, out int previousPid) && previousPid != pid) connected.Remove(serial);
                    processIds[serial] = pid;
                    if (!initialized.Contains(pid) && item.TryGetProperty("launch_time", out var ageValue) && ageValue.TryGetInt64(out long age) && age >= 0 && age < 60000) {
                        var boot = await RunAdb(adb, "-s", serial, "shell", "getprop", "sys.boot_completed");
                        if (boot.ExitCode == 0 && boot.Output.Trim() == "1") {
                            initialized.Add(pid);
                            var activity = await RunAdb(adb, "-s", serial, "shell", "dumpsys", "activity", "activities");
                            bool home = activity.Output.Split('\n').Any(line => line.Contains("topResumedActivity") && line.Contains("local.violethome/"));
                            if (home) {
                                var launch = await RunAdb(adb, "-s", serial, "shell", "am", "start", "-a", "android.settings.SETTINGS");
                                if (launch.ExitCode == 0) {
                                    await Task.Delay(800);
                                    var top = await RunAdb(adb, "-s", serial, "shell", "dumpsys", "activity", "activities");
                                    if (top.Output.Split('\n').Any(line => line.Contains("topResumedActivity") && line.Contains("com.android.settings/"))) {
                                        await RunAdb(adb, "-s", serial, "shell", "am", "force-stop", "com.android.settings");
                                        Log("mouse input initialized");
                                    } else Log("mouse initialization left activity unchanged");
                                }
                            } else Log("mouse initialization skipped: launcher not in foreground");
                        }
                    }
                }
                if (connected.TryGetValue(serial, out var lastSetup) && DateTime.UtcNow - lastSetup < TimeSpan.FromMinutes(2)) continue;
                var connect = new ProcessStartInfo(adb) { UseShellExecute = false, CreateNoWindow = true };
                connect.ArgumentList.Add("connect"); connect.ArgumentList.Add(serial);
                using (var connection = Process.Start(connect)) if (connection != null) await connection.WaitForExitAsync();
                var reverse = new ProcessStartInfo(adb) { UseShellExecute = false, CreateNoWindow = true };
                foreach (string arg in new[] { "-s", serial, "reverse", "tcp:38471", "tcp:38471" })
                    reverse.ArgumentList.Add(arg);
                using var child = Process.Start(reverse);
                if (child != null) {
                    await child.WaitForExitAsync();
                    if (child.ExitCode == 0) { connected[serial] = DateTime.UtcNow; Log("ADB reverse ready " + serial); }
                    else Log("ADB reverse failed " + serial + " exit " + child.ExitCode);
                }
            }
        } catch (Exception ex) { Log("ADB setup error: " + ex.Message); }
        await Task.Delay(ready ? 10000 : (DateTime.UtcNow - startedAt < TimeSpan.FromMinutes(1) ? 3000 : 15000));
    }
});

while (true) {
    var ctx = await listener.GetContextAsync();
    _ = Task.Run(async () => {
        try {
            var request = ctx.Request;
            if (request.HttpMethod != "POST" || request.Url?.AbsolutePath != "/open" ||
                request.Headers["Origin"] != null || request.Headers["X-AF-Token"] != token ||
                request.ContentLength64 < 1 || request.ContentLength64 > 8192) {
                ctx.Response.StatusCode = 403;
                return;
            }
            using var reader = new StreamReader(request.InputStream, Encoding.UTF8);
            string raw = (await reader.ReadToEndAsync()).Trim();
            if (!Uri.TryCreate(raw, UriKind.Absolute, out var uri) || uri.Scheme != Uri.UriSchemeHttps ||
                string.IsNullOrEmpty(uri.Host) || !string.IsNullOrEmpty(uri.UserInfo)) {
                ctx.Response.StatusCode = 400;
                return;
            }
            Process.Start(new ProcessStartInfo(uri.AbsoluteUri) { UseShellExecute = true });
            Log("opened HTTPS link");
            ctx.Response.StatusCode = 204;
        } catch { ctx.Response.StatusCode = 500; }
        finally { ctx.Response.Close(); }
    });
}
