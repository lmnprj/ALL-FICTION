#![cfg_attr(windows, windows_subsystem = "windows")]
use sha2::{Digest, Sha256};
use std::{env, fs::File, io::{self, Read, Seek, SeekFrom, Write}, path::{Path, PathBuf}, process::{Command, ExitCode}};

fn hidden_command<S: AsRef<std::ffi::OsStr>>(program: S) -> Command {
    let mut command = Command::new(program);
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000); // CREATE_NO_WINDOW
    }
    command
}

const FOOTER_MAGIC: &[u8; 8] = b"AFPKG001";
const EXTRACTOR: &[u8] = include_bytes!("../../release-prep/unpacked-patched/nx_main/7za.exe");
const INSTALLER_GUI: &str = include_str!("../installer-gui.ps1");

#[cfg(windows)]
fn launch_installer_gui() -> io::Result<()> {
    use std::os::windows::ffi::OsStrExt;
    #[link(name = "shell32")]
    unsafe extern "system" { fn ShellExecuteW(hwnd: *mut std::ffi::c_void, op: *const u16, file: *const u16, params: *const u16, dir: *const u16, show: i32) -> isize; }
    #[link(name = "kernel32")]
    unsafe extern "system" { fn GetConsoleWindow() -> *mut std::ffi::c_void; }
    #[link(name = "user32")]
    unsafe extern "system" { fn ShowWindow(hwnd: *mut std::ffi::c_void, cmd: i32) -> i32; }
    let script = env::temp_dir().join(format!("all-fiction-installer-{}.ps1", std::process::id()));
    std::fs::write(&script, [b"\xef\xbb\xbf".as_slice(), INSTALLER_GUI.as_bytes()].concat())?;
    let installer = env::current_exe()?;
    let args = format!("-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -STA -File {} -Installer {}", quote_windows_arg(&script.to_string_lossy()), quote_windows_arg(&installer.to_string_lossy()));
    let wide = |s: &std::ffi::OsStr| s.encode_wide().chain(Some(0)).collect::<Vec<u16>>();
    let operation = wide(std::ffi::OsStr::new("runas"));
    let program = wide(std::ffi::OsStr::new("powershell.exe"));
    let parameters = wide(std::ffi::OsStr::new(&args));
    unsafe { let console = GetConsoleWindow(); if !console.is_null() { ShowWindow(console, 0); } }
    let result = unsafe { ShellExecuteW(std::ptr::null_mut(), operation.as_ptr(), program.as_ptr(), parameters.as_ptr(), std::ptr::null(), 1) };
    if result <= 32 { return Err(io::Error::other(format!("Could not open installer: {result}"))); }
    Ok(())
}

fn bundle(archive: &Path, target: &Path) -> io::Result<()> {
    let mut executable = File::open(env::current_exe()?)?;
    let mut input = File::open(archive)?;
    let mut output = std::fs::OpenOptions::new().write(true).create_new(true).open(target)?;
    io::copy(&mut executable, &mut output)?;
    let mut sha = Sha256::new();
    let mut size = 0u64;
    let mut buf = vec![0; 1024 * 1024];
    loop { let n = input.read(&mut buf)?; if n == 0 { break; } output.write_all(&buf[..n])?; sha.update(&buf[..n]); size += n as u64; }
    output.write_all(FOOTER_MAGIC)?;
    output.write_all(&size.to_le_bytes())?;
    output.write_all(&sha.finalize())?;
    Ok(())
}

fn extract_bundle(target: &Path) -> io::Result<()> {
    let mut source = File::open(env::current_exe()?)?;
    let total = source.metadata()?.len();
    if total < 48 { return Err(io::Error::other("No embedded archive")); }
    source.seek(SeekFrom::End(-48))?;
    let mut footer = [0u8; 48]; source.read_exact(&mut footer)?;
    if &footer[..8] != FOOTER_MAGIC { return Err(io::Error::other("No embedded archive")); }
    let size = u64::from_le_bytes(footer[8..16].try_into().unwrap());
    if size == 0 || size > total - 48 { return Err(io::Error::other("Invalid archive size")); }
    if target.exists() { return Err(io::Error::new(io::ErrorKind::AlreadyExists, "Extraction destination already exists")); }
    let temp = env::temp_dir().join(format!("all-fiction-extract-{}", std::process::id()));
    std::fs::create_dir(&temp)?;
    let archive = temp.join("payload.7z");
    let extractor = temp.join("7za.exe");
    std::fs::write(&extractor, EXTRACTOR)?;
    let mut out = File::create(&archive)?;
    source.seek(SeekFrom::Start(total - 48 - size))?;
    let mut rest = size; let mut sha = Sha256::new(); let mut buf = vec![0u8; 1024 * 1024];
    while rest > 0 { let n = usize::try_from(rest.min(buf.len() as u64)).unwrap(); source.read_exact(&mut buf[..n])?; out.write_all(&buf[..n])?; sha.update(&buf[..n]); rest -= n as u64; }
    drop(out);
    if sha.finalize().as_slice() != &footer[16..] { return Err(io::Error::other("Embedded archive SHA-256 mismatch")); }
    std::fs::create_dir_all(target)?;
    let status = hidden_command(extractor).arg("x").arg("-y").arg(format!("-o{}", target.display())).arg(archive).status()?;
    if !status.success() { return Err(io::Error::other("Archive extraction failed; destination may be incomplete")); }
    println!("Payload extracted. This prototype does not register drivers or complete installation.");
    Ok(())
}

