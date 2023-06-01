To install the micropython firmware on supported devices, as well as example scripts (and eventually the functional scripts for this package), run:

```console
user@host:~/COSplay/devices$ ./install.sh <your_device_name>
```

where your device name corresponds to the specific microcontroller you want to use.

Accepted device name values (i.e. supported devices) are the subdirectory names in this directory, and can be listed as follows:

```console
user@host:~/COSplay/devices$ ls */ -d
WAVESHARE_RP2040-Zero/  XIAO-RP2040/
```
