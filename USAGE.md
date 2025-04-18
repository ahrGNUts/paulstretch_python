# Paulstretch Usage Guide

## Table of Contents
- [Paulstretch Usage Guide](#paulstretch-usage-guide)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Requirements](#requirements)
  - [Using Virtual Environment (Recommended)](#using-virtual-environment-recommended)
    - [Setup](#setup)
    - [Usage](#usage)
  - [Usage](#usage-1)
    - [paulstretch\_mono.py](#paulstretch_monopy)
    - [paulstretch\_stereo.py](#paulstretch_stereopy)
      - [Options:](#options)
      - [Example:](#example)
    - [paulstretch\_newmethod.py](#paulstretch_newmethodpy)
      - [Options:](#options-1)
      - [Example:](#example-1)
  - [Parameters Explained](#parameters-explained)
    - [Stretch Amount (`-s`, `--stretch`)](#stretch-amount--s---stretch)
    - [Window Size (`-w`, `--window_size`)](#window-size--w---window_size)
    - [Onset Sensitivity (`-t`, `--onset`) (only in paulstretch\_newmethod.py)](#onset-sensitivity--t---onset-only-in-paulstretch_newmethodpy)
  - [Tips for Best Results](#tips-for-best-results)
  - [License](#license)
  - [References](#references)

## Overview

Paul's Extreme Sound Stretch (Paulstretch) is an algorithm for time-stretching audio files to create ambient sounds by slowing them down dramatically without the typical pitch-shifting effects. This repository contains three Python implementations of the algorithm:

1. `paulstretch_mono.py` - Basic implementation for mono audio files
2. `paulstretch_stereo.py` - Implementation that processes stereo audio files
3. `paulstretch_newmethod.py` - Advanced implementation with onset detection

## Requirements

- Python (2.7 or 3.x)
- NumPy
- SciPy
- (Optional) Matplotlib (only for `paulstretch_newmethod.py` with plot_onsets=True)

Install dependencies:

```bash
pip install numpy scipy
# Optional
pip install matplotlib
```

## Using Virtual Environment (Recommended)

### Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv paulstretch-env
   ```

2. Activate the environment:
   - On macOS/Linux:
     ```bash
     source paulstretch-env/bin/activate
     ```
   - On Windows:
     ```bash
     paulstretch-env\Scripts\activate
     ```

3. Install dependencies from the requirements.txt file:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

1. Ensure your virtual environment is activated (you'll see `(paulstretch-env)` in your terminal prompt)
2. Run the Paulstretch scripts as described in the sections below
3. When you're done, deactivate the virtual environment:
   ```bash
   deactivate
   ```

## Usage

### paulstretch_mono.py

This is the simplest implementation that only processes mono audio files with hardcoded parameters.

```bash
python paulstretch_mono.py
```

This script expects:
- An input file named `input.wav` in the same directory
- Produces an output file named `out.wav`
- Uses fixed settings (8x stretch, 0.25s window size)

### paulstretch_stereo.py

This implementation handles stereo audio files and provides command-line options.

```bash
python paulstretch_stereo.py [options] input_wav output_wav
```

#### Options:

| Option | Long form | Description | Default |
|--------|-----------|-------------|---------|
| `-s` | `--stretch` | Stretch amount (1.0 = no stretch) | 8.0 |
| `-w` | `--window_size` | Window size in seconds | 0.25 |

#### Example:

```bash
python paulstretch_stereo.py -s 10.0 -w 0.5 input.wav output.wav
```

### paulstretch_newmethod.py

This is an improved implementation that includes onset detection for better quality stretching.

```bash
python paulstretch_newmethod.py [options] input_wav output_wav
```

#### Options:

| Option | Long form | Description | Default |
|--------|-----------|-------------|---------|
| `-s` | `--stretch` | Stretch amount (1.0 = no stretch) | 8.0 |
| `-w` | `--window_size` | Window size in seconds | 0.25 |
| `-t` | `--onset` | Onset sensitivity (0.0=max, 1.0=min) | 10.0 |

#### Example:

```bash
python paulstretch_newmethod.py -s 20.0 -w 0.3 -t 5.0 input.wav stretched_output.wav
```

## Parameters Explained

### Stretch Amount (`-s`, `--stretch`)

Controls how much to stretch the sound. For example:
- `1.0` = original length (no stretch)
- `8.0` = 8 times longer than the original
- `20.0` = 20 times longer than the original

Higher values create more ambient, drawn-out sounds.

### Window Size (`-w`, `--window_size`)

Controls the size of the processing window in seconds. This affects the quality and character of the stretched sound:
- Smaller values (e.g., `0.1`) preserve more transients but may introduce artifacts
- Larger values (e.g., `1.0`) create smoother sounds but may lose detail
- Default `0.25` is a good balance for most audio material

### Onset Sensitivity (`-t`, `--onset`) (only in paulstretch_newmethod.py)

Controls how sensitive the algorithm is to detecting onsets (attacks) in the audio:
- Lower values (closer to `0.0`) = more sensitive to onsets
- Higher values (closer to `1.0`) = less sensitive to onsets
- Default is `10.0` (low sensitivity)

## Tips for Best Results

1. Use high-quality WAV files as input
2. For extremely long stretches (>50x), use larger window sizes
3. Experiment with different window sizes to find the best sound quality
4. The newmethod implementation often produces better results for complex audio

## License

These files are released under Public Domain by Nasca Octavian PAUL.

## References

- Author's website: [http://www.paulnasca.com/](http://www.paulnasca.com/)
- Original project: [http://hypermammut.sourceforge.net/paulstretch/](http://hypermammut.sourceforge.net/paulstretch/) 