#!/usr/bin/env python
import os
import sys
import wx
import wx.adv
import threading
import scipy.io.wavfile
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

# Import the paulstretch modules
import paulstretch_mono
import paulstretch_stereo
import paulstretch_newmethod
from paulstretch_stdout_redirect import StdoutRedirector

class PaulstretchFrame(wx.Frame):
    def __init__(self, parent=None, title="Paulstretch Audio Processor"):
        super(PaulstretchFrame, self).__init__(parent, title=title, size=(900, 900))
        
        self.processing_thread = None
        self.is_processing = False
        
        # Track previous slider values
        self.prev_stretch_value = 0
        self.prev_window_value = 0
        self.prev_onset_value = 0
        
        # Set up the main panel and sizer
        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create the file selection area
        file_sizer = self.create_file_section()
        main_sizer.Add(file_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Create the script selection area
        script_sizer = self.create_script_section()
        main_sizer.Add(script_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Create the parameter controls
        params_sizer = self.create_parameter_section()
        main_sizer.Add(params_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Create the audio visualization
        viz_sizer = self.create_visualization_section()
        main_sizer.Add(viz_sizer, 1, wx.EXPAND | wx.ALL, 10)
        
        # Create the processing controls
        process_sizer = self.create_process_section()
        main_sizer.Add(process_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Create the status bar
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText("Ready")
        
        # Set up the panel sizer
        self.panel.SetSizer(main_sizer)
        self.panel.Layout()
        
        # Bind the close event
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        # Set up stdout redirector for progress updates
        self.stdout_redirector = StdoutRedirector(self.update_progress)
        
        # Final setup
        self.Centre()
        self.Show()
        wx.CallAfter(self.bring_to_front)
        
    def bring_to_front(self):
        self.Raise()
        self.SetFocus()
        # On macOS, this is particularly effective
        if self.IsIconized():
            self.Iconize(False)
        self.RequestUserAttention()
    
    def create_file_section(self):
        """Create the file selection section of the UI"""
        sizer = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "File Selection")
        
        # Input file selection
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        input_label = wx.StaticText(self.panel, label="Input File:")
        self.input_text = wx.TextCtrl(self.panel)
        browse_input_btn = wx.Button(self.panel, label="Browse...")
        
        input_sizer.Add(input_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        input_sizer.Add(self.input_text, 1, wx.EXPAND)
        input_sizer.Add(browse_input_btn, 0, wx.LEFT, 5)
        
        # Output file selection
        output_sizer = wx.BoxSizer(wx.HORIZONTAL)
        output_label = wx.StaticText(self.panel, label="Output File:")
        self.output_text = wx.TextCtrl(self.panel)
        browse_output_btn = wx.Button(self.panel, label="Browse...")
        
        output_sizer.Add(output_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        output_sizer.Add(self.output_text, 1, wx.EXPAND)
        output_sizer.Add(browse_output_btn, 0, wx.LEFT, 5)
        
        # File format indicator
        format_sizer = wx.BoxSizer(wx.HORIZONTAL)
        format_label = wx.StaticText(self.panel, label="File Format:")
        self.format_text = wx.StaticText(self.panel, label="No file selected")
        
        format_sizer.Add(format_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        format_sizer.Add(self.format_text, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Add all to main sizer
        sizer.Add(input_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(output_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(format_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Bind events
        browse_input_btn.Bind(wx.EVT_BUTTON, self.on_browse_input)
        browse_output_btn.Bind(wx.EVT_BUTTON, self.on_browse_output)
        
        return sizer
    
    def create_script_section(self):
        """Create the script selection section of the UI"""
        sizer = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Processing Method")
        
        # Radio buttons for script selection
        self.rb_mono = wx.RadioButton(self.panel, label="Basic Mono", style=wx.RB_GROUP)
        self.rb_stereo = wx.RadioButton(self.panel, label="Stereo")
        self.rb_advanced = wx.RadioButton(self.panel, label="Advanced Method")
        
        # Add tooltips
        self.rb_mono.SetToolTip("Process mono audio files (converts stereo to mono)")
        self.rb_stereo.SetToolTip("Process stereo audio files")
        self.rb_advanced.SetToolTip("Use advanced method with onset detection")
        
        # Add to sizer
        sizer.Add(self.rb_mono, 0, wx.ALL, 5)
        sizer.Add(self.rb_stereo, 0, wx.ALL, 5)
        sizer.Add(self.rb_advanced, 0, wx.ALL, 5)
        
        # Bind events
        self.rb_mono.Bind(wx.EVT_RADIOBUTTON, self.on_method_changed)
        self.rb_stereo.Bind(wx.EVT_RADIOBUTTON, self.on_method_changed)
        self.rb_advanced.Bind(wx.EVT_RADIOBUTTON, self.on_method_changed)
        
        return sizer
    
    def create_parameter_section(self):
        """Create the parameter controls section of the UI"""
        sizer = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Parameters")
        
        # Preset dropdown
        preset_sizer = wx.BoxSizer(wx.HORIZONTAL)
        preset_label = wx.StaticText(self.panel, label="Preset:")
        self.preset_combo = wx.Choice(self.panel, choices=["Custom", "Subtle", "Ambient", "Extreme"])
        self.preset_combo.SetSelection(0)
        
        preset_sizer.Add(preset_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        preset_sizer.Add(self.preset_combo, 1)
        
        # Stretch Amount slider
        stretch_sizer = wx.BoxSizer(wx.VERTICAL)
        stretch_label = wx.StaticText(self.panel, label="Stretch Amount:")
        stretch_label.SetToolTip("Amount of time stretching (1.0 = no stretch)")
        self.stretch_slider = wx.Slider(self.panel, value=80, minValue=10, maxValue=500)
        self.stretch_text = wx.StaticText(self.panel, label="8.0")
        
        stretch_ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        stretch_ctrl_sizer.Add(self.stretch_slider, 1, wx.EXPAND)
        stretch_ctrl_sizer.Add(self.stretch_text, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        
        stretch_sizer.Add(stretch_label, 0)
        stretch_sizer.Add(stretch_ctrl_sizer, 0, wx.EXPAND)
        
        # Window Size slider
        window_sizer = wx.BoxSizer(wx.VERTICAL)
        window_label = wx.StaticText(self.panel, label="Window Size (seconds):")
        window_label.SetToolTip("Size of the processing window in seconds")
        self.window_slider = wx.Slider(self.panel, value=25, minValue=10, maxValue=100)
        self.window_text = wx.StaticText(self.panel, label="0.25")
        
        window_ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        window_ctrl_sizer.Add(self.window_slider, 1, wx.EXPAND)
        window_ctrl_sizer.Add(self.window_text, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        
        window_sizer.Add(window_label, 0)
        window_sizer.Add(window_ctrl_sizer, 0, wx.EXPAND)
        
        # Onset Sensitivity slider (only for advanced method)
        onset_sizer = wx.BoxSizer(wx.VERTICAL)
        onset_label = wx.StaticText(self.panel, label="Onset Sensitivity:")
        onset_label.SetToolTip("Sensitivity to audio onsets (0.0=max, 10.0=min)")
        self.onset_slider = wx.Slider(self.panel, value=100, minValue=0, maxValue=100)
        self.onset_text = wx.StaticText(self.panel, label="10.0")
        
        onset_ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        onset_ctrl_sizer.Add(self.onset_slider, 1, wx.EXPAND)
        onset_ctrl_sizer.Add(self.onset_text, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        
        onset_sizer.Add(onset_label, 0)
        onset_sizer.Add(onset_ctrl_sizer, 0, wx.EXPAND)
        
        # Add all to main sizer
        sizer.Add(preset_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(stretch_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(window_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(onset_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Bind events
        self.stretch_slider.Bind(wx.EVT_SLIDER, self.on_stretch_changed)
        self.window_slider.Bind(wx.EVT_SLIDER, self.on_window_changed)
        self.onset_slider.Bind(wx.EVT_SLIDER, self.on_onset_changed)
        self.preset_combo.Bind(wx.EVT_CHOICE, self.on_preset_changed)
        
        # Initially disable onset sensitivity for non-advanced methods
        self.onset_slider.Enable(False)
        self.onset_text.Enable(False)
        
        return sizer
    
    def create_visualization_section(self):
        """Create the audio visualization section"""
        sizer = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Audio Visualization")
        
        # Create matplotlib figure for waveform visualization
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.canvas = FigureCanvas(self.panel, -1, self.figure)
        
        # Initially, show a placeholder
        self.axes = self.figure.add_subplot(111)
        self.axes.set_title("Load an audio file to view waveform")
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        
        sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 5)
        
        return sizer
    
    def create_process_section(self):
        """Create the processing controls section"""
        sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self.panel, "Processing")
        
        # Processing buttons
        self.process_btn = wx.Button(self.panel, label="Process")
        self.stop_btn = wx.Button(self.panel, label="Stop")
        self.preview_btn = wx.Button(self.panel, label="Preview")
        
        # Progress indicator
        self.progress = wx.Gauge(self.panel, range=100)
        
        # Add to sizer
        sizer.Add(self.process_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(self.stop_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(self.preview_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(self.progress, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        # Bind events
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_process)
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop)
        self.preview_btn.Bind(wx.EVT_BUTTON, self.on_preview)
        
        # Initially disable the stop button
        self.stop_btn.Enable(False)
        
        return sizer
    
    def on_browse_input(self, event):
        """Handle input file browsing"""
        dlg = wx.FileDialog(
            self, message="Choose an input file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="WAV files (*.wav)|*.wav",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            self.input_text.SetValue(filepath)
            
            # Set a default output filename
            input_dir = os.path.dirname(filepath)
            input_basename = os.path.basename(filepath)
            input_name, input_ext = os.path.splitext(input_basename)
            output_path = os.path.join(input_dir, f"{input_name}_stretched.wav")
            self.output_text.SetValue(output_path)
            
            # Detect file format (mono/stereo)
            self.detect_file_format(filepath)
            
            # Load and display waveform
            self.load_waveform(filepath)
        
        dlg.Destroy()
    
    def on_browse_output(self, event):
        """Handle output file browsing"""
        dlg = wx.FileDialog(
            self, message="Choose an output file",
            defaultDir=os.path.dirname(self.output_text.GetValue()) if self.output_text.GetValue() else os.getcwd(),
            defaultFile=os.path.basename(self.output_text.GetValue()) if self.output_text.GetValue() else "",
            wildcard="WAV files (*.wav)|*.wav",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            # Ensure it has a .wav extension
            if not filepath.lower().endswith('.wav'):
                filepath += '.wav'
            self.output_text.SetValue(filepath)
        
        dlg.Destroy()
    
    def detect_file_format(self, filepath):
        """Detect if the audio file is mono or stereo"""
        try:
            wavedata = scipy.io.wavfile.read(filepath)
            smp = wavedata[1]
            
            if len(smp.shape) > 1:
                channels = smp.shape[1]
                self.format_text.SetLabel(f"Stereo ({channels} channels)")
                # Auto-select stereo processing for stereo files
                self.rb_stereo.SetValue(True)
            else:
                self.format_text.SetLabel("Mono (1 channel)")
                # Auto-select mono processing for mono files
                self.rb_mono.SetValue(True)
            
            self.on_method_changed(None)
            
        except Exception as e:
            self.format_text.SetLabel(f"Error: {str(e)}")
    
    def load_waveform(self, filepath):
        """Load and display the waveform of the audio file"""
        try:
            samplerate, data = scipy.io.wavfile.read(filepath)
            
            # Convert to mono for display if stereo
            if len(data.shape) > 1:
                display_data = data.mean(axis=1)
            else:
                display_data = data
            
            # Normalize for display
            display_data = display_data / (2.0**15)
            
            # Downsample if too many samples
            if len(display_data) > 10000:
                display_data = display_data[::len(display_data)//10000]
            
            # Clear the figure and plot the waveform
            self.figure.clear()
            self.axes = self.figure.add_subplot(111)
            self.axes.plot(display_data)
            self.axes.set_title("Input Waveform")
            self.axes.set_ylim(-1, 1)
            self.axes.set_xticks([])
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            self.statusbar.SetStatusText(f"Error loading waveform: {str(e)}")
    
    def on_method_changed(self, event):
        """Handle changes to the processing method selection"""
        if self.rb_advanced.GetValue():
            self.onset_slider.Enable(True)
            self.onset_text.Enable(True)
        else:
            self.onset_slider.Enable(False)
            self.onset_text.Enable(False)
    
    def on_stretch_changed(self, event):
        """Handle changes to the stretch amount slider"""
        current_value = self.stretch_slider.GetValue()
        value = current_value / 10.0
        self.stretch_text.SetLabel(f"{value:.1f}")
        
        # Set preset to Custom only if value actually changed
        if event is not None and current_value != self.prev_stretch_value:
            self.preset_combo.SetSelection(0)
            
        # Update previous value
        self.prev_stretch_value = current_value
    
    def on_window_changed(self, event):
        """Handle changes to the window size slider"""
        current_value = self.window_slider.GetValue()
        value = current_value / 100.0
        self.window_text.SetLabel(f"{value:.2f}")
        
        # Set preset to Custom only if value actually changed
        if event is not None and current_value != self.prev_window_value:
            self.preset_combo.SetSelection(0)
            
        # Update previous value
        self.prev_window_value = current_value
    
    def on_onset_changed(self, event):
        """Handle changes to the onset sensitivity slider"""
        current_value = self.onset_slider.GetValue()
        value = current_value / 10.0
        self.onset_text.SetLabel(f"{value:.1f}")
        
        # Set preset to Custom only if value actually changed
        if event is not None and current_value != self.prev_onset_value:
            self.preset_combo.SetSelection(0)
            
        # Update previous value
        self.prev_onset_value = current_value
    
    def on_preset_changed(self, event):
        """Handle changes to the preset selection"""
        preset = self.preset_combo.GetSelection()
        
        if preset == 1:  # Subtle
            self.stretch_slider.SetValue(20)  # 2.0
            self.window_slider.SetValue(20)   # 0.20
            self.onset_slider.SetValue(50)    # 5.0
        elif preset == 2:  # Ambient
            self.stretch_slider.SetValue(80)  # 8.0
            self.window_slider.SetValue(30)   # 0.30
            self.onset_slider.SetValue(70)    # 7.0
        elif preset == 3:  # Extreme
            self.stretch_slider.SetValue(300) # 30.0
            self.window_slider.SetValue(50)   # 0.50
            self.onset_slider.SetValue(100)   # 10.0
        
        # Update the text labels
        self.on_stretch_changed(None)
        self.on_window_changed(None)
        self.on_onset_changed(None)
        
        # Update previous values to match current preset values
        self.prev_stretch_value = self.stretch_slider.GetValue()
        self.prev_window_value = self.window_slider.GetValue()
        self.prev_onset_value = self.onset_slider.GetValue()
    
    def update_progress(self, percentage):
        """Update the progress gauge based on stdout output"""
        wx.CallAfter(self.progress.SetValue, percentage)
        # Return True to continue processing, False to stop
        return self.is_processing
    
    def on_process(self, event):
        """Handle processing button click"""
        # Validate input parameters
        if not self.validate_parameters():
            return
        
        # Start processing in a new thread
        self.is_processing = True
        self.processing_thread = threading.Thread(target=self.process_audio)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        # Update UI
        self.process_btn.Enable(False)
        self.stop_btn.Enable(True)
        self.statusbar.SetStatusText("Processing...")
    
    def on_stop(self, event):
        """Handle stop button click"""
        if self.is_processing:
            self.is_processing = False
            # The processing thread will check this flag and terminate
            self.statusbar.SetStatusText("Stopping...")
    
    def on_preview(self, event):
        """Handle preview button click"""
        # Validate input parameters
        if not self.validate_parameters():
            return
        
        # Create a temporary file for the preview
        input_file = self.input_text.GetValue()
        temp_file = os.path.join(os.path.dirname(input_file), "preview_temp.wav")
        
        # Process a small segment (5-10 seconds) of the input file
        try:
            # Read the input file
            samplerate, data = scipy.io.wavfile.read(input_file)
            
            # Create a shorter version for preview (5 seconds)
            preview_length = min(len(data), 5 * samplerate)
            preview_data = data[:preview_length]
            
            # Write the preview segment to a temporary file
            scipy.io.wavfile.write(temp_file, samplerate, preview_data)
            
            # Process the preview
            self.statusbar.SetStatusText("Generating preview...")
            
            # Start preview processing in a new thread
            threading.Thread(
                target=self.preview_audio, 
                args=(temp_file,)
            ).start()
            
        except Exception as e:
            self.statusbar.SetStatusText(f"Preview error: {str(e)}")
    
    def preview_audio(self, temp_file):
        """Process and play a preview of the audio"""
        preview_output = os.path.join(os.path.dirname(temp_file), "preview_output.wav")
        
        # Get the current parameters
        stretch = float(self.stretch_text.GetLabel())
        window_size = float(self.window_text.GetLabel())
        onset = float(self.onset_text.GetLabel()) if self.rb_advanced.GetValue() else 10.0
        
        # Process the preview file
        method = "mono"
        if self.rb_stereo.GetValue():
            method = "stereo"
        elif self.rb_advanced.GetValue():
            method = "advanced"
        
        try:
            # Redirect stdout to capture progress
            with self.stdout_redirector:
                if method == "mono":
                    samplerate, smp = paulstretch_mono.load_wav(temp_file)
                    paulstretch_mono.paulstretch(samplerate, smp, stretch, window_size, preview_output)
                elif method == "stereo":
                    samplerate, smp = paulstretch_stereo.load_wav(temp_file)
                    paulstretch_stereo.paulstretch(samplerate, smp, stretch, window_size, preview_output)
                else:  # advanced
                    samplerate, smp = paulstretch_newmethod.load_wav(temp_file)
                    # Ensure onset is a float, not an int
                    paulstretch_newmethod.paulstretch(samplerate, smp, stretch, window_size, float(onset), preview_output)
            
            # Play the preview
            wx.CallAfter(self.statusbar.SetStatusText, "Playing preview...")
            
            # Use platform-specific commands to play audio
            if sys.platform == "win32":
                os.system(f'start {preview_output}')
            elif sys.platform == "darwin":  # macOS
                os.system(f'afplay "{preview_output}"')
            else:  # Linux and others
                os.system(f'aplay "{preview_output}"')
            
            wx.CallAfter(self.statusbar.SetStatusText, "Preview complete")
            
            # Clean up temporary files
            try:
                os.remove(temp_file)
                os.remove(preview_output)
            except:
                pass
                
        except Exception as e:
            wx.CallAfter(self.statusbar.SetStatusText, f"Preview error: {str(e)}")
    
    def validate_parameters(self):
        """Validate all parameters before processing"""
        # Check if input file exists
        input_file = self.input_text.GetValue()
        if not input_file or not os.path.exists(input_file):
            wx.MessageBox("Please select a valid input file", "Error", wx.OK | wx.ICON_ERROR)
            return False
        
        # Check if output path is valid
        output_file = self.output_text.GetValue()
        if not output_file:
            wx.MessageBox("Please specify an output file", "Error", wx.OK | wx.ICON_ERROR)
            return False
        
        # Check if output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except:
                wx.MessageBox("Invalid output directory", "Error", wx.OK | wx.ICON_ERROR)
                return False
        
        return True
    
    def process_audio(self):
        """Process the audio file with the selected method and parameters"""
        input_file = self.input_text.GetValue()
        output_file = self.output_text.GetValue()
        
        # Get the processing parameters
        stretch = float(self.stretch_text.GetLabel())
        window_size = float(self.window_text.GetLabel())
        onset = float(self.onset_text.GetLabel()) if self.rb_advanced.GetValue() else 10.0
        
        # Determine which method to use
        method = "mono"
        if self.rb_stereo.GetValue():
            method = "stereo"
        elif self.rb_advanced.GetValue():
            method = "advanced"
        
        try:
            # Redirect stdout to capture progress
            with self.stdout_redirector:
                # Process the file with the appropriate method
                if method == "mono":
                    samplerate, smp = paulstretch_mono.load_wav(input_file)
                    paulstretch_mono.paulstretch(samplerate, smp, stretch, window_size, output_file)
                elif method == "stereo":
                    samplerate, smp = paulstretch_stereo.load_wav(input_file)
                    paulstretch_stereo.paulstretch(samplerate, smp, stretch, window_size, output_file)
                else:  # advanced
                    samplerate, smp = paulstretch_newmethod.load_wav(input_file)
                    # Ensure onset is a float, not an int
                    paulstretch_newmethod.paulstretch(samplerate, smp, stretch, window_size, float(onset), output_file)
            
            # Update UI on completion
            if self.is_processing:  # Only update if not manually stopped
                wx.CallAfter(self.statusbar.SetStatusText, "Processing complete")
                wx.CallAfter(wx.MessageBox, "Processing complete", "Success", wx.OK | wx.ICON_INFORMATION)
            
        except Exception as e:
            wx.CallAfter(self.statusbar.SetStatusText, f"Processing error: {str(e)}")
            wx.CallAfter(wx.MessageBox, f"Error during processing: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
        
        finally:
            # Reset UI state
            self.is_processing = False
            wx.CallAfter(self.process_btn.Enable, True)
            wx.CallAfter(self.stop_btn.Enable, False)
            wx.CallAfter(self.progress.SetValue, 0)
    
    def on_close(self, event):
        """Handle window close event"""
        # If processing is active, show confirmation dialog
        if self.is_processing:
            dlg = wx.MessageDialog(
                self,
                "Processing is still active. Are you sure you want to close the application?",
                "Confirm Close",
                wx.YES_NO | wx.ICON_QUESTION
            )
            result = dlg.ShowModal()
            dlg.Destroy()
            
            # If user clicked No, abort closing
            if result == wx.ID_NO:
                event.Veto()
                return
        
        # Stop any ongoing processing
        self.is_processing = False
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(1.0)  # Wait for the thread to terminate, with timeout
        
        # Destroy the window
        self.Destroy()

if __name__ == "__main__":
    app = wx.App(False)
    frame = PaulstretchFrame()
    app.MainLoop() 