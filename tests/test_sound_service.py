"""Tests for services/sound_service.py — tone rendering and WAV output."""

import os
import wave

import numpy as np
import pytest

from services.sound_service import (
    ALARM_DURATION,
    BLIP_DURATION,
    SAMPLE_RATE,
    ensure_sound_files,
    render_alarm_chime,
    render_fill_blip,
    to_pcm16,
    write_wav,
)


class TestAlarmChime:
    def test_duration_and_range(self):
        samples = render_alarm_chime()
        assert len(samples) == pytest.approx(ALARM_DURATION * SAMPLE_RATE, abs=2)
        assert np.max(np.abs(samples)) <= 1.0

    def test_peak_normalized(self):
        samples = render_alarm_chime()
        assert np.max(np.abs(samples)) == pytest.approx(0.85, abs=0.01)

    def test_starts_silent_then_rings(self):
        samples = render_alarm_chime()
        assert abs(samples[0]) < 0.01
        assert np.max(np.abs(samples[: int(0.05 * SAMPLE_RATE)])) > 0.05

    def test_echo_arrives_late(self):
        samples = render_alarm_chime()
        third = samples[int(0.22 * SAMPLE_RATE): int(0.35 * SAMPLE_RATE)]
        first = samples[: int(0.13 * SAMPLE_RATE)]
        assert np.sqrt(np.mean(third ** 2)) > 0.0
        assert np.sqrt(np.mean(first ** 2)) > 0.0


class TestFillBlip:
    def test_duration_and_range(self):
        samples = render_fill_blip()
        assert len(samples) == pytest.approx(BLIP_DURATION * SAMPLE_RATE, abs=2)
        assert np.max(np.abs(samples)) <= 1.0

    def test_is_shorter_than_chime(self):
        assert len(render_fill_blip()) < len(render_alarm_chime())


class TestWavOutput:
    def test_write_wav_is_valid_pcm16(self, tmp_path):
        path = str(tmp_path / "tone.wav")
        write_wav(path, render_fill_blip())
        with wave.open(path, "rb") as handle:
            assert handle.getnchannels() == 1
            assert handle.getsampwidth() == 2
            assert handle.getframerate() == SAMPLE_RATE
            assert handle.getnframes() > 0

    def test_to_pcm16_clips(self):
        data = to_pcm16(np.array([2.0, -2.0, 0.0]))
        values = np.frombuffer(data, dtype="<i2")
        assert values[0] == 32767
        assert values[1] == -32767
        assert values[2] == 0


class TestEnsureSoundFiles:
    def test_creates_both_files_once(self, tmp_path):
        paths = ensure_sound_files(str(tmp_path))
        assert os.path.exists(paths["alarm"])
        assert os.path.exists(paths["fill"])
        mtime = os.path.getmtime(paths["alarm"])
        again = ensure_sound_files(str(tmp_path))
        assert again == paths
        assert os.path.getmtime(paths["alarm"]) == mtime