const PACKAGES: [(&str, &str); 2] = [
    ("MuMu-setup-mumu15-V15.8.9.5951-overseas-1027211800.exe", "fce092fa549cc1ffb05fbf98a42efcbdf51aab9e4750a25c3bd7191737b92e58"),
    ("MuMu-setup-nxmain-V1.8.9.5949-overseas-1027211357.exe", "d92747c4522a60caecb8da2f89174a80c6d0b982f9693f5e1720ef2a2fd84d8b"),
];
const REMOVED_ANDROID_PACKAGES: [&str; 15] = [
    "com.mumu.store", "com.mumu.shared.sdk", "com.mumu.acc", "com.nemu.nlp", "com.nemu.oaidmanager", "com.netease.mumu.cloner",
    "com.android.adservices.api", "com.android.ondevicepersonalization.services", "com.android.federatedcompute.services", "com.android.bluetooth", "com.android.camera2",
    "com.google.android.contacts", "com.google.android.syncadapters.contacts", "com.google.android.syncadapters.calendar", "app.lawnchair",
];
const CONFIG_TEMPLATES: [&str; 8] = [
    "configs/install_config.json", "configs/main/install_config.json", "configs/main/shell_config.json", "configs/main/vm_config.json",
    "nx_device/15.0/configs/device/hypervisor_config.json", "nx_device/15.0/configs/device/shell_config.json",
    "nx_device/15.0/configs/device/vm_config.json", "nx_device/15.0/configs/device/vms_config.json",
];

fn rewrite_config(value: &mut serde_json::Value, root: &str, documents: &str) {
    match value {
        serde_json::Value::String(s) => *s = s.replace("__AF_INSTALL_ROOT__", root).replace("__AF_DOCUMENTS__", documents),
        serde_json::Value::Array(a) => for v in a { rewrite_config(v, root, documents); },
        serde_json::Value::Object(o) => for v in o.values_mut() { rewrite_config(v, root, documents); },
        _ => (),
    }
}

fn materialize_configs(templates: &Path, target: &Path, documents: &Path) -> io::Result<()> {
    use std::io::Write;
    let root = target.to_str().ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "Invalid install path"))?;
    let docs = documents.to_str().ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "Invalid documents path"))?;
    if !target.is_absolute() || !documents.is_absolute() { return Err(io::Error::new(io::ErrorKind::InvalidInput, "Paths must be absolute")); }
    // Never overwrite an existing MuMu configuration.
    for rel in CONFIG_TEMPLATES {
        if target.join(rel).exists() { return Err(io::Error::new(io::ErrorKind::AlreadyExists, format!("Configuration already exists: {rel}"))); }
    }
    let mut prepared = Vec::new();
    for rel in CONFIG_TEMPLATES {
        let mut json: serde_json::Value = serde_json::from_reader(File::open(templates.join(rel))?)?;
        rewrite_config(&mut json, root, docs);
        prepared.push((rel, serde_json::to_vec_pretty(&json)?));
    }
    for (rel, bytes) in prepared {
        let path = target.join(rel);
        std::fs::create_dir_all(path.parent().unwrap())?;
        let mut file = std::fs::OpenOptions::new().write(true).create_new(true).open(path)?;
        file.write_all(&bytes)?;
    }
    Ok(())
}

#[cfg(windows)]
fn is_admin() -> bool {
    #[link(name = "shell32")]
    unsafe extern "system" { fn IsUserAnAdmin() -> i32; }
    unsafe { IsUserAnAdmin() != 0 }
}
#[cfg(not(windows))]
fn is_admin() -> bool { false }

fn safe_copy_tree(source: &Path, target: &Path) -> io::Result<()> {
    std::fs::create_dir(target)?;
    for entry in std::fs::read_dir(source)? {
        let entry = entry?;
        let kind = entry.file_type()?;
        if kind.is_symlink() { return Err(io::Error::other("Unexpected symbolic link in driver payload")); }
        let dest = target.join(entry.file_name());
        if kind.is_dir() { safe_copy_tree(&entry.path(), &dest)?; }
        else if kind.is_file() { std::fs::copy(entry.path(), dest)?; }
        else { return Err(io::Error::other("Unexpected item in driver payload")); }
    }
    Ok(())
}

fn service_query(name: &str) -> io::Result<Option<String>> {
    let output = hidden_command("sc.exe").args(["query", name]).output()?;
    if output.status.success() { return Ok(Some(String::from_utf8_lossy(&output.stdout).into_owned())); }
    if output.status.code() == Some(1060) { return Ok(None); }
    Err(io::Error::other(format!("Could not check service {name}: {}", output.status)))
}

