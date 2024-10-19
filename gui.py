from tkinter import filedialog

import wx
import os
from recorder import Recorder
from wx import FileDialog
from datetime import datetime
from foo import foo

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        super(MainWindow, self).__init__(parent, title=title, size=(900, 500))

        # GUI components
        panel = wx.Panel(self)
        self.dir_name = "Records"
        self.recorder = Recorder(self.dir_name)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Buttons for recording and file selection
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.change_file_button = wx.Button(panel, label="Choose File")
        self.change_file_button.Bind(wx.EVT_BUTTON, self.on_choose_file)
        button_sizer.Add(self.change_file_button, 0, wx.ALL, 5)

        self.start_recording_button = wx.Button(panel, label="Start Recording")
        self.start_recording_button.Bind(wx.EVT_BUTTON, self.on_start_recording)
        button_sizer.Add(self.start_recording_button, 0, wx.ALL, 5)

        self.stop_recording_button = wx.Button(panel, label="Stop Recording")
        self.stop_recording_button.Bind(wx.EVT_BUTTON, self.on_stop_recording)
        self.stop_recording_button.Disable()
        button_sizer.Add(self.stop_recording_button, 0, wx.ALL, 5)

        # Label to show selected file or recording info
        self.file_label = wx.StaticText(panel, label="Nothing is chosen")
        button_sizer.Add(self.file_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        main_sizer.Add(button_sizer, 0, wx.ALL, 5)
        self.output_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        main_sizer.Add(self.output_text, 1, wx.EXPAND | wx.ALL, 5)

        self.start_processing_button = wx.Button(panel, label="Start Processing")
        self.start_processing_button.Bind(wx.EVT_BUTTON, self.on_start_processing)
        self.start_processing_button.Disable()
        main_sizer.Add(self.start_processing_button, 0, wx.ALL | wx.CENTER, 5)

        panel.SetSizer(main_sizer)
        self.Show()

    def on_choose_file(self, event):
        with FileDialog(self, "Choose a .wav file", wildcard="WAV files (*.wav)|*.wav", style=wx.FD_OPEN) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_OK:
                self.selected_file = fileDialog.GetPath()
                self.file_label.SetLabel(self.selected_file)
                self.start_processing_button.Enable()

    def generate_file_name(self) -> str:
        return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    def on_start_recording(self, event):
        file_name = self.generate_file_name()
        self.start_recording_button.Disable()
        self.stop_recording_button.Enable()
        filename = file_name
        self.selected_file = self.recorder.start_recording(filename)
        self.file_label.SetLabel(self.selected_file)

    def on_stop_recording(self, event):
        self.recorder.stop_recording()
        self.start_recording_button.Enable()
        self.stop_recording_button.Disable()
        self.start_processing_button.Enable()

    def on_start_processing(self, event):
        self.output_text.AppendText("Processing started...\n")
        res = foo()
        self.output_text.AppendText(f"{res}\n")



if __name__ == "__main__":
    app = wx.App(False)
    frame = MainWindow(None, "Interkom")
    app.MainLoop()