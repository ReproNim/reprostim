# Audio Codes Notes

## Installation

```
 python3.10 -m venv venv
 source venv/bin/activate
 pip install --upgrade pip
 pip install -r audio-codes-requirements.txt
```

 On MacOS:
```
  brew install portaudio
  pip install pyaudio
```

 On Linux:
```
  sudo apt-get install portaudio19-dev
```

## TODO:

 Review `psychopy` and sound API and possibly use PTB's
 facilities in PsychoPy for precise audio placement in time:
   https://www.psychopy.org/download.html
   https://psychopy.org/api/sound/playback.html

 Look at watermark in audio.

## PsychoPy, Sound, PTB

### On MacOS:

NOTE: PsychoPy (2024.2.3) current requirements limits/suggests
      to Python version 3.10.

Download and install the standalone package:
PsychoPy 2024.2.3 modern (py3.10)
https://github.com/psychopy/psychopy/releases/download/2024.2.3/StandalonePsychoPy-2024.2.3-macOS-py3.10.dmg

Run PsychoPy and check the sound settings that `pbt` is
set as `Audio Library`.

Make sure Python 3.10 is installed and venv is explicitly created with it:
```
   python3.10 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r audio-codes-requirements.txt
```

NOTE: first time PsychoPy is run, it may takes a long time to setup audio
       download additional dependencies.

### On Linux (Ubuntu 22.04):

Create some folder for `psychopy` installation and init Python 3.10 venv:
```
   python3.10 -m venv venv
   source venv/bin/activate
```
Then fetch a wxPython wheel for your platform from:
https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ and
download it locally to your machine.
In my case it was `https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04/wxPython-4.2.1-cp310-cp310-linux_x86_64.whl`
downloaded to `wxPython/wxPython-4.2.1-cp310-cp310-linux_x86_64.whl` .

Install sound dependencies (1st one may fail):
```
   sudo apt-get install libusb-1.0-0-dev portaudio19-dev libasound2-dev
   pip install psychtoolbox
```

Install wxPython in `venv` with, e.g.:
```
   pip install wxPython/wxPython-4.2.1-cp310-cp310-linux_x86_64.whl
```

Then install `psychopy`:
```
   pip install psychopy
```

Run psychopy:
```
   psychopy
```

NOTE: PsychoPy PTB sound was non tested on Ubuntu 22.04, due to upgrade to 24.04.

### On Linux (Ubuntu 24.04):

Somehow was unable to run `python3.10` directly so installed it manually together with venv:

```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10
sudo apt install python3.10-venv
```

After this `python3.10` failed to create `venv` so used following commands to create it:

```
python3.10 -m venv --without-pip venv
source venv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
```

Then installed `wxPython` it can take up to 1 hour to compile it (there is no pre-built wheels for Ubuntu 24.04 ATM):

```
sudo apt update
sudo apt install python3-dev python3-pip libgtk-3-dev
pip install wxPython
```

Finally installed `psychopy`:

```
pip install psychopy
```

Applied security fix for audio scripts user, by adding current user to `audio` group:

```
sudo usermod -a -G audio $USER
```

and to adjust real-time permissions by creating a file `/etc/security/limits.d/99-realtime.conf` 

```
sudo vi /etc/security/limits.d/99-realtime.conf
```

with the following content:

```
@audio   -  rtprio     99
@audio   -  memlock    unlimited
```

Then rebooted the system.

NOTE: PsychoPy PTB still doesn't work on Ubuntu 24.04 and script produces error, TBD:

```
[DEBUG] play sound with psychopy ptb
Failure: No such entity
Failure: No such entity
```

## NeuroDebian/Singularity

On Linux (Ubuntu 22.04) :

Was unable to install `singularity-container` from `neurodebian` repository after multiple attempts, so finally upgraded Linux 22.04 to 24.04.


On Linux (Ubuntu 24.04) :

```
wget -O- http://neuro.debian.net/lists/noble.de-m.libre | sudo tee /etc/apt/sources.list.d/neurodebian.sources.list
sudo apt-key adv --recv-keys --keyserver hkps://keyserver.ubuntu.com 0xA5D32F012649A5A9

sudo apt-get update

sudo apt-get install singularity-container
```

```
singularity --version
  singularity-ce version 4.1.1
```

## Summary
  - `PyDub` allows you to generate simple tones easily.
  -  FSK modulation can be achieved using `numpy` and
  `scipy` to create varying frequency tones based on
  binary input.
  - Optionally `DTMF` encoding is implemented using
  predefined frequency pairs, and you can detect
  DTMF tones by analyzing the audio input.

  - Chirp SDK:
    Chirp.io / https://www.sonos.com/en/home
    https://github.com/chirp

  - GNU Radio - can be used to encode/modulate/demodulate.
    https://www.gnuradio.org/
    Supports Frequency Shift Keying (FSK),
    Phase Shift Keying (PSK), or Amplitude Modulation (AM).

  - `reedsolo` can be used for ECC (Error Correction Codes).

