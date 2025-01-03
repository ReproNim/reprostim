# SPDX-FileCopyrightText: 2024-present ReproNim <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import os
import tempfile
import time
from datetime import datetime
from enum import Enum

import numpy as np
import sounddevice as sd
from reedsolo import RSCodec
from scipy.io import wavfile
from scipy.io.wavfile import read, write

# setup logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("REPROSTIM_LOG_LEVEL", "INFO"))

######################################
# Setup psychopy audio library


# Enum for the audio libs
class AudioLib(str, Enum):
    # PsychoPy SoundDevice audio lib
    PSYCHOPY_SOUNDDEVICE = "psychopy_sounddevice"
    # PsychoPy SoundPTB audio lib
    PSYCHOPY_PTB = "psychopy_ptb"
    # sounddevice audio lib
    # http://python-sounddevice.readthedocs.io/
    SOUNDDEVICE = "sounddevice"


_audio_lib = os.environ.get("REPROSTIM_AUDIO_LIB", AudioLib.PSYCHOPY_SOUNDDEVICE)

from psychopy import prefs  # noqa: E402

prefs.hardware["audioLib"] = ["sounddevice"]
if _audio_lib == AudioLib.PSYCHOPY_SOUNDDEVICE:
    logger.debug("Set psychopy audio library: sounddevice")
    prefs.hardware["audioLib"] = ["sounddevice"]
elif _audio_lib == AudioLib.PSYCHOPY_PTB:
    logger.debug("Set psychopy audio library: ptb")
    prefs.hardware["audioLib"] = ["ptb"]

# logger.info("Using psychopy audio library: %s", prefs.hardware['audioLib'])
from psychopy import core, sound  # noqa: E402
from psychtoolbox import audio  # noqa: E402

######################################
# Audio code/qr helper functions


def bit_enumerator(data):
    if isinstance(data, DataMessage):
        data = data.encode()
    if isinstance(data, str):
        # If data is a string, iterate over each character
        for char in data:
            if char not in ("0", "1"):
                raise ValueError("String must only contain '0' and '1'.")
            yield int(char)  # Yield the bit as an integer
    elif isinstance(data, bytes):
        # If data is bytes, iterate over each byte
        for byte in data:
            for i in range(7, -1, -1):  # Iterate from MSB to LSB
                yield (byte >> i) & 1  # Extract and yield the bit
    else:
        raise TypeError(
            "Data must be either a string or bytes. Got: " + str(type(data))
        )


# Convert a list of bits to bytes
def bits_to_bytes(detected_bits):
    # Check if the length of detected_bits is a multiple of 8
    if len(detected_bits) % 8 != 0:
        raise ValueError(
            f"Detected bits array must be aligned to 8 bits. Length={len(detected_bits)}"
        )

    byte_array = bytearray()  # Use bytearray for mutable bytes
    for i in range(0, len(detected_bits), 8):
        # Get the next 8 bits
        byte_bits = detected_bits[i : i + 8]  # noqa: E203

        # Convert the list of bits to a byte (big-endian)
        byte_value = 0
        for bit in byte_bits:
            byte_value = (byte_value << 1) | bit  # Shift left and add the bit

        byte_array.append(byte_value)  # Append the byte to the bytearray

    return bytes(byte_array)  # Convert bytearray to bytes


def crc8(data: bytes, polynomial: int = 0x31, init_value: int = 0x00) -> int:
    crc = init_value
    for byte in data:
        crc ^= byte  # XOR byte into the CRC
        for _ in range(8):  # Process each bit
            if crc & 0x80:  # If the highest bit is set
                crc = (crc << 1) ^ polynomial  # Shift left and XOR with polynomial
            else:
                crc <<= 1  # Just shift left
            crc &= 0xFF  # Keep CRC to 8 bits
    return crc


######################################
# Constants


class AudioCodec(str, Enum):
    # Frequency Shift Keying (FSK) where binary data is
    # encoded as two different frequencies f0 and f1 with
    # a fixed bit duration (baud rate or bit_rate).
    FSK = "FSK"

    # Numerical Frequency Encoding (NFE) numbers are mapped
    # directly to specific frequencies
    # can encode only some numeric hash.
    NFE = "NFE"


