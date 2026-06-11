; Inno Setup script - Tool Voice Clone (Doanhbadboiz)
; Bien dich: ISCC.exe installer.iss  -> Output\ToolVoiceClone_Setup.exe
; Cai vao thu muc nguoi dung (khong can quyen admin); deps tai khi chay lan dau.

#define AppName "Tool Voice Clone (Doanhbadboiz)"
#define AppVer "1.3.5"
#define AppPub "Doanhbadboiz - Vu Duc Doanh"

[Setup]
AppId={{8F3A1C42-7D9E-4B6A-9C21-A1B2C3D4E5F6}
AppName={#AppName}
AppVersion={#AppVer}
AppPublisher={#AppPub}
DefaultDirName={localappdata}\Programs\ToolVoiceClone
DefaultGroupName=Tool Voice Clone
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=ToolVoiceClone_Setup
InfoBeforeFile=THONG_BAO_TRUOC_KHI_CAI.txt
SetupIconFile=app.ico
UninstallDisplayIcon={app}\app.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Tao bieu tuong ngoai Desktop"; GroupDescription: "Tuy chon:"

[Files]
; KHONG dong goi admin tool cho user (chi owner moi co)
Source: "*.py";              DestDir: "{app}"; Excludes: "admin_tool.py,voice_admin_client.py"; Flags: ignoreversion
Source: "*.bat";             DestDir: "{app}"; Excludes: "Chay_Admin.bat"; Flags: ignoreversion
Source: "start_app.vbs";     DestDir: "{app}"; Flags: ignoreversion
Source: "auth_config.json";  DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt";  DestDir: "{app}"; Flags: ignoreversion
Source: "app.ico";           DestDir: "{app}"; Flags: ignoreversion
Source: "logo.png";          DestDir: "{app}"; Flags: ignoreversion
Source: "THONG_BAO_TRUOC_KHI_CAI.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "*.md";              DestDir: "{app}"; Flags: ignoreversion
Source: "wsl\*";             DestDir: "{app}\wsl"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Tool Voice Clone"; Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\tts_gui.py"""; IconFilename: "{app}\app.ico"; WorkingDir: "{app}"
Name: "{group}\Huong dan";        Filename: "{app}\HUONG_DAN.md";   IconFilename: "{app}\app.ico"; WorkingDir: "{app}"
Name: "{group}\Go cai dat Tool Voice Clone"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Tool Voice Clone"; Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\tts_gui.py"""; IconFilename: "{app}\app.ico"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\start_app.bat"; Description: "Mo Tool Voice Clone ngay"; Flags: postinstall nowait skipifsilent shellexec