fn driver_preflight() -> io::Result<PathBuf> {
    if !is_admin() { return Err(io::Error::new(io::ErrorKind::PermissionDenied, "Administrator rights are required for MuMu drivers")); }
    for service in ["MuMuNxSup", "MuMuNxNetLwf", "MuMuNxNetAdp6", "MuMuNxUSBMon", "MuMuNxUSB", "MuMuPlayerRemoteService"] {
        if service_query(service)?.is_some() { return Err(io::Error::new(io::ErrorKind::AlreadyExists, format!("Existing MuMu service {service}; refusing to modify it"))); }
    }
    let pf = PathBuf::from(env::var_os("ProgramFiles").ok_or_else(|| io::Error::other("Program Files is unavailable"))?);
    let runtime = pf.join("MuMuNxVbox");
    if runtime.exists() { return Err(io::Error::new(io::ErrorKind::AlreadyExists, "MuMu hypervisor runtime already exists")); }
    let registration = hidden_command("reg.exe").args(["query", r"HKCR\CLSID\{50859a2f-a5dd-4fcd-b107-ff2a37b33e4a}"]).output()?;
    if registration.status.success() { return Err(io::Error::new(io::ErrorKind::AlreadyExists, "Existing MuMu COM registration")); }
    let uninstall = hidden_command("reg.exe").args(["query", r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayerGlobal"]).output()?;
    if uninstall.status.success() { return Err(io::Error::new(io::ErrorKind::AlreadyExists, "Existing MuMu uninstall registration")); }
    Ok(runtime)
}

fn run_driver_script(path: &Path) -> io::Result<()> {
    let parent = path.parent().ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "Driver script has no directory"))?;
    let path = path.to_str().ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "Invalid driver path"))?;
    if path.chars().any(|c| "&|<>^%!\"\r\n".contains(c)) { return Err(io::Error::new(io::ErrorKind::InvalidInput, "Unsafe driver script path")); }
    #[cfg(windows)]
    let status = {
        use std::os::windows::process::CommandExt;
        hidden_command("cmd.exe").current_dir(parent).args(["/d", "/s", "/c"]).raw_arg(format!("\"\"{path}\"\"")).status()?
    };
    #[cfg(not(windows))]
    let status = return Err(io::Error::other("Driver scripts require Windows"));
    if !status.success() { return Err(io::Error::other(format!("Driver step failed: {path} ({status})"))); }
    Ok(())
}

fn install_drivers(root: &Path) -> io::Result<()> {
    let runtime = driver_preflight()?;
    let source = root.join("nx_device/15.0/hypervisor");
    for name in ["comregister.cmd", "load.cmd", "loadlwf.cmd", "MuMuNxSVC.exe", "VBoxC.dll"] {
        if !source.join(name).is_file() { return Err(io::Error::new(io::ErrorKind::NotFound, format!("Missing driver file: {name}"))); }
    }
    std::fs::create_dir(&runtime)?;
    let hypervisor = runtime.join("Hypervisor");
    safe_copy_tree(&source, &hypervisor)?;
    for script in ["comregister.cmd", "load.cmd", "loadlwf.cmd"] { run_driver_script(&hypervisor.join(script))?; }
    let status = service_query("MuMuNxSup")?.ok_or_else(|| io::Error::other("Support driver was not registered"))?;
    if !status.contains("RUNNING") { return Err(io::Error::other("Support driver is not running")); }
    if service_query("MuMuNxNetLwf")?.is_none() { return Err(io::Error::other("Network driver was not registered")); }
    println!("MuMu support and network drivers registered.");
    Ok(())
}

#[cfg(windows)]
fn known_folder(data1: u32, data2: u16, data3: u16, data4: [u8; 8]) -> io::Result<PathBuf> {
    use std::os::windows::ffi::OsStringExt;
    #[repr(C)]
    struct Guid { d1: u32, d2: u16, d3: u16, d4: [u8; 8] }
    #[link(name = "shell32")]
    unsafe extern "system" { fn SHGetKnownFolderPath(id: *const Guid, flags: u32, token: *mut std::ffi::c_void, path: *mut *mut u16) -> i32; }
    #[link(name = "ole32")]
    unsafe extern "system" { fn CoTaskMemFree(ptr: *mut std::ffi::c_void); }
    let guid = Guid { d1: data1, d2: data2, d3: data3, d4: data4 };
    let mut ptr = std::ptr::null_mut();
    let hr = unsafe { SHGetKnownFolderPath(&guid, 0, std::ptr::null_mut(), &mut ptr) };
    if hr < 0 || ptr.is_null() { return Err(io::Error::other(format!("Cannot locate Windows folder: HRESULT {hr:#x}"))); }
    let mut len = 0usize;
    while unsafe { *ptr.add(len) } != 0 { len += 1; }
    let value = unsafe { std::ffi::OsString::from_wide(std::slice::from_raw_parts(ptr, len)) };
    unsafe { CoTaskMemFree(ptr.cast()); }
    Ok(PathBuf::from(value))
}

#[cfg(windows)]
fn user_documents() -> io::Result<PathBuf> { known_folder(0xfdd39ad0, 0x238f, 0x46af, [0xad, 0xb4, 0x6c, 0x85, 0x48, 0x03, 0x69, 0xc7]) }
#[cfg(windows)]
fn user_desktop() -> io::Result<PathBuf> { known_folder(0xb4bfcc3a, 0xdb2c, 0x424c, [0xb0, 0x29, 0x7f, 0xe9, 0x9a, 0x87, 0xc6, 0x41]) }

