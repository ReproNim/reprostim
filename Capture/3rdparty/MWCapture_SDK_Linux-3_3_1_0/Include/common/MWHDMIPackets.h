////////////////////////////////////////////////////////////////////////////////
// CONFIDENTIAL and PROPRIETARY software of Magewell Electronics Co., Ltd.
// Copyright (c) 2011-2016 Magewell Electronics Co., Ltd. (Nanjing) 
// All rights reserved.
// This copyright notice MUST be reproduced on all authorized copies.
////////////////////////////////////////////////////////////////////////////////

#pragma once

#pragma pack(push)
#pragma pack(1)

// AVI infoframe
#define HDMI_EC_XVYCC601			0x00
#define HDMI_EC_XVYCC709			0x01
#define HDMI_EC_SYCC601				0x02
#define HDMI_EC_ADOBEYCC601			0x03
#define HDMI_EC_ADOBERGB			0x04

#define HDMI_YQ_LIMITED_RANGE		0x00
#define HDMI_YQ_FULL_RANGE			0x01

#define HDMI_CN_NONE_OR_GRAPHICS	0x00
#define HDMI_CN_PHOTO				0x01
#define HDMI_CN_CINEMA				0x02
#define HDMI_CN_GAME				0x03

typedef struct _HDMI_VIC_FORMAT {
	uint16_t						cx;
	uint16_t						cy;
	bool							bInterlaced;
	uint16_t						wAspectX;
	uint16_t						wAspectY;
	uint32_t						dwFrameDuration;
} HDMI_VIC_FORMAT;

