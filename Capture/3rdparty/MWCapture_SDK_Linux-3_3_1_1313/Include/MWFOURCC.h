////////////////////////////////////////////////////////////////////////////////
// CONFIDENTIAL and PROPRIETARY software of Magewell Electronics Co., Ltd.
// Copyright (c) 2011-2019 Magewell Electronics Co., Ltd. (Nanjing) 
// All rights reserved.
// This copyright notice MUST be reproduced on all authorized copies.
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "LibMWCapture/WinTypes.h"

#ifndef MWFOURCC
#define MWFOURCC(ch0, ch1, ch2, ch3)											\
        ((DWORD)(BYTE)(ch0) | ((DWORD)(BYTE)(ch1) << 8) |							\
        ((DWORD)(BYTE)(ch2) << 16) | ((DWORD)(BYTE)(ch3) << 24))
#endif

/**
 * @ingroup group_fourcc
 * @brief Unknown color formate
 * @details Unknown color formate\n
*/
#define MWFOURCC_UNK		MWFOURCC('U', 'N', 'K', 'N')

/**
 * @ingroup group_fourcc
 * @brief 8bits Grey
 * @details 8bits Grey\n
 * 1 byte per pixel\n
 * Data structure:\n
 * 			   [Y0], [Y1], [Y2], ...\n
 *             ...\n
*/
#define MWFOURCC_GREY		MWFOURCC('G', 'R', 'E', 'Y')					

/**
 * @ingroup group_fourcc
 * @brief 8bits Grey
 * @details 8bits Grey; the same as #MWFOURCC_GREY\n
 * 1 byte per pixel\n
 * Data structure:\n
 * 			   [Y0], [Y1], [Y2], ...\n
 *             ...\n
*/
#define MWFOURCC_Y800		MWFOURCC('Y', '8', '0', '0')

/**
 * @ingroup group_fourcc
 * @brief 8bits Grey
 * @details 8bits Grey; the same as #MWFOURCC_GREY\n
 * 1 byte per pixel\n
 * Data structure:\n
 * 			   [Y0], [Y1], [Y2], ...\n
 *             ...\n
*/
#define MWFOURCC_Y8			MWFOURCC('Y', '8', ' ', ' ')

/**
 * @ingroup group_fourcc
 * @brief 16bits Grey
 * @details 16bits Grey\n
 * 2 bytes per pixel\n
 * Data structure:\n
 * 			   [Y0], [Y1], [Y2], ...\n
 *             ...\n
*/
#define MWFOURCC_Y16		MWFOURCC('Y', '1', '6', ' ')

/**
 * @ingroup group_fourcc
 * @brief 16bits R5G5B5A1
 * @details 16bits R5G5B5A1\n
 * 2 bytes per pixel, R takes 5bits, G takes 5bits, B takes 5bits, A takes 1bit\n
 * Data structure:\n
 * 			   [R5, G5, B5, A1], ...\n
 * 			   ...\n
*/
#define MWFOURCC_RGB15		MWFOURCC('R', 'G', 'B', '5')

/**
 * @ingroup group_fourcc
 * @brief 16bits R5G6B5
 * @details 16bits R5G6B5\n
 * 2 bytes per pixel, R takes 5bits, G takes 5bits, B takes 5bits, A takes 1bit\n
 * Data structure:\n
 * 			   [R5, G6, B5],[R5, G6, B5] ...\n
 * 			   ...\n
*/
#define MWFOURCC_RGB16		MWFOURCC('R', 'G', 'B', '6')

/**
 * @ingroup group_fourcc
 * @brief 24bits R8G8B8
 * @details 24bits R8G8B8\n
 * 3 bytes per pixel, R takes 8bits, G takes 8bits, B takes 8bits\n
 * Data structure:\n
 * 			   [R8, G8, B8],[R8, G8, B8] ...\n
 * 			   ...\n
*/
#define MWFOURCC_RGB24		MWFOURCC('R', 'G', 'B', ' ')					

/**
 * @ingroup group_fourcc
 * @brief 32bits R8G8B8A8
 * @details 32bits R8G8B8A8\n
 * 4 bytes per pixel, R takes 8bits, G takes 8bits, B takes 8bits, A takes 8bits\n
 * Data structure:\n
 * 			   [R8, G8, B8, A8],[R8, G8, B8, A8] ...\n
 * 			   ...\n
*/
#define MWFOURCC_RGBA		MWFOURCC('R', 'G', 'B', 'A')

/**
 * @ingroup group_fourcc
 * @brief 32bits A8R8G8B8
 * @details 32bits A8R8G8B8\n
 * 4 bytes per pixel, R takes 8bits, G takes 8bits, B takes 8bits, A takes 8bits\n
 * Data structure:\n
 * 			   [A8, R8, G8, B8],[A8, R8, G8, B8] ...\n
 * 			   ...\n
*/
#define MWFOURCC_ARGB		MWFOURCC('A', 'R', 'G', 'B')

/**
 * @ingroup group_fourcc
 * @brief 16bits B5G5R5A1
 * @details 16bits B5G5R5A1\n
 * 2 bytes per pixel, B takes 5bits, G takes 5bits, R takes 5bits, A takes 1bits\n
 * Data structure:\n
 * 			   [B5, G5, R5, A1],[B5, G5, R5, A1] ...\n
 * 			   ...\n
*/
#define MWFOURCC_BGR15		MWFOURCC('B', 'G', 'R', '5')

/**
 * @ingroup group_fourcc
 * @brief 16bits B5G6R5
 * @details 16bits B5G6R5\n
 * 2 bytes per pixel, B takes 5bits, G takes 6bits, R takes 5bits\n
 * Data structure:\n
 * 			   [B5, G6, R5],[B5, G6, R5] ...\n
 * 			   ...\n
*/
#define MWFOURCC_BGR16		MWFOURCC('B', 'G', 'R', '6')

/**
 * @ingroup group_fourcc
 * @brief 24bits B8G8R8
 * @details 24bits B8G8R8\n
 * 3 bytes per pixel, B takes 8bits, G takes 8bits, R takes 8bits\n
 * Data structure:\n
 * 			   [B8, G8, R8],[B8, G8, R8] ...\n
 * 			   ...\n
*/
#define MWFOURCC_BGR24		MWFOURCC('B', 'G', 'R', ' ')

