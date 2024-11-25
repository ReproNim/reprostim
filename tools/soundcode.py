# TODO: Move to reprostim.soundcode module

import logging
import os
import time
from datetime import datetime
import tempfile

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from scipy.io import wavfile
from reedsolo import RSCodec


# setup logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('REPROSTIM_LOG_LEVEL', 'INFO'))

# setup audio library
from psychopy import prefs
prefs.hardware['audioLib'] = [os.environ.get('REPROSTIM_AUDIO_LIB',
                                             'sounddevice')]
#logger.info("Using psychopy audio library: %s", prefs.hardware['audioLib'])
from psychopy import core, sound
from psychtoolbox import audio


######################################
# Sound code/qr helper functions

def bit_enumerator(data):
    if isinstance(data, DataMessage):
        data = data.encode()
    if isinstance(data, str):
        # If data is a string, iterate over each character
        for char in data:
            if char not in ('0', '1'):
                raise ValueError("String must only contain '0' and '1'.")
            yield int(char)  # Yield the bit as an integer
    elif isinstance(data, bytes):
        # If data is bytes, iterate over each byte
        for byte in data:
            for i in range(7, -1, -1):  # Iterate from MSB to LSB
                yield (byte >> i) & 1  # Extract and yield the bit
    else:
        raise TypeError("Data must be either a string or bytes. Got: " + str(type(data)))


# Convert a list of bits to bytes
def bits_to_bytes(detected_bits):
    # Check if the length of detected_bits is a multiple of 8
    if len(detected_bits) % 8 != 0:
        raise ValueError(f"Detected bits array must be aligned to 8 bits. Length={len(detected_bits)}")

    byte_array = bytearray()  # Use bytearray for mutable bytes
    for i in range(0, len(detected_bits), 8):
        # Get the next 8 bits
        byte_bits = detected_bits[i:i + 8]

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
    # USB capture but defult one is not shown
    # logger.debug(sound.backend_ptb.getDevices())


def beep(duration: float = 2.0, async_: bool = False):
    logger.debug(f"beep(duration={duration})")
    play_sound('A', duration, async_)


def play_sound(name: str, duration: float = None, async_: bool = False):
    logger.debug(f"play_sound(name={name}, duration={duration}, async_={async_})")
    snd = None
    if duration:
        snd = sound.Sound(name, secs=duration, stereo=True)
    else:
        snd = sound.Sound(name, stereo=True)
    logger.debug(f"Play sound '{snd.sound}' with psychopy {prefs.hardware['audioLib']}")
    snd.play()
    if not async_:
        logger.debug("Waiting for sound to finish playing...")
        core.wait(snd.duration)
        logger.debug(f"Sound '{snd.sound}' has finished playing.")


def save_soundcode(fname: str = None,
                   code_uint16: int = None,
                   code_uint32: int = None,
                   code_uint64: int = None,
                   code_str: str = None,
                   code_bytes: bytes = None,
                   engine=None) -> str:
    logger.debug(f"save_sound(fname={fname}...)")
    if not fname:
        fname = tempfile.mktemp(
            prefix=f"soundcode_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}_",
            suffix=".wav")

    data = DataMessage()
    if not code_uint16 is None:
        data.set_uint16(code_uint16)
    elif not code_uint32 is None:
        data.set_uint32(code_uint32)
    elif not code_uint64 is None:
        data.set_uint64(code_uint64)
    elif code_str:
        data.set_str(code_str)
    elif code_bytes:
        data.set_bytes(code_bytes)
    else:
        raise ValueError("No code data provided.")

    if not engine:
        engine = SoundCodeFsk()
    engine.save(data, fname)
    logger.debug(f" -> {fname}")
    return fname

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
        self.value: bytes = b''
        self.length: int = 0
        self.crc8: int = 0
        self.use_ecc: bool = True
        self.rsc = RSCodec(4)

    def decode(self, data: bytes):
        if self.use_ecc:
            dec, dec_full, errata_pos_all = self.rsc.decode(data)
            data = bytes(dec)

        #logger.debug(f"decoded data  : {data}")
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

    def get_uint16(self) -> int:
        if len(self.value) != 2:
            raise ValueError(f"Data length for uint16 must be 2 bytes, "
                             f"but was {len(self.value)}")
        return int.from_bytes(self.value, 'big')

    def get_uint32(self) -> int:
        if len(self.value) != 4:
            raise ValueError(f"Data length for uint32 must be 4 bytes, "
                             f"but was {len(self.value)}")
        return int.from_bytes(self.value, 'big')

    def get_uint64(self) -> int:
        if len(self.value) != 8:
            raise ValueError(f"Data length for uint64 must be 8 bytes, "
                             f"but was {len(self.value)}")
        return int.from_bytes(self.value, 'big')

    def set_bytes(self, data: bytes):
        self.value = data
        self.length = len(data)
        self.crc8 = crc8(data)

    def set_str(self, s: str):
        self.set_bytes(s.encode("utf-8"))

    def set_uint16(self, i: int):
        self.set_bytes(i.to_bytes(2, 'big'))

    def set_uint32(self, i: int):
        self.set_bytes(i.to_bytes(4, 'big'))

    def set_uint64(self, i: int):
        self.set_bytes(i.to_bytes(8, 'big'))