#[cfg(windows)]
fn user_start_menu_programs() -> io::Result<PathBuf> { known_folder(0xa77f5d77, 0x2e2b, 0x44c3, [0xa6, 0xa2, 0xab, 0xa6, 0x01, 0x05, 0x4a, 0x51]) }

fn create_desktop_shortcut(root: &Path, desktop: &Path) -> io::Result<()> {
    let target = root.join("nx_main/MuMuNxMain.exe");
    if !target.is_file() || !desktop.is_dir() { return Err(io::Error::new(io::ErrorKind::NotFound, "Launcher or desktop folder missing")); }
    let link = desktop.join("ALL FICTION.lnk");
    if link.exists() { return Err(io::Error::new(io::ErrorKind::AlreadyExists, "Desktop shortcut already exists")); }
    let script = "$ErrorActionPreference='Stop'; $sh=New-Object -ComObject WScript.Shell; $s=$sh.CreateShortcut($env:AF_SHORTCUT_PATH); $s.TargetPath=$env:AF_SHORTCUT_TARGET; $s.WorkingDirectory=$env:AF_SHORTCUT_WORKDIR; $s.IconLocation=$env:AF_SHORTCUT_ICON; $s.Save()";
    let status = hidden_command("powershell.exe").args(["-NoProfile", "-NonInteractive", "-Command", script])
        .env("AF_SHORTCUT_PATH", &link).env("AF_SHORTCUT_TARGET", &target)
        .env("AF_SHORTCUT_WORKDIR", root.join("nx_main"))
        .env("AF_SHORTCUT_ICON", root.join("nx_main/MuMuNxMain.ico")).status()?;
    if !status.success() || !link.is_file() { return Err(io::Error::other("Could not create desktop shortcut")); }
    Ok(())
}

fn register_uninstaller_at(root: &Path, key: &str) -> io::Result<()> {
    let uninstall = root.join("uninstall.exe");
    if !uninstall.is_file() { return Err(io::Error::new(io::ErrorKind::NotFound, "MuMu uninstaller missing")); }
    if hidden_command("reg.exe").args(["query", key]).output()?.status.success() {
        return Err(io::Error::new(io::ErrorKind::AlreadyExists, "Uninstall registry entry already exists"));
    }
    let location = root.to_str().ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "Invalid install path"))?;
    let uninstaller = format!("\"{}\"", uninstall.display());
    let icon = format!("\"{}\"", root.join("nx_main/MuMuNxMain.ico").display());
    for (name, kind, value) in [
        ("DisplayName", "REG_SZ", "ALL FICTION"), ("Publisher", "REG_SZ", "ALL FICTION"),
        ("DisplayVersion", "REG_SZ", "6.8.9"), ("InstallLocation", "REG_SZ", location),
        ("DisplayIcon", "REG_SZ", icon.as_str()), ("UninstallString", "REG_SZ", uninstaller.as_str()),
        ("NoModify", "REG_DWORD", "1"), ("NoRepair", "REG_DWORD", "1"),
    ] {
        let result = hidden_command("reg.exe").args(["add", key, "/v", name, "/t", kind, "/d", value, "/f"]).output()?;
        if !result.status.success() { return Err(io::Error::other(format!("Registry registration failed at {name}: {}", String::from_utf8_lossy(&result.stderr)))); }
    }
    Ok(())
}

fn install_bundle(target: &Path, documents: &Path) -> io::Result<()> {
    if !target.is_absolute() || !documents.is_absolute() || target.parent().is_none() {
        return Err(io::Error::new(io::ErrorKind::InvalidInput, "Installation and documents paths must be absolute"));
    }
    if target.exists() { return Err(io::Error::new(io::ErrorKind::AlreadyExists, "Installation directory already exists")); }
    driver_preflight()?;
    println!("Extracting ALL FICTION files...");
    extract_bundle(target)?;
    println!("Preparing configuration...");
    materialize_configs(&target.join("installer-templates"), target, documents)?;
    std::fs::create_dir_all(target.join("vms"))?;
    println!("Installing MuMu drivers...");
    install_drivers(target)?;
    println!("Registering the uninstaller...");
    register_uninstaller_at(target, r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayerGlobal")?;
    #[cfg(windows)]
    match user_desktop().and_then(|desktop| create_desktop_shortcut(target, &desktop)) {
        Ok(()) => println!("Desktop shortcut created."),
        Err(e) => eprintln!("Could not create desktop shortcut: {e}"),
    }
    #[cfg(windows)]
    match user_start_menu_programs().and_then(|programs| create_desktop_shortcut(target, &programs)) {
        Ok(()) => println!("Start menu shortcut created."),
        Err(e) => eprintln!("Could not create Start menu shortcut: {e}"),
    }
    println!("Importing prepared Android...");
    import_android(&target.join("nx_main/MuMuManager.exe"), &target.join("ALL-FICTION-Android15.mumudata"))?;
    println!("Files, drivers and Android import completed.");
    Ok(())
}

fn quote_windows_arg(value: &str) -> String {
    let mut out = String::from("\""); let mut slashes = 0;
    for c in value.chars() {
        if c == '\\' { slashes += 1; continue; }
        if c == '"' { out.push_str(&"\\".repeat(slashes * 2 + 1)); out.push('"'); }
        else { out.push_str(&"\\".repeat(slashes)); out.push(c); }
        slashes = 0;
    }
    out.push_str(&"\\".repeat(slashes * 2)); out.push('"'); out
}

#[cfg(windows)]
fn elevate_install(target: &Path, docs: &Path) -> io::Result<()> {
    use std::os::windows::ffi::OsStrExt;
    #[link(name = "shell32")]
    unsafe extern "system" { fn ShellExecuteW(hwnd: *mut std::ffi::c_void, op: *const u16, file: *const u16, params: *const u16, dir: *const u16, show: i32) -> isize; }
    let exe = env::current_exe()?;
    let path = target.to_str().ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "Invalid install path"))?;
    let documents = docs.to_str().ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "Invalid Documents path"))?;
    let params = format!("install-interactive {} {}", quote_windows_arg(path), quote_windows_arg(documents));
    let wide = |s: &std::ffi::OsStr| s.encode_wide().chain(Some(0)).collect::<Vec<u16>>();
    let operation = wide(std::ffi::OsStr::new("runas")); let program = wide(exe.as_os_str()); let parameters = wide(std::ffi::OsStr::new(&params));
    let rc = unsafe { ShellExecuteW(std::ptr::null_mut(), operation.as_ptr(), program.as_ptr(), parameters.as_ptr(), std::ptr::null(), 1) };
    if rc <= 32 { return Err(io::Error::other(format!("Could not request administrator rights: {rc}"))); }
    Ok(())
}