/**
 * @ingroup group_fourcc
 * @brief 32bits B8G8R8A8
 * @details 32bits B8G8R8A8\n
 * 4 bytes per pixel, B takes 8bits, G takes 8bits, R takes 8bits, A takes 8bits\n
 * Data structure:\n
 * 			   [B8, G8, R8, A8],[B8, G8, R8, A8] ...\n
 *             ...\n
*/
#define MWFOURCC_BGRA		MWFOURCC('B', 'G', 'R', 'A')

/**
 * @ingroup group_fourcc
 * @brief 32bits A8B8G8R8
 * @details 32bits A8B8G8R8\n
 * 4 bytes per pixel, A takes 8bits, B takes 8bits, G takes 8bits, R takes 8bits\n
 * Data structure:\n
 * 			   [A8, B8, G8, R8],[A8, B8, G8, R8] ...\n
 *             ...\n
*/
#define MWFOURCC_ABGR		MWFOURCC('A', 'B', 'G', 'R')

/**
 * @ingroup group_fourcc
 * @brief NV16
 * @details YUV 8bits 4:2:2 semi-planar(16bits)\n
 * 2 byte per pixel, all Y data in one plane, all UV data in one plane\n
 * Data structure:\n
 * 			   [Y00][Y01][Y02][Y03] ...\n
 * 			   [Y10][Y11][Y12][Y13] ...\n
 * 			   [Y20][Y21][Y22][Y23] ...\n
 * 			   [Y30][Y31][Y32][Y33] ...\n
 * 			   ...\n
 * 			   [U00  V00][U01  V01] ...\n
 * 			   [U10  V10][U11  V11] ...\n
 *			   [U20  V20][U21  V21] ...\n
 * 			   [U30  V30][U31  V31] ...\n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00 U00 V00][Y01 U00 V00][Y02 U01 V01][Y03 U01 V01] ...\n
 * 			   ...\n
*/
#define MWFOURCC_NV16		MWFOURCC('N', 'V', '1', '6')

/**
 * @ingroup group_fourcc
 * @brief NV61
 * @details YUV 8bits 4:2:2 semi-planar (16bits)\n
 * 2 byte per pixel, all Y data in one plane, all UV data in one plane\n
 * Data structure:\n
 * 			   [Y00][Y01][Y02][Y03] ...\n
 * 			   [Y10][Y11][Y12][Y13] ...\n
 * 			   [Y20][Y21][Y22][Y23] ...\n
 * 			   [Y30][Y31][Y32][Y33] ...\n
 * 			   ...\n
 * 			   [V00  U00][V01  U01] ...\n
 * 			   [V10  U10][V11  U11] ...\n
 *			   [V20  U20][V21  U21] ...\n
 * 			   [V30  U30][V31  U31] ...\n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00 U00 V00][Y01 U00 V00][Y02 U01 V01][Y03 U01 V01] ...\n
 * 	           ...\n
*/
#define MWFOURCC_NV61		MWFOURCC('N', 'V', '6', '1')

/**
 * @ingroup group_fourcc
 * @brief I422
 * @details YUV 8bits 4:2:2 plannar (16bits)\n
 * 2 byte per pixel. All Y/U/V data is in one plane respectively.\n
 * Data structure:\n
 * 			   [Y00][Y01][Y02][Y03] ...\n
 * 			   [Y10][Y11][Y12][Y13] ...\n
 * 			   [Y20][Y21][Y22][Y23] ...\n
 * 			   [Y30][Y31][Y32][Y33] ...\n
 * 			   ...\n
 * 			   [U00][U01] ...\n
 * 			   [U10][U11] ...\n
 *			   [U20][U21] ...\n
 * 			   [U30][U31] ...\n
 * 			   ...\n
 * 			   [V00][V01] ...\n
 * 			   [V10][V11] ...\n
 *			   [V20][V21] ...\n
 * 			   [V30][V31] ...\n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00 U00 V00][Y01 U00 V00][Y02 U01 V01][Y03 U01 V01] ...\n
 * 			   ...\n
*/
#define MWFOURCC_I422		MWFOURCC('I', '4', '2', '2')

/**
 * @ingroup group_fourcc
 * @brief YV16
 * @details YUV 8bits 4:2:2 plannar (16bits)\n
 * 2 byte per pixel. All Y/U/V data is in one plane respectively.\n
 * Data structure:\n
 * 			   [Y00][Y01][Y02][Y03] ...\n
 * 			   [Y10][Y11][Y12][Y13] ...\n
 * 			   [Y20][Y21][Y22][Y23] ...\n
 * 			   [Y30][Y31][Y32][Y33] ...\n
 * 			   ...\n
 * 			   [V00][V01] ...\n
 * 			   [V10][V11] ...\n
 *			   [V20][V21] ...\n
 * 			   [V30][V31] ...\n
 * 			   ...\n
 * 			   [U00][U01] ...\n
 * 			   [U10][U11] ...\n
 *			   [U20][U21] ...\n
 * 			   [U30][U31] ...\n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00 U00 V00][Y01 U00 V00][Y02 U01 V01][Y03 U01 V01] ...\n
 * 			   ...\n
*/
#define MWFOURCC_YV16		MWFOURCC('Y', 'V', '1', '6')


/**
 * @ingroup group_fourcc
 * @brief YUY2
 * @details Packed YUV 8bits 4:2:2 (16bits)\n
 * 2 byte per pixel. 2 pixels as a base unit.\n
 * Data structure:\n
 * 			   {[Y00 U00][Y01 V01]} {[Y02 U02][Y03 V03]} ...\n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00 U00 V01][Y01 U00 V01][Y02 U02 V03][Y03 U02 V03] ...\n
 * 			   ...\n
*/
#define MWFOURCC_YUY2       MWFOURCC('Y', 'U', 'Y', '2')

