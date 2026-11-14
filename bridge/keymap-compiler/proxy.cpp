#define UNICODE
#define _UNICODE
#include <windows.h>
#include <wchar.h>
#include <string>

using Loader = void* (__cdecl *)(const void*);
using Utf16 = const wchar_t* (__cdecl *)(const void*);
using FromWchar = void* (__cdecl *)(void*, const wchar_t*, int);
using QStringDestructor = void (__cdecl *)(void*);

static bool HasMarker(const wchar_t* path) {
    HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                              nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) return false;
    LARGE_INTEGER size = {0};
    if (!GetFileSizeEx(file, &size) || size.QuadPart < 0 || size.QuadPart > 4 * 1024 * 1024) { CloseHandle(file); return false; }
    std::string contents(static_cast<size_t>(size.QuadPart), '\0');
    DWORD read = 0;
    bool ok = ReadFile(file, contents.empty() ? nullptr : &contents[0], static_cast<DWORD>(contents.size()), &read, nullptr) != FALSE;
    CloseHandle(file);
    return ok && read == contents.size() && (contents.find("AFSWIPE:") != std::string::npos ||
        contents.find("AF Weapon") != std::string::npos || contents.find("AF Grenades") != std::string::npos);
}

#ifdef AF_PROXY_TEST
static void trace(const wchar_t* value) {
    wchar_t path[32768]; DWORD n=GetEnvironmentVariableW(L"LOCALAPPDATA",path,32768);
    if (!n || n>32680) return;
    wcscat_s(path,32768,L"\\af-proxy-test.log");
    HANDLE f=CreateFileW(path,FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(f!=INVALID_HANDLE_VALUE){DWORD written;WriteFile(f,value,(DWORD)(wcslen(value)*sizeof(wchar_t)),&written,nullptr);CloseHandle(f);}
}
#else
#define trace(value) ((void)0)
#endif

extern "C" void* AF_LoadKeymap(const void* source) {
    trace(L"entered\r\n");
    HMODULE original = GetModuleHandleW(L"nemu-keymapmanager.dll");
    if (!original) {
        HMODULE module = nullptr;
        wchar_t sibling[32768];
        if (GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                               reinterpret_cast<LPCWSTR>(&AF_LoadKeymap), &module) &&
            GetModuleFileNameW(module, sibling, 32768)) {
            wchar_t* end = wcsrchr(sibling, L'\\');
            if (end) { *(end + 1) = 0; wcscat_s(sibling, 32768, L"nemu-keymapmanager.dll"); original = LoadLibraryW(sibling); }
        }
    }
    auto load = original ? reinterpret_cast<Loader>(GetProcAddress(original, "?LoadKeymapConfigAndInfo@nemukeymapmanager@@YAPEAVKeymapConfig@1@AEBVQString@@@Z")) : nullptr;
    if (!load) { trace(L"no loader\r\n"); return nullptr; }
    HMODULE qt = GetModuleHandleW(L"Qt5Core.dll");
    auto utf16 = qt ? reinterpret_cast<Utf16>(GetProcAddress(qt, "?utf16@QString@@QEBAPEBGXZ")) : nullptr;
    auto from = qt ? reinterpret_cast<FromWchar>(GetProcAddress(qt, "?fromWCharArray@QString@@SA?AV1@PEB_WH@Z")) : nullptr;
    auto destroy = qt ? reinterpret_cast<QStringDestructor>(GetProcAddress(qt, "??1QString@@QEAA@XZ")) : nullptr;
    if (!source || !utf16 || !from || !destroy) { trace(L"missing Qt\r\n"); return load(source); }
    const wchar_t* path = utf16(source);
    if (!path || !HasMarker(path)) { trace(L"other profile\r\n"); return load(source); }
    trace(L"profile matched\r\n");

    HMODULE self = nullptr;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                            reinterpret_cast<LPCWSTR>(&AF_LoadKeymap), &self)) return load(source);
    wchar_t shell[32768], compiler[32768], outputDir[32768], output[32768], command[32768];
    DWORD n = GetModuleFileNameW(self, shell, 32768);
    if (!n || n >= 32768) return load(source);
    wchar_t* end = wcsrchr(shell, L'\\');
    if (!end) return load(source);
    *end = 0;
    if (swprintf_s(compiler, L"%s\\..\\..\\..\\nx_main\\af-bridge\\AFKeymapCompiler.exe", shell) < 0) return load(source);
    n = GetEnvironmentVariableW(L"LOCALAPPDATA", outputDir, 32768);
    if (!n || n >= 32768) return load(source);
    if (swprintf_s(output, L"%s\\ALL-FICTION\\MuMuBridge\\af-runtime-%lu-%lu.json", outputDir, GetCurrentProcessId(), GetCurrentThreadId()) < 0) return load(source);
    if (swprintf_s(command, L"\"%s\" \"%s\" \"%s\"", compiler, path, output) < 0) return load(source);
    STARTUPINFOW startup = {0}; PROCESS_INFORMATION child = {0}; startup.cb = sizeof(startup);
    if (!CreateProcessW(compiler, command, nullptr, nullptr, FALSE, CREATE_NO_WINDOW, nullptr, nullptr, &startup, &child)) { trace(L"process failed\r\n"); return load(source); }
    DWORD result = WaitForSingleObject(child.hProcess, 5000), code = 1;
    if (result == WAIT_OBJECT_0) GetExitCodeProcess(child.hProcess, &code);
    else TerminateProcess(child.hProcess, 1);
    CloseHandle(child.hThread); CloseHandle(child.hProcess);
    if (result != WAIT_OBJECT_0 || code != 0) { trace(L"compiler failed\r\n"); return load(source); }
    trace(L"compiler succeeded\r\n");
    void* converted = nullptr;
    from(&converted, output, -1);
    void* answer = load(&converted);
    destroy(&converted);
    return answer;
}
