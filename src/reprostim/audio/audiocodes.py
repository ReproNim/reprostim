# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
Audiocodes module for reprostim, provides functionality to
generate and parse QR-like audiocodes to be included in
psychopy based scripts.
"""

import importlib
import logging
import os
import tempfile
import time
from datetime import datetime
from enum import Enum

import numpy as np
from reedsolo import RSCodec
from scipy.io import wavfile
from scipy.io.wavfile import read, write

# optionally: import sounddevice as sd
sd = (
    importlib.import_module("sounddevice")
    if importlib.util.find_spec("sounddevice")
    else None
)


# setup logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("REPROSTIM_LOG_LEVEL", "INFO"))

######################################
# Setup psychopy audio library


class AudioLib(str, Enum):
    """
    Enum for the audio libs constants.
    """

    PSYCHOPY_SOUNDDEVICE = "psychopy_sounddevice"
    """
    PsychoPy `SoundDevice` audio lib
    """

    PSYCHOPY_PTB = "psychopy_ptb"
    """
    PsychoPy `SoundPTB` audio lib
    """

    SOUNDDEVICE = "sounddevice"
    """
    `sounddevice` audio lib, see more at:
    http://python-sounddevice.readthedocs.io/
    """


_audio_lib = os.environ.get("REPROSTIM_AUDIO_LIB", AudioLib.PSYCHOPY_SOUNDDEVICE)

# optionally import psychopy
try:
    from psychopy import prefs  # noqa: E402

    # skip setup under sphinx/RTD
    if os.getenv("REPROSTIM_DOCS") != "True":
        prefs.hardware["audioLib"] = ["sounddevice"]
        if _audio_lib == AudioLib.PSYCHOPY_SOUNDDEVICE:
            logger.debug("Set psychopy audio library: sounddevice")
            prefs.hardware["audioLib"] = ["sounddevice"]
        elif _audio_lib == AudioLib.PSYCHOPY_PTB:
            logger.debug("Set psychopy audio library: ptb")
            prefs.hardware["audioLib"] = ["ptb"]

    from psychopy import core, sound  # noqa: E402
    from psychtoolbox import audio  # noqa: E402
except ImportError:
    logger.warn(
        "psychopy module not found, if necessary "
        "install reprostim with [all] extra dependencies"
    )


######################################
# Audio code/qr helper functions


def bit_enumerator(data):
    """
    Enumerate audio data bits.

    This function takes either a string representation of binary digits (`0` and `1`)
    or a bytes object and yields individual bits as integers (`0` or `1`).

    :param data: The input data containing bits.
    :type data: str | bytes | DataMessage

    :yield: The extracted bits as integers (`0` or `1`).
    :rtype: int

    :raises ValueError: If a string contains characters other than `0` and `1`.
    :raises TypeError: If the input data type is not supported.
    """
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


def bits_to_bytes(detected_bits):
    """
    Convert a list of bits (`0` and `1`) into a bytes object.

    This function takes a list of bits, groups them into bytes
    (8 bits each), and converts them into a bytes object in big-endian order.

    :param detected_bits: A list containing only `0` and `1`. The length
                          of the list must be a multiple of 8.
    :type detected_bits: list of int

    :returns: A bytes object representing the converted bit sequence.
    :rtype: bytes

    :raises ValueError: If the length of `detected_bits` is not a multiple of 8.

    Example
    -------
        >>> bits_to_bytes([1, 0, 0, 0, 0, 0, 0, 1])
        b'\\x81'
    """
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
    """
    Compute the CRC-8 checksum for a given byte sequence.

    :param data: The input data for which to compute the CRC-8 checksum.
    :type data: bytes

    :param polynomial: Polynomial to calculate CRC (default: 0x31).
    :type polynomial: int, optional

    :param init_value: The initial CRC value (default: 0x00).
    :type init_value: int, optional

    :returns: The computed 8-bit CRC checksum.
    :rtype: int

    Example
    -------
    >>> crc8(b"123456789")
    b'\\0xA2'

    >>> crc8(b"Hello", polynomial=0x07, init_value=0xFF)
    b'\\0xFC'
    """
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
    """
    Enum for audio codecs constants.
    """

    FSK = "FSK"
    """
    Frequency Shift Keying (FSK), where binary data is
    encoded as two different frequencies (f0 and f1)
    with a fixed bit duration (baud rate or bit_rate).
    """

    NFE = "NFE"
    """
    Numerical Frequency Encoding (NFE), where numbers
    are mapped directly to specific frequencies. This
    codec can encode only certain numeric hash values.
    """


######################################
# Classes


class DataMessage:
    """
    Class representing an audio data message in big-endian format,
    encoded with Reed-Solomon error correction.

    The message is structured as follows:
    - 1st byte: CRC-8 checksum
    - 2nd byte: Length of the data
    - 3rd byte onward: The data itself
    """

    def __init__(self):
        """
        Initializes a new DataMessage instance.

        Attributes are set to default values: empty data, length 0, and CRC-8 0.
        Reed-Solomon error correction is enabled by default.
        """
        self.value: bytes = b""
        self.length: int = 0
        self.crc8: int = 0
        self.use_ecc: bool = True
        self.rsc = RSCodec(4)

    def decode(self, data: bytes):
        """
        Decodes the given data bytes, verifying the CRC-8 checksum and parsing the
        length and data. If error correction is enabled, Reed-Solomon error correction
        is applied to the data before decoding.

        :param data: The encoded byte data to decode, including the CRC-8 checksum
                     and length.
        :type data: bytes

        :raises ValueError: If the CRC-8 checksum does not match the computed checksum
                             of the data.
        """
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
        """
        Encodes the data message, including the CRC-8 checksum and length,
        and applies Reed-Solomon error correction if enabled. Returns the
        encoded byte sequence.

        :returns: The encoded byte sequence with the CRC-8 checksum, length,
                  and optionally Reed-Solomon error correction.
        :rtype: bytes
        """
        logger.debug("size info")
        logger.debug(f"  - data      : {len(self.value)} bytes, {self.value}")
        b: bytes = bytes([self.crc8, self.length]) + self.value
        logger.debug(f"  - message   : {len(b)} bytes, {b}")
        if self.use_ecc:
            b = bytes(self.rsc.encode(b))
            logger.debug(f"  - ecc       : {len(b)} bytes, {b}")
        return b

    def get_bytes(self) -> bytes:
        """
        Returns the data value as a bytes object.

        :returns: The data stored in the message.
        :rtype: bytes
        """
        return self.value

    def get_str(self) -> str:
        """
        Returns the data value as a UTF-8 decoded string.

        :returns: The decoded string from the message data.
        :rtype: str
        """
        return self.value.decode("utf-8")

    def get_uint(self) -> int:
        """
        Returns the stored data as an unsigned integer.

        Decodes the data based on its length (2, 4, or 8 bytes) and returns it as
        either a `uint16`, `uint32`, or `uint64`.

        :returns: The decoded unsigned integer.
        :rtype: int
        :raises ValueError: If the data length is not 2, 4, or 8 bytes.
        """
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
        """
        Returns the stored data as a 16-bit unsigned integer (uint16).

        The method assumes the data length is exactly 2 bytes. If the length is
        not 2, a `ValueError` is raised.

        :returns: The decoded 16-bit unsigned integer.
        :rtype: int
        :raises ValueError: If the data length is not 2 bytes.
        """
        if len(self.value) != 2:
            raise ValueError(
                f"Data length for uint16 must be 2 bytes, " f"but was {len(self.value)}"
            )
        return int.from_bytes(self.value, "big")

    def get_uint32(self) -> int:
        """
        Returns the stored data as a 32-bit unsigned integer (uint32).

        The method assumes the data length is exactly 4 bytes. If the length is
        not 4, a `ValueError` is raised.

        :returns: The decoded 32-bit unsigned integer.
        :rtype: int
        :raises ValueError: If the data length is not 4 bytes.
        """
        if len(self.value) != 4:
            raise ValueError(
                f"Data length for uint32 must be 4 bytes, " f"but was {len(self.value)}"
            )
        return int.from_bytes(self.value, "big")

    def get_uint64(self) -> int:
        """
        Returns the stored data as a 64-bit unsigned integer (uint64).

        The method assumes the data length is exactly 8 bytes. If the length is
        not 8, a `ValueError` is raised.

        :returns: The decoded 64-bit unsigned integer.
        :rtype: int
        :raises ValueError: If the data length is not 8 bytes.
        """
        if len(self.value) != 8:
            raise ValueError(
                f"Data length for uint64 must be 8 bytes, " f"but was {len(self.value)}"
            )
        return int.from_bytes(self.value, "big")

    def set_bytes(self, data: bytes):
        """
        Sets the bytes data value.

        :param data: The data to be stored in the message.
        :type data: bytes
        """
        self.value = data
        self.length = len(data)
        self.crc8 = crc8(data)

    def set_str(self, s: str):
        """
        Sets the string data value.

        :param s: The string to be stored in the message.
        :type s: str
        """
        self.set_bytes(s.encode("utf-8"))

    def set_uint16(self, i: int):
        """
        Sets the 16-bit unsigned integer data value.

        :param i: The uint16 to be stored in the message.
        :type i: int
        """
        self.set_bytes(i.to_bytes(2, "big"))

    def set_uint32(self, i: int):
        """
        Sets the 32-bit unsigned integer data value.

        :param i: The uint32 to be stored in the message.
        :type i: int
        """
        self.set_bytes(i.to_bytes(4, "big"))

    def set_uint64(self, i: int):
        """
        Sets the 64-bit unsigned integer data value.

        :param i: The uint64 to be stored in the message.
        :type i: int
        """
        self.set_bytes(i.to_bytes(8, "big"))


class AudioCodeInfo:
    """
    Class to provide general information about an audiocode.
    """

    def __init__(self):
        self.codec = None
        """The codec used for the audiocode (e.g., `FSK`, `NFE`)."""
        self.f1 = None
        """The frequency corresponding to logic `1` in FSK modulation."""
        self.f0 = None
        """The frequency corresponding to logic `0` in FSK modulation."""
        self.nfe_df = None
        """Frequency difference in Hz used by NFE codec."""
        self.sample_rate = None
        """The sample rate of the audio signal"""
        self.bit_duration = None
        """Bit duration in seconds for FSK audiocode."""
        self.nfe_duration = None
        """Duration of NFE signal in seconds."""
        self.nfe_freq = None
        """Frequency for NFE modulation when this codec is used."""
        self.bit_count = None
        """The number of bits in the encoded data."""
        self.volume = None
        """The volume level of the audio signal on range 0..1 ."""
        self.duration = None
        """The total duration of the audio signal in seconds."""
        self.pre_delay = None
        """Pre-delay time before the audio code starts in seconds."""
        self.post_delay = None
        """Post-delay time after the audio code ends in seconds."""

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
            f"duration={self.duration},"
            f"pre_delay={self.pre_delay}, "
            f"post_delay={self.post_delay})"
        )


class AudioCodeEngine:
    """
    Class to generate and parse QR-like audiocodes with Frequency Shift Keying
    (FSK) or Numerical Frequency Encoding (NFE) modulations.

    This class handles the encoding and decoding of audio data using FSK or
    NFE modulation schemes, where data is represented as special audio tones.

    :param codec: The codec used for encoding the audio data. Defaults to
                  `AudioCodec.FSK`.
    :type codec: AudioCodec

    :param f0: The frequency for representing a binary `0` in FSK modulation.
               Defaults to 1000 Hz.
    :type f0: int

    :param f1: The frequency for representing a binary `1` in FSK modulation.
               Defaults to 5000 Hz.
    :type f1: int

    :param nfe_df: The frequency difference used for Numerical Frequency Encoding
                   (NFE). Defaults to 100 Hz.
    :type nfe_df: int

    :param sample_rate: The sample rate used for audio generation. Defaults
                        to 44100 Hz.
    :type sample_rate: int

    :param bit_duration: The duration of each bit in FSK modulation. Defaults
                         to 0.0070 seconds.
    :type bit_duration: float

    :param nfe_duration: The duration for each frequency in NFE encoding.
                         Defaults to 0.5 seconds.
    :type nfe_duration: float

    :param volume: The volume level for the audio output. Defaults to 0.80.
    :type volume: float

    :param pre_delay: The pre-delay before the audio signal starts.
                      Defaults to 0.1 seconds.
    :type pre_delay: float

    :param pre_f: The frequency before the start of the tone in FSK encoding.
                  Defaults to 0 Hz (1780 Hz).
    :type pre_f: int

    :param post_delay: The post-delay after the audio signal ends. Defaults
                       to 0.1 seconds.
    :type post_delay: float

    :param post_f: The frequency after the end of the tone in FSK encoding.
                   Defaults to 0 Hz (3571 Hz).
    :type post_f: int
    """

    def __init__(
        self,
        codec=AudioCodec.FSK,
        f0=1000,
        f1=5000,
        nfe_df=100,  # used only in NFE
        sample_rate=44100,
        bit_duration=0.0070,  # used only in FSK
        nfe_duration=0.5,  # used only in NFE
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
        """
        Generates a sine wave audio signal with a specified frequency and duration.

        :param freq_hz: The frequency of the sine wave in Hz.
        :type freq_hz: float

        :param duration_sec: The duration of the sine wave signal in seconds.
        :type duration_sec: float

        :return: A numpy array representing the generated sine wave audio signal.
        :rtype: numpy.ndarray
        """
        t = np.linspace(
            0, duration_sec, int(self.sample_rate * duration_sec), endpoint=False
        )
        signal = self.volume * np.sin(2 * np.pi * freq_hz * t)
        return signal

    def generate_fsk(self, data) -> (np.array, AudioCodeInfo):
        """
        Generates `FSK` audio signal from the given data.

        :param data: The data to be encoded into the FSK signal. This could be a
                     string, bytes, or int.
        :type data: str | bytes | int

        :return: A tuple with FSK audio signal and related audiocode information.
        :rtype: tuple(np.ndarray, AudioCodeInfo)
        """
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
        """
        Generates `NFE` audio signal from the given data.

        :param data: The data to be encoded into the NFE signal. This could be a
                     string, bytes, or int.
        :type data: str | bytes | int

        :return: A tuple with NFE audio signal and related audiocode information.
        :rtype: tuple(np.ndarray, AudioCodeInfo)
        """
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
        """
        Generates an audio signal based on the specified codec
        and provided data.

        This method selects the appropriate encoding method based on
        the codec and generates the corresponding audio signal. Currently
        supports `FSK` and `NFE` encodings.

        :param data: The data to be encoded into the audio signal.
                     The format of the data depends on the selected codec.
        :type data: str | bytes | int

        :return: A tuple containing the generated audio signal and related
                 audiocode information.
        :rtype: tuple(np.ndarray, AudioCodeInfo)

        :raises ValueError: If the codec is not supported.

        Example
        -------
            >>> engine = AudioCodeEngine(codec=AudioCodec.FSK)
            >>> signal, info = engine.generate("Hello")
        """
        if self.codec == AudioCodec.FSK:
            return self.generate_fsk(data)
        elif self.codec == AudioCodec.NFE:
            return self.generate_nfe(data)
        else:
            raise ValueError(f"Unsupported codec: {self.codec}")

    # play audio data with sounddevice
    def play_data_sd(self, data):
        """
        Plays the audio data using the `sounddevice` library.

        This method generates an audio signal based on the provided
        data and plays it using the `sounddevice` library.

        :param data: The data to be encoded into the audio signal and played.
        :type data: str | bytes | int

        :return: None

        :Example:
            >>> engine = AudioCodeEngine()
            >>> engine.play_data_sd("Hello")
        """
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
        """
        Generates and saves the audio signal to `*.wav` file.

        :param data: The data to be encoded into the audio signal.
        :type data: str | bytes | int

        :param filename: The name of the `*.wav` file where the
                         signal will be saved.
        :type filename: str

        :return: The AudioCodeInfo object containing information
                 about the saved audiocode.
        :rtype: AudioCodeInfo

        Example
        -------
            >>> engine = AudioCodeEngine()
            >>> engine.save("Hello", "output.wav")
        """
        fsk_signal, sci = self.generate(data)

        # Save the signal to a WAV file
        write(filename, self.sample_rate, (fsk_signal * 32767).astype(np.int16))
        return sci

    def parse(self, filename):
        """
        Parses the audiocode file to detect and decode stored data.

        :param filename: The name of the `*.wav` file to parse.
        :type filename: str

        :return: The decoded data as bytes.
        :rtype: bytes

        :raises ValueError: If audiocode is not possible to parse nor decode.

        Example
        -------
            >>> engine = AudioCodeEngine()
            >>> decoded_data = engine.parse("encoded_audio.wav")
        """
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
    """
    Play a beep sound for the given duration.

    :param duration: The duration of the beep in seconds. Default is 2.0 seconds.
    :type duration: float

    :param async_: If True, play the sound asynchronously. Default is False.
    :type async_: bool
    """
    logger.debug(f"beep(duration={duration})")
    play_audio("A", duration, async_)


def list_audio_devices():
    """
    List all available audio devices.

    This function queries and logs available audio devices from different libraries
    (`psychopy`, `sounddevice`, `psytoolbox`, and `psychopy.backend_ptb`), and logs
    the current default input and output devices.

    The function does not return any value but logs detailed information about
    each device to the standard logger.

    :returns: None
    :rtype: None

    :raises: None

    Example
    -------
    >>> list_audio_devices()
    # Logs detailed information about available audio devices
    """
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
        f" sampleRate={snd.sampleRate}, duration={snd.getDuration()}, "
        f"volume={snd.getVolume()}"
    )
    if not async_:
        logger.debug("Waiting for audio to finish playing...")
        core.wait(snd.getDuration())
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
    """
    Play an audio file with specified parameters.

    This function plays an audio file using the specified audio library.
    It supports different libraries such as PsychoPy (using Sounddevice or PTB)
    and Sounddevice.

    :param name: The name of the audio file to play.
    :type name: str

    :param duration: The duration (in seconds) for which to play the audio.
                     If not specified, the audio will play in its entirety.
    :type duration: float, optional

    :param volume: The volume level to set for the audio. Should be a value
                   between 0.0 and 1.0, where 1.0 is the maximum volume.
                   Default is 0.8.
    :type volume: float, optional

    :param sample_rate: The sample rate (in Hz) for the audio playback.
                        Default is 44100.
    :type sample_rate: int, optional

    :param async_: Whether to play the audio asynchronously.
                   If set to `True`, the audio will play in the background.
                   Default is `False`.
    :type async_: bool, optional

    :raises ValueError: If the selected audio library is unsupported.

    Example
    -------
    >>> play_audio("sound.wav", duration=5, volume=0.5)
    # Plays the audio file "sound.wav" for 5 seconds at half-volume.
    """
    logger.info(
        f"play_audio: name={name}, duration={duration}, "
        f"volume={volume}, sample_rate={sample_rate}, "
        f"async_={async_}"
    )
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
    code_duration: float = 0.5,
    codec: AudioCodec = AudioCodec.FSK,
    engine=None,
) -> (str, AudioCodeInfo):
    """
    Save an audiocode to a file (`*.wav`).

    This function saves an audiocode to a file using the specified encoding
    engine and codec. The code can be provided in various formats, such as
    unsigned integers (16, 32, 64 bits), a string, or bytes.

    :param fname: The name of the file where the audio code will be saved.
                  If not provided, a temporary filename is generated.
    :type fname: str, optional

    :param code_uint16: The audio code as a 16-bit unsigned integer.
    :type code_uint16: int, optional

    :param code_uint32: The audio code as a 32-bit unsigned integer.
    :type code_uint32: int, optional

    :param code_uint64: The audio code as a 64-bit unsigned integer.
    :type code_uint64: int, optional

    :param code_str: The audio code as a string.
    :type code_str: str, optional

    :param code_bytes: The audio code as bytes.
    :type code_bytes: bytes, optional

    :param code_duration: The duration of the audio code in seconds,
                          used only for NFE codec ATM. Default is 0.5
                          seconds.
    :type code_bytes: float, optional

    :param codec: The audio codec to use for encoding the audio code.
                  Default is `AudioCodec.FSK`.
    :type codec: AudioCodec, optional

    :param engine: The encoding engine to use. If not specified, an
                   `AudioCodeEngine` is created using the provided
                   codec.
    :type engine: AudioCodeEngine, optional

    :returns: A tuple containing the file name where the audio code
              was saved and the corresponding `AudioCodeInfo` object.
    :rtype: tuple of (str, AudioCodeInfo)

    :raises ValueError: If no code data is provided.

    Example
    -------
    >>> save_audiocode(fname="code.wav", code_uint16=12345)
    ('code.wav', <AudioCodeInfo object>)
    """

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
        engine = AudioCodeEngine(codec=codec, nfe_duration=code_duration)
    sci: AudioCodeInfo = engine.save(data, fname)
    logger.debug(f" -> {fname}")
    return (fname, sci)