######################################
# Classes


# Class representing audio data message in big-endian
# format and encoded with Reed-Solomon error correction
# where the message is structured as follows:
#  - 1st byte is CRC-8 checksum
#  - 2nd byte is the length of the data
#  - 3+ and the rest is the data itself
class DataMessage:
    def __init__(self):
        self.value: bytes = b""
        self.length: int = 0
        self.crc8: int = 0
        self.use_ecc: bool = True
        self.rsc = RSCodec(4)

    def decode(self, data: bytes):
        if self.use_ecc:
            dec, dec_full, errata_pos_all = self.rsc.decode(data)
            data = bytes(dec)

        # logger.debug(f"decoded data  : {data}")
        self.crc8 = data[0]
        self.length = data[1]
        self.value = data[2:]
        n = crc8(self.value)
        if self.crc8 != n:
            raise ValueError(f"CRC-8 checksum mismatch: {self.crc8} <-> {n}")

    def encode(self) -> bytes:
        logger.debug("size info")
        logger.debug(f"  - data      : {len(self.value)} bytes, {self.value}")
        b: bytes = bytes([self.crc8, self.length]) + self.value
        logger.debug(f"  - message   : {len(b)} bytes, {b}")
        if self.use_ecc:
            b = bytes(self.rsc.encode(b))
            logger.debug(f"  - ecc       : {len(b)} bytes, {b}")
        return b

    def get_bytes(self) -> bytes:
        return self.value

    def get_str(self) -> str:
        return self.value.decode("utf-8")

    def get_uint(self) -> int:
        c = len(self.value)
        if c == 2:
            return self.get_uint16()
        elif c == 4:
            return self.get_uint32()
        elif c == 8:
            return self.get_uint64()
        else:
            raise ValueError(f"Data length must be 2, 4, or 8 bytes, " f"but was {c}")

    def get_uint16(self) -> int:
        if len(self.value) != 2:
            raise ValueError(
                f"Data length for uint16 must be 2 bytes, " f"but was {len(self.value)}"
            )
        return int.from_bytes(self.value, "big")

    def get_uint32(self) -> int:
        if len(self.value) != 4:
            raise ValueError(
                f"Data length for uint32 must be 4 bytes, " f"but was {len(self.value)}"
            )
        return int.from_bytes(self.value, "big")

    def get_uint64(self) -> int:
        if len(self.value) != 8:
            raise ValueError(
                f"Data length for uint64 must be 8 bytes, " f"but was {len(self.value)}"
            )
        return int.from_bytes(self.value, "big")

    def set_bytes(self, data: bytes):
        self.value = data
        self.length = len(data)
        self.crc8 = crc8(data)

    def set_str(self, s: str):
        self.set_bytes(s.encode("utf-8"))

    def set_uint16(self, i: int):
        self.set_bytes(i.to_bytes(2, "big"))

    def set_uint32(self, i: int):
        self.set_bytes(i.to_bytes(4, "big"))

    def set_uint64(self, i: int):
        self.set_bytes(i.to_bytes(8, "big"))


# Class to provide general information about audio code
class AudioCodeInfo:
    def __init__(self):
        self.codec = None
        self.f1 = None
        self.f0 = None
        self.nfe_df = None
        self.sample_rate = None
        self.bit_duration = None
        self.nfe_duration = None
        self.nfe_freq = None
        self.bit_count = None
        self.volume = None
        self.duration = None
        self.pre_delay = None
        self.post_delay = None

    # to string
    def __str__(self):
        return (
            f"AudioCodeInfo(codec={self.codec}, "
            f"f1={self.f1}, "
            f"f0={self.f0}, "
            f"nfe_df={self.nfe_df}, "
            f"rate={self.sample_rate}, "
            f"bit_duration={self.bit_duration}, "
            f"bit_count={self.bit_count}, "
            f"nfe_freq={self.nfe_freq}, "
            f"volume={self.volume}, "
            f"duration={self.duration})"
            f"pre_delay={self.pre_delay}, "
            f"post_delay={self.post_delay}"
        )


