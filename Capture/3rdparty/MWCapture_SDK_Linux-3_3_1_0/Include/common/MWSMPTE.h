////////////////////////////////////////////////////////////////////////////////
// CONFIDENTIAL and PROPRIETARY software of Magewell Electronics Co., Ltd.
// Copyright (c) 2011-2016 Magewell Electronics Co., Ltd. (Nanjing) 
// All rights reserved.
// This copyright notice MUST be reproduced on all authorized copies.
////////////////////////////////////////////////////////////////////////////////

#pragma once

#pragma pack(push)
#pragma pack(1)

enum _ST352_STANDARD {
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
};

typedef int32_t ST352_STANDARD;

enum _SDI_BIT_DEPTH {
	SDI_BIT_DEPTH_8BIT					= 0,
	SDI_BIT_DEPTH_10BIT					= 1,
	SDI_BIT_DEPTH_12BIT					= 2
};

typedef int32_t SDI_BIT_DEPTH;

enum _SDI_DYNAMIC_RANGE {
	SDI_DYNAMIC_RANGE_100_PERCENT		= 0,
	SDI_DYNAMIC_RANGE_200_PERCENT		= 1,
	SDI_DYNAMIC_RANGE_400_PERCENT		= 2
};

typedef int32_t SDI_DYNAMIC_RANGE;

static const uint32_t g_adwFrameDuration[] = {
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

typedef union _SMPTE_ST352_PAYLOAD_ID {
	uint32_t	dwData;

	struct {
		uint8_t	byStandard				: 7;	// ST352_STANDARD
		uint8_t	byVersion				: 1;	// Must be 1

		uint8_t	byPictureRate			: 4;	// g_adwFrameDuration
		uint8_t	byReserved1				: 2;
		uint8_t	byProgressivePicture	: 1;
		uint8_t	byProgressiveTransport	: 1;	// Not valid for ST352_STANDARD_483_576_270M_360M, ST352_STANDARD_720P_1_5G, ST352_STANDARD_720P_DS_3G, ST352_STANDARD_483_576_DS_3G

		uint8_t	bySamplingStruct		: 4;	// SDI_SAMPLING_STRUCT
		uint8_t	byColorimetry			: 2;	// Valid for ST352_STANDARD_6G_MODE1, ST352_STANDARD_6G_MODE2
		uint8_t	byHorzYSampling			: 1;	// Valid for ST352_STANDARD_483_576_270M_360M, ST352_STANDARD_483_576_DS_3G, ST352_STANDARD_1080_3G
		uint8_t	byImageAspectRatio		: 1;	// Valid for ST352_STANDARD_483_576_270M_360M, ST352_STANDARD_483_576_DS_3G

		uint8_t	byBitDepth				: 2;
		uint8_t	byReserved3				: 1;
		uint8_t	byDynamicRange			: 2;	// Valid for ST352_STANDARD_1080_DL_1_5G, ST352_STANDARD_720P_3G, ST352_STANDARD_1080_3G
		uint8_t	byReserved4				: 1;
		uint8_t	byChannelAssignment		: 1;	// Valid for ST352_STANDARD_1080_DL_1_5G
		uint8_t	byReserved5				: 1;
	} V1;
} SMPTE_ST352_PAYLOAD_ID;

#pragma pack(pop)
