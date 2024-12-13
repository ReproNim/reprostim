////////////////////////////////////////////////////////////////////////////////
// CONFIDENTIAL and PROPRIETARY software of Magewell Electronics Co., Ltd.
// Copyright (c) 2011-2016 Magewell Electronics Co., Ltd. (Nanjing)
// All rights reserved.
// This copyright notice MUST be reproduced on all authorized copies.
////////////////////////////////////////////////////////////////////////////////

#pragma once

#pragma pack(push, 1)

const uint8_t g_abyEDIDHeader[] = { 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00 };

#define EDID_WEEK_NOT_SPECIFIED							(0x00)
#define EDID_WEEK_MODEL_YEAR							(0xFF)			// Valid for EDID 1.4
#define EDID_WEEK_MIN									(1)
#define EDID_WEEK_MAX									(54)
#define EDID_YEAR_MIN									(0x10)
#define EDID_YEAR_BASE									(1990)

#define EDID_INPUT_INTERFACE_DIGITAL					(0x80)

#define EDID_INPUT_ANALOG_LEVEL_SHIFT					(5)
#define EDID_INPUT_ANALOG_LEVEL_MASK					(0x03)
#define EDID_INPUT_ANALOG_LEVEL_0700_0300				(0)
#define EDID_INPUT_ANALOG_LEVEL_0714_0286				(1)
#define EDID_INPUT_ANALOG_LEVEL_1000_0400				(2)
#define EDID_INPUT_ANALOG_LEVEL_0700_0000				(3)

#define EDID_INPUT_ANALOG_BLANK_SETUP_EXPECTED			(0x10)
#define EDID_INPUT_ANALOG_SEPARATE_SYNC					(0x08)
#define EDID_INPUT_ANALOG_COMPOSITE_SYNC				(0x04)
#define EDID_INPUT_ANALOG_SYNC_ON_GREEN					(0x02)
#define EDID_INPUT_ANALOG_SERRATION						(0x01)

#define EDID_INPUT_DIGITAL_BIT_DEPTH_SHIFT				(4)				// Valid for EDID 1.4
#define EDID_INPUT_DIGITAL_BIT_DEPTH_MASK				(0x07)
#define EDID_INPUT_DIGITAL_BIT_DEPTH_UNDEFINED			(0)
#define EDID_INPUT_DIGITAL_BIT_DEPTH_6					(1)
#define EDID_INPUT_DIGITAL_BIT_DEPTH_8					(2)
#define EDID_INPUT_DIGITAL_BIT_DEPTH_10					(3)
#define EDID_INPUT_DIGITAL_BIT_DEPTH_12					(4)
#define EDID_INPUT_DIGITAL_BIT_DEPTH_14					(5)
#define EDID_INPUT_DIGITAL_BIT_DEPTH_16					(6)

#define EDID_INPUT_DIGITAL_INTERFACE_MASK				(0x0F)			// Valid for EDID 1.4
#define EDID_INPUT_DIGITAL_INTERFACE_UNDEFINED			(0)
#define EDID_INPUT_DIGITAL_INTERFACE_DVI				(1)
#define EDID_INPUT_DIGITAL_INTERFACE_HDMI_A				(2)
#define EDID_INPUT_DIGITAL_INTERFACE_HDMI_B				(3)
#define EDID_INPUT_DIGITAL_INTERFACE_MDDI				(4)
#define EDID_INPUT_DIGITAL_INTERFACE_DP					(5)

#define EDID_FEATURE_DFP1X_COMPATIBLE					(0x01)			// Valid for EDID 1.3

#define EDID_HORZ_PORTRAIT_AR							(0x00)			// Valid for EDID 1.4
#define EDID_VERT_LANDSCAPE_AR							(0x00)			// Valid for EDID 1.4
#define EDID_HORZ_FROM_LANDSCAPE_AR(ar)					(round((ar) * 100.0f) - 99)
#define EDID_HORZ_TO_LANDSCAPE_AR(val)					(((val) + 99) / 100.0f)
#define EDID_VERT_FROM_PORTRAIT_AR(ar)					(round(100.0f / (ar)) - 99)
#define EDID_VERT_TO_PORTRAIT_AR(val)					(100.0f / ((val) + 99))

#define EDID_DTC_FROM_GAMMA(gamma)						(round((gamma) * 100.0f) - 100)
#define EDID_DTC_TO_GAMMA(val)							(((val) + 100) / 100.0f)

#define EDID_FEATURE_STANDBY							(0x80)
#define EDID_FEATURE_SUSPEND							(0x40)
#define EDID_FEATURE_ACTIVE_OFF							(0x20)

#define EDID_FEATURE_DISPLAY_COLOR_TYPE_SHIFT			(3)
#define EDID_FEATURE_DISPLAY_COLOR_TYPE_MASK			(0x03)
#define EDID_FEATURE_COLOR_TYPE_A_MONO					(0)
#define EDID_FEATURE_COLOR_TYPE_A_RGB					(1)
#define EDID_FEATURE_COLOR_TYPE_A_NON_RGB				(2)
#define EDID_FEATURE_COLOR_TYPE_A_UNDEFINED				(3)
#define EDID_FEATURE_COLOR_TYPE_D_RGB444				(0)				// Valid for EDID 1.4 when EDID_INPUT_INTERFACE_DIGITAL
#define EDID_FEATURE_COLOR_TYPE_D_RGBYUV444				(1)
#define EDID_FEATURE_COLOR_TYPE_D_RGB444_YUV422			(2)
#define EDID_FEATURE_COLOR_TYPE_D_RGB444_YUV444_422		(3)

#define EDID_FEATURE_DEFAULT_SRGB						(0x04)
#define EDID_FEATURE_PREFERRED_TIMING_MODE				(0x02)			// Must set for EDID 1.3
#define EDID_FEATURE_DEFAULT_GTF						(0x01)			// Valid for EDID 1.3
#define EDID_FEATURE_CONTINUOUS_FREQUENCY				(0x01)			// Valid for EDID 1.4