/**
 * @ingroup group_fourcc
 * @brief YUYV
 * @details Packed YUV 8bits 4:2:2 (16bits); the same as #MWFOURCC_YUY2\n
 * 2 byte per pixel. 2 pixels as a base unit.\n
 * Data structure:\n
 * 			   {[Y00 U00][Y01 V01]} {[Y02 U02][Y03 V03]} ...\n
 * 			    ...\n
 * Converts to YUV data as:\n
 * 			   [Y00 U00 V01][Y01 U00 V01][Y02 U02 V03][Y03 U02 V03] ...\n
 * 			   ...\n
*/
#define MWFOURCC_YUYV       MWFOURCC('Y', 'U', 'Y', 'V')

/**
 * @ingroup group_fourcc
 * @brief UYVY
 * @details Packed YUV 8bits 4:2:2 (16bits)\n
 * 2 byte per pixel. 2 pixels as a base unit.\n
 * Data structure:\n
 * 			   {[U00 Y00][V01 Y01]} {[U02 Y02][V03 Y03]} ...\n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00 U00 V01][Y01 U00 V01][Y02 U02 V03][Y03 U02 V03] ...\n
 * 			   ...\n
*/
#define MWFOURCC_UYVY       MWFOURCC('U', 'Y', 'V', 'Y')

/**
 * @ingroup group_fourcc
 * @brief YVYU
 * @details Packed YUV 8bits 4:2:2 (16bits)\n
 * 2 byte per pixel. 2 pixels as a base unit.\n
 * Data structure:\n
 * 			   {[Y00 V00][Y01 U01]} {[Y02 V02][Y03 U03]} ...\n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00 U01 V00][Y01 U01 V00][Y02 U03 V02][Y03 U03 V02] ...\n
 *             ...\n
*/
#define MWFOURCC_YVYU       MWFOURCC('Y', 'V', 'Y', 'U')

/**
 * @ingroup group_fourcc
 * @brief VYUY
 * @details Packed YUV 8bits 4:2:2 (16bits)\n
 * 2 byte per pixel. 2 pixels as a base unit.\n
 * Data structure:\n
 * 			   {[V00 Y00][U01 Y01]} {[V02 Y02][U03 Y03]} ...\n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00 U01 V00][Y01 U01 V00][Y02 U03 V02][Y03 U03 V02] ...\n
 *  		   ...\n
*/
#define MWFOURCC_VYUY       MWFOURCC('V', 'Y', 'U', 'Y')

/**
 * @ingroup group_fourcc
 * @brief I420
 * @details YUV 8bits 4:2:0 planar (12bits)\n
 * A single pixel of the image takes 12bits.\n
 * Data structure:\n
 * 			   [Y00][Y01][Y02][Y03] ...\n
 *  		   [Y10][Y11][Y12][Y13] ...\n
 *  		   [Y20][Y21][Y22][Y23] ...\n
 *  		   [Y30][Y31][Y32][Y33] ...\n
 * 			   ...\n
 * 			   [U00][U01] ...\n
 * 			   [U10][U11] ...\n
 * 	 		   ...\n
 * 			   [V00][V01] ...\n
 * 			   [V10][V11] ...\n
 * 			   ...\n
 * Converts to YUV data as:
 * 			   [Y00 U00 V00][Y01 U00 V00][Y02 U01 V01][Y03 U01 V01] ...\n
 * 			   [Y10 U00 V00][Y11 U00 V00][Y12 U01 V01][Y13 U01 V01] ...\n
 * 			   [Y20 U10 V10][Y21 U10 V10][Y22 U11 V11][Y23 U11 V11] ...\n
 * 			   [Y30 U10 V10][Y31 U10 V10][Y32 U11 V11][Y33 U11 V11] ...\n
 * 			   ...\n
*/
#define MWFOURCC_I420       MWFOURCC('I', '4', '2', '0')

/**
 * @ingroup group_fourcc
 * @brief IYUV
 * @details YUV 8bits 4:2:0 planar (12bits); the same as #MWFOURCC_I420\n
 * A single pixel of the image takes 12bits.\n
 * Data structure:\n
 * 			   [Y00][Y01][Y02][Y03] ...\n
 *  		   [Y10][Y11][Y12][Y13] ...\n
 *  		   [Y20][Y21][Y22][Y23] ...\n
 *  		   [Y30][Y31][Y32][Y33] ...\n
 * 			   ...\n
 * 			   [U00][U01] ...\n
 * 			   [U10][U11] ...\n
 * 	 		   ...\n
 * 			   [V00][V01] ...\n
 * 			   [V10][V11] ...\n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00 U00 V00][Y01 U00 V00][Y02 U01 V01][Y03 U01 V01] ...\n
 * 			   [Y10 U00 V00][Y11 U00 V00][Y12 U01 V01][Y13 U01 V01] ...\n
 * 			   [Y20 U10 V10][Y21 U10 V10][Y22 U11 V11][Y23 U11 V11] ...\n
 * 			   [Y30 U10 V10][Y31 U10 V10][Y32 U11 V11][Y33 U11 V11] ...\n
 * 			   ...\n
*/
#define MWFOURCC_IYUV       MWFOURCC('I', 'Y', 'U', 'V')

/**
 * @ingroup group_fourcc
 * @brief NV12
 * @details YUV 8bits 4:2:0 semi-planar (12bits)\n
 * A single pixel of the image takes 12bits.\n
 * All Y data is in one plane, all UV data is in one plane.\n
 * Data structure:\n
 * 			   [Y00][Y01][Y02][Y03] ...\n
 *  		   [Y10][Y11][Y12][Y13] ...\n
 *  		   [Y20][Y21][Y22][Y23] ...\n
 *  		   [Y30][Y31][Y32][Y33] ...\n
 * 			   ...\n
 * 			   [U00 V00][U01 V01] ...\n
 * 			   [U10 V10][U11 V11] ...\n
 * 			   ...\n
 * Converts to YUV data as:
 * 			   [Y00 U00 V00][Y01 U00 V00][Y02 U01 V01][Y03 U01 V01] ...\n
 * 			   [Y10 U00 V00][Y11 U00 V00][Y12 U01 V01][Y13 U01 V01] ...\n
 * 			   [Y20 U10 V10][Y21 U10 V10][Y22 U11 V11][Y23 U11 V11] ...\n
 * 			   [Y30 U10 V10][Y31 U10 V10][Y32 U11 V11][Y33 U11 V11] ...\n
 * 			   ...\n
*/
#define MWFOURCC_NV12       MWFOURCC('N', 'V', '1', '2')

