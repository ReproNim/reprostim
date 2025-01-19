from ..audio.audiocodes import crc8


def test_crc8():
    assert crc8(b"1234567890") == 91
    assert crc8(b"ABFF") == 77