#define EDID_EST_TIMING_I_720x400_70					(0x80)
#define EDID_EST_TIMING_I_720x400_88					(0x40)
#define EDID_EST_TIMING_I_640x480_60					(0x20)
#define EDID_EST_TIMING_I_640x480_67					(0x10)
#define EDID_EST_TIMING_I_640x480_72					(0x08)
#define EDID_EST_TIMING_I_640x480_75					(0x04)
#define EDID_EST_TIMING_I_800x600_56					(0x02)
#define EDID_EST_TIMING_I_800x600_60					(0x01)

#define EDID_EST_TIMING_II_800x600_72					(0x80)
#define EDID_EST_TIMING_II_800x600_75					(0x40)
#define EDID_EST_TIMING_II_832x624_75					(0x20)
#define EDID_EST_TIMING_II_1024x768_87i					(0x10)
#define EDID_EST_TIMING_II_1024x768_60					(0x08)
#define EDID_EST_TIMING_II_1024x768_70					(0x04)
#define EDID_EST_TIMING_II_1024x768_75					(0x02)
#define EDID_EST_TIMING_II_1280x1024_75					(0x01)

#define EDID_RES_TIMING_1152x870_75						(0x80)

#define EDID_STD_TIMING_UNUSED							(0x0101)
#define EDID_STD_TIMING_AR_16_10						(0)
#define EDID_STD_TIMING_AR_4_3							(1)
#define EDID_STD_TIMING_AR_5_4							(2)
#define EDID_STD_TIMING_AR_16_9							(3)
#define EDID_STD_TIMING_GET_AR(w)						((w) >> 14)
#define EDID_STD_TIMING_GET_REFRESH(w)					(((w) >> 8) & 0x3F)			// 60-123
#define EDID_STD_TIMING_GET_H_ACTIVE(w)					((((w) & 0xFF) + 31) * 8)	// 256-2288
#define EDID_STD_TIMING_PACK(h, refresh, ar)			(((h) / 8 - 31) | (((refresh) - 60) << 8) | ((ar) << 14))

typedef struct _EDID_BASE_BLOCK {
	// 00h Header
	uint8_t abyHeader[8];
	// 08h Vendor & Product Identification
	uint8_t abyManufacturerName[2];
	uint16_t wProductCode;
	uint32_t dwSerialNumber;
	uint8_t byWeek;
	uint8_t byYear;
	// 12h EDID Structure Version & Revision
	uint8_t byVersion;
	uint8_t byRevision;
	// 14h Basic Display Parameters & Features
	uint8_t byVideoInputDefinision;						// EDID_INPUT_XXX
	uint8_t byHorizontalSize;							// EDID_HORZ_AR_PORTRAIT or size in CM or AR (when byVerticalSize == EDID_VERT_LANDSCAPE_AR)	// AR = 1..3.54
	uint8_t byVerticalSize;								// EDID_VERT_AR_LANDSCAPE or size in CM or AR (when byHorizontalSize == EDID_HORZ_PORTRAIT_AR)	// AR = 0.28..0.99
	uint8_t byDisplayXferCharacteristics;				// EDID_DTC_XXX
	uint8_t byFeatureSupport;							// EDID_FEATURE_XXX
	// 19h Color Characteristics
	uint8_t byRedGreenLSB;								// Rx[1:0], Ry[1:0], Gx[1:0], Gy[1:0]
	uint8_t byBlueWhiteLSB;								// Bx[1:0], By[1:0], Wx[1:0], Wy[1:0]
	uint8_t byRedXMSB;									// Rx[9:2]
	uint8_t byRedYMSB;									// Ry[9:2]
	uint8_t byGreenXMSB;								// Gx[9:2]
	uint8_t byGreenYMSB;								// Gy[9:2]
	uint8_t byBlueXMSB;									// Bx[9:2]
	uint8_t byBlueYMSB;									// By[9:2]
	uint8_t byWhiteXMSB;								// Wx[9:2]
	uint8_t byWhiteYMSB;								// Wy[9:2]
	// 23h Established Timings
	uint8_t byEstablishedTimingsI;						// EDID_EST_TIMING_I_XXX
	uint8_t byEstablishedTimingsII;						// EDID_EST_TIMING_II_XXX
	uint8_t byManufacturerReservedTimings;				// EDID_RES_TIMING_XXX
	// 26h Standard Timings
	uint16_t abyStandardTimings[8];						// EDID_STD_TIMING_XXX
	// 36h 18 Byte Data Blocks
	uint8_t abyPreferredTimingMode[18];
	uint8_t abyDTD2OrDisplayDescriptor[18];
	uint8_t abyDTD3OrDisplayDescriptor[18];
	uint8_t abyDTD4OrDisplayDescriptor[18];
	// 7eh 
	uint8_t byExtensionBlockCount;
	uint8_t byCheckSum;
} EDID_BASE_BLOCK, *PEDID_BASE_BLOCK;

inline void EDID_DecodeISAPnPID(char * pszName, const uint8_t * pbyID) {
	uint16_t wID = (pbyID[0] << 8) | pbyID[1];
	pszName[3] = '\0';
	pszName[2] = ((wID >> 0) & 0x1F) + 'A' - 1;
	pszName[1] = ((wID >> 5) & 0x1F) + 'A' - 1;
	pszName[0] = ((wID >> 10) & 0x1F) + 'A' - 1;
}

inline void EDID_EncodeISAPnPID(const char * pszName, uint8_t * pbyID) {
	uint16_t wID = 0;
	wID |= (((pszName[0] - 'A') + 1) & 0x1F) << 10;
	wID |= (((pszName[1] - 'A') + 1) & 0x1F) << 5;
	wID |= (((pszName[2] - 'A') + 1) & 0x1F) << 0;

	pbyID[0] = (wID >> 8);
	pbyID[1] = (wID & 0xFF);
}

inline bool EDID_VerifyBlock(uint8_t * pbyEDIDBlock)
{
	uint8_t bySum = 0;
	for (int i = 0; i < 128; i++)
		bySum += *pbyEDIDBlock++;

	return (bySum == 0);
}

inline uint8_t EDID_CalcCheckSum(const uint8_t * pbyEDIDBlock)
{
	uint8_t bySum = 0;
	for (int i = 0; i < 127; i++)
		bySum += *pbyEDIDBlock++;

	return -bySum;
}