static const HDMI_VIC_FORMAT		g_aHDMIVICFormats[] = {
	{ /*  0  */	   0,    0, false,   0,   0,      0 },
	{ /*  1 */	 640,  480, false,   4,   3, 166667 },
	{ /*  2 */	 720,  480, false,   4,   3, 166667 },
	{ /*  3 */	 720,  480, false,  16,   9, 166667 },
	{ /*  4 */	1280,  720, false,  16,   9, 166667 },
	{ /*  5 */	1920, 1080,  true,  16,   9, 333333 },
	{ /*  6 */	 720,  480,  true,   4,   3, 333333 },
	{ /*  7 */	 720,  480,  true,  16,   9, 333333 },
	{ /*  8 */	 720,  240, false,   4,   3, 166667 },
	{ /*  9 */	 720,  240, false,  16,   9, 166667 },
	{ /* 10 */	2880,  480,  true,   4,   3, 333333 },
	{ /* 11 */	2880,  480,  true,  16,   9, 333333 },
	{ /* 12 */	2880,  240, false,   4,   3, 166667 },
	{ /* 13 */	2880,  240, false,  16,   9, 166667 },
	{ /* 14 */	1440,  480, false,   4,   3, 166667 },
	{ /* 15 */	1440,  480, false,  16,   9, 166667 },
	{ /* 16 */	1920, 1080, false,  16,   9, 166667 },
	{ /* 17 */	 720,  576, false,   4,   3, 200000 },
	{ /* 18 */	 720,  576, false,  16,   9, 200000 },
	{ /* 19 */	1280,  720, false,  16,   9, 200000 },
	{ /* 20 */	1920, 1080,  true,  16,   9, 400000 },
	{ /* 21 */	 720,  576,  true,   4,   3, 400000 },
	{ /* 22 */	 720,  576,  true,  16,   9, 400000 },
	{ /* 23 */	 720,  288, false,   4,   3, 200000 },
	{ /* 24 */	 720,  288, false,  16,   9, 200000 },
	{ /* 25 */	2880,  576,  true,   4,   3, 400000 },
	{ /* 26 */	2880,  576,  true,   4,   3, 400000 },
	{ /* 27 */	2880,  288, false,   4,   3, 200000 },
	{ /* 28 */	2880,  288, false,  16,   9, 200000 },
	{ /* 29 */	1440,  576, false,   4,   3, 200000 },
	{ /* 30 */	1440,  576, false,  16,   9, 200000 },
	{ /* 31 */	1920, 1080, false,  16,   9, 200000 },
	{ /* 32 */	1920, 1080, false,  16,   9, 416667 },
	{ /* 33 */	1920, 1080, false,  16,   9, 400000 },
	{ /* 34 */	1920, 1080, false,  16,   9, 333333 },
	{ /* 35 */	2880,  480, false,   4,   3, 166667 },
	{ /* 36 */	2880,  480, false,  16,   9, 166667 },
	{ /* 37 */	2880,  576, false,   4,   3, 200000 },
	{ /* 38 */	2880,  576, false,  16,   9, 200000 },
	{ /* 39 */	1920, 1080,  true,  16,   9, 400000 },
	{ /* 40 */	1920, 1080,  true,  16,   9, 200000 },
	{ /* 41 */	1280,  720, false,  16,   9, 100000 },
	{ /* 42 */	 720,  576, false,   4,   3, 100000 },
	{ /* 43 */	 720,  576, false,  16,   9, 100000 },
	{ /* 44 */	 720,  576,  true,   4,   3, 200000 },
	{ /* 45 */	 720,  576,  true,  16,   9, 200000 },
	{ /* 46 */	1920, 1080,  true,  16,   9, 166667 },
	{ /* 47 */	1280,  720, false,  16,   9,  83333 },
	{ /* 48 */	 720,  480, false,   4,   3,  83333 },
	{ /* 49 */	 720,  480, false,  16,   9,  83333 },
	{ /* 50 */	 720,  480,  true,   4,   3, 166667 },
	{ /* 51 */	 720,  480,  true,  16,   9, 166667 },
	{ /* 52 */	 720,  576, false,   4,   3,  50000 },
	{ /* 53 */	 720,  576, false,  16,   9,  50000 },
	{ /* 54 */	 720,  576,  true,   4,   3, 100000 },
	{ /* 55 */	 720,  576,  true,  16,   9, 100000 },
	{ /* 56 */	 720,  480, false,   4,   3,  41667 },
	{ /* 57 */	 720,  480, false,  16,   9,  41667 },
	{ /* 58 */	 720,  480,  true,   4,   3,  83333 },
	{ /* 59 */	 720,  480,  true,  16,   9,  83333 },
	{ /* 60 */	1280,  720, false,  16,   9, 416667 },
	{ /* 61 */	1280,  720, false,  16,   9, 400000 },
	{ /* 62 */	1280,  720, false,  16,   9, 333333 },
	{ /* 63 */	1920, 1080, false,  16,   9,  83333 },
	{ /* 64 */	1920, 1080, false,  16,   9, 100000 },
	{ /* 65 */	1280,  720, false,  64,  27, 416667 },
	{ /* 66 */	1280,  720, false,  64,  27, 400000 },
	{ /* 67 */	1280,  720, false,  64,  27, 333333 },
	{ /* 68 */	1280,  720, false,  64,  27, 200000 },
	{ /* 69 */	1280,  720, false,  64,  27, 166667 },
	{ /* 70 */	1280,  720, false,  64,  27, 100000 },
	{ /* 71 */	1280,  720, false,  64,  27,  83333 },
	{ /* 72 */	1920, 1080, false,  64,  27, 416667 },
	{ /* 73 */	1920, 1080, false,  64,  27, 400000 },
	{ /* 74 */	1920, 1080, false,  64,  27, 333333 },
	{ /* 75 */	1920, 1080, false,  64,  27, 200000 },
	{ /* 76 */	1920, 1080, false,  64,  27, 166667 },
	{ /* 77 */	1920, 1080, false,  64,  27, 100000 },
	{ /* 78 */	1920, 1080, false,  64,  27,  83333 },
	{ /* 79 */	1780,  720, false,  64,  27, 416667 },
	{ /* 80 */	1780,  720, false,  64,  27, 400000 },
	{ /* 81 */	1780,  720, false,  64,  27, 333333 },
	{ /* 82 */	1780,  720, false,  64,  27, 200000 },
	{ /* 83 */	1780,  720, false,  64,  27, 166667 },
	{ /* 84 */	1780,  720, false,  64,  27, 100000 },
	{ /* 85 */	1780,  720, false,  64,  27,  83333 },
	{ /* 86 */	2560, 1080, false,  64,  27, 416667 },
	{ /* 87 */	2560, 1080, false,  64,  27, 400000 },
	{ /* 88 */	2560, 1080, false,  64,  27, 333333 },
	{ /* 89 */	2560, 1080, false,  64,  27, 200000 },
	{ /* 90 */	2560, 1080, false,  64,  27, 166667 },
	{ /* 91 */	2560, 1080, false,  64,  27, 100000 },
	{ /* 92 */	2560, 1080, false,  64,  27,  83333 },
	{ /* 93 */	3840, 2160, false,  16,   9, 416667 },
	{ /* 94 */	3840, 2160, false,  16,   9, 400000 },
	{ /* 95 */	3840, 2160, false,  16,   9, 333333 },
	{ /* 96 */	3840, 2160, false,  16,   9, 200000 },
	{ /* 97 */	3840, 2160, false,  16,   9, 166667 },
	{ /* 98 */	4096, 2160, false, 256, 135, 416667 },
	{ /* 99 */	4096, 2160, false, 256, 135, 400000 },
	{ /* 100 */	4096, 2160, false, 256, 135, 333333 },
	{ /* 101 */	4096, 2160, false, 256, 135, 200000 },
	{ /* 102 */	4096, 2160, false, 256, 135, 166667 },
	{ /* 103 */	3840, 2160, false,  64,  27, 416667 },
	{ /* 104 */	3840, 2160, false,  64,  27, 400000 },
	{ /* 105 */	3840, 2160, false,  64,  27, 333333 },
	{ /* 106 */	3840, 2160, false,  64,  27, 200000 },
	{ /* 107 */	3840, 2160, false,  64,  27, 166667 }
};

