"""Synthesized alert tones.

Ports the Web Audio alarm chime described in dev_docs/delta.md §3 to numpy
rendering + QSoundEffect playback:

  * Alarm chime  - three overlapping oscillators: an 880Hz sine gliding down to
                   875Hz over 0.35s, a 1318.5Hz triangle starting at +80ms, and
                   a 1760Hz sine "echo" starting at +220ms.

The pure render_* helpers have no Qt dependency and are unit tested directly.
"""

import os
import tempfile
import wave

import numpy as np

SAMPLE_RATE = 44100
ALARM_DURATION = 0.75

try:
    from PyQt6.QtCore import QObject, QUrl
    from PyQt6.QtMultimedia import QSoundEffect
except Exception:  # pragma: no cover - QtMultimedia may be unavailable
    QObject = object
    QUrl = None
    QSoundEffect = None


def _time_axis(duration: float) -> np.ndarray:
    return np.arange(int(SAMPLE_RATE * duration)) / SAMPLE_RATE


def _decay_envelope(t: np.ndarray, start: float, tau: float,
                    attack: float = 0.006) -> np.ndarray:
    env = np.zeros_like(t)
    mask = t >= start
    local = t[mask] - start
    env[mask] = np.where(local < attack,
                         local / attack,
                         np.exp(-local / tau))
    return env


def _sine(phase: np.ndarray) -> np.ndarray:
    return np.sin(phase)


def _triangle(phase: np.ndarray) -> np.ndarray:
    return (2.0 / np.pi) * np.arcsin(np.sin(phase))


def render_alarm_chime() -> np.ndarray:
    """Return the alarm chime as a float array in [-1, 1]."""
    t = _time_axis(ALARM_DURATION)

    glide = 0.35
    freq = np.where(t < glide, 880.0 + (875.0 - 880.0) * (t / glide), 875.0)
    phase1 = 2.0 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    osc1 = _sine(phase1) * _decay_envelope(t, 0.0, tau=0.18)

    phase2 = 2.0 * np.pi * 1318.5 * t
    osc2 = _triangle(phase2) * _decay_envelope(t, 0.08, tau=0.16) * 0.7

    phase3 = 2.0 * np.pi * 1760.0 * t
    osc3 = _sine(phase3) * _decay_envelope(t, 0.22, tau=0.14) * 0.5

    samples = osc1 + osc2 + osc3
    return _normalize(samples, peak=0.85)


def _normalize(samples: np.ndarray, peak: float = 0.9) -> np.ndarray:
    max_abs = float(np.max(np.abs(samples))) if samples.size else 0.0
    if max_abs == 0.0:
        return samples
    return samples * (peak / max_abs)


def to_pcm16(samples: np.ndarray) -> bytes:
    clipped = np.clip(samples, -1.0, 1.0)
    return (clipped * 32767.0).astype("<i2").tobytes()


def write_wav(path: str, samples: np.ndarray,
              rate: int = SAMPLE_RATE) -> str:
    with wave.open(path, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(to_pcm16(samples))
    return path


def default_sound_dir() -> str:
    directory = os.path.join(tempfile.gettempdir(), "tos_charting_sounds")
    os.makedirs(directory, exist_ok=True)
    return directory


def ensure_sound_files(directory: str | None = None) -> dict:
    directory = directory or default_sound_dir()
    os.makedirs(directory, exist_ok=True)
    alarm_path = os.path.join(directory, "alarm_chime.wav")
    if not os.path.exists(alarm_path):
        write_wav(alarm_path, render_alarm_chime())
    return {"alarm": alarm_path}


class SoundService(QObject):
    """Lazily loads the pre-rendered tones and plays them on demand."""

    def __init__(self, enabled: bool = True, sound_dir: str | None = None):
        super().__init__()
        self._enabled = enabled
        self._sound_dir = sound_dir
        self._paths: dict | None = None
        self._alarm_effect = None

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def is_enabled(self) -> bool:
        return self._enabled

    def _paths_or_create(self) -> dict:
        if self._paths is None:
            self._paths = ensure_sound_files(self._sound_dir)
        return self._paths

    def _effect(self):
        if QSoundEffect is None or QUrl is None:
            return None
        effect = self._alarm_effect
        if effect is None:
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(self._paths_or_create()["alarm"]))
            effect.setVolume(1.0)
            self._alarm_effect = effect
        return effect

    def warm(self) -> None:
        self._paths_or_create()

    def play_alarm(self) -> None:
        if not self._enabled:
            return
        effect = self._effect()
        if effect is not None:
            effect.play()