// NOTE: all detailed video timing descriptors precede other types of display descriptor
// The display's preferred timing mode is a required ELEMENT in EDID data structure version 1, revision 4.
#define EDID_DTD_TIMING_FLAGS_INTERLACED				(0x80)

#define EDID_DTD_TIMING_FLAGS_STEREO_SUPPORT(val)		((((val) >> 4) && 0x06) | ((val) & 0x01))
#define EDID_DTD_TIMING_FLAGS_STEREO_NONE_0				(0x00)
#define EDID_DTD_TIMING_FLAGS_STEREO_NONE_1				(0x01)
#define EDID_DTD_TIMING_FLAGS_STEREO_FS_R				(0x02)
#define EDID_DTD_TIMING_FLAGS_STEREO_FS_L				(0x04)
#define EDID_DTD_TIMING_FLAGS_STEREO_2WAY_R				(0x03)
#define EDID_DTD_TIMING_FLAGS_STEREO_2WAY_L				(0x05)
#define EDID_DTD_TIMING_FLAGS_STEREO_4WAY				(0x06)
#define EDID_DTD_TIMING_FLAGS_STEREO_SIDE_BY_SIDE		(0x07)

#define EDID_DTD_TIMING_FLAGS_SYNC_DIGITAL_SYNC			(0x08)
#define EDID_DTD_TIMING_FLAGS_SYNC_A_BIPOLAR			(0x04)
#define EDID_DTD_TIMING_FLAGS_SYNC_A_ON_RGB				(0x01)
#define EDID_DTD_TIMING_FLAGS_SYNC_D_SEPARATE			(0x04)
#define EDID_DTD_TIMING_FLAGS_SYNC_D_POSITIVE_VS		(0x02)			// Valid for separate digital sync
#define EDID_DTD_TIMING_FLAGS_SYNC_D_POSITIVE_HS		(0x01)			// Valid for separate digital sync
#define EDID_DTD_TIMING_FLAGS_SYNC_SERRATIONS			(0x02)			// Valid for analog or composite digital sync

#define EDID_DTD_TIMING_FLAGS_PACK(i, sync, stereo)		(((i) ? 0x80 : 0x00) | (sync) | ((stereo) & 0x01) | (((stereo) & 0x06) << 4))

typedef struct _EDID_DETAILED_TIMING_DESC {
	uint16_t wPixelClockFreq;							// in 10KHz unit
	uint8_t byHAddrLSB;
	uint8_t byHBlankLSB;
	uint8_t byHAddrBlankMSB;							// HAddr[11:8], HBlank[11:8]
	uint8_t byVAddrLSB;
	uint8_t byVBlankLSB;
	uint8_t byVAddrBlankMSB;							// VAddr[11:8], VBlank[11:8]
	uint8_t byHFrontPorchLSB;
	uint8_t byHSyncPulseWidthLSB;
	uint8_t byVFrontPorchSyncPulseWidthLSB;				// VFrontPorch[3:0], VSyncPulseWidth[3:0]
	uint8_t byFrontPorchSyncPulseWidthMSB;				// HFrontPorch[9:8], HSyncPulseWidth[9:8], VFrontPorch[5:4], VSyncPulseWidth[5:4]
	uint8_t byHImageSizeLSB;							// in mm unit
	uint8_t byVImageSizeLSB;
	uint8_t byImageSizeMSB;								// HImageSize[11:8], VImageSize[11:8]
	uint8_t byHBorderPixels;
	uint8_t byVBorderPixels;
	uint8_t byFlags;									// EDID_DTD_TIMING_XXX
} EDID_DETAILED_TIMING_DESC, *PEDID_DETAILED_TIMING_DESC;

#define EDID_DISPLAY_TAG_SN								(0xFF)
#define EDID_DISPLAY_TAG_ASCII							(0xFE)
#define EDID_DISPLAY_TAG_RANGE_LIMITS					(0xFD)
#define EDID_DISPLAY_TAG_PRODUCT_NAME					(0xFC)
#define EDID_DISPLAY_TAG_COLOR_POINT_DATA				(0xFB)
#define EDID_DISPLAY_TAG_STANDARD_TIMING_IDS			(0xFA)
#define EDID_DISPLAY_TAG_DCM_DATA						(0xF9)
#define EDID_DISPLAY_TAG_CVT3_BYTE_TIMING_CODES			(0xF8)
#define EDID_DISPLAY_TAG_EST_TIMINGS_III				(0xF7)
#define EDID_DISPLAY_TAG_DUMMY							(0x10)
#define EDID_DISPLAY_TAG_MANUFACTURER_MAX				(0x0F)
#define EDID_DISPLAY_TAG_MANUFACTURER_MIN				(0x00)

typedef struct _EDID_DISPLAY_DESC {
	uint16_t wZero;
	uint8_t byZero;
	uint8_t byDisplayDescTagNumber;
	uint8_t byReserved;									// Set to zero
	uint8_t abyData[13];								// Serial number, ASCII string, Product name
} EDID_DISPLAY_DESC, *PEDID_DISPLAY_DESC;

#define EDID_DISPLAY_RANGE_MIN_VERT_OFFSET_255Hz		(0x01)
#define EDID_DISPLAY_RANGE_MAX_VERT_OFFSET_255Hz		(0x02)
#define EDID_DISPLAY_RANGE_MIN_HORZ_OFFSET_255KHz		(0x04)
#define EDID_DISPLAY_RANGE_MAX_HORZ_OFFSET_255KHz		(0x08)

#define EDID_DISPLAY_RANGE_DEFAULT_GTF					(0x00)		// EDID_FEATURE_CONTINUOUS_FREQUENCY must be set for this mode
#define EDID_DISPLAY_RANGE_RANGE_LIMIT_ONLY				(0x01)		// Valid in 1.4
#define EDID_DISPLAY_RANGE_SECONDARY_GTF				(0x02)		// EDID_FEATURE_CONTINUOUS_FREQUENCY must be set for this mode
#define EDID_DISPLAY_RANGE_CVT							(0x04)		// Valid in 1.4, EDID_FEATURE_CONTINUOUS_FREQUENCY must be set for this mode

const uint8_t g_abyEDIDRangeLimitVideoTimingDataEmpty[7] = { 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20 };

