[Setup]
AppId={{5E6F7A8B-9C0D-1E2F-3A4B-5C6D7E8F9A0B}
AppName=VRChat Discord Uploader
AppVersion=1.1.5
AppPublisher=VRCUploader Team
AppPublisherURL=https://github.com/TTakep/VRCUploader
AppSupportURL=https://github.com/TTakep/VRCUploader/issues
AppUpdatesURL=https://github.com/TTakep/VRCUploader/releases
DefaultDirName={autopf}\VRChatDiscordUploader
DefaultGroupName=VRChat Discord Uploader
DisableProgramGroupPage=yes
OutputBaseFilename=VRCUploader_Setup
OutputDir=dist
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
SetupIconFile=src\assets\icon.ico
UninstallDisplayIcon={app}\VRChatDiscordUploader.exe

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\VRChatDiscordUploader.exe"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\VRChat Discord Uploader"; Filename: "{app}\VRChatDiscordUploader.exe"
Name: "{autodesktop}\VRChat Discord Uploader"; Filename: "{app}\VRChatDiscordUploader.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\VRChatDiscordUploader.exe"; Description: "{cm:LaunchProgram,VRChat Discord Uploader}"; Flags: nowait postinstall skipifsilent