static const uint8_t g_abyDefaultYUV709VICs[] = {
	0, 1, 4, 5, 16, 19, 20, 31, 32, 33, 34, 39, 40, 46, 47, 60, 61, 62, 63, 64
};

// byRGB_YCbCr
typedef struct _HDMI_AVI_INFOFRAME_PAYLOAD {
	uint8_t								byScanInfo : 2;
	uint8_t								byBarDataPresent : 2;
	uint8_t								byActiveFormatInfoPresent : 1;
	uint8_t								byRGB_YCbCr : 2;
	uint8_t								byFutureUseByte1 : 1;

	uint8_t								byActivePortionAspectRatio : 4;
	uint8_t								byCodedFrameAspectRatio : 2;
	uint8_t								byColorimetry : 2;

	uint8_t								byNonUniformPictureScaling : 2;
	uint8_t								byRGBQuantizationRange : 2;
	uint8_t								byExtendedColorimetry : 3;
	uint8_t								byITContent : 1;

	uint8_t								byVIC : 7;
	uint8_t								byFutureUseByte4 : 1;

	uint8_t								byPixelRepetitionFactor : 4;
	uint8_t								byITContentType : 2;
	uint8_t								byYCCQuantizationRange : 2;

	uint16_t							wEndOfTopBar;
	uint16_t							wStartOfBottomBar;
	uint16_t							wEndOfLeftBar;
	uint16_t							wStartOfRightBar;
} HDMI_AVI_INFOFRAME_PAYLOAD;

// Audio infoframe
#define HDMI_AUDIO_CODING_TYPE_STREAM	0x00
#define HDMI_AUDIO_CODING_TYPE_PCM		0x01
#define HDMI_AUDIO_CODING_TYPE_AC3		0x02
#define HDMI_AUDIO_CODING_TYPE_MPEG1	0x03
#define HDMI_AUDIO_CODING_TYPE_MP3		0x04
#define HDMI_AUDIO_CODING_TYPE_MPEG2	0x05
#define HDMI_AUDIO_CODING_TYPE_AAC_LC	0x06
#define HDMI_AUDIO_CODING_TYPE_DTS		0x07
#define HDMI_AUDIO_CODING_TYPE_ATRAC	0x08
#define HDMI_AUDIO_CODING_TYPE_DSD		0x09
#define HDMI_AUDIO_CODING_TYPE_EAC3		0x0A
#define HDMI_AUDIO_CODING_TYPE_DTS_HD	0x0B

