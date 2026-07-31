; Inno Setup Installer Script for BTIS3053 Kindergarten Graduation Video Editor
; Compiles standalone AI_Video_Editor directory into 1-click Windows Installer Wizard (AI_Video_Editor_Setup.exe)

[Setup]
AppName=BTIS3053 AI Video Editor
AppVersion=1.0.0
AppPublisher=Southern University College - BTIS3053
DefaultDirName={autopf}\BTIS3053_AI_Video_Editor
DefaultGroupName=BTIS3053 AI Video Editor
OutputDir=..\dist
OutputBaseFilename=AI_Video_Editor_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\AI_Video_Editor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\BTIS3053 AI Video Editor"; Filename: "{app}\AI_Video_Editor.exe"
Name: "{group}\{cm:UninstallProgram,BTIS3053 AI Video Editor}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\BTIS3053 AI Video Editor"; Filename: "{app}\AI_Video_Editor.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AI_Video_Editor.exe"; Description: "{cm:LaunchProgram,BTIS3053 AI Video Editor}"; Flags: nowait postinstall skipifsilent
