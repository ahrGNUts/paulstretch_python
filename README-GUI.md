# Paulstretch GUI

A GUI application for controlling the Paulstretch audio time-stretching Python scripts.

## Features

- Clean, modern interface
- Support for all three Paulstretch implementations:
  - Mono (Basic): Simple mono implementation
  - Stereo: Enhanced stereo implementation
  - New Method: Advanced implementation with onset detection
- Parameter adjustment sliders with presets
- Progress indicator for long processing operations
- Log/output area for process monitoring
- Drag-and-drop support for audio files
- Settings persistence between sessions

## Installation

1. Make sure you have Python 3.6 or higher installed
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python paulstretch_gui.py
```

### Quick Start

1. Select or drag-and-drop an input WAV file
2. Choose an output location (auto-generated when you select an input file)
3. Select which Paulstretch implementation to use
4. Adjust parameters:
   - Stretch Amount: Higher values create longer, more ambient sounds
   - Window Size: Affects the timbre/texture quality
   - Onset Sensitivity: (Only for New Method) Controls detection of note attacks
5. Click "Process Audio" to generate the stretched audio file

### Presets

You can save and load parameter presets:
1. Set your desired parameters
2. Enter a name in the preset field
3. Click "Save Preset"
4. Load presets from the dropdown menu

### Script Implementations

- **Mono (Basic)**: Simple, efficient implementation for mono files
- **Stereo**: Better quality stereo processing
- **New Method**: Advanced implementation with onset detection, better preserves transients

## License

This application is released under the Public Domain.

## Credits

- Original Paulstretch algorithms by Nasca Octavian PAUL
- GUI application built with Kivy 