////////////////////////////////////////////////////////////////////////////////
// CONFIDENTIAL and PROPRIETARY software of Magewell Electronics Co., Ltd.
// Copyright (c) 2011-2017 Magewell Electronics Co., Ltd. (Nanjing)
// All rights reserved.
// This copyright notice MUST be reproduced on all authorized copies.
////////////////////////////////////////////////////////////////////////////////

#pragma once

#pragma pack(push)
#pragma pack(1)

typedef enum _SDI_TYPE {
    SDI_TYPE_SD,
    SDI_TYPE_HD,
    SDI_TYPE_3GA,
    SDI_TYPE_3GB_DL,
    SDI_TYPE_3GB_DS,
    SDI_TYPE_DL_CH1,
    SDI_TYPE_DL_CH2,
    SDI_TYPE_6G_MODE1,
    SDI_TYPE_6G_MODE2,
    SDI_TYPE_12G,
    SDI_TYPE_DL_HD,
    SDI_TYPE_DL_3GA,
    SDI_TYPE_DL_3GB,
    SDI_TYPE_DL_6G,
    SDI_TYPE_QL_HD,
    SDI_TYPE_QL_3GA,
    SDI_TYPE_QL_3GB
} SDI_TYPE;

typedef enum _SDI_SCANNING_FORMAT {
	SDI_SCANING_INTERLACED = 0,
	SDI_SCANING_SEGMENTED_FRAME = 1,
    SDI_SCANING_PROGRESSIVE = 3
} SDI_SCANNING_FORMAT;

typedef enum _ST352_STANDARD {
    ST352_STANDARD_483_576_270M_360M	= 0x1,
    ST352_STANDARD_720P_1_5G			= 0x4,
    ST352_STANDARD_1080_1_5G			= 0x5,
    ST352_STANDARD_1080_DL_1_5G			= 0x7,
    ST352_STANDARD_720P_3G				= 0x8,
    ST352_STANDARD_1080_3G				= 0x9,
    ST352_STANDARD_DL_3G				= 0xA,
    ST352_STANDARD_720P_DS_3G			= 0xB,
    ST352_STANDARD_1080_DS_3G			= 0xC,
    ST352_STANDARD_483_576_DS_3G		= 0xD,
    ST352_STANDARD_6G_MODE1				= 0x40,
    ST352_STANDARD_6G_MODE2				= 0x41
} ST352_STANDARD;

typedef enum _SDI_BIT_DEPTH {
	SDI_BIT_DEPTH_8BIT = 0,
	SDI_BIT_DEPTH_10BIT = 1,
	SDI_BIT_DEPTH_12BIT = 2
} SDI_BIT_DEPTH;

typedef enum _SDI_SAMPLING_STRUCT {
	SDI_SAMPLING_422_YCbCr = 0x00,
	SDI_SAMPLING_444_YCbCr = 0x01,
	SDI_SAMPLING_444_RGB = 0x02,
    SDI_SAMPLING_420_YCbCr = 0x03,
	SDI_SAMPLING_4224_YCbCrA = 0x04,
	SDI_SAMPLING_4444_YCbCrA = 0x05,
	SDI_SAMPLING_4444_RGBA = 0x06,
	SDI_SAMPLING_4224_YCbCrD = 0x08,
	SDI_SAMPLING_4444_YCbCrD = 0x09,
	SDI_SAMPLING_4444_RGBD = 0x0A,
	SDI_SAMPLING_444_XYZ = 0x0E
} SDI_SAMPLING_STRUCT;

typedef enum _SDI_DYNAMIC_RANGE {
    SDI_DYNAMIC_RANGE_100_PERCENT		= 0,
    SDI_DYNAMIC_RANGE_200_PERCENT		= 1,
    SDI_DYNAMIC_RANGE_400_PERCENT		= 2
} SDI_DYNAMIC_RANGE;

static const DWORD g_adwFrameDuration[] = {
    0,									// 0, Not defined
    0,									// 1, Reserved
    417083,								// 2, 24/1.001fps
    416667,								// 3, 24fps
    208542,								// 4, 48/1.001fps
    400000,								// 5, 25fps
    333667,								// 6, 30/1.001fps
    333333,								// 7, 30fps
    208333,								// 8, 48fps
    200000,								// 9, 50fps
    166833,								// A, 60/1.001fps
    166667,								// B, 60fps
    104167,								// C, 96fps
    100000,								// D, 100fps
    83417,								// E, 120/1.001 fps
    83333								// F, 120fps
};