#define HDMI_AUDIO_SAMPLE_SIZE_STREAM	0x00
#define HDMI_AUDIO_SAMPLE_SIZE_16BIT	0x01
#define HDMI_AUDIO_SAMPLE_SIZE_20BIT	0x02
#define HDMI_AUDIO_SAMPLE_SIZE_24BIT	0x03

#define HDMI_AUDIO_SAMPLE_RATE_STREAM	0x00
#define HDMI_AUDIO_SAMPLE_RATE_32000	0x01
#define HDMI_AUDIO_SAMPLE_RATE_44100	0x02
#define HDMI_AUDIO_SAMPLE_RATE_48000	0x03
#define HDMI_AUDIO_SAMPLE_RATE_88200	0x04
#define HDMI_AUDIO_SAMPLE_RATE_96000	0x05
#define HDMI_AUDIO_SAMPLE_RATE_176400	0x06
#define HDMI_AUDIO_SAMPLE_RATE_192000	0x07

typedef struct _HDMI_AUDIO_INFOFRAME_PAYLOAD {
	uint8_t								byChannelCount : 3;		// +1 for channel count
	uint8_t								byReserved1 : 1;
	uint8_t								byAudioCodingType : 4;

	uint8_t								bySampleSize : 2;
	uint8_t								bySampleFrequency : 3;
	uint8_t								byReserved2 : 3;

	uint8_t								byAudioCodingExtensionType : 5;
	uint8_t								byReserved3 : 3;

	uint8_t								byChannelAllocation;

	uint8_t								byLFEPlaybackLevel : 2;
	uint8_t								byReserved4 : 1;
	uint8_t								byLevelShiftValue : 4;
	uint8_t								byDownMixInhibitFlag : 1;
} HDMI_AUDIO_INFOFRAME_PAYLOAD;

// SPD Infoframe
#define HDMI_SPD_SORUCE_UNKOWN			0x00
#define HDMI_SPD_SORUCE_DIGITAL_STB		0x01
#define HDMI_SPD_SORUCE_DVD_PLAYER		0x02
#define HDMI_SPD_SORUCE_D_VHS			0x03
#define HDMI_SPD_SORUCE_HDD_RECORDER	0x04
#define HDMI_SPD_SORUCE_DVC				0x05
#define HDMI_SPD_SORUCE_DSC				0x06
#define HDMI_SPD_SORUCE_VIDEO_CD		0x07
#define HDMI_SPD_SORUCE_GAME			0x08
#define HDMI_SPD_SORUCE_PC_GENERAL		0x09
#define HDMI_SPD_SORUCE_BLUE_RAY_DISC	0x0A
#define HDMI_SPD_SORUCE_SUPER_AUDIO_CD	0x0B
#define HDMI_SPD_SORUCE_HD_DVD			0x0C
#define HDMI_SPD_SORUCE_PMP				0x0D

typedef struct _HDMI_SPD_INFOFRAME_PAYLOAD {
	char								achVendorName[8];
	char								achProductDescription[16];
	uint8_t								bySourceInformation;
} HDMI_SPD_INFOFRAME_PAYLOAD;

// HDMI 1.4b VS Infoframe
#define HDMI14B_VS_REGISTRATION_ID		0x000C03

#define HDMI14B_VS_FORMAT_NONE			0x00
#define HDMI14B_VS_FORMAT_EXT_RES		0x01
#define HDMI14B_VS_FORMAT_3D_FORMAT		0x02

// by3DStructure
#define HDMI14B_3DS_FRAME_PACKING		0x00
#define HDMI14B_3DS_FIELD_ALTERNATIVE	0x01
#define HDMI14B_3DS_LINE_ALTERNATIVE	0x02
#define HDMI14B_3DS_SIDE_BY_SIDE_FULL	0x03
#define HDMI14B_3DS_TOP_AND_BOTTOM		0x06
#define HDMI14B_3DS_SIDE_BY_SIDE_HALF	0x08