// NOTE: shall be included if bit 0 of the Feature Support Byte at address 18h is set to 1 (indicating a continuous frequency display)
typedef struct _EDID_DISPLAY_RANGE_LIMITS_DESC {
	uint16_t wZero;
	uint8_t byZero;
	uint8_t byDisplayDescTagNumber;						// EDID_DISPLAY_TAG_RANGE_LIMITS
	uint8_t byRangeLimitOffsets;						// EDID_DISPLAY_RANGE_XXX
	uint8_t byMinVertRate;								// in Hz unit
	uint8_t byMaxVertRate;
	uint8_t byMinHorzRate;								// in KHz unit
	uint8_t byMaxHorzRate;
	uint8_t byMaxPixelClockFreq;						// in 10MHz unit
	uint8_t byVideoTimingSupportFlags;
	uint8_t abyVideoTimingData[7];						// Empty for EDID_DISPLAY_RANGE_DEFAULT_GTF & EDID_DISPLAY_RANGE_RANGE_LIMIT_ONLY
} EDID_DISPLAY_RANGE_LIMITS_DESC, *PEDID_DISPLAY_RANGE_LIMITS_DESC;

inline PEDID_DISPLAY_RANGE_LIMITS_DESC FindDisplayRangeLimitDesc(PEDID_BASE_BLOCK pBaseBlock) {
	PEDID_DISPLAY_RANGE_LIMITS_DESC pDisplayRangeDesc = (PEDID_DISPLAY_RANGE_LIMITS_DESC)pBaseBlock->abyDTD2OrDisplayDescriptor;

	for (int i = 0; i < 3; i++) {
		if (pDisplayRangeDesc->wZero == 0
			&& pDisplayRangeDesc->byZero == 0
			&& pDisplayRangeDesc->byDisplayDescTagNumber == EDID_DISPLAY_TAG_RANGE_LIMITS) {
			return pDisplayRangeDesc;
		}

		pDisplayRangeDesc++;
	}

	return NULL;
}

typedef struct _EDID_DISPLAY_RANGE_SECONDARY_GTF_DATA {
	uint8_t byReserved;									// Must be zero
	uint8_t byStartBreakFreq;							// in 2KHz unit
	uint8_t byCx2;
	uint16_t wM;
	uint8_t byK;
	uint8_t byJx2;
} EDID_DISPLAY_RANGE_SECONDARY_GTF_DATA, *PEDID_DISPLAY_RANGE_SECONDARY_GTF_DATA;

#define EDID_DISPLAY_RANGE_CVT_SUPPORTED_AR_4_3			(0x80)
#define EDID_DISPLAY_RANGE_CVT_SUPPORTED_AR_16_9		(0x40)
#define EDID_DISPLAY_RANGE_CVT_SUPPORTED_AR_16_10		(0x20)
#define EDID_DISPLAY_RANGE_CVT_SUPPORTED_AR_5_4			(0x10)
#define EDID_DISPLAY_RANGE_CVT_SUPPORTED_AR_15_9		(0x08)
#define EDID_DISPLAY_RANGE_CVT_PREFERED_AR_4_3			(0)
#define EDID_DISPLAY_RANGE_CVT_PREFERED_AR_16_9			(1)
#define EDID_DISPLAY_RANGE_CVT_PREFERED_AR_16_10		(2)
#define EDID_DISPLAY_RANGE_CVT_PREFERED_AR_5_4			(3)
#define EDID_DISPLAY_RANGE_CVT_PREFERED_AR_15_9			(4)
#define EDID_DISPLAY_RANGE_CVT_REDUCED_BLANKING			(0x10)
#define EDID_DISPLAY_RANGE_CVT_STANDARD_BLANKING		(0x08)
#define EDID_DISPLAY_RANGE_CVT_HORZ_SHRINK				(0x80)
#define EDID_DISPLAY_RANGE_CVT_HORZ_STRETCH				(0x40)
#define EDID_DISPLAY_RANGE_CVT_VERT_SHRINK				(0x20)
#define EDID_DISPLAY_RANGE_CVT_VERT_STRETCH				(0x10)

typedef struct _EDID_DISPLAY_RANGE_SECONDARY_CVT_DATA {
	uint8_t byVersion;									// 11h for 1.1
	uint8_t byMaxHActiveMSB : 2;
	uint8_t byAdditionalPixelClockPrecision : 6;		// in 0.25MHz unit
	uint8_t byMaxHActiveLSB;							// 0 for no limit
	uint8_t bySupportedAR;
	uint8_t byReserved : 3;
	uint8_t byCVTBlankingSupport : 2;
	uint8_t byPreferedAR : 3;
	uint8_t byDisplayScalingSupport;
	uint8_t byPreferedVertRefreshRate;					// in Hz unit
} EDID_DISPLAY_RANGE_SECONDARY_CVT_DATA, *PEDID_DISPLAY_RANGE_SECONDARY_CVT_DATA;

typedef struct _EDID_DISPLAY_STANDARD_TIMING_IDS_DESC {
	uint16_t wZero;
	uint8_t byZero;
	uint8_t byDisplayDescTagNumber;						// EDID_DISPLAY_TAG_STANDARD_TIMING_IDS
	uint8_t byReserved;									// Set to zero
	uint16_t awStandardTimings[6];
	uint8_t byLineFeed;									// Set to 0x0A
} EDID_DISPLAY_STANDARD_TIMING_IDS_DESC, *PEDID_DISPLAY_STANDARD_TIMING_IDS_DESC;

#define EDID_EST_TIMING_III_1_640x350_85 				(0x80)
#define EDID_EST_TIMING_III_1_640x400_85				(0x40)
#define EDID_EST_TIMING_III_1_720x400_85				(0x20)
#define EDID_EST_TIMING_III_1_640x480_85 				(0x10)
#define EDID_EST_TIMING_III_1_848x480_60				(0x08)
#define EDID_EST_TIMING_III_1_800x600_85 				(0x04)
#define EDID_EST_TIMING_III_1_1024x768_85				(0x02)
#define EDID_EST_TIMING_III_1_1152x864_75				(0x01)

