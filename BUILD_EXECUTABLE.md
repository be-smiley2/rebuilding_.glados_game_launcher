# GLaDOS Game Launcher - Executable Build

This document explains how to build the GLaDOS Game Launcher as a Windows executable (.exe) file.

## Prerequisites

- Python 3.7 or higher
- Virtual environment (recommended)
- PyInstaller package

## Building the Executable

### Method 1: Using the Build Scripts (Recommended)

#### Option A: Batch File
```cmd
# Run the batch file
build_exe.bat
```

#### Option B: PowerShell Script
```powershell
# Run the PowerShell script
.\build_exe.ps1
```

### Method 2: Manual Build

1. **Install PyInstaller**:
   ```cmd
   python -m pip install pyinstaller
   ```

2. **Build the executable**:
   ```cmd
   python -m PyInstaller --clean glados_launcher.spec
   ```

3. **Find your executable**:
   The executable will be created in the `dist` folder as `GLaDOS_Game_Launcher.exe`

## Build Configuration

The build is configured using the `glados_launcher.spec` file, which includes:

- **Entry point**: `glados_game_launcher.py`
- **Output name**: `GLaDOS_Game_Launcher.exe`
- **Window mode**: GUI (no console window)
- **All dependencies**: Automatically included
- **Single file**: Everything bundled into one executable

## File Details

- **Executable size**: ~10.7 MB
- **Location**: `dist/GLaDOS_Game_Launcher.exe`
- **Dependencies**: All Python packages bundled internally
- **Requirements**: No additional installation needed on target system

## Customization

To customize the build:

1. **Add an icon**: 
   - Add `icon='path/to/icon.ico'` in the `glados_launcher.spec` file
   
2. **Change the executable name**:
   - Modify the `name` parameter in the spec file

3. **Include additional files**:
   - Add them to the `datas` list in the spec file

## Distribution

The generated executable (`GLaDOS_Game_Launcher.exe`) can be distributed as a standalone file. Users can run it directly without needing Python installed on their system.

## Troubleshooting

- **Build fails**: Ensure all dependencies are installed in your environment
- **Runtime errors**: Check that all required modules are listed in `hiddenimports`
- **Missing files**: Add any additional data files to the `datas` section in the spec file

## Notes

- The first run may be slower as the executable extracts temporary files
- Antivirus software might flag the executable as suspicious (false positive)
- The executable includes the entire Python runtime, making it larger but fully standalone