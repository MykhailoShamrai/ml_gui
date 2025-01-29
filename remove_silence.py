import argparse
import wave

from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

def check_if_wav_is_longer(path, min_duration=3):
    try:
        with wave.open(path, 'rb') as wav_file:
            num_frames = wav_file.getnframes()
            frame_rate = wav_file.getframerate()

            duration = num_frames / float(frame_rate)

            return duration >= min_duration
    except Exception as e:
        return False



def remove_silence(input_file, output_file, min_silence_len=500, silence_thresh=-40):
    print("Loading the audio file...")
    audio = AudioSegment.from_wav(input_file)

    print("Splitting the audio based on silence...")
    chunks = split_on_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

    print("Concatenating non-silent chunks...")
    output = AudioSegment.empty()
    for chunk in chunks:
        output += chunk

    if not os.path.exists(output_file):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'wb') as f:
        pass

    print("Saving the audio file without silence parts...")
    output.export(output_file, format="wav")
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove silence from an audio file.")
    parser.add_argument("input_file", type=str, help="Path to the input WAV file.")
    parser.add_argument("output_file", type=str, help="Path to save the output WAV file.")

    args = parser.parse_args()

    remove_silence(args.input_file)