#define EDID_EST_TIMING_III_2_1280x768_60_RB			(0x80)
#define EDID_EST_TIMING_III_2_1280x768_60				(0x40)
#define EDID_EST_TIMING_III_2_1280x768_75				(0x20)
#define EDID_EST_TIMING_III_2_1280x768_85				(0x10)
#define EDID_EST_TIMING_III_2_1280x960_60				(0x08)
#define EDID_EST_TIMING_III_2_1280x960_85				(0x04)
#define EDID_EST_TIMING_III_2_1280x1024_60				(0x02)
#define EDID_EST_TIMING_III_2_1280x1024_85				(0x01)

#define EDID_EST_TIMING_III_3_1360x768_60				(0x80)
#define EDID_EST_TIMING_III_3_1440x900_60_RB			(0x40)
#define EDID_EST_TIMING_III_3_1440x900_60				(0x20)
#define EDID_EST_TIMING_III_3_1440x900_75				(0x10)
#define EDID_EST_TIMING_III_3_1440x900_85				(0x08)
#define EDID_EST_TIMING_III_3_1400x1050_60_RB			(0x04)
#define EDID_EST_TIMING_III_3_1400x1050_60				(0x02)
#define EDID_EST_TIMING_III_3_1400x1050_75				(0x01)

#define EDID_EST_TIMING_III_4_1400x1050_85				(0x80)
#define EDID_EST_TIMING_III_4_1680x1050_60_RB			(0x40)
#define EDID_EST_TIMING_III_4_1680x1050_60				(0x20)
#define EDID_EST_TIMING_III_4_1680x1050_75				(0x10)
#define EDID_EST_TIMING_III_4_1680x1050_85				(0x08)
#define EDID_EST_TIMING_III_4_1600x1200_60				(0x04)
#define EDID_EST_TIMING_III_4_1600x1200_65				(0x02)
#define EDID_EST_TIMING_III_4_1600x1200_70				(0x01)

#define EDID_EST_TIMING_III_5_1600x1200_75				(0x80)
#define EDID_EST_TIMING_III_5_1600x1200_85				(0x40)
#define EDID_EST_TIMING_III_5_1792x1344_60				(0x20)
#define EDID_EST_TIMING_III_5_1792x1344_75				(0x10)
#define EDID_EST_TIMING_III_5_1856x1392_60				(0x08)
#define EDID_EST_TIMING_III_5_1856x1392_75				(0x04)
#define EDID_EST_TIMING_III_5_1920x1200_60_RB			(0x02)
#define EDID_EST_TIMING_III_5_1920x1200_60				(0x01)

#define EDID_EST_TIMING_III_6_1920x1200_75				(0x80)
#define EDID_EST_TIMING_III_6_1920x1200_85				(0x40)
#define EDID_EST_TIMING_III_6_1920x1440_60				(0x20)
#define EDID_EST_TIMING_III_6_1920x1440_75				(0x10)

typedef struct _EDID_DISPLAY_EST_TIMINGS_III_DESC {
	uint16_t wZero;
	uint8_t byZero;
	uint8_t byDisplayDescTagNumber;						// EDID_DISPLAY_TAG_EST_TIMINGS_III
	uint8_t byReserved;									// Set to zero
	uint8_t byRevision;									// Set to 0x0A
	uint8_t byEstTimingIII_1;
	uint8_t byEstTimingIII_2;
	uint8_t byEstTimingIII_3;
	uint8_t byEstTimingIII_4;
	uint8_t byEstTimingIII_5;
	uint8_t byEstTimingIII_6;
	uint8_t abyReserved[6];
} EDID_DISPLAY_EST_TIMINGS_III_DESC, *PEDID_DISPLAY_EST_TIMINGS_III_DESC;

#define EDID_BLOCK_TAG_UNUSED							(0x00)
#define EDID_BLOCK_TAG_CEA_EXT							(0x02)
#define EDID_BLOCK_TAG_VTB_EXT							(0x10)
#define EDID_BLOCK_TAG_DI_EXT							(0x40)
#define EDID_BLOCK_TAG_LS_EXT							(0x50)
#define EDID_BLOCK_TAG_DPVL_EXT							(0x60)
#define EDID_BLOCK_TAG_BLOCK_MAP						(0xF0)
#define EDID_BLOCK_TAG_MANUFACTURER						(0xFF)

typedef struct _EDID_EXT_BLOCK {
	uint8_t byBlockTagNumber;
	uint8_t byRevisionNumber;
	uint8_t abyData[125];
	uint8_t byCheckSum;
} EDID_EXT_BLOCK, *PEDID_EXT_BLOCK;

typedef struct _EDID_MAP_BLOCK {
	uint8_t byMapBlockTagNumber;						// EDID_TAG_BLOCK_MAP
	uint8_t abyBlockTagNumbers[126];
	uint8_t byCheckSum;
} EDID_MAP_BLOCK, *PEDID_MAP_BLOCK;

#define EDID_CEA_FLAG_UNDERSCAN							(0x08)
#define EDID_CEA_FLAG_BASIC_AUDIO						(0x04)
#define EDID_CEA_FLAG_YCbCr444							(0x02)
#define EDID_CEA_FLAG_YCbCr422							(0x01)

#define EDID_CEA_PADDING_DATA							(0x00)

typedef struct _EDID_CEA_EXT_BLOCK_HEADER {
	uint8_t byBlockTagNumber;							// EDID_BLOCK_TAG_CEA_EXT
	uint8_t byRevisionNumber;							// 0x03
	uint8_t byDetailedTimingDescOffset;					// 0 for no data block & detailed timings
	uint8_t byNumNativeDTDs : 4;
	uint8_t byFlags : 4;
	// Data block collections
	// Detailed timing desc @byDetailedTimingDescOffset
	// byCheckSum
} EDID_CEA_EXT_BLOCK_HEADER, *PEDID_CEA_EXT_BLOCK_HEADER;

#define EDID_CEA_BLOCK_TAG_AUDIO						(0x01)
#define EDID_CEA_BLOCK_TAG_VIDEO						(0x02)
#define EDID_CEA_BLOCK_TAG_VENDOR_SPECIFIC				(0x03)
#define EDID_CEA_BLOCK_TAG_SPEAKER_ALLOCATION			(0x04)
#define EDID_CEA_BLOCK_TAG_VESA_DISPLAY_XFER			(0x05)
#define EDID_CEA_BLOCK_TAG_USE_EXTENDED_TAG				(0x07)

