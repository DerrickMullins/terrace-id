import io
import os
import subprocess
import tempfile

import librosa
import numpy as np

SAMPLE_RATE = 22050
DURATION    = 30
N_MFCC      = 20
VECTOR_DIM  = 104  # 40 MFCC + 40 delta-MFCC + 24 chroma


def _to_wav(audio_bytes: bytes) -> bytes:
    result = subprocess.run(
        ["ffmpeg", "-i", "pipe:0", "-ar", str(SAMPLE_RATE), "-ac", "1",
         "-f", "wav", "-loglevel", "error", "pipe:1"],
        input=audio_bytes,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg: {result.stderr.decode()}")
    return result.stdout


def extract_features(audio_bytes: bytes) -> np.ndarray:
    """104-dim vector: MFCC + delta-MFCC + chroma (mean & std of each)."""
    wav = _to_wav(audio_bytes)
    y, _ = librosa.load(io.BytesIO(wav), sr=SAMPLE_RATE, duration=DURATION)

    mfcc       = librosa.feature.mfcc(y=y, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
    delta_mfcc = librosa.feature.delta(mfcc)
    chroma     = librosa.feature.chroma_stft(y=y, sr=SAMPLE_RATE)

    return np.concatenate([
        mfcc.mean(axis=1),       mfcc.std(axis=1),
        delta_mfcc.mean(axis=1), delta_mfcc.std(axis=1),
        chroma.mean(axis=1),     chroma.std(axis=1),
    ]).astype(np.float32)


def generate_fingerprint(audio_bytes: bytes) -> str:
    """
    Generate a chromaprint fingerprint via fpcalc.
    Returns a comma-separated string of raw 32-bit integers.
    """
    wav = _to_wav(audio_bytes)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["fpcalc", "-raw", tmp_path],
            capture_output=True, text=True,
        )
        for line in result.stdout.strip().splitlines():
            if line.startswith("FINGERPRINT="):
                return line[len("FINGERPRINT="):]
        raise RuntimeError(f"fpcalc gave no fingerprint: {result.stderr}")
    finally:
        os.unlink(tmp_path)


def fingerprint_similarity(fp1: str, fp2: str) -> float:
    """
    Hamming-distance similarity between two raw chromaprint fingerprints.
    Returns 0.0 (completely different) to 1.0 (identical).
    """
    a = [int(x) for x in fp1.split(",")]
    b = [int(x) for x in fp2.split(",")]
    length = max(len(a), len(b))
    if length == 0:
        return 0.0
    # XOR on 32-bit unsigned integers; negative values need masking
    errors = sum(bin((x & 0xFFFFFFFF) ^ (y & 0xFFFFFFFF)).count("1")
                 for x, y in zip(a, b))
    return 1.0 - errors / (32 * length)