# Class to generate/parse QR-like audio codes with FSK modulation
class AudioCodeEngine:
    def __init__(
        self,
        codec=AudioCodec.FSK,
        f0=1000,
        f1=5000,
        nfe_df=100,  # used only in NFE
        sample_rate=44100,
        bit_duration=0.0070,  # used only in FSK
        nfe_duration=0.3,  # used only in NFE
        volume=0.80,
        pre_delay=0.1,
        pre_f=0,  # 1780
        post_delay=0.1,
        post_f=0,  # 3571
    ):
        self.codec = codec
        self.f0 = f0
        self.f1 = f1
        self.nfe_df = nfe_df
        self.sample_rate = sample_rate
        self.bit_duration = bit_duration
        self.nfe_duration = nfe_duration
        if volume < 0.0 or volume > 1.0:
            raise ValueError("Volume must be between 0.0 and 1.0.")
        self.volume = volume
        self.pre_delay = pre_delay
        self.pre_f = pre_f
        self.post_delay = post_delay
        self.post_f = post_f

    def generate_sin(self, freq_hz, duration_sec):
        t = np.linspace(
            0, duration_sec, int(self.sample_rate * duration_sec), endpoint=False
        )
        signal = self.volume * np.sin(2 * np.pi * freq_hz * t)
        return signal

    def generate_fsk(self, data) -> (np.array, AudioCodeInfo):
        logger.debug(
            f"audio config  : f1={self.f1} Hz, f0={self.f0} Hz, "
            f"rate={self.sample_rate} Hz, "
            f"bit duration={self.bit_duration} sec, "
            f"volume={self.volume}"
        )
        t = np.linspace(
            0,
            self.bit_duration,
            int(self.sample_rate * self.bit_duration),
            endpoint=False,
        )

        # Create FSK signal
        fsk_signal = np.array([])
        pre_signal = np.array([])
        post_signal = np.array([])

        # generate pre-signal if any
        if self.pre_delay > 0:
            pre_signal = self.generate_sin(self.pre_f, self.pre_delay)

        # generate post-signal if any
        if self.post_delay > 0:
            post_signal = self.generate_sin(self.post_f, self.post_delay)

        # generate data signal properly
        c: int = 0
        sb: str = ""
        for bit in bit_enumerator(data):
            c += 1
            sb += str(bit)
            if bit == 1:
                fsk_signal = np.concatenate(
                    (fsk_signal, self.volume * np.sin(2 * np.pi * self.f1 * t))
                )
            else:
                fsk_signal = np.concatenate(
                    (fsk_signal, self.volume * np.sin(2 * np.pi * self.f0 * t))
                )

        # concatenate pre-signal, data signal, and post-signal
        if self.pre_delay > 0 or self.post_delay > 0:
            fsk_signal = np.concatenate((pre_signal, fsk_signal, post_signal))

        # Normalize the signal for 100% volume
        if self.volume == 1.0:
            fsk_signal /= np.max(np.abs(fsk_signal))

        sci: AudioCodeInfo = AudioCodeInfo()
        sci.codec = AudioCodec.FSK
        sci.f1 = self.f1
        sci.f0 = self.f0
        sci.sample_rate = self.sample_rate
        sci.bit_duration = self.bit_duration
        sci.bit_count = c
        sci.volume = self.volume
        sci.duration = c * self.bit_duration + self.pre_delay + self.post_delay
        sci.pre_delay = self.pre_delay
        sci.post_delay = self.post_delay

        logger.debug(f"audio raw bits: count={c}, {sb}")
        logger.debug(f"audio duration: {sci.duration:.6f} seconds")
        return (fsk_signal, sci)

    def generate_nfe(self, data) -> (np.array, AudioCodeInfo):
        # Create NFE signal
        nfe_signal = np.array([])
        pre_signal = np.array([])
        post_signal = np.array([])

        # generate pre-signal if any
        if self.pre_delay > 0:
            pre_signal = self.generate_sin(self.pre_f, self.pre_delay)

        # generate post-signal if any
        if self.post_delay > 0:
            post_signal = self.generate_sin(self.post_f, self.post_delay)

        n = data.get_uint()
        c = int((self.f1 - self.f0) / self.nfe_df) + 1
        freq = self.f0 + (n % c) * self.nfe_df
        logger.debug(f" n={n}, c={c}, freq={freq}")
        nfe_signal = self.generate_sin(freq, self.nfe_duration)

        # concatenate pre-signal, data signal, and post-signal
        if self.pre_delay > 0 or self.post_delay > 0:
            nfe_signal = np.concatenate((pre_signal, nfe_signal, post_signal))

        # Normalize the signal for 100% volume
        if self.volume == 1.0:
            nfe_signal /= np.max(np.abs(nfe_signal))

        sci: AudioCodeInfo = AudioCodeInfo()
        sci.codec = AudioCodec.NFE
        sci.f1 = self.f1
        sci.f0 = self.f0
        sci.nfe_df = self.nfe_df
        sci.sample_rate = self.sample_rate
        sci.nfe_duration = self.nfe_duration
        sci.nfe_freq = freq
        sci.volume = self.volume
        sci.duration = self.nfe_duration + self.pre_delay + self.post_delay
        sci.pre_delay = self.pre_delay
        sci.post_delay = self.post_delay

        logger.debug(f"audio duration: {sci.duration:.6f} seconds")
        return nfe_signal, sci

    def generate(self, data) -> (np.array, AudioCodeInfo):
        if self.codec == AudioCodec.FSK:
            return self.generate_fsk(data)
        elif self.codec == AudioCodec.NFE:
            return self.generate_nfe(data)
        else:
            raise ValueError(f"Unsupported codec: {self.codec}")

    # play audio data with sounddevice
    def play_data_sd(self, data):
        ts = time.perf_counter()
        fsk_signal, sci = self.generate(data)
        ts = time.perf_counter() - ts
        logger.debug(f"generate time : {ts:.6f} seconds")

        ts = time.perf_counter()
        # Play the FSK signal
        sd.play(fsk_signal, samplerate=self.sample_rate)

        # Wait until audio is finished playing
        sd.wait()
        ts = time.perf_counter() - ts
        logger.debug(f"play time     : {ts:.6f} seconds")

    def save(self, data, filename):
        fsk_signal, sci = self.generate(data)

        # Save the signal to a WAV file
        write(filename, self.sample_rate, (fsk_signal * 32767).astype(np.int16))
        return sci

    def parse(self, filename):
        # Read the WAV file
        rate, data = wavfile.read(filename)

        # Check if audio is stereo and convert to mono if necessary
        if len(data.shape) > 1:
            data = data.mean(axis=1)

        # Calculate the number of samples for each bit duration
        samples_per_bit = int(self.sample_rate * self.bit_duration)

        # Prepare a list to hold the detected bits
        detected_bits = []

        # Analyze the audio in chunks
        for i in range(0, len(data), samples_per_bit):
            if i + samples_per_bit > len(data):
                break  # Avoid out of bounds

            # Extract the current chunk of audio
            chunk = data[i : i + samples_per_bit]  # noqa: E203

            # Perform FFT on the chunk
            fourier = np.fft.fft(chunk)
            frequencies = np.fft.fftfreq(len(fourier), 1 / rate)

            # Get the magnitudes and filter out positive frequencies
            magnitudes = np.abs(fourier)
            positive_frequencies = frequencies[: len(frequencies) // 2]
            positive_magnitudes = magnitudes[: len(magnitudes) // 2]

            # Find the peak frequency
            peak_freq = positive_frequencies[np.argmax(positive_magnitudes)]

            # Determine if the peak frequency corresponds to a '1' or '0'
            if abs(peak_freq - self.f1) < 50:  # Frequency for '1'
                detected_bits.append(1)
            elif abs(peak_freq - self.f0) < 50:  # Frequency for '0'
                detected_bits.append(0)

        dbg_bits: str = "".join([str(bit) for bit in detected_bits])
        logger.debug(f"detected bits : count={len(dbg_bits)}, {dbg_bits}")
        return bits_to_bytes(detected_bits)


######################################
# Public functions


def beep(duration: float = 2.0, async_: bool = False):
    logger.debug(f"beep(duration={duration})")
    play_audio("A", duration, async_)


def list_audio_devices():
    logger.debug("list_audio_devices()")

    logger.debug("[psychopy]")
    logger.debug(f"audioLib     : {prefs.hardware['audioLib']}")
    logger.debug(f"audioDevice  : {prefs.hardware['audioDevice']}")

    logger.debug("[sounddevice]")
    devices = sd.query_devices()  # Query all devices
    for i, device in enumerate(devices):
        logger.debug(f"device [{i}]  : {device['name']}")
    default_device = sd.default.device  # Get the current default input/output devices
    logger.debug(f"default in  : {default_device[0]}")
    logger.debug(f"default out : {default_device[1]}")

    logger.debug("[psytoolbox]")
    for i, device in enumerate(audio.get_devices()):
        logger.debug(f"device [{i}]  : {device}")

    logger.debug("[psychopy.backend_ptb]")
    # TODO: investigate why only single out device listed from
    # USB capture but default one is not shown
    # logger.debug(sound.backend_ptb.getDevices())


def _play_audio_psychopy(
    name: str,
    duration: float = None,
    volume: float = 0.8,
    sample_rate: int = 44100,
    async_: bool = False,
):
    logger.debug(
        f"_play_audio_psychopy(name={name}, duration={duration}, async_={async_})"
    )
    snd = None
    if duration:
        snd = sound.Sound(
            name, secs=duration, sampleRate=sample_rate, stereo=True, volume=volume
        )
    else:
        snd = sound.Sound(name, stereo=True, sampleRate=sample_rate, volume=volume)
    logger.debug(f"Play audio '{snd.sound}' with psychopy {prefs.hardware['audioLib']}")
    snd.play()
    logger.debug(
        f" sampleRate={snd.sampleRate}, duration={snd.duration}, volume={snd.volume}"
    )
    if not async_:
        logger.debug("Waiting for audio to finish playing...")
        core.wait(snd.duration)
        logger.debug(f"Audio '{snd.sound}' has finished playing.")


def _play_audio_sd(
    name: str,
    duration: float = None,
    volume: float = 0.8,
    sample_rate: int = 44100,
    async_: bool = False,
):
    logger.debug(f"_play_audio_sd(name={name}, duration={duration}, async_={async_})")
    data = name

    if os.path.exists(name):
        rate, signal = read(name)
        logger.debug(f"Read audio file: {name}, rate={rate}")
        # Convert from int16 to float32
        # signal = signal.astype(np.float32) / 32767
        data = signal

    sd.play(data, samplerate=sample_rate)


def play_audio(
    name: str,
    duration: float = None,
    volume: float = 0.8,
    sample_rate: int = 44100,
    async_: bool = False,
):
    logger.debug(f"play_audio(name={name}, duration={duration}, async_={async_})")
    if (
        _audio_lib == AudioLib.PSYCHOPY_SOUNDDEVICE
        or _audio_lib == AudioLib.PSYCHOPY_PTB  # noqa: W503
    ):
        _play_audio_psychopy(name, duration, volume, sample_rate, async_)
    elif _audio_lib == AudioLib.SOUNDDEVICE:
        _play_audio_sd(name, duration, volume, sample_rate, async_)
    else:
        raise ValueError(f"Unsupported audio library: {_audio_lib}")


def save_audiocode(
    fname: str = None,
    code_uint16: int = None,
    code_uint32: int = None,
    code_uint64: int = None,
    code_str: str = None,
    code_bytes: bytes = None,
    codec: AudioCodec = AudioCodec.FSK,
    engine=None,
) -> (str, AudioCodeInfo):
    logger.debug(f"save_audiocode(fname={fname}...)")
    if not fname:
        fname = tempfile.mktemp(
            prefix=f"audiocode_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}_",
            suffix=".wav",
        )

    data = DataMessage()
    if code_uint16 is not None:
        data.set_uint16(code_uint16)
    elif code_uint32 is not None:
        data.set_uint32(code_uint32)
    elif code_uint64 is not None:
        data.set_uint64(code_uint64)
    elif code_str:
        data.set_str(code_str)
    elif code_bytes:
        data.set_bytes(code_bytes)
    else:
        raise ValueError("No code data provided.")

    if not engine:
        engine = AudioCodeEngine(codec=codec)
    sci: AudioCodeInfo = engine.save(data, fname)
    logger.debug(f" -> {fname}")
    return (fname, sci)
