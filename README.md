# Paulstretch GUI

A unified graphical interface for Paul's Extreme Sound Stretch (Paulstretch) audio processing scripts.

## Overview

Paulstretch GUI provides a user-friendly interface for time-stretching audio files to create ambient, atmospheric sounds. It integrates three different Paulstretch processing methods:

1. **Basic Mono**: For mono audio processing (converts stereo to mono)
2. **Stereo**: For stereo audio processing
3. **Advanced Method**: Uses onset detection for better quality stretching

## Features

- File selection for input and output WAV files
- Automatic detection of mono/stereo format
- Processing method selection
- Parameter controls with sliders:
  - Stretch Amount (1.0-50.0)
  - Window Size (0.1-1.0 seconds)
  - Onset Sensitivity (0.0-10.0, for Advanced Method only)
- Audio processing controls (Process, Stop, Preview)
- Parameter presets (Subtle, Ambient, Extreme)
- Waveform visualization
- Status bar showing current operation

## Requirements

- Python 3.6+
- wxPython 4.0+
- NumPy
- SciPy
- Matplotlib

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```
pip install -r requirements.txt
```

## Usage

1. Run the application:

```
python paulstretch_gui.py
```

2. Select an input WAV file using the "Browse..." button
3. Choose an output file location or use the default
4. Select a processing method (Basic Mono, Stereo, or Advanced Method)
5. Adjust parameters using the sliders or select a preset
6. Click "Preview" to hear a short sample of the processed audio
7. Click "Process" to process the entire file

## Parameters

- **Stretch Amount**: Controls how much the audio is stretched (1.0 = no stretch, higher values = longer)
- **Window Size**: Size of the FFT window in seconds (affects quality and character of stretching)
- **Onset Sensitivity**: (Advanced Method only) Controls how much the algorithm preserves transients (0.0 = maximum sensitivity, 10.0 = minimum)

## Presets

- **Subtle**: Light stretching (2x) with smaller window
- **Ambient**: Medium stretching (8x) with moderate window
- **Extreme**: Heavy stretching (30x) with large window

## Credits

Original Paulstretch algorithm by Nasca Octavian PAUL
http://www.paulnasca.com/ 