typedef struct _EDID_CEA_DATA_BLOCK_HEADER {
	uint8_t byDataLength : 5;							// total number of video bytes following
	uint8_t byTagCode : 3;
	// uint8_t abyData[byDataLength];
} EDID_CEA_DATA_BLOCK_HEADER, *PEDID_CEA_DATA_BLOCK_HEADER;

#define EDID_CEA_BLOCK_EXT_TAG_VIDEO_CAPABILITY			(00)		
#define EDID_CEA_BLOCK_EXT_TAG_VENDOR_SPECIFIC_VIDEO 	(01)		
#define EDID_CEA_BLOCK_EXT_TAG_VESA_DISPLAY_DEVICE		(02)		
#define EDID_CEA_BLOCK_EXT_TAG_VESA_VIDEO_TIMING 		(03)
#define EDID_CEA_BLOCK_EXT_TAG_HDMI_VIDEO				(04)
#define EDID_CEA_BLOCK_EXT_TAG_COLORIMETRY				(05)		
#define EDID_CEA_BLOCK_EXT_TAG_VIDEO_FORMAT_PREFERENCE	(13)		
#define EDID_CEA_BLOCK_EXT_TAG_YUV420_VIDEO				(14)		
#define EDID_CEA_BLOCK_EXT_TAG_YUV420_CAPABILITY_MAP	(15)		
#define EDID_CEA_BLOCK_EXT_TAG_VENDOR_SPECIFIC_AUDIO 	(17)
#define EDID_CEA_BLOCK_EXT_TAG_HDMI_AUDIO				(18)
#define EDID_CEA_BLOCK_EXT_TAG_INFO_FRAME				(32)

typedef struct _EDID_CEA_EXT_DATA_BLOCK_HEADER {
	uint8_t byDataLength : 5;							// total number of video bytes following
	uint8_t byTagCode : 3;
	uint8_t byExtendedTagCode;
	// uint8_t abyData[byDataLength - 1];
} EDID_CEA_EXT_DATA_BLOCK_HEADER, *PEDID_CEA_EXT_DATA_BLOCK_HEADER;

inline PEDID_CEA_DATA_BLOCK_HEADER EDID_FindCEAGetFirstDataBlock(PEDID_CEA_EXT_BLOCK_HEADER pCEAExt, int& cbTotalBlockSize) {
	cbTotalBlockSize = pCEAExt->byDetailedTimingDescOffset - 4;
	if (cbTotalBlockSize <= 0)
		return NULL;

	PEDID_CEA_DATA_BLOCK_HEADER pBlockHdr = (PEDID_CEA_DATA_BLOCK_HEADER)(pCEAExt + 1);
	if (cbTotalBlockSize < (pBlockHdr->byDataLength + 1))
		return NULL;

	return pBlockHdr;
}

inline PEDID_CEA_DATA_BLOCK_HEADER EDID_FindCEAGetNextDataBlock(PEDID_CEA_DATA_BLOCK_HEADER pDataBlock, int& cbTotalBlockSize) {
	uint8_t * pbyData = (uint8_t *)pDataBlock + pDataBlock->byDataLength + 1;
	cbTotalBlockSize -= pDataBlock->byDataLength + 1;
	if (cbTotalBlockSize <= 0)
		return NULL;

	PEDID_CEA_DATA_BLOCK_HEADER pBlockHdr = (PEDID_CEA_DATA_BLOCK_HEADER)pbyData;
	if (cbTotalBlockSize < (pBlockHdr->byDataLength + 1))
		return NULL;

	return pBlockHdr;
}

inline PEDID_CEA_DATA_BLOCK_HEADER EDID_FindVSDB(PEDID_CEA_EXT_BLOCK_HEADER pCEAExt, const uint8_t * pbyIEEE_OUI) {
	int cbTotalBlockSize;
	PEDID_CEA_DATA_BLOCK_HEADER pHdr = EDID_FindCEAGetFirstDataBlock(pCEAExt, cbTotalBlockSize);

	while (pHdr) {
		if (pHdr->byTagCode == EDID_CEA_BLOCK_TAG_VENDOR_SPECIFIC
			&& pHdr->byDataLength >= 3) {
			if (memcmp(pHdr + 1, pbyIEEE_OUI, 3) == 0)
				return pHdr;
		}

		pHdr = EDID_FindCEAGetNextDataBlock(pHdr, cbTotalBlockSize);
	}

	return NULL;
}

inline int EDID_GetCEADetailedTimingCount(PEDID_CEA_EXT_BLOCK_HEADER pCEAExt) {
	int cbMaxDTDs = 127 - pCEAExt->byDetailedTimingDescOffset;
	int cMaxDTDs = cbMaxDTDs / 18;

	PEDID_DETAILED_TIMING_DESC pDTD = (PEDID_DETAILED_TIMING_DESC)((uint8_t *)pCEAExt + pCEAExt->byDetailedTimingDescOffset);

	int cDTDs = 0;
	while (cDTDs < cMaxDTDs) {
		if (pDTD->wPixelClockFreq == 0)
			break;
		cDTDs++;
	}

	return cDTDs;
}

inline void EDID_RemoveCEADataBlock(PEDID_CEA_EXT_BLOCK_HEADER pCEAExt, PEDID_CEA_DATA_BLOCK_HEADER pDataBlock) {
	int cbDataBlock = pDataBlock->byDataLength + 1;

	uint8_t * pbyStart = (uint8_t *)pCEAExt;
	uint8_t * pbyClear = (pbyStart + 127) - cbDataBlock;
	uint8_t * pbyBlock = (uint8_t *)pDataBlock;
	uint8_t * pbyNextBlock = pbyBlock + cbDataBlock;
	int cbMove = 127 - (int)(pbyNextBlock - pbyStart);

	memmove(pbyBlock, pbyNextBlock, cbMove);
	memset(pbyClear, 0, cbDataBlock);

	pCEAExt->byDetailedTimingDescOffset -= cbDataBlock;
}

