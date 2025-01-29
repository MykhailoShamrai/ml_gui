import shutil
import threading
import torch
from PIL import Image
from pathlib import Path
import wx
import os
from recorder import Recorder
from wx import FileDialog
from datetime import datetime
from remove_noise import remove_noise_from_wav
from remove_silence import remove_silence
from remove_silence import check_if_wav_is_longer
from split_all_files import split_all_files
from save_spectrograms import save_spectrograms
from cnn import SpectrogramCNN
import torchvision.transforms as transforms
from modified_cnn import ModifiedSpectrogramCNN


def generate_file_name() -> str:
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")


def clean_directory(path_dir):
    try:
        for filename in os.listdir(path_dir):
            file_path = os.path.join(path_dir, filename)

            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    except Exception as e:
        print(f"Failed to remove content of {path_dir}. Reason: {e}")


class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        super(MainWindow, self).__init__(parent, title=title, size=(900, 500),
                                         style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER & ~wx.MAXIMIZE_BOX)
        self.device = None
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        self.model = SpectrogramCNN(num_classes=2)
        self.model_path = "best_cnn_default.pth"   # Add name of .pth file for weights from trained model in
                                                # the folder of project.
        self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()

        self.temp_dir = "./Temp"
        self.removed_noise_dirname = "RemovedNoise"
        self.removed_silence_dirname = "RemovedSilence"
        self.cut_segments_dirname = "CutSegments"
        self.spectrograms_dirname = "Spectrograms"

        # GUI components
        self.selected_file = None
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
        with FileDialog(self, "Choose a .wav file",
                        wildcard="WAV files (*.wav)|*.wav",
                        style=wx.FD_OPEN) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_OK:
                self.selected_file = fileDialog.GetPath()
                self.file_label.SetLabel(self.selected_file)
                self.start_processing_button.Enable()

    def on_start_recording(self, event):
        file_name = generate_file_name()

        self.start_recording_button.Disable()
        self.stop_recording_button.Enable()
        self.start_processing_button.Disable()
        self.change_file_button.Disable()

        filename = file_name
        self.selected_file = self.recorder.start_recording(filename)
        self.file_label.SetLabel(self.selected_file)

    def on_stop_recording(self, event):
        self.recorder.stop_recording()
        # Re-enable buttons after recording
        self.start_recording_button.Enable()
        self.stop_recording_button.Disable()
        self.start_processing_button.Enable()
        self.change_file_button.Enable()

    def on_start_processing(self, event):
        dir_path_to_cut_segments = os.path.join(self.temp_dir, self.cut_segments_dirname)
        dir_path_to_removed_silence = os.path.join(self.temp_dir, self.removed_silence_dirname)
        dir_path_to_spectrograms = os.path.join(self.temp_dir, self.spectrograms_dirname)
        dir_path_to_removed_noise = os.path.join(self.temp_dir, self.removed_noise_dirname)
        clean_directory(dir_path_to_cut_segments)
        clean_directory(dir_path_to_removed_silence)
        clean_directory(dir_path_to_spectrograms)
        clean_directory(dir_path_to_removed_noise)

        # Disable all buttons during processing

        self.change_file_button.Disable()
        self.start_recording_button.Disable()
        self.stop_recording_button.Disable()
        self.start_processing_button.Disable()

        # Start processing in a separate thread
        processing_thread = threading.Thread(target=self.process_file)
        processing_thread.start()


    def process_file(self):
        dir_path_to_cut_segments = os.path.join(self.temp_dir, self.cut_segments_dirname)
        dir_path_to_removed_silence = os.path.join(self.temp_dir, self.removed_silence_dirname)
        dir_path_to_spectrograms = os.path.join(self.temp_dir, self.spectrograms_dirname)
        try:
            # Use wx.CallAfter to safely update UI from a different thread
            wx.CallAfter(self.output_text.AppendText, "Processing started...\n")

            # Firstly, start with noise removal
            filename_without_noise = os.path.basename(self.selected_file).rsplit('.', 1)[0] + '_denoised.wav'
            file_without_noise = os.path.join(self.temp_dir, self.removed_noise_dirname, filename_without_noise)
            remove_noise_from_wav(self.selected_file,
                                  file_without_noise,
                                  noise_clip_length=1.0,
                                  noise_reduction_type='stationary',
                                  prop_decrease=1.0)

            # After that we should remove silence
            filename_without_silence = os.path.basename(self.selected_file).rsplit('.', 1)[0] + '_without_silence.wav'
            file_without_silence = os.path.join(self.temp_dir, self.removed_silence_dirname, filename_without_silence)
            remove_silence(file_without_noise, file_without_silence)



            if not check_if_wav_is_longer(file_without_silence, 3):
                wx.CallAfter(self.output_text.AppendText, "File too short or contain a lot of silence!\n")
                wx.CallAfter(self.enable_buttons)
                wx.CallAfter(clean_directory(dir_path_to_spectrograms))
                wx.CallAfter(clean_directory(dir_path_to_cut_segments))
                wx.CallAfter(clean_directory(dir_path_to_removed_silence))
                return False

            # The next step is - cutting the wav file after cleaning to 3sec segments

            split_all_files(dir_path_to_removed_silence, dir_path_to_cut_segments)

            # After - create spectrograms
            save_spectrograms(Path(dir_path_to_cut_segments), Path(dir_path_to_spectrograms))

            predictions = self.evaluate_spectrograms(dir_path_to_spectrograms)
            if predictions:
                most_common_prediction = max(set(predictions), key=predictions.count)
                if most_common_prediction == 1:
                    wx.CallAfter(self.output_text.SetDefaultStyle, wx.TextAttr(wx.Colour(0, 128, 0)))
                    wx.CallAfter(self.output_text.AppendText, f"Welcome!!!\n")
                else:
                    wx.CallAfter(self.output_text.SetDefaultStyle, wx.TextAttr(wx.Colour(128, 0, 0)))
                    wx.CallAfter(self.output_text.AppendText, "Access rejected!!!\n")
                wx.CallAfter(self.output_text.AppendText, f"Prediction Confidence: {predictions.count(most_common_prediction) / len(predictions) * 100:.2f}%\n")
                wx.CallAfter(self.output_text.SetDefaultStyle, wx.TextAttr(wx.Colour(0, 0, 0)))
            else:
                wx.CallAfter(self.output_text.AppendText, "No valid predictions found.\n")

            # Re-enable buttons after processing

            wx.CallAfter(self.enable_buttons)

        except Exception as e:
            wx.CallAfter(self.output_text.AppendText, f"Processing error: {str(e)}\n")
            wx.CallAfter(self.enable_buttons)


    def enable_buttons(self):
        self.change_file_button.Enable()
        self.start_recording_button.Enable()
        self.start_processing_button.Enable()

    def evaluate_spectrograms(self, spectrograms_dir):
        predictions = []

        # Iterate through spectrogram files
        for filename in os.listdir(spectrograms_dir):
            if filename.endswith(('.png', '.jpg', '.jpeg')):  # Adjust extensions as needed
                try:
                    # Prepare the spectrogram
                    spectrogram_path = os.path.join(spectrograms_dir, filename)
                    spectrogram = Image.open(spectrogram_path)


                    transform = transforms.Compose([
                        transforms.Resize((224, 224)),
                        transforms.Grayscale(),
                        transforms.ToTensor(),
                        transforms.Normalize(mean=[0.5], std=[0.5])
                    ])

                    spectrogram_tensor = transform(spectrogram).unsqueeze(0).to(self.device)

                    # Perform inference
                    with torch.no_grad():
                        outputs = self.model(spectrogram_tensor)
                        _, predicted = torch.max(outputs, 1)
                        predictions.append(predicted.item())

                except Exception as e:
                    wx.CallAfter(self.output_text.AppendText, f"Error processing {filename}: {str(e)}\n")

        return predictions


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainWindow(None, "Intercom")
    app.MainLoop()
