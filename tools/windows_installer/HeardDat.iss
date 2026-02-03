; HeardDat PC Server installer
; Build with Inno Setup 6+ after producing dist/HeardDatServer.exe

[Setup]
AppName=HeardDat PC Server
AppVersion=0.1.0
DefaultDirName={pf}\HeardDat
DefaultGroupName=HeardDat
UninstallDisplayIcon={app}\HeardDatServer.exe
OutputBaseFilename=HeardDatInstaller
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
; Main packaged executable (build with PyInstaller before running this script)
Source: "..\..\dist\HeardDatServer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\HeardDat PC Server"; Filename: "{app}\HeardDatServer.exe"

[Tasks]
Name: "runatstartup"; Description: "Start HeardDat server when Windows starts"; Flags: unchecked
Name: "runnow"; Description: "Start HeardDat server immediately after install"; Flags: unchecked

[Run]
; Optional immediate launch after install
Filename: "{app}\HeardDatServer.exe"; Description: "Launch HeardDat server"; Flags: nowait postinstall skipifsilent; Tasks: runnow

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  StartupShortcut: string;
  TargetPath: string;
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('runatstartup') then
  begin
    TargetPath := ExpandConstant('{app}\HeardDatServer.exe');
    StartupShortcut := ExpandConstant('{userstartup}\HeardDat PC Server.lnk');
    ; Create a Startup shortcut so the server auto-starts after login.
    CreateShellLink(StartupShortcut, 'HeardDat PC Server', TargetPath, '', '', 0, SW_SHOWNORMAL);
  end;
end;
