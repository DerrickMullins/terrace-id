import librosa
import requests
import io
import numpy as np

def load_audio_from_url(url):
    response = requests.get(url)
    # Wrap the byte content in a file-like object
    audio_file = io.BytesIO(response.content)
    # Load with Librosa; sr=None preserves native sampling rate
    y, sr = librosa.load(audio_file, sr=None)
    return y, sr

url = "https://www.fanchants.com/media/chants/full/download/champions-league-youre-having-a-laugh-fanchants-free.mp3"
y, sr = load_audio_from_url(url)

# 3. Run the default beat tracker
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

print('beat_frames: ', beat_frames)

# Use [0] to get the scalar value from the numpy array
print('Estimated tempo: {:.2f} beats per minute'.format(tempo[0]))

# 4. Convert the frame indices of beat events into timestamps
beat_times = librosa.frames_to_time(beat_frames, sr=sr)