/**
 * @ingroup group_fourcc
 * @brief YV12
 * @details YUV 8bits 4:2:0 planar (12bits)\n
 * A single pixel of the image takes 12bits.\n
 * Data structure:\n
 * 			   [Y00][Y01][Y02][Y03] ...\n
 *  		   [Y10][Y11][Y12][Y13] ...\n
 *  		   [Y20][Y21][Y22][Y23] ...\n
 *  		   [Y30][Y31][Y32][Y33] ...\n
 * 	 		   ...\n
 * 			   [V00][V01] ...\n
 * 			   [V10][V11] ...\n
 * 			   ...\n
 * 			   [U00][U01] ...\n
 * 			   [U10][U11] ...\n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00 U00 V00][Y01 U00 V00][Y02 U01 V01][Y03 U01 V01] ...\n
 * 			   [Y10 U00 V00][Y11 U00 V00][Y12 U01 V01][Y13 U01 V01] ...\n
 * 			   [Y20 U10 V10][Y21 U10 V10][Y22 U11 V11][Y23 U11 V11] ...\n
 * 			   [Y30 U10 V10][Y31 U10 V10][Y32 U11 V11][Y33 U11 V11] ...\n
 * 			   ...\n
*/
#define MWFOURCC_YV12       MWFOURCC('Y', 'V', '1', '2')

/**
 * @ingroup group_fourcc
 * @brief NV21
 * @details YUV 8bits 4:2:0 semi-planar (12bits)\n
 * A single pixel of the image takes 12bits.\n
 * All Y data is in one plane, all UV data is in one plane.\n
 * Data structure:\n
 * 			   [Y00][Y01][Y02][Y03] ...\n
 *  		   [Y10][Y11][Y12][Y13] ...\n
 *  		   [Y20][Y21][Y22][Y23] ...\n
 *  		   [Y30][Y31][Y32][Y33] ...\n
 * 			   ...\n
 * 			   [V00 U00][V01 U01] ...\n
 * 			   [V10 U10][V11 U11] ...\n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00 U00 V00][Y01 U00 V00][Y02 U01 V01][Y03 U01 V01] ...\n
 * 			   [Y10 U00 V00][Y11 U00 V00][Y12 U01 V01][Y13 U01 V01] ...\n
 * 			   [Y20 U10 V10][Y21 U10 V10][Y22 U11 V11][Y23 U11 V11] ...\n
 * 			   [Y30 U10 V10][Y31 U10 V10][Y32 U11 V11][Y33 U11 V11] ...\n
 * 			   ...\n
*/
#define MWFOURCC_NV21       MWFOURCC('N', 'V', '2', '1')

/**
 * @ingroup group_fourcc
 * @brief P010
 * @details YUV 10bits 4:2:0 semi-planar(24bits)\n
 * A single pixel takes 3 bytes.\n
 * All Y data is in one plane, all UV data is in one plane.\n
 * Data structure:\n
 * 			   [Y00(Y10bits)][Y01(Y10bits)][Y02(Y10bits)][Y03(Y10bits)] ...      \n
 *  		   [Y10(Y10bits)][Y11(Y10bits)][Y12(Y10bits)][Y13(Y10bits)] ...      \n
 *  		   [Y20(Y10bits)][Y21(Y10bits)][Y22(Y10bits)][Y23(Y10bits)] ...      \n
 *  		   [Y30(Y10bits)][Y31(Y10bits)][Y32(Y10bits)][Y33(Y10bits)] ...      \n
 * 			   ...\n
 * 			   [U00(U10bits) V00(V10bits)][U01(U10bits) V01(V10bits)] ...		 \n
 * 			   [U10(U10bits) V10(V10bits)][U11(U10bits) V11(V10bits)] ...	     \n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00(Y10bits) U00(U10bits) V00(V10bits)][Y01(Y10bits) U00(U10bits) V00(V10bits)][Y02(Y10bits) U01(U10bits) V01(V10bits)][Y03(Y10bits) U01(U10bits) V01(V10bits)] ...\n
 * 			   [Y10(Y10bits) U00(U10bits) V00(V10bits)][Y11(Y10bits) U00(U10bits) V00(V10bits)][Y12(Y10bits) U01(U10bits) V01(V10bits)][Y13(Y10bits) U01(U10bits) V01(V10bits)] ...\n
 * 			   [Y20(Y10bits) U10(U10bits) V10(V10bits)][Y21(Y10bits) U10(U10bits) V10(V10bits)][Y22(Y10bits) U11(U10bits) V11(V10bits)][Y23(Y10bits) U11(U10bits) V11(V10bits)] ...\n
 * 			   [Y30(Y10bits) U10(U10bits) V10(V10bits)][Y31(Y10bits) U10(U10bits) V10(V10bits)][Y32(Y10bits) U11(U10bits) V11(V10bits)][Y33(Y10bits) U11(U10bits) V11(V10bits)] ...\n
 * 			   ...\n
*/
#define MWFOURCC_P010		MWFOURCC('P', '0', '1', '0')