enum SDI_PAYLOAD_ID_VALUE {
    SDI_PAYLOAD_ID_ST292_HD_720					= 0x84,
    SDI_PAYLOAD_ID_ST292_HD_1080				= 0x85,
    SDI_PAYLOAD_ID_ST292_DL_HD_3D				= 0xB1,
    SDI_PAYLOAD_ID_ST352_SD						= 0x81,
    SDI_PAYLOAD_ID_ST352_DL_SD					= 0x82,
    SDI_PAYLOAD_ID_ST352_540M					= 0x83,
    SDI_PAYLOAD_ID_ST352_HD_SD					= 0x86,
    SDI_PAYLOAD_ID_ST372_DL_HD_1080				= 0x87,
    SDI_PAYLOAD_ID_ST425_1_3GB_DS_720			= 0x8B,
    SDI_PAYLOAD_ID_ST425_1_3GB_DS_1080			= 0x8C,
    SDI_PAYLOAD_ID_ST425_1_3GB_DS_SD			= 0x8D,
    SDI_PAYLOAD_ID_ST425_1_3GB_DL_1080			= 0x8A,
    SDI_PAYLOAD_ID_ST425_1_3GA_720				= 0x88,
    SDI_PAYLOAD_ID_ST425_1_3GA_1080				= 0x89,
    SDI_PAYLOAD_ID_ST425_3_DL_3GA_1080			= 0x94,
    SDI_PAYLOAD_ID_ST425_3_DL_3GB_1080			= 0x95,
    SDI_PAYLOAD_ID_ST425_3_DL_3GB_2160			= 0x96,
    SDI_PAYLOAD_ID_ST425_4_DL_3GA_3D_720		= 0x91,
    SDI_PAYLOAD_ID_ST425_4_DL_3GA_3D_1080		= 0x92,
    SDI_PAYLOAD_ID_ST425_4_DL_3GB_DL_3D_1080	= 0x93,
    SDI_PAYLOAD_ID_ST425_5_QL_3GA_2160			= 0x97,
    SDI_PAYLOAD_ID_ST425_5_QL_3GB_2160			= 0x98,
    SDI_PAYLOAD_ID_ST425_6_QL_3GA_3D_1080		= 0x99,
    SDI_PAYLOAD_ID_ST425_6_QL_3GB_DL_3D_1080	= 0x9A,
    SDI_PAYLOAD_ID_ST425_6_QL_3GB_DS_3D_2160	= 0x9B,
    SDI_PAYLOAD_ID_ST2081_10_6G_2160			= 0xC0,
    SDI_PAYLOAD_ID_ST2081_10_6G_1080			= 0xC1,
    SDI_PAYLOAD_ID_ST2081_11_DL_6G_2160			= 0xC2,
    SDI_PAYLOAD_ID_ST2082_10_12G_2160			= 0xCE
};

