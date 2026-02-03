# Windows Installer (HeardDat PC Server)

## Purpose
This folder contains the Inno Setup script that builds a Windows installer for the HeardDat PC server.

## Build steps
1. Build the server executable with PyInstaller (or your preferred packager) into `dist/HeardDatServer.exe`.
2. Open `HeardDat.iss` in Inno Setup and click **Build**.
3. Share the generated installer `.exe` (do not commit it to git).

## Installer behavior
- Offers a checkbox to **start the server at Windows startup** by creating a Startup folder shortcut.
- Offers a checkbox to **launch the server immediately** after install.
- Creates a Start Menu shortcut for manual launches.

## Notes
- Add new runtime dependencies to the installer assets if future work requires them.
- Keep the installer script in sync with any packaging changes.