/**
 * @ingroup group_fourcc
 * @brief P210
 * @details YUV 10bits 4:2:2 semi-planar (32bits)\n
 * A single pixel takes 4 bytes.\n
 * All Y data is in one plane, all UV data is in one plane.\n
 * Data structure:\n
 * 			   [Y00(Y10bits)][Y01(Y10bits)][Y02(Y10bits)][Y03(Y10bits)] ...      \n
 *  		   [Y10(Y10bits)][Y11(Y10bits)][Y12(Y10bits)][Y13(Y10bits)] ...      \n
 *  		   [Y20(Y10bits)][Y21(Y10bits)][Y22(Y10bits)][Y23(Y10bits)] ...      \n
 *  		   [Y30(Y10bits)][Y31(Y10bits)][Y32(Y10bits)][Y33(Y10bits)] ...      \n
 * 			   ...\n
 * 			   [U00(U10bits) V00(V10bits)][U01(U10bits) V01(V10bits)] ...		 \n
 * 			   [U10(U10bits) V10(V10bits)][U11(U10bits) V11(V10bits)] ...	     \n
 * 			   [U20(U10bits) V20(V10bits)][U21(U10bits) V21(V10bits)] ...		 \n
 * 			   [U30(U10bits) V30(V10bits)][U31(U10bits) V31(V10bits)] ...	     \n
 * 			   ...\n
 * Converts to YUV data as:\n
 * 			   [Y00(Y10bits) U00(U10bits) V00(V10bits)][Y01(Y10bits) U00(U10bits) V00(V10bits)][Y02(Y10bits) U01(U10bits) V01(V10bits)][Y03(Y10bits) U01(U10bits) V01(V10bits)] ...\n
 * 			   [Y10(Y10bits) U10(U10bits) V10(V10bits)][Y11(Y10bits) U10(U10bits) V10(V10bits)][Y12(Y10bits) U11(U10bits) V11(V10bits)][Y13(Y10bits) U11(U10bits) V11(V10bits)] ...\n
 * 			   [Y20(Y10bits) U20(U10bits) V20(V10bits)][Y21(Y10bits) U20(U10bits) V20(V10bits)][Y22(Y10bits) U21(U10bits) V21(V10bits)][Y23(Y10bits) U21(U10bits) V21(V10bits)] ...\n
 * 			   [Y30(Y10bits) U30(U10bits) V30(V10bits)][Y31(Y10bits) U30(U10bits) V30(V10bits)][Y32(Y10bits) U31(U10bits) V31(V10bits)][Y33(Y10bits) U31(U10bits) V31(V10bits)] ...\n
 * 			   ...\n
*/
#define MWFOURCC_P210		MWFOURCC('P', '2', '1', '0')

/**
 * @ingroup group_fourcc
 * @brief IYU2
 * @details Packed YUV 8bits 4:4:4 (24bits)\n
 * A single pixel takes 3 bytes.\n
 * Data structure:\n
 * 			   [U00 Y00 V00][U01 Y01 V01][U02 Y02 V02][U03 Y03 V03] ...\n
 *			   [U10 Y10 V10][U11 Y11 V11][U12 Y12 V12][U13 Y13 V13] ...\n
 * 			   [U20 Y20 V20][U21 Y21 V21][U22 Y22 V22][U23 Y23 V23] ...\n
 * 			   [U30 Y30 V30][U31 Y31 V31][U32 Y32 V32][U33 Y33 V33] ...\n
 * 			   ...\n
*/
#define MWFOURCC_IYU2		MWFOURCC('I', 'Y', 'U', '2')

/**
 * @ingroup group_fourcc
 * @brief V308
 * @details Packed YUV 8bits 4:4:4 (24bits) \n
 * A single pixel takes 3 bytes.\n
 * Data structure:\n
 * 			   [V00 Y00 U00][V01 Y01 U01][V02 Y02 U02][V03 Y03 U03] ...\n
 *			   [V10 Y10 U10][V11 Y11 U11][V12 Y12 U12][V13 Y13 U13] ...\n
 * 			   [V20 Y20 U20][V21 Y21 U21][V22 Y22 U22][V23 Y23 U23] ...\n
 * 			   [V30 Y30 U30][V31 Y31 U31][V32 Y32 U32][V33 Y33 U33] ...\n
 * 			   ...\n
*/
#define MWFOURCC_V308		MWFOURCC('v', '3', '0', '8')


/**
 * @ingroup group_fourcc
 * @brief AYUV
 * @details Packed YUV 8bits 4:4:4 (32bits) \n
 * A single pixel takes 4 bytes.\n
 * Data structure:\n
 * 			   [A00 Y00 U00 V00][A01 Y01 U01 V01][A02 Y02 U02 V02][A03 Y03 U03 V03] ...\n
 *			   [A10 Y10 U10 V10][A11 Y11 U11 V11][A12 Y12 U12 V12][A13 Y13 U13 V13] ...\n
 * 			   [A20 Y20 U20 V20][A21 Y21 U21 V21][A22 Y22 U22 V22][A23 Y23 U23 V23] ...\n
 * 			   [A30 Y30 U30 V30][A31 Y31 U31 V31][A32 Y32 U32 V32][A33 Y33 U33 V33] ...\n
 * 			   ...\n
*/
#define MWFOURCC_AYUV		MWFOURCC('A', 'Y', 'U', 'V')

/**
 * @ingroup group_fourcc
 * @brief UYVA
 * @details Packed YUV 8bits 4:4:4 (32bits) \n
 * A single pixel takes 4 bytes.\n
 * Data structure:\n
 * 			   [U00 Y00 V00 A00][U01 Y01 V01 A01][U02 Y02 V02 A02][U03 Y03 V03 A03] ...\n
 *			   [U10 Y10 V10 A10][U11 Y11 V11 A11][U12 Y12 V12 A12][U13 Y13 V13 A13] ...\n
 * 			   [U20 Y20 V20 A20][U21 Y21 V21 A21][U22 Y22 V22 A22][U23 Y23 V23 A23] ...\n
 * 			   [U30 Y30 V30 A30][U31 Y31 V31 A31][U32 Y32 V32 A32][U33 Y33 V33 A33] ...\n
 * 			   ...\n
*/
#define MWFOURCC_UYVA		MWFOURCC('U', 'Y', 'V', 'A')

/**
 * @ingroup group_fourcc
 * @brief V408
 * @details Packed YUV 8bits 4:4:4 (32bits); the same as #MWFOURCC_UYVA \n
 * A single pixel takes 4 bytes.\n
 * Data structure:\n
 * 			   [U00 Y00 V00 A00][U01 Y01 V01 A01][U02 Y02 V02 A02][U03 Y03 V03 A03] ...\n
 *			   [U10 Y10 V10 A10][U11 Y11 V11 A11][U12 Y12 V12 A12][U13 Y13 V13 A13] ...\n
 * 			   [U20 Y20 V20 A20][U21 Y21 V21 A21][U22 Y22 V22 A22][U23 Y23 V23 A23] ...\n
 * 			   [U30 Y30 V30 A30][U31 Y31 V31 A31][U32 Y32 V32 A32][U33 Y33 V33 A33] ...\n
 * 			   ...\n
*/
#define MWFOURCC_V408		MWFOURCC('v', '4', '0', '8')

