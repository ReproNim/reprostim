/************************************************************************************************/
// MWCapture.h : header file

// MAGEWELL PROPRIETARY INFORMATION

// The following license only applies to head files and library within Magewell's SDK 
// and not to Magewell's SDK as a whole. 

// Copyrights © Nanjing Magewell Electronics Co., Ltd. ("Magewell") All rights reserved.

// Magewell grands to any person who obtains the copy of Magewell's head files and library 
// the rights,including without limitation, to use on the condition that the following terms are met:
// - The above copyright notice shall be retained in any circumstances.
// -The following disclaimer shall be included in the software and documentation and/or 
// other materials provided for the purpose of publish, distribution or sublicense.

// THE SOFTWARE IS PROVIDED BY MAGEWELL "AS IS" AND ANY EXPRESS, INCLUDING BUT NOT LIMITED TO,
// THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
// IN NO EVENT SHALL MAGEWELL BE LIABLE 

// FOR ANY CLAIM, DIRECT OR INDIRECT DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT,
// TORT OR OTHERWISE, ARISING IN ANY WAY OF USING THE SOFTWARE.

// CONTACT INFORMATION:
// SDK@magewell.net
// http://www.magewell.com/
//
/************************************************************************************************/
#pragma once

#ifdef LIBMWCAPTURE_EXPORTS
#define LIBMWCAPTURE_API __declspec(dllexport)
#elif LIBMWCAPTURE_DLL
#define LIBMWCAPTURE_API __declspec(dllimport)
#else
#define LIBMWCAPTURE_API 
#endif

#include <stdint.h>
#include "MWLinux.h"
#include "MWCaptureExtension.h"

#ifdef __cplusplus

extern "C"
{
#endif

/**
 * @ingroup group_functions_ecocapture
 * @brief Starts video capturing for Eco Capture device.
 * @param[in] hChannel      	Opened channel handle
 * @param[in] pEcoCaptureOpen   Eco video capture parameters
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 */
MW_RESULT
LIBMWCAPTURE_API
MWStartVideoEcoCapture(
	HCHANNEL 						hChannel,
	MWCAP_VIDEO_ECO_CAPTURE_OPEN	*pEcoCaptureOpen
	);

/**
 * @ingroup group_functions_ecocapture
 * @brief Sets capture parameters for Eco capture card
 * @param[in] hChannel      	Opened channel handle
 * @param[in] pSettings        	Eco capture parameters
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details 
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * 	...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_VIDEO_ECO_CAPTURE_SETTINGS t_setting;
 * t_setting.xx=...;
 * ...
 * MWSetVideoEcoCaptureSettings(hChannel ,& t_setting);
 * ...
 * MWCloseChannel(hChannel);
@endcode
*/
MW_RESULT
	LIBMWCAPTURE_API
	MWSetVideoEcoCaptureSettings(
	HCHANNEL 							hChannel,
	MWCAP_VIDEO_ECO_CAPTURE_SETTINGS	*pSettings
	);

/**
 * @ingroup group_functions_ecocapture
 * @brief Sets storage frames for Eco to capture video frames
 * @param[in] hChannel      	Opened channel handle
 * @param[in] pFrame           	Storage frames of Eco to capture video frame
 * @return Function return values are as follows:
 * <table>
 * 		<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * It always works with [MWStartVideoEcoCapture](@ref MWStartVideoEcoCapture). \n
 */
MW_RESULT
LIBMWCAPTURE_API
MWCaptureSetVideoEcoFrame(
	HCHANNEL 						hChannel,
	MWCAP_VIDEO_ECO_CAPTURE_FRAME   *pFrame
	);

/**
 * @ingroup group_functions_ecocapture
 * @brief Gets status of Eco capture card, gets captured video frames.
 * @param[in] hChannel      Opened channel handle
 * @param[out] pStatus      Eco capture status
 * @return Function return values are as follows:
 * <table>
 * 		<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * It always works with [MWStartVideoEcoCapture](@ref MWStartVideoEcoCapture) \n
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWGetVideoEcoCaptureStatus(
	HCHANNEL 						hChannel,
	MWCAP_VIDEO_ECO_CAPTURE_STATUS  *pStatus
	);

/**
 * @ingroup group_functions_ecocapture
 * @brief Stops Eco capture
 * @param[in] hChannel      	Opened channel handle
 * @return Function return values are as follows:
 * <table>
 * 		<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * It always works with [MWStartVideoEcoCapture](@ref MWStartVideoEcoCapture) \n
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWStopVideoEcoCapture(
	HCHANNEL 						hChannel
	);

#ifdef __cplusplus
}
#endif