typedef union _SMPTE_ST352_PAYLOAD_ID {
    DWORD	dwData;

    struct {
        BYTE	byStandard				: 7;	// ST352_STANDARD
        BYTE	byVersion				: 1;	// Must be 1

        BYTE	byPictureRate			: 4;	// g_adwFrameDuration
        BYTE	byReserved1				: 2;
        BYTE	byProgressivePicture	: 1;
        BYTE	byProgressiveTransport	: 1;	// Not valid for ST352_STANDARD_483_576_270M_360M, ST352_STANDARD_720P_1_5G, ST352_STANDARD_720P_DS_3G, ST352_STANDARD_483_576_DS_3G

        BYTE	bySamplingStruct		: 4;	// SDI_SAMPLING_STRUCT
        BYTE	byColorimetry			: 2;	// Valid for ST352_STANDARD_6G_MODE1, ST352_STANDARD_6G_MODE2
        BYTE	byHorzYSampling			: 1;	// Valid for ST352_STANDARD_483_576_270M_360M, ST352_STANDARD_483_576_DS_3G, ST352_STANDARD_1080_3G
        BYTE	byImageAspectRatio		: 1;	// Valid for ST352_STANDARD_483_576_270M_360M, ST352_STANDARD_483_576_DS_3G

        BYTE	byBitDepth				: 2;
        BYTE	byReserved3				: 1;
        BYTE	byDynamicRange			: 2;	// Valid for ST352_STANDARD_1080_DL_1_5G, ST352_STANDARD_720P_3G, ST352_STANDARD_1080_3G
        BYTE	byReserved4				: 1;
        BYTE	byChannelAssignment		: 1;	// Valid for ST352_STANDARD_1080_DL_1_5G
        BYTE	byReserved5				: 1;
    } V1;

    struct {
        BYTE	byID;

        union {
            // SDI_PAYLOAD_ID_ST292_HD_720
            // SDI_PAYLOAD_ID_ST425_1_3GB_DS_720
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;
                BYTE	byReserved2 : 1;

                BYTE	bySamplingStruct : 4;		// 0: 4:2:2
                BYTE	byReserved3 : 4;

                BYTE	byBitDepth : 1;				// 1: 10-bit, 0: 8-bit
                BYTE	byReserved4 : 7;
            } ST292_HD_720;

            // SDI_PAYLOAD_ID_ST292_HD_1080
            // SDI_PAYLOAD_ID_ST425_1_3GB_DS_1080
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;
                BYTE	byProgressiveTransport : 1;

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byReserved2 : 1;
                BYTE	byAspectRatio16x9 : 1;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byReserved3 : 1;

                BYTE	byBitDepth : 1;				// 0: 8-bit, 1: 10-bit
                BYTE	byReserved4 : 7;
            } ST292_HD_1080;

            // SDI_PAYLOAD_ID_ST292_DL_HD_3D
            struct {
                BYTE	byPictureRate : 4;
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;
                BYTE	byProgressiveTransport : 1;

                BYTE	bySamplingStruct : 4;
                BYTE	byReserved2 : 1;
                BYTE	byAspectRatio16x9 : 1;
                BYTE	byHorzPixelCount : 2;		// 0: 1920, 1: 2048, 2: 1280

                BYTE	byBitDepth : 2;				// 0: Reserved, 1: 10-bit, 2,3: Reserved
                BYTE	byRightEyeAudio : 2;		// 0: Not present, 1: Copy of left, 2: Additional
                BYTE	byReserved3 : 2;
                BYTE	byStreamAssignment : 1;		// 0: Left, 1: Right
                BYTE	byReserved4 : 1;
            } ST292_DL_HD_3D;

            // SDI_PAYLOAD_ID_ST352_SD
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 0
                BYTE	byReserved2 : 1;

                BYTE	bySamplingStruct : 4;
                BYTE	byReserved3 : 2;
                BYTE	byHorzSampling : 1;			// 0: 720, 1: 960
                BYTE	byAspectRatio16x9 : 1;		// 0: 4:3, 1: 16:9

                BYTE	byBitDepth : 1;				// 1: 10-bit, 0: 8-bit
                BYTE	byReserved4 : 7;
            } ST352_SD;

            // SDI_PAYLOAD_ID_ST352_DL_SD
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;
                BYTE	byReserved2 : 1;

                BYTE	bySamplingStruct : 4;
                BYTE	byReserved3 : 2;
                BYTE	byHorzSampling : 1;			// 0: 720, 1: 960
                BYTE	byAspectRatio16x9 : 1;		// 0: 4:3, 1: 16:9

                BYTE	byBitDepth : 1;				// 1: 10-bit, 0: 8-bit
                BYTE	byReserved4 : 5;
                BYTE	byChannelAssignment : 1;	// 0: CH1, 1: CH2
                BYTE	byReserved5 : 1;
            } ST352_DL_SD;

            // SDI_PAYLOAD_ID_ST352_540M
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;
                BYTE	byReserved2 : 1;

                BYTE	bySamplingStruct : 4;
                BYTE	byReserved3 : 3;
                BYTE	byAspectRatio16x9 : 1;		// 0: 4:3, 1: 16:9

                BYTE	byBitDepth : 1;				// 1: 10-bit, 0: 8-bit
                BYTE	byReserved4 : 7;
            } ST352_540M;

            // SDI_PAYLOAD_ID_ST352_HD_SD
            // SDI_PAYLOAD_ID_ST425_1_3GB_DS_SD
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byTotalLineNumber : 1;		// 0: 483, 1: 576
                BYTE	byReserved1 : 3;

                BYTE	bySamplingStruct : 4;
                BYTE	byReserved2 : 4;

                BYTE	byBitDepth : 1;				// 1: 10-bit, 0: 8-bit
                BYTE	byReserved3 : 2;
                BYTE	byMappingMode : 1;			// 0: Normal, 1: Whole-line
                BYTE	byAspectRatio16x9 : 1;
                BYTE	byReserved4 : 1;
                BYTE	byChannelAssignment : 1;	// 0: CH1, 1: CH1 & CH2
                BYTE	byReserved5 : 1;
            } ST352_HD_SD;

            // SDI_PAYLOAD_ID_ST372_DL_HD_1080
            // SDI_PAYLOAD_ID_ST425_1_3GB_DL_1080
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;
                BYTE	byProgressiveTransport : 1;

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byReserved2 : 1;
                BYTE	byAspectRatio16x9 : 1;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byReserved3 : 1;

                BYTE	byBitDepth : 2;				// 0: 8-bit, 1: 10-bit, 2: 12-bit
                BYTE	byReserved4 : 4;
                BYTE	byChannelAssignment : 1;	// 0: Link A, 1: Link B
                BYTE	byReserved5 : 1;
            } ST372_DL_HD_1080;

            // SDI_PAYLOAD_ID_ST425_1_3GA_720
            // SDI_PAYLOAD_ID_ST425_1_3GA_1080
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;
                BYTE	byProgressiveTransport : 1;

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byReserved2 : 2;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byAspectRatio16x9 : 1;

                BYTE	byBitDepth : 2;				// 0: 8-bit, 1: 10-bit, 2: 12-bit
                BYTE	byReserved3 : 6;
            } ST425_1_3GA;

            // SDI_PAYLOAD_ID_ST425_3_DL_3GA_1080
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 1

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byReserved2 : 2;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byAspectRatio16x9 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit, 2: 12-bit
                BYTE	byLink2Audio : 1;			// 0: Not present, 1: Copy of link 1
                BYTE	byReserved3 : 3;
                BYTE	byLinkAssignment : 1;		// 0: Link 0, 1: Link 1
                BYTE	byReserved4 : 1;
            } ST425_3_DL_3GA_1080;

            // SDI_PAYLOAD_ID_ST425_3_DL_3GB_1080
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 0

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byReserved2 : 1;
                BYTE	byAspectRatio16x9 : 1;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byReserved3 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit, 2: 12-bit
                BYTE	byLink2Audio : 1;			// 0: Not present, 1: Copy of link 1
                BYTE	byReserved4 : 3;
                BYTE	byChannelAssignment : 2;	// 0: DS1, 1: DS2, 2: DS3, 3: DS4
            } ST425_3_DL_3GB_1080;

            // SDI_PAYLOAD_ID_ST425_3_DL_3GB_2160
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 1

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byColorimetry1 : 1;
                BYTE	byAspectRatio16x9 : 1;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byColorimetry2 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit
                BYTE	byLink2Audio : 1;			// 0: Not present, 1: Copy of link 1
                BYTE	byReserved3 : 3;
                BYTE	byChannelAssignment : 2;	// 0: DS1, 1: DS2, 2: DS3, 3: DS4
            } ST425_3_DL_3GB_2160;

            // SDI_PAYLOAD_ID_ST425_4_DL_3GA_3D_720
            // SDI_PAYLOAD_ID_ST425_4_DL_3GA_3D_1080
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 1

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byReserved2 : 2;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byAspectRatio16x9 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit, 2: 12-bit
                BYTE	byRightEyeAudio : 2;		// 0: Not present, 1: Copy of left, 2: Additional
                BYTE	byReserved3 : 2;
                BYTE	byInterfaceAssignment : 1;	// 0: Left, 1: Right
                BYTE	byReserved4 : 1;
            } ST425_4_DL_3GA_3D;

            // SDI_PAYLOAD_ID_ST425_4_DL_3GB_DL_3D_1080
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;
                BYTE	byProgressiveTransport : 1;

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byReserved2 : 1;
                BYTE	byAspectRatio16x9 : 1;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byReserved3 : 1;

                BYTE	byBitDepth : 2;				// 0: 8-bit, 1: 10-bit, 2: 12-bit
                BYTE	byRightEyeAudio : 2;		// 0: Not present, 1: Copy of left, 2: Additional
                BYTE	byReserved4 : 1;
                BYTE	byInterfaceAssignment : 1;	// 0: Left, 1: Right
                BYTE	byLinkAssignment : 1;		// 0: Link A, 1: Link B
                BYTE	byReserved5 : 1;
            } ST425_4_DL_3GB_DL_3D_1080;

            // SDI_PAYLOAD_ID_ST425_5_QL_3GA_2160
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 1

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byColorimetry : 2;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byAspectRatio16x9 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit, 2: 12-bit
                BYTE	byLink2to4Audio : 1;		// 0: Not present, 1: Copy of link 1
                BYTE	byReserved3 : 3;
                BYTE	byLinkAssignment : 2;		// 0: Link 1, 1: Link 2, 2: Link 3, 3: Link 4
            } ST425_5_QL_3GA_2160;

            // SDI_PAYLOAD_ID_ST425_5_QL_3GB_2160
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 1

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byColorimetry1 : 1;
                BYTE	byAspectRatio16x9 : 1;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byColorimetry2 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit, 2: 12-bit
                BYTE	byLink2to4Audio : 1;		// 0: Not present, 1: Copy of link 1
                BYTE	byReserved3 : 2;
                BYTE	byChannelAssignment : 3;	// 0: DS1, 1: DS2, 2: DS3, 3: DS4, ...
            } ST425_5_QL_3GB_2160;

            // SDI_PAYLOAD_ID_ST425_6_QL_3GA_3D_1080
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 1

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byReserved2 : 2;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byAspectRatio16x9 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit, 2: 12-bit
                BYTE	byRightEyeAudio : 2;		// 0: Not present, 1: Copy of left, 2: Additional
                BYTE	byReserved3 : 1;
                BYTE	byInterfaceAssignment : 1;	// 0: Left, 1: Right
                BYTE	byChannelAssignment : 1;	// 0: DS1 & DS2, 1: DS3 & DS4
                BYTE	byReserved4 : 1;
            } ST425_6_QL_3GA_3D_1080;

            // SDI_PAYLOAD_ID_ST425_6_QL_3GB_DL_3D_1080
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 0

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byReserved2 : 1;
                BYTE	byAspectRatio16x9 : 1;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byReserved3 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit, 2: 12-bit
                BYTE	byRightEyeAudio : 2;		// 0: Not present, 1: Copy of left, 2: Additional
                BYTE	byReserved4 : 1;
                BYTE	byInterfaceAssignment : 1;	// 0: Left, 1: Right
                BYTE	byChannelAssignment : 2;	// 0: DS1, 1: DS2, 2: DS3, 3: DS4
            } ST425_6_QL_3GB_DL_3D_1080;

            // SDI_PAYLOAD_ID_ST425_6_QL_3GB_DS_3D_2160
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 1

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byColorimetry1 : 1;
                BYTE	byAspectRatio16x9 : 1;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byColorimetry2 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit
                BYTE	byRightEyeAudio : 2;		// 0: Not present, 1: Copy of left, 2: Additional
                BYTE	byReserved3 : 1;
                BYTE	byInterfaceAssignment : 1;	// 0: Left, 1: Right
                BYTE	byChannelAssignment : 2;	// 0: DS1, 1: DS2, 2: DS3, 3: DS4
            } ST425_6_QL_3GB_DS_3D_2160;

            // SDI_PAYLOAD_ID_ST2081_10_6G_2160
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 1

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byColorimetry : 2;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byAspectRatio16x9 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit
                BYTE	byAudioCopyStatus : 1;		// 0: Not present, 1: Copy of DS1
                BYTE	byReserved2 : 2;
                BYTE	byLinkAssignment : 2;		// 0
            } ST2081_10_6G_2160;

            // SDI_PAYLOAD_ID_ST2081_10_6G_1080
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 1

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byColorimetry : 2;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byAspectRatio16x9 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit
                BYTE	byAudioCopyStatus : 1;		// 0: Not present, 1: Copy of DS1
                BYTE	byReserved2 : 2;
                BYTE	byLinkAssignment : 2;		// 0
            } ST2081_10_6G_1080;

            // SDI_PAYLOAD_ID_ST2081_11_DL_6G_2160
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 1

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byColorimetry : 2;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byAspectRatio16x9 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit
                BYTE	byAudioCopyStatus : 1;		// 0: Not present, 1: Copy of DS1
                BYTE	byReserved2 : 2;
                BYTE	byLinkAssignment : 2;		// 0: Link 1, 1: Link 2
            } ST2081_11_DL_6G_2160;

            // SDI_PAYLOAD_ID_ST2082_10_12G_2160
            struct {
                BYTE	byPictureRate : 4;			// ST-352
                BYTE	byReserved1 : 2;
                BYTE	byProgressivePicture : 1;	// 1
                BYTE	byProgressiveTransport : 1;	// 1

                BYTE	bySamplingStruct : 4;		// SDI_SAMPLING_STRUCT
                BYTE	byColorimetry : 2;
                BYTE	byHorzPixelCount : 1;		// 0: 1920, 1: 2048
                BYTE	byAspectRatio16x9 : 1;

                BYTE	byBitDepth : 2;				// 1: 10-bit
                BYTE	byAudioCopyStatus : 1;		// 0: Not present, 1: Copy of DS1
                BYTE	byReserved2 : 2;
                BYTE	byLinkAssignment : 2;		// 0
            } ST2082_10_12G_2160;
        };
    };
} SMPTE_ST352_PAYLOAD_ID;

#pragma pack(pop)