/**
 * @ingroup group_fourcc
 * @brief VYUA
 * @details Packed YUV 8bits 4:4:4 (32bits) \n
 * A single pixel takes 4 bytes.\n
 * Data structure:\n
 * 			   [V00 Y00 U00 A00][V01 Y01 U01 A01][V02 Y02 U02 A02][V03 Y03 U03 A03] ...\n
 *			   [V10 Y10 U10 A10][V11 Y11 U11 A11][V12 Y12 U12 A12][V13 Y13 U13 A13] ...\n
 * 			   [V20 Y20 U20 A20][V21 Y21 U21 A21][V22 Y22 U22 A22][V23 Y23 U23 A23] ...\n
 * 			   [V30 Y30 U30 A30][V31 Y31 U31 A31][V32 Y32 U32 A32][V33 Y33 U33 A33] ...\n
 * 			   ...\n
*/
#define MWFOURCC_VYUA		MWFOURCC('V', 'Y', 'U', 'A')

/**
* @ingroup group_fourcc
* @vrief V210
* @details Packed YUV 10bit 4:2:2 (24bits)\n
* 2 byte per pixel\n
* Data structure is:\n
*             [2'b00 V00 Y00 U00][2'b00 Y02 U01 Y01][2'b00 U02 Y03 V01][2'b00 Y05 V02 Y04] ...\n
*             [2'b00 V10 Y10 U10][2'b00 Y12 U11 Y11][2'b00 U12 Y13 V11][2'b00 Y15 V12 Y14] ...\n
*             [2'b00 V20 Y20 U20][2'b00 Y22 U21 Y21][2'b00 U22 Y23 V21][2'b00 Y25 V22 Y24] ...\n
*             [2'b00 V30 Y30 U30][2'b00 Y32 U31 Y31][2'b00 U32 Y33 V31][2'b00 Y35 V32 Y34] ...\n
*             ...\n
*
*/
#define MWFOURCC_V210		MWFOURCC('v', '2', '1', '0')

/**
 * @ingroup group_fourcc
 * @brief Y410
 * @details Packed YUV 10bits 4:4:4 (32bits Y10U10V10A2) \n
 * A single pixel takes 4 bytes.\n
 * Data structure:\n
 * 			   [U00 Y00 V00 A00 (U10Y10V10A2)][U01 Y01 V01 A01 (U10Y10V10A2)][U02 Y02 V02 A02 (U10Y10V10A2)][U03 Y03 V03 A03 (U10Y10V10A2)] ...\n
 *			   [U10 Y10 V10 A10 (U10Y10V10A2)][U11 Y11 V11 A11 (U10Y10V10A2)][U12 Y12 V12 A12 (U10Y10V10A2)][U13 Y13 V13 A13 (U10Y10V10A2)] ...\n
 * 			   [U20 Y20 V20 A20 (U10Y10V10A2)][U21 Y21 V21 A21 (U10Y10V10A2)][U22 Y22 V22 A22 (U10Y10V10A2)][U23 Y23 V23 A23 (U10Y10V10A2)] ...\n
 * 			   [U30 Y30 V30 A30 (U10Y10V10A2)][U31 Y31 V31 A31 (U10Y10V10A2)][U32 Y32 V32 A32 (U10Y10V10A2)][U33 Y33 V33 A33 (U10Y10V10A2)] ...\n
 * 			   ...\n
*/
#define MWFOURCC_Y410		MWFOURCC('Y', '4', '1', '0')

/**
 * @ingroup group_fourcc
 * @brief V410
 * @details Packed YUV 10bits 4:4:4 (32bits Y10U10V10A2)\n
 * A single pixel takes 4 bytes.\n
 * Data structure:\n
 * 			   [A00 U00 Y00 V00 (A2U10Y10V10)][A01 U01 Y01 V01 (A2U10Y10V10)][A02 U02 Y02 V02 (A2U10Y10V10)][A03 U03 Y03 V03 (A2U10Y10V10)] ...\n
 *			   [A10 U10 Y10 V10 (A2U10Y10V10)][A11 U11 Y11 V11 (A2U10Y10V10)][A12 U12 Y12 V12 (A2U10Y10V10)][A13 U13 Y13 V13 (A2U10Y10V10)] ...\n
 * 			   [A20 U20 Y20 V20 (A2U10Y10V10)][A21 U21 Y21 V21 (A2U10Y10V10)][A22 U22 Y22 V22 (A2U10Y10V10)][A23 U23 Y23 V23 (A2U10Y10V10)] ...\n
 * 			   [A30 U30 Y30 V30 (A2U10Y10V10)][A31 U31 Y31 V31 (A2U10Y10V10)][A32 U32 Y32 V32 (A2U10Y10V10)][A33 U33 Y33 V33 (A2U10Y10V10)] ...\n
 * 			   ...\n
*/
#define MWFOURCC_V410		MWFOURCC('v', '4', '1', '0')

/**
 * @ingroup group_fourcc
 * @brief RGB10
 * @details Packed RGB 10bits (32bits R10G10B10A2)\n
 * A single pixel takes 4 bytes.\n
 * Data structure:\n
 * 			   [R00 G00 B00 A00 (R10G10B10A2)][R01 G01 B01 A01 (R10G10B10A2)][R02 G02 B02 A02 (R10G10B10A2)][R03 G03 B03 A03 (R10G10B10A2)] ...\n
 * 			   ...\n
*/
#define MWFOURCC_RGB10		MWFOURCC('R', 'G', '1', '0')