#[cfg(windows)]
fn interactive_install() -> io::Result<()> {
    println!("ALL FICTION experimental installer. Test on a clean Windows installation only.");
    let default = PathBuf::from(env::var_os("ProgramFiles").ok_or_else(|| io::Error::other("Program Files unavailable"))?).join("ALL FICTION");
    println!("Install folder [Enter for {}]:", default.display());
    let mut line = String::new(); io::stdin().read_line(&mut line)?;
    let input = line.trim().trim_matches('"');
    let target = if input.is_empty() { default } else { PathBuf::from(input) };
    if !target.is_absolute() || target.exists() { return Err(io::Error::new(io::ErrorKind::InvalidInput, "Choose a new absolute installation folder")); }
    let docs = user_documents()?;
    if is_admin() { install_bundle(&target, &docs) } else { elevate_install(&target, &docs) }
}

fn manager_json(manager: &Path, args: &[&str]) -> io::Result<serde_json::Value> {
    let out = hidden_command(manager).args(args).output()?;
    if !out.status.success() { return Err(io::Error::other(format!("MuMuManager failed: {}", String::from_utf8_lossy(&out.stderr)))); }
    let value: serde_json::Value = serde_json::from_slice(&out.stdout)?;
    if value.get("errcode").and_then(|v| v.as_i64()).is_some_and(|v| v != 0) {
        return Err(io::Error::other(format!("MuMuManager error: {value}")));
    }
    Ok(value)
}

fn random_identity() -> io::Result<(String, String, String)> {
    let mut bytes = [0u8; 26];
    getrandom::fill(&mut bytes).map_err(|e| io::Error::other(format!("System RNG failed: {e}")))?;
    let android_id = bytes[..8].iter().map(|b| format!("{b:02x}")).collect::<String>();
    let mut mac = [0u8; 6]; mac.copy_from_slice(&bytes[8..14]); mac[0] = (mac[0] & 0xfc) | 0x02;
    let mac = mac.iter().map(|b| format!("{b:02x}")).collect::<Vec<_>>().join(":");
    let mut digits = vec![3u8, 5];
    for i in 0..12 { digits.push(bytes[14 + i] % 10); }
    let sum: u32 = digits.iter().enumerate().map(|(i, d)| { let mut n = *d as u32; if i % 2 == 1 { n *= 2; if n > 9 { n -= 9; } } n }).sum();
    digits.push(((10 - sum % 10) % 10) as u8);
    let imei = digits.into_iter().map(|d| char::from(b'0' + d)).collect();
    Ok((android_id, mac, imei))
}

fn wait_for_android(manager: &Path, adb_path: &Path, index: &str) -> io::Result<String> {
    for _ in 0..45 {
        if let Ok(info) = manager_json(manager, &["info", "-v", index]) {
            if info.get("adb_host_ip").and_then(|v| v.as_str()) == Some("127.0.0.1") {
                if let Some(port) = info.get("adb_port").and_then(|v| v.as_u64()).filter(|p| *p > 0 && *p <= 65535) {
                    let serial = format!("127.0.0.1:{port}");
                    let _ = hidden_command(adb_path).args(["connect", &serial]).output();
                    if adb(adb_path, &serial, &["shell", "getprop", "sys.boot_completed"]).is_ok_and(|v| v.trim() == "1") { return Ok(serial); }
                }
            }
        }
        std::thread::sleep(std::time::Duration::from_secs(1));
    }
    Err(io::Error::new(io::ErrorKind::TimedOut, "Android did not finish booting"))
}

fn wait_for_shutdown(manager: &Path, index: &str) -> io::Result<()> {
    for _ in 0..30 {
        if let Ok(info) = manager_json(manager, &["info", "-v", index]) {
            if info.get("is_process_started").and_then(|v| v.as_bool()) == Some(false) { return Ok(()); }
        }
        std::thread::sleep(std::time::Duration::from_secs(1));
    }
    Err(io::Error::new(io::ErrorKind::TimedOut, "Android did not shut down"))
}

