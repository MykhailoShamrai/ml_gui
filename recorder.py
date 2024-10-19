import os
import wave
import pyaudio
import threading


class Recorder:
    def __init__(self, folderName):
        self._dest_folder = os.path.join(".", f"{folderName}")
        os.makedirs(self._dest_folder, exist_ok=True)
        self.is_recording = False
        self._chunk = 1024  # size of buffer for writing
        self._format = pyaudio.paInt16
        self._channels = 1  # Mono
        self._rate = 44100  # Sample rate
        self._audio = pyaudio.PyAudio()
        self._stream = None
        self._wave_file = None
        self._recording_thread = None

    def __record(self):
        while self.is_recording:
            data = self._stream.read(self._chunk)
            self._wave_file.writeframes(data)

    def start_recording(self, filename) -> str:
        out_file_path = os.path.join(self._dest_folder, f"{filename}.wav")
        self._wave_file = wave.open(out_file_path, 'wb')
        self._wave_file.setnchannels(self._channels)
        self._wave_file.setsampwidth(self._audio.get_sample_size(self._format))
        self._wave_file.setframerate(self._rate)

        self._stream = self._audio.open(format=self._format,
                                        channels=self._channels,
                                        rate=self._rate,
                                        input=True,
                                        frames_per_buffer=self._chunk)
        self.is_recording = True
        # launching recording on another thread
        self._recording_thread = threading.Thread(target=self.__record)
        self._recording_thread.start()
        return out_file_path

    def stop_recording(self):
        self.is_recording = False
        # wait for end of a thread with recording process
        self._recording_thread.join()

        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
            self._audio.terminate()
        if self._wave_file is not None:
            self._wave_file.close()
            self._wave_file = None
