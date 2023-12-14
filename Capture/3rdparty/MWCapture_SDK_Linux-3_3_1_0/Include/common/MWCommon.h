////////////////////////////////////////////////////////////////////////////////
// CONFIDENTIAL and PROPRIETARY software of Magewell Electronics Co., Ltd.
// Copyright (c) 2011-2014 Magewell Electronics Co., Ltd. (Nanjing) 
// All rights reserved.
// This copyright notice MUST be reproduced on all authorized copies.
////////////////////////////////////////////////////////////////////////////////

#pragma once

#pragma pack(push)
#pragma pack(1)

// Firmware header
#define MW_SERIAL_NO_LEN				16
#define MW_FAMILY_NAME_LEN				64
#define MW_PRODUCT_NAME_LEN				64

enum _MW_FAMILY_ID {
	MW_FAMILY_ID_PRO_CAPTURE			= 0x00,
	MW_FAMILY_ID_VALUE_CAPTURE			= 0x01,
	MW_FAMILY_ID_USB_CAPTURE			= 0x02
};

typedef int32_t MW_FAMILY_ID;

typedef struct _MW_DATE_TIME {
	uint16_t							wYear;
	uint8_t								byMonth;
	uint8_t								byDay;
	uint8_t								byHour;
	uint8_t								byMinute;
	uint8_t								bySecond;
	uint8_t								byReserved;
} MW_DATE_TIME;

#define MW_FIRMWARE_HEADER_MAGIC		'HFWM'
#define MW_FIRMWARE_HEADER_VERSION		1
#define MW_FIRMWARE_NAME_LEN			64
#define MW_FIRMWARE_SECTION_NAME_LEN	16

#define MW_MAX_NUM_FIRMWARE_SECTIONS	16

// Compatible ID: wProductID, chHardwareVersion and byFirmwareID
typedef struct _MW_FIRMWARE_INFO_HEADER {
	uint32_t							dwMagic;
	uint32_t							dwCheckSum;
	uint16_t							wVersion;
	uint16_t							cbHeader;
	uint16_t							wProductID;
	char								chHardwareVersion;
	uint8_t								byFirmwareID;
	uint32_t							dwFirmwareVersion;
	char								szProductName[MW_PRODUCT_NAME_LEN];
	char								szFirmwareName[MW_FIRMWARE_NAME_LEN];
	MW_DATE_TIME						dtBuild;
	uint8_t								cSections;
} MW_FIRMWARE_INFO_HEADER;

typedef struct _MW_FIRMWARE_SECTION_HEADER {
	int8_t								szName[MW_FIRMWARE_SECTION_NAME_LEN];
	uint32_t							cbOffset;
	uint32_t							cbSection;
	uint32_t							dwCheckSum;
} MW_FIRMWARE_SECTION_HEADER;

typedef struct _MW_FIRMWARE_HEADER {
	MW_FIRMWARE_INFO_HEADER				infoHeader;
	MW_FIRMWARE_SECTION_HEADER			aSectionHeaders[MW_MAX_NUM_FIRMWARE_SECTIONS];
} MW_FIRMWARE_HEADER;

#pragma pack(pop)