fn initialize_system_id(manager: &Path, index: &str, android_id: &str) -> io::Result<()> {
    if index.parse::<u32>().is_err() || android_id.len() != 16 || !android_id.bytes().all(|b| b.is_ascii_hexdigit()) {
        return Err(io::Error::new(io::ErrorKind::InvalidInput, "Invalid device index or Android ID"));
    }
    let adb_path = manager.parent().ok_or_else(|| io::Error::other("Manager path has no parent"))?.join("adb.exe");
    if !adb_path.is_file() { return Err(io::Error::new(io::ErrorKind::NotFound, "MuMu adb.exe missing")); }
    manager_json(manager, &["control", "-v", index, "launch"])?;
    let serial = wait_for_android(manager, &adb_path, index)?;
    let mut rooted = false;
    for _ in 0..6 {
        let _ = adb(&adb_path, &serial, &["root"]);
        std::thread::sleep(std::time::Duration::from_secs(1));
        let _ = hidden_command(&adb_path).args(["connect", &serial]).output();
        if adb(&adb_path, &serial, &["shell", "id", "-u"]).is_ok_and(|v| v.trim() == "0") { rooted = true; break; }
    }
    if !rooted { return Err(io::Error::other("ADB root unavailable for initial Android ID setup")); }
    adb(&adb_path, &serial, &["shell", "settings", "put", "secure", "android_id", android_id])?;
    let actual = adb(&adb_path, &serial, &["shell", "settings", "get", "secure", "android_id"])?;
    if actual.trim() != android_id { return Err(io::Error::other("Android ID write did not verify")); }
    adb(&adb_path, &serial, &["shell", "sync"])?;
    std::thread::sleep(std::time::Duration::from_secs(12));
    adb(&adb_path, &serial, &["shell", "sync"])?;
    manager_json(manager, &["control", "-v", index, "shutdown"])?;
    wait_for_shutdown(manager, index)?;
    manager_json(manager, &["control", "-v", index, "launch"])?;
    let serial = wait_for_android(manager, &adb_path, index)?;
    let actual = adb(&adb_path, &serial, &["shell", "settings", "get", "secure", "android_id"])?;
    if actual.trim() != android_id { return Err(io::Error::other("Android ID did not persist after reboot")); }
    manager_json(manager, &["control", "-v", index, "shutdown"])?;
    wait_for_shutdown(manager, index)?;
    Ok(())
}

fn import_android(manager: &Path, image: &Path) -> io::Result<()> {
    if !manager.is_file() || !image.is_file() { return Err(io::Error::new(io::ErrorKind::NotFound, "MuMuManager or Android export is missing")); }
    let list = manager_json(manager, &["info", "-v", "all"])?;
    let items = list.as_object().ok_or_else(|| io::Error::other("Unexpected MuMu device list"))?;
    if items.keys().any(|key| key.parse::<u32>().is_ok()) {
        return Err(io::Error::new(io::ErrorKind::AlreadyExists, "Existing Android devices detected; automatic import aborted"));
    }
    let path = image.to_str().ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "Invalid image path"))?;
    let imported = manager_json(manager, &["import", "-p", path, "-n", "1", "-ver", "15"])?;
    let devices = imported.as_object().ok_or_else(|| io::Error::other("Unexpected import result"))?;
    let ids: Vec<_> = devices.iter().filter(|(k, _)| k.parse::<u32>().is_ok()).collect();
    if ids.len() != 1 || ids[0].1.get("errcode").and_then(|v| v.as_i64()) != Some(0) {
        return Err(io::Error::other(format!("Android import failed: {imported}")));
    }
    let index = ids[0].0;
    let (android_id, mac, imei) = random_identity()?;
    for (key, value) in [("android_id", &android_id), ("mac_address", &mac), ("imei", &imei)] {
        let result = manager_json(manager, &["simulation", "-v", index, "-sk", key, "-sv", value])?;
        if result.get(key).and_then(|v| v.as_str()) != Some(value.as_str()) {
            return Err(io::Error::other(format!("Could not set device property {key}")));
        }
    }
    println!("Android imported as device {index}; device properties configured.");
    Ok(())
}

fn hash(path: &Path) -> io::Result<String> {
    let mut file = File::open(path)?;
    let mut sha = Sha256::new();
    let mut buf = vec![0; 1024 * 1024];
    loop {
        let n = file.read(&mut buf)?;
        if n == 0 { break; }
        sha.update(&buf[..n]);
    }
    Ok(format!("{:x}", sha.finalize()))
}

fn verify(dir: &Path) -> io::Result<()> {
    for (name, expected) in PACKAGES {
        let path = dir.join(name);
        let actual = hash(&path)?;
        if actual != expected {
            return Err(io::Error::new(io::ErrorKind::InvalidData, format!("SHA-256 mismatch: {}", path.display())));
        }
        println!("OK: {name}");
    }
    Ok(())
}

fn valid_serial(serial: &str) -> bool {
    serial.strip_prefix("127.0.0.1:").and_then(|port| port.parse::<u16>().ok()).is_some_and(|port| port != 0)
}

