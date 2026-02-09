; ============================================================================
; Conduital — Inno Setup Installer Script
;
; Builds a Windows installer for Conduital with:
;   - Start Menu shortcuts
;   - Optional Desktop shortcut
;   - Uninstaller registered in Windows "Apps & Features"
;   - EULA screen during installation
;   - "Launch after install" checkbox on final screen
;
; Prerequisites:
;   - PyInstaller build completed (backend\dist\Conduital\)
;   - Inno Setup 6.x installed (https://jrsoftware.org/isinfo.php)
;
; Usage:
;   Open this file in Inno Setup Compiler and click Build > Compile
;   Or from command line: iscc installer\conduital.iss
;
; Output:
;   installer\Output\ConduitalSetup-1.0.0-alpha.exe
; ============================================================================

#define MyAppName "Conduital"
#define MyAppVersion "1.0.0-alpha"
#define MyAppPublisher "Conduital"
#define MyAppURL "https://conduital.com"
#define MyAppExeName "Conduital.exe"
#define MyAppDescription "Intelligent Momentum Productivity System"

[Setup]
; Unique AppId — do NOT change after first release (used for upgrades)
AppId={{B4F7E2A1-8C3D-4E5F-9A1B-6D2C8E4F0A3B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; Show EULA before installation
LicenseFile=..\LICENSE
; Allow user to choose directory
AllowNoIcons=yes
; Output installer location and naming
OutputDir=Output
OutputBaseFilename=ConduitalSetup-{#MyAppVersion}
; Use the app icon if available, otherwise Inno Setup default
; Uncomment when icon is available:
; SetupIconFile=..\assets\conduital.ico
Compression=lzma2/ultra64
SolidCompression=yes
; Modern installer UI
WizardStyle=modern
; Require admin rights for Program Files installation
PrivilegesRequired=admin
; Minimum Windows version (Windows 10)
MinVersion=10.0
; Uninstaller settings
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; Architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Version info embedded in installer exe
VersionInfoVersion=1.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoCopyright=Copyright (c) 2026 Greg Maxfield
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=1.0.0.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable
Source: "..\backend\dist\Conduital\Conduital.exe"; DestDir: "{app}"; Flags: ignoreversion

; All bundled dependencies and data files
Source: "..\backend\dist\Conduital\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; Third-party license notices
Source: "..\THIRD_PARTY_LICENSES.txt"; DestDir: "{app}"; Flags: ignoreversion

; License file
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; Comment: "Uninstall {#MyAppName}"

; Desktop shortcut (optional, user chooses during install)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "{#MyAppDescription}"

[Run]
; "Launch Conduital" checkbox on final installer screen
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up any files created at runtime in the install directory
; (User data in %LOCALAPPDATA%\Conduital\ is intentionally preserved)
Type: filesandordirs; Name: "{app}\__pycache__"
Type: files; Name: "{app}\*.log"

[Code]
// Custom uninstall prompt: offer to remove user data
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
  MsgResult: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{localappdata}\Conduital');
    if DirExists(DataDir) then
    begin
      MsgResult := MsgBox(
        'Do you want to remove your Conduital user data?' + Chr(13) + Chr(10) +
        Chr(13) + Chr(10) +
        'This includes your database, settings, and log files stored in:' + Chr(13) + Chr(10) +
        DataDir + Chr(13) + Chr(10) +
        Chr(13) + Chr(10) +
        'Click Yes to remove all data, or No to keep it (recommended if you plan to reinstall).',
        mbConfirmation, MB_YESNO or MB_DEFBUTTON2);
      if MsgResult = IDYES then
      begin
        DelTree(DataDir, True, True, True);
      end;
    end;
  end;
end;

// Try graceful shutdown via the /api/v1/shutdown endpoint, then fall back to force-kill.
// The shutdown endpoint (BACKLOG-115) triggers a cooperative shutdown of the FastAPI server.
procedure GracefulShutdown();
var
  ErrorCode: Integer;
  WaitCount: Integer;
begin
  // Step 1: Try graceful shutdown via HTTP POST to localhost
  Exec('powershell', '-NoProfile -Command "try { Invoke-WebRequest -Uri ''http://127.0.0.1:52140/api/v1/shutdown'' -Method POST -TimeoutSec 5 -UseBasicParsing | Out-Null } catch {}"',
    '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);

  // Step 2: Wait up to 8 seconds for the process to exit gracefully
  WaitCount := 0;
  while WaitCount < 8 do
  begin
    Sleep(1000);
    WaitCount := WaitCount + 1;
    // Check if process is still running (tasklist returns 0 if found)
    Exec('tasklist', '/FI "IMAGENAME eq Conduital.exe" /NH', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
    // tasklist always returns 0; we cannot reliably check via exit code here,
    // so just wait the full period on graceful path
  end;

  // Step 3: Force-kill if still running (safety net)
  Exec('taskkill', '/F /IM Conduital.exe', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  if ErrorCode = 0 then
    Sleep(1000);  // Brief pause after force-kill
end;

// Close any running Conduital instance before installing/upgrading
function InitializeSetup(): Boolean;
begin
  Result := True;
  GracefulShutdown();
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
  GracefulShutdown();
end;