inline bool EDID_InsertCEADataBlock(PEDID_CEA_EXT_BLOCK_HEADER pCEAExt, PEDID_CEA_DATA_BLOCK_HEADER pDataBlockPos, PEDID_CEA_DATA_BLOCK_HEADER pDataBlock) {
	int cbBlock = (pDataBlock->byDataLength + 1);
	int cDTDs = EDID_GetCEADetailedTimingCount(pCEAExt);
	int cbDTDs = cDTDs * sizeof(EDID_DETAILED_TIMING_DESC);
	int cbPrevEnd = pCEAExt->byDetailedTimingDescOffset + cbDTDs;
	int cbNewEnd = cbPrevEnd + cbBlock;
	if (cbNewEnd > 127)
		return false;

	uint8_t * pbyStart = (uint8_t *)pCEAExt;
	uint8_t * pbyPos = (pDataBlockPos == NULL) ? (uint8_t *)(pCEAExt + 1) : (uint8_t *)pDataBlockPos;

	int cbMove = cbPrevEnd - (int)(pbyPos - pbyStart);
	memmove(pbyPos + (pDataBlock->byDataLength + 1), pbyPos, cbMove);
	memcpy(pbyPos, pDataBlock, cbBlock);
	pCEAExt->byDetailedTimingDescOffset += cbBlock;

	return true;
}

// EDID_CEA_BLOCK_TAG_VIDEO, EDID_CEA_BLOCK_EXT_TAG_YUV420_VIDEO, EDID_CEA_BLOCK_EXT_TAG_YUV420_CAPABILITY_MAP
#define EDID_CEA_SVD_MAX_NUM							(31)
#define EDID_CEA_SVD_FROM_VIC(native, vic)				((vic) <= 64 ? ((vic) | ((native) ? 0x80 : 0x00)) : (vic))
#define EDIA_CEA_SVD_TO_VIC(svd)						(((svd) & 0x7F) <= 64 ? ((svd) & 0x7F) : svd)

// EDID_CEA_BLOCK_TAG_AUDIO (Addtion to Basic Audio)
#define EDID_CEA_SAD_MAX_NUM							(10)

#define EDID_CEA_SAD_FORMAT_LPCM						(1)
#define EDID_CEA_SAD_FORMAT_AC3							(2)
#define EDID_CEA_SAD_FORMAT_MPEG1						(3)
#define EDID_CEA_SAD_FORMAT_MP3							(4)
#define EDID_CEA_SAD_FORMAT_MPEG2						(5)
#define EDID_CEA_SAD_FORMAT_AAC_LC						(6)
#define EDID_CEA_SAD_FORMAT_DTS							(7)
#define EDID_CEA_SAD_FORMAT_ATRAC						(8)
#define EDID_CEA_SAD_FORMAT_ONE_BIT						(9)
#define EDID_CEA_SAD_FORMAT_ENHANCED_AC3				(10)
#define EDID_CEA_SAD_FORMAT_DTS_HD						(11)
#define EDID_CEA_SAD_FORMAT_MAT							(12)
#define EDID_CEA_SAD_FORMAT_DST							(13)
#define EDID_CEA_SAD_FORMAT_WMA_PRO						(14)
#define EDID_CEA_SAD_FORMAT_EXTENSION					(15)

#define EDID_CEA_SAD_SAMPLE_RATE_32K					(0x01)
#define EDID_CEA_SAD_SAMPLE_RATE_44K1					(0x02)
#define EDID_CEA_SAD_SAMPLE_RATE_48K					(0x04)
#define EDID_CEA_SAD_SAMPLE_RATE_88K2					(0x08)
#define EDID_CEA_SAD_SAMPLE_RATE_96K					(0x10)
#define EDID_CEA_SAD_SAMPLE_RATE_176K4					(0x20)
#define EDID_CEA_SAD_SAMPLE_RATE_192K					(0x40)

#define EDID_CEA_SAD_LPCM_BITS_16						(0x01)
#define EDID_CEA_SAD_LPCM_BITS_20						(0x02)
#define EDID_CEA_SAD_LPCM_BITS_24						(0x04)

#define EDID_CEA_SAD_WMA_PRO_PROFILE_MASK				(0x07)

#define EDID_CEA_SAD_EXT_FORMAT_SHIFT					(3)
#define EDID_CEA_SAD_EXT_FORMAT_MASK					(0x1F)
#define EDID_CEA_SAD_EXT_FORMAT_DRA						(0x00)
#define EDID_CEA_SAD_EXT_FORMAT_MPEG4_HE_AAC			(0x04)
#define EDID_CEA_SAD_EXT_FORMAT_MPEG4_HE_AAC_V2			(0x05)
#define EDID_CEA_SAD_EXT_FORMAT_MPEG4_AAC_LC			(0x06)
#define EDID_CEA_SAD_EXT_FORMAT_MPEG4_HE_AAC_MPS		(0x08)
#define EDID_CEA_SAD_EXT_FORMAT_MPEG4_AAC_LC_MPS		(0x10)
#define EDID_CEA_SAD_EXT_AAC_1024_TL					(0x04)	// Valid for 4-6, 8, 10
#define EDID_CEA_SAD_EXT_AAC_960_TL						(0x02)	// Valid for 4-6, 8, 10
#define EDID_CEA_SAD_EXT_AAC_MPS_L						(0x01)	// Valid for 8, 10

typedef struct _EDID_CEA_SAD {
	uint8_t byMaxNumChannelsMinusOne : 3;
	uint8_t byAudioFormatCode : 4;
	uint8_t byReserved1 : 1;
	uint8_t bySampleRateSupported;
	uint8_t byFormatRelatedData;						// LPCM: bits per sample, 2-8: MaxBitRate / 8K, WMA Pro: Profile, Ext: EDID_CEA_SAD_EXT_XXX
} EDID_CEA_SAD, *PEDID_CEA_SAD;

// EDID_CEA_BLOCK_TAG_SPEAKER_ALLOCATION 
// Shall be included if the Sink supports multi-channel uncompressed digital audio
#define EDID_CEA_SPEAKER_1_FLW_FRW						(0x80)
#define EDID_CEA_SPEAKER_1_RLC_RRC						(0x40)
#define EDID_CEA_SPEAKER_1_FLC_FRC						(0x20)
#define EDID_CEA_SPEAKER_1_RC							(0x10)
#define EDID_CEA_SPEAKER_1_RL_RR						(0x08)
#define EDID_CEA_SPEAKER_1_FC							(0x04)
#define EDID_CEA_SPEAKER_1_LFE							(0x02)
#define EDID_CEA_SPEAKER_1_FL_FR						(0x01)