fn adb(adb_path: &Path, serial: &str, args: &[&str]) -> io::Result<String> {
    let output = hidden_command(adb_path).arg("-s").arg(serial).args(args).output()?;
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_owned();
    if !output.status.success() {
        return Err(io::Error::other(format!("ADB failed: {}", String::from_utf8_lossy(&output.stderr).trim())));
    }
    Ok(stdout)
}

fn init_android(adb_path: &Path, serial: &str, apk: &Path) -> io::Result<()> {
    if !valid_serial(serial) { return Err(io::Error::new(io::ErrorKind::InvalidInput, "Expected an explicit local emulator address (127.0.0.1:port)")); }
    if !apk.is_file() { return Err(io::Error::new(io::ErrorKind::NotFound, "Launcher APK missing")); }
    if adb(adb_path, serial, &["shell", "getprop", "sys.boot_completed"])? != "1" {
        return Err(io::Error::other("Android has not finished booting"));
    }
    let apk_str = apk.to_str().ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "Invalid APK path"))?;
    let output = adb(adb_path, serial, &["install", "--no-incremental", "-r", apk_str])?;
    if !output.lines().any(|line| line.trim() == "Success") { return Err(io::Error::other(format!("APK installation failed: {output}"))); }
    let home = "local.violethome/.MainActivity";
    adb(adb_path, serial, &["shell", "cmd", "package", "set-home-activity", home])?;
    let resolved = adb(adb_path, serial, &["shell", "cmd", "package", "resolve-activity", "--brief", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME"])?;
    if !resolved.lines().any(|line| line.trim() == home) { return Err(io::Error::other("Launcher did not become the default home")); }
    let available = adb(adb_path, serial, &["shell", "pm", "list", "packages", "--user", "0"])?;
    let mut removed = Vec::new();
    for package in REMOVED_ANDROID_PACKAGES {
        if available.lines().any(|line| line.trim().strip_prefix("package:") == Some(package)) {
            let result = adb(adb_path, serial, &["shell", "pm", "uninstall", "--user", "0", package])?;
            if result.trim() != "Success" { return Err(io::Error::other(format!("Could not uninstall {package}: {result}"))); }
            removed.push(package);
        } else {
            println!("Package not present: {package}");
        }
    }
    let actual = adb(adb_path, serial, &["shell", "pm", "list", "packages", "--user", "0"])?;
    for package in &removed {
        if actual.lines().any(|line| line.trim().strip_prefix("package:") == Some(*package)) {
            return Err(io::Error::other(format!("Package still installed for user 0: {package}")));
        }
    }
    println!("Uninstalled and verified {} packages for user 0; system copies may remain.", removed.len());
    println!("ALL FICTION launcher installed and selected as home.");
    Ok(())
}

fn main() -> ExitCode {
    let args: Vec<_> = env::args_os().collect();
    let pause_at_end = args.len() == 4 && args[1] == "install-interactive";
    let result = if args.len() == 1 {
        #[cfg(windows)]
        { launch_installer_gui() }
        #[cfg(not(windows))]
        { Err(io::Error::other("Installation is only supported on Windows")) }
    } else if args.len() == 4 && args[1] == "bundle" {
        bundle(&PathBuf::from(&args[2]), &PathBuf::from(&args[3]))
    } else if args.len() == 3 && args[1] == "extract" {
        extract_bundle(&PathBuf::from(&args[2]))
    } else if args.len() == 3 && args[1] == "verify" {
        verify(&PathBuf::from(&args[2]))
    } else if args.len() == 5 && args[1] == "render-config" {
        materialize_configs(&PathBuf::from(&args[2]), &PathBuf::from(&args[3]), &PathBuf::from(&args[4]))
    } else if args.len() == 4 && args[1] == "import-android" {
        import_android(&PathBuf::from(&args[2]), &PathBuf::from(&args[3]))
    } else if args.len() == 3 && args[1] == "install-drivers" {
        install_drivers(&PathBuf::from(&args[2]))
    } else if args.len() == 4 && args[1] == "create-shortcut" {
        create_desktop_shortcut(&PathBuf::from(&args[2]), &PathBuf::from(&args[3]))
    } else if args.len() == 4 && (args[1] == "install-experimental" || args[1] == "install-interactive") {
        install_bundle(&PathBuf::from(&args[2]), &PathBuf::from(&args[3]))
    } else if args.len() == 3 && args[1] == "install-experimental" {
        #[cfg(windows)]
        { user_documents().and_then(|docs| install_bundle(&PathBuf::from(&args[2]), &docs)) }
        #[cfg(not(windows))]
        { Err(io::Error::other("Installation is only supported on Windows")) }
    } else if args.len() == 5 && args[1] == "set-android-id" {
        match (args[3].to_str(), args[4].to_str()) {
            (Some(index), Some(id)) => initialize_system_id(&PathBuf::from(&args[2]), index, id),
            _ => Err(io::Error::new(io::ErrorKind::InvalidInput, "Invalid index or ID")),
        }
    } else if args.len() == 5 && args[1] == "init-android" {
        match args[3].to_str() {
            Some(serial) => init_android(&PathBuf::from(&args[2]), serial, &PathBuf::from(&args[4])),
            None => Err(io::Error::new(io::ErrorKind::InvalidInput, "Invalid emulator address")),
        }
    } else {
        eprintln!("Development tool only. Usage: verify <package-directory> | init-android <adb.exe> <127.0.0.1:port> <launcher.apk>");
        return ExitCode::from(2);
    };
    let code = match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => { eprintln!("Operation failed: {e}"); ExitCode::FAILURE }
    };
    if pause_at_end { println!("Press Enter to close."); let mut line = String::new(); let _ = io::stdin().read_line(&mut line); }
    code
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn sha256_known_input() {
        let path = env::temp_dir().join(format!("all-fiction-hash-test-{}", std::process::id()));
        std::fs::write(&path, b"abc").unwrap();
        assert_eq!(hash(&path).unwrap(), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
        std::fs::remove_file(path).unwrap();
    }
    #[test]
    fn missing_packages_fail_closed() {
        let path = env::temp_dir().join(format!("all-fiction-missing-test-{}", std::process::id()));
        assert!(verify(&path).is_err());
    }
    #[test]
    fn only_accept_explicit_loopback_emulators() {
        assert!(valid_serial("127.0.0.1:16416"));
        for s in ["127.0.0.1:0", "127.0.0.1:65536", "192.168.1.2:5555", "emulator-5554", "127.0.0.1:5555:1"] { assert!(!valid_serial(s)); }
    }
    #[test]
    fn rewrite_paths_in_nested_json_without_touching_other_values() {
        let mut v = serde_json::json!({"path":"__AF_INSTALL_ROOT__\\nx_main", "nested":["__AF_DOCUMENTS__\\MuMuSharedFolder", 2]});
        rewrite_config(&mut v, "D:\\Games\\ALL FICTION", "C:\\Users\\Example\\Documents");
        assert_eq!(v["path"], "D:\\Games\\ALL FICTION\\nx_main");
        assert_eq!(v["nested"][0], "C:\\Users\\Example\\Documents\\MuMuSharedFolder");
        assert_eq!(v["nested"][1], 2);
    }
    #[test]
    fn removal_list_is_complete_and_unique() {
        let unique: std::collections::HashSet<_> = REMOVED_ANDROID_PACKAGES.iter().collect();
        assert_eq!(unique.len(), 15);
        assert!(!unique.contains(&"local.violethome"));
    }
    #[test]
    fn generated_identity_has_valid_shapes_and_luhn_checksum() {
        let (a, m, i) = random_identity().unwrap();
        assert_eq!(a.len(), 16); assert_eq!(m.len(), 17); assert_eq!(i.len(), 15);
        let sum: u32 = i.bytes().enumerate().map(|(n, b)| { let mut d = (b-b'0') as u32; if n % 2 == 1 { d *= 2; if d > 9 { d -= 9; } } d }).sum();
        assert_eq!(sum % 10, 0);
    }
    #[test]
    fn windows_arguments_escape_quotes_and_trailing_slashes() {
        assert_eq!(quote_windows_arg("C:\\Program Files\\ALL FICTION"), "\"C:\\Program Files\\ALL FICTION\"");
        assert_eq!(quote_windows_arg("C:\\folder\\"), "\"C:\\folder\\\\\"");
        assert_eq!(quote_windows_arg("a\"b"), "\"a\\\"b\"");
    }
    #[cfg(windows)]
    #[test]
    fn driver_script_runs_with_space_in_path_and_propagates_failure() {
        let root = env::temp_dir().join(format!("AF script test {}", std::process::id()));
        std::fs::create_dir(&root).unwrap();
        let ok = root.join("ok.cmd"); let fail = root.join("fail.cmd");
        std::fs::write(&ok, b"@echo off\r\nif not exist ok.cmd exit /b 8\r\nexit /b 0\r\n").unwrap();
        std::fs::write(&fail, b"@echo off\r\nexit /b 7\r\n").unwrap();
        let success = run_driver_script(&ok); let failure = run_driver_script(&fail);
        let _ = std::fs::remove_file(ok); let _ = std::fs::remove_file(fail); let _ = std::fs::remove_dir(root);
        assert!(success.is_ok()); assert!(failure.is_err());
    }
    #[cfg(windows)]
    #[test]
    fn register_test_entry_and_reject_existing_key() {
        let key = format!(r"HKCU\Software\ALLFICTION\InstallerTest{}", std::process::id());
        let root = env::temp_dir().join(format!("af-registry-test-{}", std::process::id()));
        std::fs::create_dir(&root).unwrap();
        std::fs::write(root.join("uninstall.exe"), b"test").unwrap();
        let first = register_uninstaller_at(&root, &key);
        let second = register_uninstaller_at(&root, &key);
        let q = hidden_command("reg.exe").args(["query", &key, "/v", "DisplayName"]).output().unwrap();
        let _ = hidden_command("reg.exe").args(["delete", &key, "/f"]).output();
        let _ = std::fs::remove_file(root.join("uninstall.exe"));
        let _ = std::fs::remove_dir(root);
        assert!(first.is_ok());
        assert_eq!(second.unwrap_err().kind(), io::ErrorKind::AlreadyExists);
        assert!(q.status.success());
        assert!(String::from_utf8_lossy(&q.stdout).contains("ALL FICTION"));
    }
}