# Class to generate/parse QR-like sound codes with FSK modulation
class SoundCodeFsk:
    def __init__(self,
                 f1=1000,
                 f0=5000,
                 sample_rate=44100,
                 duration=0.0070,
                 volume=0.75
                 ):
        self.f1 = f1
        self.f0 = f0
        self.sample_rate = sample_rate
        self.duration = duration
        if volume < 0.0 or volume > 1.0:
            raise ValueError("Volume must be between 0.0 and 1.0.")
        self.volume = volume

    def generate(self, data):
        logger.debug(f"audio config  : f1={self.f1} Hz, f0={self.f0} Hz, rate={self.sample_rate} Hz, bit duration={self.duration} sec, volume={self.volume}")
        t = np.linspace(0, self.duration,
                        int(self.sample_rate * self.duration),
                        endpoint=False)

        # Create FSK signal
        fsk_signal = np.array([])

        c: int = 0
        sb: str = ''
        for bit in bit_enumerator(data):
            c += 1
            sb += str(bit)
            if bit == 1:
                fsk_signal = np.concatenate((fsk_signal,
                                             self.volume * np.sin(2 * np.pi * self.f1 * t)))
            else:
                fsk_signal = np.concatenate((fsk_signal,
                                             self.volume * np.sin(2 * np.pi * self.f0 * t)))

        # Normalize the signal for 100% volume
        if self.volume==1.0:
            fsk_signal /= np.max(np.abs(fsk_signal))
        logger.debug(f"audio raw bits: count={c}, {sb}")
        logger.debug(f"audio duration: {c * self.duration:.6f} seconds")
        return fsk_signal

    def play(self, data):
        ts = time.perf_counter()
        fsk_signal = self.generate(data)
        ts = time.perf_counter() - ts
        logger.debug(f"generate time : {ts:.6f} seconds")

        ts = time.perf_counter()
        # Play the FSK signal
        sd.play(fsk_signal, samplerate=self.sample_rate)

        # Wait until sound is finished playing
        sd.wait()
        ts = time.perf_counter() - ts
        logger.debug(f"play time     : {ts:.6f} seconds")


    def save(self, data, filename):
        fsk_signal = self.generate(data)

        # Save the signal to a WAV file
        write(filename, self.sample_rate,
              (fsk_signal * 32767).astype(np.int16))

    def parse(self, filename):
        # Read the WAV file
        rate, data = wavfile.read(filename)

        # Check if audio is stereo and convert to mono if necessary
        if len(data.shape) > 1:
            data = data.mean(axis=1)

        # Calculate the number of samples for each bit duration
        samples_per_bit = int(self.sample_rate * self.duration)

        # Prepare a list to hold the detected bits
        detected_bits = []

        # Analyze the audio in chunks
        for i in range(0, len(data), samples_per_bit):
            if i + samples_per_bit > len(data):
                break  # Avoid out of bounds

            # Extract the current chunk of audio
            chunk = data[i:i + samples_per_bit]

            # Perform FFT on the chunk
            fourier = np.fft.fft(chunk)
            frequencies = np.fft.fftfreq(len(fourier), 1 / rate)

            # Get the magnitudes and filter out positive frequencies
            magnitudes = np.abs(fourier)
            positive_frequencies = frequencies[:len(frequencies) // 2]
            positive_magnitudes = magnitudes[:len(magnitudes) // 2]

            # Find the peak frequency
            peak_freq = positive_frequencies[np.argmax(positive_magnitudes)]

            # Determine if the peak frequency corresponds to a '1' or '0'
            if abs(peak_freq - self.f1) < 50:  # Frequency for '1'
                detected_bits.append(1)
            elif abs(peak_freq - self.f0) < 50:  # Frequency for '0'
                detected_bits.append(0)

        dbg_bits: str = ''.join([str(bit) for bit in detected_bits])
        logger.debug(f"detected bits : count={len(dbg_bits)}, {dbg_bits}")
        return bits_to_bytes(detected_bits)