/**
 * @ingroup group_fourcc
 * @brief BGR10
 * @details Packed BGR 10bits (32bits B10G10R10A2)\n
 * A single pixel takes 4 bytes.\n
 * Data structure:\n
 * 			   [B00 G00 R00 A00 (B10G10R10A2)][B01 G01 R01 A01 (B10G10R10A2)][B02 G02 R02 A02 (B10G10R10A2)][B03 G03 R03 A03 (B10G10R10A2)] ...\n
 * 			   ...\n
*/
#define MWFOURCC_BGR10		MWFOURCC('B', 'G', '1', '0')

/**
 * @ingroup group_fourcc
 * @brief Determines whether the color format is RGB
 * @param[in] dwFOURCC			color format
 * @return If the color format is RGB, which returns TRUE; otherwise returns FALSE.
*/
static inline BOOLEAN FOURCC_IsRGB(
	DWORD dwFOURCC
	)
{
	switch (dwFOURCC) {
	case MWFOURCC_RGB15:
	case MWFOURCC_BGR15:
	case MWFOURCC_RGB16:
	case MWFOURCC_BGR16:
	case MWFOURCC_RGB24:
	case MWFOURCC_BGR24:
	case MWFOURCC_RGBA:
	case MWFOURCC_BGRA:
	case MWFOURCC_ARGB:
	case MWFOURCC_ABGR:
	case MWFOURCC_RGB10:
	case MWFOURCC_BGR10:
		return TRUE;
	default:
		return FALSE;
	}
}

/**
 * @ingroup group_fourcc
 * @brief Determines whether the color format is packed
 * @param[in] dwFOURCC			color format
 * @return If the color format is packed, which returns TRUE; otherwise returns FALSE.
*/
static inline BOOLEAN FOURCC_IsPacked(
        DWORD dwFOURCC
        )
{
    switch (dwFOURCC) {
        case MWFOURCC_NV12:
        case MWFOURCC_NV21:
        case MWFOURCC_YV12:
        case MWFOURCC_IYUV:
        case MWFOURCC_I420:
        case MWFOURCC_I422:
        case MWFOURCC_YV16:
        case MWFOURCC_NV16:
        case MWFOURCC_NV61:
        case MWFOURCC_P010:
        case MWFOURCC_P210:
            return FALSE;
        default:
            return TRUE;
    }
}

/**
 * @ingroup group_fourcc
 * @brief Gets the bits that pixel of color format takes
 * @param[in] dwFOURCC			color format
 * @return Returns the bits that pixel of color format takess
*/
static inline int FOURCC_GetBpp(
        DWORD dwFOURCC
        )
{
    switch (dwFOURCC) {
        case MWFOURCC_GREY:
        case MWFOURCC_Y800:
        case MWFOURCC_Y8:
            return 8;

        case MWFOURCC_I420:
        case MWFOURCC_IYUV:
        case MWFOURCC_YV12:
        case MWFOURCC_NV12:
        case MWFOURCC_NV21:
            return 12;

        case MWFOURCC_Y16:
        case MWFOURCC_RGB15:
        case MWFOURCC_BGR15:
        case MWFOURCC_RGB16:
        case MWFOURCC_BGR16:
        case MWFOURCC_YUY2:
        case MWFOURCC_YUYV:
        case MWFOURCC_UYVY:
        case MWFOURCC_YVYU:
        case MWFOURCC_VYUY:
        case MWFOURCC_I422:
        case MWFOURCC_YV16:
        case MWFOURCC_NV16:
        case MWFOURCC_NV61:
            return 16;

        case MWFOURCC_IYU2:
        case MWFOURCC_V308:
        case MWFOURCC_RGB24:
        case MWFOURCC_BGR24:
        case MWFOURCC_P010:
	    case MWFOURCC_V210:
            return 24;

        case MWFOURCC_AYUV:
        case MWFOURCC_UYVA:
        case MWFOURCC_V408:
        case MWFOURCC_VYUA:
        case MWFOURCC_RGBA:
        case MWFOURCC_BGRA:
        case MWFOURCC_ARGB:
        case MWFOURCC_ABGR:
        case MWFOURCC_Y410:
        case MWFOURCC_V410:
        case MWFOURCC_P210:
            return 32;

        default:
            return 0;
    }
}

/**
 * @ingroup group_fourcc
 * @brief Counts the number of bytes that a line data of image takes, depending on the width of image and the color format.
 * @param[in] 	dwFOURCC			Color format
 * @param[in] 	cx					Width of a line
 * @param[in]	dwAlign				Byte alignment
 * @return Returns the the number of bytes that a line data of image takes.
*/
static inline DWORD FOURCC_CalcMinStride(
	DWORD dwFOURCC,
	int cx,
	DWORD dwAlign
	)
{
    BOOLEAN bPacked = FOURCC_IsPacked(dwFOURCC);

    DWORD cbLine;

    if (bPacked) {
        if (dwFOURCC == MWFOURCC_V210) {
            cx = (cx + 47) / 48 * 48;
            cbLine = cx * 8 / 3;
        } else {
            int nBpp = FOURCC_GetBpp(dwFOURCC);
            cbLine = (cx * nBpp) / 8;
        }
    } else {
        switch (dwFOURCC) {
            case MWFOURCC_P010:
            case MWFOURCC_P210:
                cbLine = cx * 2;
                break;
            default:
                cbLine = cx;
                break;
        }
    }

    return (cbLine + dwAlign - 1) & ~(dwAlign - 1);
}