#define EDID_CEA_SPEAKER_2_FCH							(0x04)
#define EDID_CEA_SPEAKER_2_TC							(0x02)
#define EDID_CEA_SPEAKER_2_FLH_FRH						(0x01)

typedef struct _EDID_CEA_SPEAKER_ALLOCATION {
	uint8_t byFlags1;
	uint8_t byFlags2;
	uint8_t byFlags3;
} EDID_CEA_SPEAKER_ALLOCATION, *PEDID_CEA_SPEAKER_ALLOCATION;

// EDID_CEA_BLOCK_EXT_TAG_COLORIMETRY
#define EDID_CEA_COLORIMETRY_xvYCC601					(0x80)
#define EDID_CEA_COLORIMETRY_xvYCC709					(0x40)
#define EDID_CEA_COLORIMETRY_sYCC601					(0x20)
#define EDID_CEA_COLORIMETRY_ADOBE_YCC601				(0x10)
#define EDID_CEA_COLORIMETRY_ADOBE_RGB					(0x08)
#define EDID_CEA_COLORIMETRY_BT2020_CYCC				(0x04)
#define EDID_CEA_COLORIMETRY_BT2020_YCC					(0x02)
#define EDID_CEA_COLORIMETRY_BT2020_RGB					(0x01)

typedef struct _EDID_CEA_EXT_COLORIMETRY {
	uint8_t byColorimetry;
	uint8_t byFutureMetaData;
} EDID_CEA_EXT_COLORIMETRY, *PEDID_CEA_EXT_COLORIMETRY;

// EDID_CEA_BLOCK_EXT_TAG_VIDEO_CAPABILITY				(Only 1 byte data)
#define EDID_CEA_VIDEO_CAPABILITY_CE_SCAN_SHIFT			(0)
#define EDID_CEA_VIDEO_CAPABILITY_IT_SCAN_SHIFT			(2)
#define EDID_CEA_VIDEO_CAPABILITY_PT_SCAN_SHIFT			(4)
#define EDID_CEA_VIDEO_CAPABILITY_SCAN_MASK				(3)
#define EDID_CEA_VIDEO_CAPABILITY_SCAN_UNSUPPORTED		(0)
#define EDID_CEA_VIDEO_CAPABILITY_SCAN_OVERSCANNED		(1)
#define EDID_CEA_VIDEO_CAPABILITY_SCAN_UNDERSCANNED		(2)
#define EDID_CEA_VIDEO_CAPABILITY_SCAN_BOTH_SUPPORTED	(3)
#define EDID_CEA_VIDEO_CAPABILITY_QYCC_SELECTABLE		(0x80)
#define EDID_CEA_VIDEO_CAPABILITY_QRGB_SELECTABLE		(0x40)

// EDID_CEA_BLOCK_EXT_TAG_VIDEO_FORMAT_PREFERENCE		(List of 1-byte SVRs)
#define EDID_CEA_SVR_MAX_NUM							(31)
#define EDID_CEA_SVR_DTD_INDEX							(0x80)

// EDID_CEA_BLOCK_EXT_TAG_YUV420_CAPABILITY_MAP			(Bit map of SVDs can support YUV420)

// EDID_CEA_BLOCK_TAG_VENDOR_SPECIFIC
const uint8_t g_abyHDMI_FORUM[3] = { 0xD8, 0x5D, 0xC4 };

#define EDID_HDMI_FORUM_FLAG_1_SCDC_PRESENT				(0x80)
#define EDID_HDMI_FORUM_FLAG_1_RR_CAPABLE				(0x40)
#define EDID_HDMI_FORUM_FLAG_1_LTE_340M_SCRAMBLE		(0x08)
#define EDID_HDMI_FORUM_FLAG_1_INDEPENDENT_VIEW			(0x04)
#define EDID_HDMI_FORUM_FLAG_1_DUAL_VIEW				(0x02)
#define EDID_HDMI_FORUM_FLAG_1_3D_OSD_DISPARITY			(0x01)

#define EDID_HDMI_FORUM_FLAG_2_DC_48BIT_420				(0x04)
#define EDID_HDMI_FORUM_FLAG_2_DC_36BIT_420				(0x02)
#define EDID_HDMI_FORUM_FLAG_2_DC_30BIT_420				(0x01)

typedef struct _EDID_HDMI_FORUM_VSDB {
	uint8_t byDataLength : 5;							// total number of video bytes following
	uint8_t byTagCode : 3;
	uint8_t abyIEEE_OUI[3];								// g_abyHDMI_FORUM
	uint8_t byVersion;									// 1
	uint8_t byMaxTMDSCharacterRate;						// 0 for Rate < 340Mcsc
	uint8_t byFlags1;
	uint8_t byFlags2;
} EDID_HDMI_FORUM_VSDB, *PEDID_HDMI_FORUM_VSDB;

// EDID_CEA_BLOCK_TAG_VENDOR_SPECIFIC
const uint8_t g_abyHDMI_VSDB[3] = { 0x03, 0x0C, 0x00 };

typedef struct _EDID_HDMI_VSDB_HEADER {
	uint8_t byDataLength : 5;							// total number of video bytes following
	uint8_t byTagCode : 3;
	uint8_t abyIEEE_OUI[3];								// g_abyHDMI_VSDB
	uint8_t byAB;										// A[3:0], B[3:0]
	uint8_t byCD;										// C[3:0], D[3:0]
	uint8_t byFlags1;
	uint8_t byMaxTMDSClockFreq;
	uint8_t byFlags2;
	uint8_t byVideoLatency;
	uint8_t byAudioLatency;
	uint8_t byInterlacedVideoLatency;
	uint8_t byInterlacedAudioLatency;
	uint8_t byFlags3;
	uint8_t byHDMI3DLen : 4;
	uint8_t byHDMIVICLen : 4;
	// ...
} EDID_HDMI_VSDB_HEADER, *PEDID_HDMI_VSDB_HEADER;

#pragma pack(pop)

