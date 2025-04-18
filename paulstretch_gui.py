#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import subprocess
import threading
from functools import partial

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.config import Config
from kivy.factory import Factory
from kivy.logger import Logger

# Configure window
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('kivy', 'window_icon', 'icon.png')

# Constants
SCRIPTS = {
    'Mono (Basic)': 'paulstretch_mono.py',
    'Stereo': 'paulstretch_stereo.py',
    'New Method (with Onset Detection)': 'paulstretch_newmethod.py'
}

DEFAULT_SETTINGS = {
    'input_path': '',
    'output_path': '',
    'selected_script': 'Stereo',
    'stretch_amount': 8.0,
    'window_size': 0.25,
    'onset_sensitivity': 10.0,
    'presets': {}
}

SETTINGS_FILE = os.path.join(os.path.expanduser('~'), '.paulstretch_gui.json')

class ToolTipButton(Button):
    tooltip_text = StringProperty('')
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Show tooltip
            tooltip = Factory.ToolTip(text=self.tooltip_text)
            tooltip.pos = (touch.x + 10, touch.y - 10)
            Window.add_widget(tooltip)
            Clock.schedule_once(lambda dt: Window.remove_widget(tooltip), 2)
        return super(ToolTipButton, self).on_touch_down(touch)

class ParameterSlider(BoxLayout):
    label_text = StringProperty('')
    min_value = NumericProperty(0.0)
    max_value = NumericProperty(100.0)
    default_value = NumericProperty(8.0)
    value = NumericProperty(8.0)
    tooltip_text = StringProperty('')
    
    def __init__(self, **kwargs):
        super(ParameterSlider, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        
        # Create label
        self.label = Label(text=self.label_text, size_hint_x=0.25)
        self.add_widget(self.label)
        
        # Create slider
        self.slider = Slider(min=self.min_value, max=self.max_value, value=self.default_value, size_hint_x=0.5)
        self.slider.bind(value=self.on_slider_value)
        self.add_widget(self.slider)
        
        # Create value input
        self.input = TextInput(text=str(self.default_value), multiline=False, size_hint_x=0.15, input_filter='float')
        self.input.bind(text=self.on_text_value)
        self.add_widget(self.input)
        
        # Create info button for tooltip
        self.info_btn = Button(text='?', size_hint_x=0.1)
        self.info_btn.bind(on_press=self.show_tooltip)
        self.add_widget(self.info_btn)
    
    def on_slider_value(self, instance, value):
        self.value = value
        self.input.text = f"{value:.2f}"
    
    def on_text_value(self, instance, text):
        try:
            value = float(text)
            if self.min_value <= value <= self.max_value:
                self.value = value
                self.slider.value = value
        except ValueError:
            pass
    
    def show_tooltip(self, instance):
        tooltip = Factory.ToolTip(text=self.tooltip_text)
        tooltip.pos = (instance.x + instance.width + 10, instance.y)
        Window.add_widget(tooltip)
        Clock.schedule_once(lambda dt: Window.remove_widget(tooltip), 2)
    
    def set_value(self, value):
        self.value = value
        self.slider.value = value
        self.input.text = f"{value:.2f}"

class FileSelectorWidget(BoxLayout):
    file_path = StringProperty('')
    label_text = StringProperty('File Path:')
    
    def __init__(self, **kwargs):
        super(FileSelectorWidget, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        
        # Create label
        self.label = Label(text=self.label_text, size_hint_x=0.2)
        self.add_widget(self.label)
        
        # Create text input for path
        self.text_input = TextInput(text=self.file_path, multiline=False, size_hint_x=0.6)
        self.text_input.bind(text=self.on_text)
        self.add_widget(self.text_input)
        
        # Create browse button
        self.browse_btn = Button(text='Browse', size_hint_x=0.2)
        self.browse_btn.bind(on_press=self.show_file_browser)
        self.add_widget(self.browse_btn)
    
    def on_text(self, instance, value):
        self.file_path = value
    
    def show_file_browser(self, instance):
        # Create file chooser layout
        content = BoxLayout(orientation='vertical')
        
        if self.label_text.startswith('Input'):
            # For input, use a file chooser
            file_chooser = FileChooserListView(filters=['*.wav'], path=os.path.expanduser('~'))
            select_btn = Button(text='Select', size_hint_y=None, height=50)
            
            def select_file(btn):
                if file_chooser.selection:
                    self.file_path = file_chooser.selection[0]
                    self.text_input.text = self.file_path
                popup.dismiss()
            
            select_btn.bind(on_press=select_file)
        else:
            # For output, use a file chooser and text input for filename
            file_chooser = FileChooserListView(path=os.path.expanduser('~'))
            
            filename_layout = BoxLayout(size_hint_y=None, height=50)
            filename_layout.add_widget(Label(text='Filename:', size_hint_x=0.3))
            filename_input = TextInput(text='out.wav', multiline=False, size_hint_x=0.7)
            filename_layout.add_widget(filename_input)
            
            select_btn = Button(text='Save As', size_hint_y=None, height=50)
            
            def select_output(btn):
                if file_chooser.selection:
                    directory = os.path.dirname(file_chooser.selection[0])
                else:
                    directory = file_chooser.path
                
                output_path = os.path.join(directory, filename_input.text)
                self.file_path = output_path
                self.text_input.text = output_path
                popup.dismiss()
            
            select_btn.bind(on_press=select_output)
            content.add_widget(filename_layout)
        
        content.add_widget(file_chooser)
        
        buttons = BoxLayout(size_hint_y=None, height=50)
        
        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        
        buttons.add_widget(select_btn)
        buttons.add_widget(cancel_btn)
        
        content.add_widget(buttons)
        
        popup = Popup(title='File Browser', content=content, size_hint=(0.9, 0.9))
        popup.open()

class LogArea(ScrollView):
    log_text = StringProperty('')
    
    def __init__(self, **kwargs):
        super(LogArea, self).__init__(**kwargs)
        # Label is already defined in the KV file, don't add it again here
    
    def _set_label_height(self, instance, size):
        instance.height = size[1]
    
    def append_log(self, text):
        self.log_text += text + '\n'

class PaulstretchGUI(BoxLayout):
    input_selector = ObjectProperty(None)
    output_selector = ObjectProperty(None)
    script_spinner = ObjectProperty(None)
    stretch_slider = ObjectProperty(None)
    window_slider = ObjectProperty(None)
    onset_slider = ObjectProperty(None)
    process_btn = ObjectProperty(None)
    log_area = ObjectProperty(None)
    progress_bar = ObjectProperty(None)
    preset_spinner = ObjectProperty(None)
    preset_name = ObjectProperty(None)
    
    settings = DEFAULT_SETTINGS.copy()
    
    def __init__(self, **kwargs):
        super(PaulstretchGUI, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [10, 10, 10, 10]
        self.spacing = 10
        
        # Load settings
        self.load_settings()
        
        # Set up drag and drop
        Window.bind(on_dropfile=self._on_dropfile)
        
        # Build UI
        self._build_ui()
        
        # Update UI based on loaded settings
        self._update_ui_from_settings()
    
    def _build_ui(self):
        # File selection area
        file_area = BoxLayout(orientation='vertical', size_hint_y=0.2, spacing=5)
        
        self.input_selector = FileSelectorWidget(label_text='Input File:')
        file_area.add_widget(self.input_selector)
        
        self.output_selector = FileSelectorWidget(label_text='Output File:')
        file_area.add_widget(self.output_selector)
        
        self.add_widget(file_area)
        
        # Script selection and parameters area
        param_area = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=5)
        
        # Script selection
        script_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2)
        script_layout.add_widget(Label(text='Script:', size_hint_x=0.2))
        self.script_spinner = Spinner(text='Stereo', values=list(SCRIPTS.keys()), size_hint_x=0.8)
        self.script_spinner.bind(text=self.on_script_selected)
        script_layout.add_widget(self.script_spinner)
        param_area.add_widget(script_layout)
        
        # Parameter sliders
        self.stretch_slider = ParameterSlider(
            label_text='Stretch Amount:',
            min_value=1.0,
            max_value=100.0,
            default_value=8.0,
            tooltip_text='Amount to stretch the audio (1.0 = no stretch)')
        param_area.add_widget(self.stretch_slider)
        
        self.window_slider = ParameterSlider(
            label_text='Window Size:',
            min_value=0.1,
            max_value=1.0,
            default_value=0.25,
            tooltip_text='Size of the processing window in seconds')
        param_area.add_widget(self.window_slider)
        
        self.onset_slider = ParameterSlider(
            label_text='Onset Sensitivity:',
            min_value=0.0,
            max_value=20.0,
            default_value=10.0,
            tooltip_text='Sensitivity to detect onsets (0.0=max, 20.0=min)')
        param_area.add_widget(self.onset_slider)
        
        self.add_widget(param_area)
        
        # Presets area
        preset_area = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=5)
        
        preset_layout = BoxLayout(orientation='horizontal', size_hint_x=0.7)
        preset_layout.add_widget(Label(text='Preset:', size_hint_x=0.2))
        self.preset_spinner = Spinner(text='Default', values=['Default'] + list(self.settings['presets'].keys()), size_hint_x=0.5)
        self.preset_spinner.bind(text=self.on_preset_selected)
        preset_layout.add_widget(self.preset_spinner)
        
        self.preset_name = TextInput(hint_text='Preset name', multiline=False, size_hint_x=0.3)
        preset_layout.add_widget(self.preset_name)
        
        preset_area.add_widget(preset_layout)
        
        preset_buttons = BoxLayout(orientation='horizontal', size_hint_x=0.3)
        save_preset_btn = Button(text='Save Preset')
        save_preset_btn.bind(on_press=self.save_preset)
        preset_buttons.add_widget(save_preset_btn)
        
        reset_btn = Button(text='Reset to Defaults')
        reset_btn.bind(on_press=self.reset_to_defaults)
        preset_buttons.add_widget(reset_btn)
        
        preset_area.add_widget(preset_buttons)
        self.add_widget(preset_area)
        
        # Process button and progress bar
        process_area = BoxLayout(orientation='vertical', size_hint_y=0.1, spacing=5)
        
        self.process_btn = Button(text='Process Audio', size_hint_y=0.7)
        self.process_btn.bind(on_press=self.process_audio)
        process_area.add_widget(self.process_btn)
        
        self.progress_bar = ProgressBar(max=100, size_hint_y=0.3)
        process_area.add_widget(self.progress_bar)
        
        self.add_widget(process_area)
        
        # Log area
        log_container = BoxLayout(orientation='vertical', size_hint_y=0.2)
        label = Label(text='Output Log:', size_hint_y=0.1, halign='left')
        label.bind(size=lambda *x: setattr(label, 'text_size', (label.width, None)))
        log_container.add_widget(label)
        
        self.log_area = LogArea(size_hint_y=0.9)
        log_container.add_widget(self.log_area)
        
        self.add_widget(log_container)
        
        # Update visibility of onset slider based on selected script
        self.update_parameters_visibility()
    
    def on_script_selected(self, spinner, text):
        self.settings['selected_script'] = text
        self.update_parameters_visibility()
        self.save_settings()
    
    def update_parameters_visibility(self):
        # Show/hide onset slider based on the selected script
        if self.settings['selected_script'] == 'New Method (with Onset Detection)':
            self.onset_slider.opacity = 1
            self.onset_slider.disabled = False
            self.onset_slider.height = self.stretch_slider.height
        else:
            self.onset_slider.opacity = 0
            self.onset_slider.disabled = True
            self.onset_slider.height = 0
    
    def on_preset_selected(self, spinner, text):
        if text == 'Default':
            self.reset_to_defaults(None)
        elif text in self.settings['presets']:
            preset = self.settings['presets'][text]
            self.script_spinner.text = preset['selected_script']
            self.stretch_slider.set_value(preset['stretch_amount'])
            self.window_slider.set_value(preset['window_size'])
            self.onset_slider.set_value(preset['onset_sensitivity'])
            self.update_parameters_visibility()
    
    def save_preset(self, instance):
        preset_name = self.preset_name.text.strip()
        if not preset_name:
            self.log_area.append_log("Please enter a preset name")
            return
        
        preset = {
            'selected_script': self.script_spinner.text,
            'stretch_amount': self.stretch_slider.value,
            'window_size': self.window_slider.value,
            'onset_sensitivity': self.onset_slider.value
        }
        
        self.settings['presets'][preset_name] = preset
        self.save_settings()
        
        # Update preset spinner
        current_values = self.preset_spinner.values
        if preset_name not in current_values:
            self.preset_spinner.values = current_values + [preset_name]
        
        self.log_area.append_log(f"Preset '{preset_name}' saved")
    
    def reset_to_defaults(self, instance):
        self.script_spinner.text = DEFAULT_SETTINGS['selected_script']
        self.stretch_slider.set_value(DEFAULT_SETTINGS['stretch_amount'])
        self.window_slider.set_value(DEFAULT_SETTINGS['window_size'])
        self.onset_slider.set_value(DEFAULT_SETTINGS['onset_sensitivity'])
        self.update_parameters_visibility()
    
    def _update_ui_from_settings(self):
        if self.settings['input_path']:
            self.input_selector.file_path = self.settings['input_path']
            self.input_selector.text_input.text = self.settings['input_path']
        
        if self.settings['output_path']:
            self.output_selector.file_path = self.settings['output_path']
            self.output_selector.text_input.text = self.settings['output_path']
        
        self.script_spinner.text = self.settings['selected_script']
        self.stretch_slider.set_value(self.settings['stretch_amount'])
        self.window_slider.set_value(self.settings['window_size'])
        self.onset_slider.set_value(self.settings['onset_sensitivity'])
        
        # Update preset spinner
        presets = list(self.settings['presets'].keys())
        if presets:
            self.preset_spinner.values = ['Default'] + presets
        
        self.update_parameters_visibility()
    
    def _on_dropfile(self, window, file_path):
        file_path = file_path.decode('utf-8')
        if file_path.lower().endswith('.wav'):
            self.input_selector.file_path = file_path
            self.input_selector.text_input.text = file_path
            
            # Auto-generate output path
            dir_name = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            name, ext = os.path.splitext(file_name)
            output_path = os.path.join(dir_name, f"{name}_stretched{ext}")
            
            self.output_selector.file_path = output_path
            self.output_selector.text_input.text = output_path
            
            self.settings['input_path'] = file_path
            self.settings['output_path'] = output_path
            self.save_settings()
            
            self.log_area.append_log(f"Loaded file: {file_path}")
    
    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    loaded_settings = json.load(f)
                    # Update default settings with loaded settings
                    self.settings.update(loaded_settings)
        except Exception as e:
            Logger.error(f"Failed to load settings: {e}")
    
    def save_settings(self):
        # Update settings from UI
        self.settings['input_path'] = self.input_selector.file_path
        self.settings['output_path'] = self.output_selector.file_path
        self.settings['selected_script'] = self.script_spinner.text
        self.settings['stretch_amount'] = self.stretch_slider.value
        self.settings['window_size'] = self.window_slider.value
        self.settings['onset_sensitivity'] = self.onset_slider.value
        
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f)
        except Exception as e:
            Logger.error(f"Failed to save settings: {e}")
            self.log_area.append_log(f"Error saving settings: {e}")
    
    def _parse_progress(self, line):
        if "%" in line:
            try:
                percentage = int(line.strip().replace("%", ""))
                Clock.schedule_once(partial(self._update_progress, percentage), 0)
            except:
                pass
    
    def _update_progress(self, percentage, dt):
        self.progress_bar.value = percentage
    
    def process_audio(self, instance):
        input_path = self.input_selector.file_path
        output_path = self.output_selector.file_path
        
        if not input_path or not os.path.exists(input_path):
            self.log_area.append_log("Error: Input file does not exist")
            return
        
        if not output_path:
            self.log_area.append_log("Error: Output file path not specified")
            return
        
        # Save current settings
        self.save_settings()
        
        # Disable process button during processing
        self.process_btn.disabled = True
        
        # Reset progress bar
        self.progress_bar.value = 0
        
        # Prepare command
        script_name = SCRIPTS[self.script_spinner.text]
        stretch_amount = self.stretch_slider.value
        window_size = self.window_slider.value
        
        # Build command based on selected script
        if script_name == 'paulstretch_mono.py':
            # This script doesn't use command line arguments, so we need to modify it temporarily
            self._process_mono_script(input_path, output_path, stretch_amount, window_size)
        else:
            cmd = ['python', script_name, '-s', str(stretch_amount), '-w', str(window_size)]
            
            # Add onset parameter if using new method
            if script_name == 'paulstretch_newmethod.py':
                onset_sensitivity = self.onset_slider.value
                cmd.extend(['-t', str(onset_sensitivity)])
            
            # Add input and output files
            cmd.extend([input_path, output_path])
            
            self.log_area.append_log(f"Running: {' '.join(cmd)}")
            
            # Start processing in a separate thread
            threading.Thread(target=self._run_process, args=(cmd,)).start()
    
    def _process_mono_script(self, input_path, output_path, stretch_amount, window_size):
        """Special handling for mono script which doesn't use command line args"""
        import tempfile
        
        # Create a temporary modified version of the script
        temp_script = tempfile.NamedTemporaryFile(delete=False, suffix='.py')
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'paulstretch_mono.py')
        
        try:
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Replace the hardcoded parameters
            modified_content = content.replace(
                '(samplerate,smp)=load_wav("input.wav")',
                f'(samplerate,smp)=load_wav("{input_path}")'
            )
            modified_content = modified_content.replace(
                'paulstretch(samplerate,smp,8.0,0.25,"out.wav")',
                f'paulstretch(samplerate,smp,{stretch_amount},{window_size},"{output_path}")'
            )
            
            with open(temp_script.name, 'w') as f:
                f.write(modified_content)
            
            cmd = ['python', temp_script.name]
            self.log_area.append_log(f"Running modified mono script with: stretch={stretch_amount}, window_size={window_size}")
            
            # Start processing in a separate thread
            threading.Thread(target=self._run_process, args=(cmd, temp_script.name)).start()
            
        except Exception as e:
            self.log_area.append_log(f"Error preparing mono script: {e}")
            self.process_btn.disabled = False
    
    def _run_process(self, cmd, temp_file=None):
        try:
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitor output for progress updates
            for line in iter(process.stdout.readline, ''):
                Clock.schedule_once(partial(self._append_log, line.strip()), 0)
                self._parse_progress(line)
            
            # Get any errors
            for line in iter(process.stderr.readline, ''):
                Clock.schedule_once(partial(self._append_log, f"ERROR: {line.strip()}"), 0)
            
            # Wait for the process to finish
            process.wait()
            
            if process.returncode == 0:
                Clock.schedule_once(lambda dt: self._append_log("Processing completed successfully"), 0)
            else:
                Clock.schedule_once(lambda dt: self._append_log(f"Processing failed with code {process.returncode}"), 0)
            
        except Exception as e:
            Clock.schedule_once(partial(self._append_log, f"Error during processing: {e}"), 0)
        
        finally:
            # Re-enable the process button
            Clock.schedule_once(lambda dt: setattr(self.process_btn, 'disabled', False), 0)
            
            # Clean up temporary file if used
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    def _append_log(self, text, dt):
        self.log_area.append_log(text)

class PaulstretchApp(App):
    def build(self):
        self.title = 'Paulstretch Audio Processor'
        return PaulstretchGUI()

# Define the tooltip widget in kv language
Factory.register('ToolTip', cls=Popup)

if __name__ == '__main__':
    PaulstretchApp().run() 