/**
 * @ingroup group_fourcc
 * @brief Counts the number of bytes that a frame takes, depending on the color format, resolution and the line width.
 * @param[in] 	dwFOURCC			Color format
 * @param[in] 	cx					Image width
 * @param[in]	cy					Image height
 * @param[in]	cbStride			The bytes of line width
 * @return Returns the number of bytes that the image takes.
*/
static inline DWORD FOURCC_CalcImageSize(
	DWORD dwFOURCC,
	int cx,
	int cy,
	DWORD cbStride
	)
{
    BOOLEAN bPacked = FOURCC_IsPacked(dwFOURCC);

    if (bPacked) {
        DWORD cbLine;

        if (dwFOURCC == MWFOURCC_V210) {
            cx = (cx + 47) / 48 * 48;
            cbLine = cx * 8 / 3;
        } else {
            int nBpp = FOURCC_GetBpp(dwFOURCC);
            cbLine = (cx * nBpp) / 8;
        }

        if (cbStride < cbLine)
            return 0;

        return cbStride * cy;
    }
    else {
        if (cbStride < (DWORD)cx)
            return 0;

        switch (dwFOURCC) {
            case MWFOURCC_NV12:
            case MWFOURCC_NV21:
            case MWFOURCC_YV12:
            case MWFOURCC_IYUV:
            case MWFOURCC_I420:
                if ((cbStride & 1) || (cy & 1))
                    return 0;
                return cbStride * cy * 3 / 2;
            case MWFOURCC_I422:
            case MWFOURCC_YV16:
            case MWFOURCC_NV16:
            case MWFOURCC_NV61:
                if (cbStride & 1)
                    return 0;
                return cbStride * cy * 2;
            case MWFOURCC_P010:
                if ((cbStride & 3) || (cy & 1))
                    return 0;
                return cbStride * cy * 3 / 2;
            case MWFOURCC_P210:
                if (cbStride & 3)
                    return 0;
                return cbStride * cy * 2;

            default:
                return 0;
        }
    }
}

#pragma pack(push, 1)
typedef struct tagKS_BITMAPINFOHEADER {
  DWORD biSize;
  int   biWidth;
  int   biHeight;
  WORD  biPlanes;
  WORD  biBitCount;
  DWORD biCompression;
  DWORD biSizeImage;
  int   biXPelsPerMeter;
  int   biYPelsPerMeter;
  DWORD biClrUsed;
  DWORD biClrImportant;
} KS_BITMAPINFOHEADER, *PKS_BITMAPINFOHEADER;
#pragma pack(pop)
#define KS_BI_RGB           0L
#define KS_BI_RLE8          1L
#define KS_BI_RLE4          2L
#define KS_BI_BITFIELDS     3L
#define MWCAP_BITMAPINFOHEADER	KS_BITMAPINFOHEADER
#define MWCAP_BI_RGB			KS_BI_RGB
#define MWCAP_BI_BITFIELDS		KS_BI_BITFIELDS

/**
 * @ingroup group_fourcc
 * @brief Determins whether the mask is the same as specified color format.
 * @param[in] 	pdwMasks			Color format mask
 * @param[in] 	dwRedMask			Red mask
 * @param[in]	dwGreenMask			Green mask
 * @param[in]	dwBlueMask			Blue mask
 * @return If the mask is the same as specified color format, it returns TRUE; otherwise, which returns FALSE.
*/
static inline BOOLEAN FOURCC_IsMask(const DWORD * pdwMasks, DWORD dwRedMask, DWORD dwGreenMask, DWORD dwBlueMask)
{
	return ((pdwMasks[0] == dwRedMask) && (pdwMasks[1] == dwGreenMask) && (pdwMasks[2] == dwBlueMask));
}

/**
 * @ingroup group_fourcc
 * @brief Gets color format from the bitmap header
 * @param[in] 	biCompression		Bitmap compression format
 * @param[in] 	biBitCount			Color bit counts
 * @param[in]	pdwMasks			Color mask
 * @return Returns the bitmap color format fits the mask.
*/
static inline DWORD FOURCC_GetFromBitmapHeader(
	DWORD biCompression,
	WORD biBitCount,
	DWORD * pdwMasks
	)
{
	switch (biCompression) {
	case MWCAP_BI_RGB:
		switch (biBitCount) {
		case 16:
			return MWFOURCC_BGR15;
		case 24:
			return MWFOURCC_BGR24;
		case 32:
			return MWFOURCC_BGRA;
		default:
			return MWFOURCC_UNK;
		}
		break;

	case MWCAP_BI_BITFIELDS:
	{
		switch (biBitCount) {
		case 16:
			if (FOURCC_IsMask(pdwMasks, 0x0000F800, 0x000007E0, 0x0000001F))
				return MWFOURCC_BGR16;
			else if (FOURCC_IsMask(pdwMasks, 0x0000001F, 0x000007E0, 0x0000F800))
				return MWFOURCC_RGB16;
			else if (FOURCC_IsMask(pdwMasks, 0x00007C00, 0x000003E0, 0x0000001F))
				return MWFOURCC_BGR15;
			else if (FOURCC_IsMask(pdwMasks, 0x0000001F, 0x000003E0, 0x00007C00))
				return MWFOURCC_RGB15;
			else
				return MWFOURCC_UNK;

		case 24:
			if (FOURCC_IsMask(pdwMasks, 0x00FF0000, 0x0000FF00, 0x000000FF))
				return MWFOURCC_BGR24;
			else if (FOURCC_IsMask(pdwMasks, 0x000000FF, 0x0000FF00, 0x00FF0000))
				return MWFOURCC_RGB24;
			else
				return MWFOURCC_UNK;

		case 32:
			if (FOURCC_IsMask(pdwMasks, 0x00FF0000, 0x0000FF00, 0x000000FF))
				return MWFOURCC_BGRA;
			else if (FOURCC_IsMask(pdwMasks, 0x000000FF, 0x0000FF00, 0x00FF0000))
				return MWFOURCC_RGBA;
			else if (FOURCC_IsMask(pdwMasks, 0xFF000000, 0x00FF0000, 0x0000FF00))
				return MWFOURCC_ABGR;
			else if (FOURCC_IsMask(pdwMasks, 0x0000FF00, 0x00FF0000, 0xFF000000))
				return MWFOURCC_ARGB;
			else
				return MWFOURCC_UNK;

		default:
			return MWFOURCC_UNK;
		}
	}
	break;

	default:
		return biCompression;
	}
}

/**
 * @ingroup group_fourcc
 * @brief Gets color format from the bitmap header.
 * @param[in] 	pbmih		Bitmap header address
 * @return Returns the color format which fits the mask.
*/
static inline DWORD FOURCC_GetFromBitmapHeader2(
	const MWCAP_BITMAPINFOHEADER * pbmih
	)
{
	DWORD *pdwMasks = (DWORD *)(pbmih + 1);
	return FOURCC_GetFromBitmapHeader(pbmih->biCompression, pbmih->biBitCount, pdwMasks);
}