// by3DExtData
#define HDMI_SUB_SAMPLING_HORIZONTAL_00			0x00
#define HDMI_SUB_SAMPLING_HORIZONTAL_01			0x01
#define HDMI_SUB_SAMPLING_HORIZONTAL_10			0x02
#define HDMI_SUB_SAMPLING_HORIZONTAL_11			0x03
#define HDMI_SUB_SAMPLING_QUINCUNX_ODD_ODD		0x04
#define HDMI_SUB_SAMPLING_QUINCUNX_ODD_EVEN		0x05
#define HDMI_SUB_SAMPLING_QUINCUNX_EVEN_ODD		0x06
#define HDMI_SUB_SAMPLING_QUINCUNX_EVEN_EVEN	0x07

typedef struct _HDMI14B_VS_DATA_EXT_RES {
	uint8_t								byHDMI_VIC;
} HDMI14B_VS_DATA_EXT_RES;

typedef struct _HDMI14B_VS_DATA_3D_FORMAT {
	uint8_t								byReserved1 : 3;
	uint8_t								by3DMetaPresent : 1;
	uint8_t								by3DStructure : 4;

	uint8_t								byReserved2 : 4;
	uint8_t								by3DExtData : 4;

	uint8_t								by3DMetadataLength : 5;
	uint8_t								by3DMetadataType : 3;
} HDMI14B_VS_DATA_3D_FORMAT;

typedef struct _HDMI14B_VS_DATA {
	uint8_t								byReserved1 : 5;
	uint8_t								byHDMIVideoFormat : 3;

	union {
		HDMI14B_VS_DATA_EXT_RES			vsDataExtRes;
		HDMI14B_VS_DATA_3D_FORMAT		vsData3DFormat;
	};
} HDMI14B_VS_DATA;

// Generic VS Infoframe
typedef struct _HDMI_VS_INFOFRAME_PAYLOAD {
	uint8_t								abyRegistrationId[3];
	
	union {
		uint8_t							abyVSData[24];
		HDMI14B_VS_DATA					vsDataHDMI14B;
	};

public:
	uint32_t GetRegistrationId() {
		return abyRegistrationId[0] | (abyRegistrationId[1] << 8) | (abyRegistrationId[2] << 16);
	}

} HDMI_VS_INFOFRAME_PAYLOAD;

// Generic Infoframe
#define HDMI_INFOFRAME_TYPE_VS			0x81
#define HDMI_INFOFRAME_TYPE_AVI			0x82
#define HDMI_INFOFRAME_TYPE_SPD			0x83
#define HDMI_INFOFRAME_TYPE_AUDIO		0x84
#define HDMI_INFOFRAME_TYPE_MS			0x85

typedef struct _HDMI_INFOFRAME_HEADER {
	uint8_t								byPacketType;
	uint8_t								byVersion;
	uint8_t								byLength : 5;
	uint8_t								byReservedZero : 3;
} HDMI_INFOFRAME_HEADER;

typedef struct _HDMI_INFOFRAME_PACKET {
	HDMI_INFOFRAME_HEADER				header;
	uint8_t								byChecksum;

	union {
		uint8_t							abyPayload[27];
		HDMI_AVI_INFOFRAME_PAYLOAD		aviInfoFramePayload;
		HDMI_AUDIO_INFOFRAME_PAYLOAD	audioInfoFramePayload;
		HDMI_SPD_INFOFRAME_PAYLOAD		spdInfoFramePayload;
		HDMI_VS_INFOFRAME_PAYLOAD		vsInfoFramePayload;
	};

public:
	bool IsValid(
		) const {
		uint8_t * pbyData = (uint8_t *)&header;
		uint8_t cbData = header.byLength + sizeof(header) + 1;

		uint8_t bySum = 0;
		while (cbData-- != 0)
			bySum += *pbyData++;

		return (bySum == 0);
	}
} HDMI_INFOFRAME_PACKET;

#pragma pack(pop)
