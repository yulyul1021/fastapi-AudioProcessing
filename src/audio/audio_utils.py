import io

import webrtcvad
import struct
import numpy as np
from scipy.io import wavfile
import speech_recognition as sr
import googletrans
from gtts import gTTS

import warnings
import os


def audio_to_text(audio):
    """
    audio -> text

    :param audio: 한국어 음성 파일
    :return: 음성 인식 결과 text
    """
    r = sr.Recognizer()
    read_audio = sr.AudioFile(audio)
    with read_audio as source:
        f = r.record(source)
    out_text = r.recognize_google(f, language="ko-KR")
    return out_text


def text_translate(in_text):
    """
    kr_text -> en_text

    :param in_text: 한국어 text
    :return: 영어로 번역된 text
    """
    translator = googletrans.Translator()
    out_text = translator.translate(in_text, dest='en').text
    return out_text


def text_to_tts(in_text):
    """
    en_text -> tts(wav file)

    :param in_text: tts로 읽을 텍스트
    :return: tts wav file
    """
    tts = gTTS(text=in_text, lang='en')
    wav_data = io.BytesIO()
    tts.write_to_fp(wav_data)
    return wav_data


'''def rename_audio_file(pk, audio_data, audio_type):
    """
    Rename the audio file associated with the AudioData model.

    :param pk: primary key of AudioData model instance
    :param audio_data: processed/original audio data of AudioData model instance
    :param audio_type: 'processed' or 'original'
    :return: None
    """
    initial_path = audio_data.path
    if audio_type == 'processed':
        audio_data.name = f"audio/processed/{pk}_processed.wav"
    else:
        audio_data.name = f"audio/original/{pk}_original.wav"
    new_path = settings.MEDIA_ROOT / audio_data.name
    os.rename(initial_path, new_path)'''

#################################################################################
#################################################################################
class WebRTCVAD:
    def __init__(self, mode=3, sr=16000):
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(mode)

        self.sample_rate = sr
        self.window_duration = 0.03  # duration in seconds
        self.samples_per_window = int(self.window_duration * self.sample_rate)
        self.bytes_per_sample = 2

    def read_audio(self, filepath):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, samples = wavfile.read(filepath)
        raw_samples = struct.pack("%dh" % len(samples), *samples)

        return raw_samples, samples

    def detect_endpoints(self, filepath):
        raw_samples, samples = self.read_audio(filepath)
        len_samples = int((len(raw_samples) // (self.samples_per_window * 2)) * self.samples_per_window)

        segments = []
        for start in np.arange(0, len_samples, self.samples_per_window):
            stop = min(start + self.samples_per_window, len_samples)

            is_speech = self.vad.is_speech(raw_samples[start * self.bytes_per_sample: stop * self.bytes_per_sample],
                                           sample_rate=self.sample_rate)
            segments.append(is_speech)

        onsets, offsets = self.calc_vad(segments)
        onsets, offsets = self.smoothing_vad(onsets, offsets)
        crop_audios = self.crop_audio(onsets, offsets, samples)
        num_audios = self.write_audio(crop_audios)
        wav_audios = self.create_wav(crop_audios)

        return num_audios, onsets, offsets, crop_audios, wav_audios

    def calc_vad(self, segments):
        onsets, offsets = [], []
        for i in range(len(segments)):
            if i == 0:
                if (segments[i] == True):
                    onset = i * self.window_duration
                    onsets.append(onset)
            elif i == int(len(segments) - 1):
                if (segments[i] == True):
                    offset = i * self.window_duration
                    offsets.append(offset)
            else:
                if (segments[i - 1] == False) and (segments[i] == True):
                    onset = i * self.window_duration
                    onsets.append(onset)
                if (segments[i - 1] == True) and (segments[i] == False):
                    offset = i * self.window_duration
                    offsets.append(offset)

        return onsets, offsets

    def smoothing_vad(self, onsets, offsets, smoothing_factor=0.3):
        num_vad = len(onsets)
        if num_vad == 1:
            return onsets, offsets

        idx = 0
        while True:
            if abs(onsets[idx + 1] - offsets[idx]) < smoothing_factor:
                del offsets[idx]
                del onsets[idx + 1]
                idx = 0
                num_vad = len(onsets)
            else:
                idx += 1
                if idx == num_vad - 1:
                    break

        return onsets, offsets

    def crop_audio(self, onsets, offsets, audio):
        num_speech = len(onsets)

        crop_audios = []
        for i in range(num_speech):
            onset_sample = int(max(onsets[i] * self.sample_rate - 0.1 * self.sample_rate, 0))
            offset_sample = int(min(offsets[i] * self.sample_rate + 0.1 * self.sample_rate, len(audio)))
            crop_audios.append(audio[onset_sample:offset_sample])

        return crop_audios

    def write_audio(self, audios):
        num_audios = len(audios)
        dir_name = "tmp"

        self.create_folder(dir_name=dir_name)
        for i in range(num_audios):
            filename = f"{dir_name}/{i:04}.wav"
            wavfile.write(filename, self.sample_rate, audios[i])

        return num_audios

    def create_wav(self, audios):
        num_audios = len(audios)
        wav_audios = []

        for i in range(num_audios):
            buffer = io.BytesIO()
            wavfile.write(buffer, self.sample_rate, audios[i])
            wav_audios.append(buffer)

        return wav_audios

    def create_folder(self, dir_name):
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)


#################################################################################
#################################################################################
import speech_recognition as sr


class SpeechRecognition:
    def __init__(self):
        self.r = sr.Recognizer()

    def recognize_korean(self, num_audios):
        dir_name = "tmp"
        texts = []
        for i in range(num_audios):
            with sr.AudioFile(f"{dir_name}/{i:04}.wav") as source:
                audio = self.r.record(source)
                texts.append(self.r.recognize_google(audio, language='ko-KR'))

        return texts