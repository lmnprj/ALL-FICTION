using System.Text.Json;
using System.Text.Json.Nodes;

// This runs only when MuMu loads a keymap. It leaves the editor's file untouched.
if (args.Length != 2) return 2;
try {
    var input = Path.GetFullPath(args[0]);
    var output = Path.GetFullPath(args[1]);
    if (string.Equals(input, output, StringComparison.OrdinalIgnoreCase)) return 2;
    var config = JsonNode.Parse(File.ReadAllText(input))?.AsObject() ?? throw new InvalidDataException();
    var items = config["keymaps"]?.AsArray() ?? throw new InvalidDataException();
    var replacement = new JsonArray();
    int groups = 0;
    foreach (var node in items) {
        if (node is not JsonObject item) throw new InvalidDataException();
        string description = item["icon"]?["description"]?.GetValue<string>() ?? "";
        bool weapon = description.StartsWith("AFSWIPE:weapon", StringComparison.Ordinal) || description == "AF Weapon";
        bool grenade = description.StartsWith("AFSWIPE:grenade", StringComparison.Ordinal) || description == "AF Grenades";
        if (item["type"]?.GetValue<string>() != "Swipehold" || (!weapon && !grenade)) {
            replacement.Add(item.DeepClone());
            continue;
        }
        double x = item["rel_work_position"]?["rel_x"]?.GetValue<double>() ?? throw new InvalidDataException();
        double y = item["rel_work_position"]?["rel_y"]?.GetValue<double>() ?? throw new InvalidDataException();
        double radius = item["rel_radius"]?.GetValue<double>() ?? throw new InvalidDataException();
        if (x < 0 || x > 1 || y < 0 || y > 1 || radius <= 0 || radius > 0.5) throw new InvalidDataException();
        // Preserve the direction lengths that passed the in-game movement test.
        var vectors = weapon ? new[] { (.005502, -.163754), (-.003056, .115858), (-.110636, 0.0), (.143032, -.001942) }
                             : new[] { (-.000611, -.104854), (-.002445, .115210), (-.109414, .007767), (.093520, 0.0) };
        string[] fields = ["top_key", "bottom_key", "left_key", "right_key"];
        for (int i = 0; i < fields.Length; i++) {
            var key = item[fields[i]]?.DeepClone() ?? throw new InvalidDataException();
            if (string.IsNullOrEmpty(key["text"]?.GetValue<string>())) continue;
            double dx = vectors[i].Item1 * radius / .1;
            double dy = vectors[i].Item2 * radius / .1;
            if (x + dx < 0 || x + dx > 1 || y + dy < 0 || y + dy > 1) throw new InvalidDataException();
            var position = new JsonObject { ["rel_x"] = x, ["rel_y"] = y };
            var icon = item["icon"]?.DeepClone()?.AsObject() ?? new JsonObject();
            icon["rel_position"] = position.DeepClone();
            string points = string.Concat(Enumerable.Range(0, 13).Select(n =>
                FormattableString.Invariant($"{dx * n / 12:0.00000000},{dy * n / 12:0.00000000};")));
            replacement.Add(new JsonObject {
                ["type"] = "Curve", ["key"] = key, ["break_staring"] = item["break_staring"]?.DeepClone() ?? JsonValue.Create(false),
                ["editor_icon_scale"] = item["editor_icon_scale"]?.DeepClone() ?? JsonValue.Create(1),
                ["icon"] = icon, ["rel_work_position"] = position,
                ["rel_start_pos"] = new JsonObject { ["rel_x"] = 0, ["rel_y"] = 0 },
                ["rel_end_pos"] = new JsonObject { ["rel_x"] = dx, ["rel_y"] = dy },
                ["rel_all_points_pos"] = points, ["act_as_line"] = true, ["start_wait_time"] = 0
            });
        }
        groups++;
    }
    if (groups == 0) return 3;
    config["keymaps"] = replacement;
    Directory.CreateDirectory(Path.GetDirectoryName(output)!);
    string temp = output + ".tmp";
    File.WriteAllText(temp, config.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
    File.Move(temp, output, true);
    return 0;
} catch { return 1; }
