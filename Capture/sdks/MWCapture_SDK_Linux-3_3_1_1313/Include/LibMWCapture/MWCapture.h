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
#include "MWProCapture.h"
#include "MWCaptureExtension.h"
#include "MWUSBCapture.h"
#include "MWUSBCaptureExtension.h"
#include "../ProductVer.h"
#ifdef __cplusplus

extern "C"
{
#endif

/**
 * @ingroup group_functions_common
 * @brief Gets the version number of SDK.
 * @param[out] pbyMaj      Major version number
 * @param[out] pbyMin      Minor version number
 * @param[out] pwBuild     Build version number
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
 * @note Always returns #MW_SUCCEEDED, but the specified version number would not be filled in if an invalid value is input.
 * @details Usage:\n
 * Calls the API wherever you need, even before the MWCaptureInitInstance(). \n
 *
*/
static inline
MW_RESULT
MWGetVersion(
	BYTE*							pbyMaj,
	BYTE*							pbyMin,
	WORD*							pwBuild
	)
{
    if (pbyMaj != NULL)
        *pbyMaj = VER_MAJOR;

    if (pbyMin != NULL)
        *pbyMin = VER_MINOR;
#ifdef VER_BUILD
    if (pwBuild != NULL)
        *pwBuild = VER_BUILD;
#else
    if (pwBuild != NULL)
        *pwBuild = 0;
#endif
    return MW_SUCCEEDED;

}
/**
 * @ingroup group_functions_common+
 * @brief Initializes the MWCapture interfaces.
 * @return  A Boolean variable. True if the initialization is successful, otherwise returns False.
 * @details  Mainly uses the API to start a device-monitoring thread.\n
 * It is recommended to call this api once before using SDK to initialize MWCapture. It works with [MWCaptureExitInstance](@ref MWCaptureExitInstance).
*/
BOOL
LIBMWCAPTURE_API
MWCaptureInitInstance(
	);

	
/**
 * @ingroup group_functions_common
 * @brief Quits instance.
 * @details The API is used to quit the current instance. It always used with [MWCaptureInitInstance](@ref MWCaptureInitInstance).\n
*/
void
LIBMWCAPTURE_API
MWCaptureExitInstance(
	);

/**
 * @ingroup group_functions_common
 * @brief  Refreshes device list.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Calls the API to refresh device list when the connected devices changed.\n
*/
MW_RESULT
LIBMWCAPTURE_API
MWRefreshDevice(
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the total number of channels
 * @return  The total number of channels
 * @details Usage: \n
 * @code 
 * MWRefreshDevice();
 * int t_n_channel_count=MWGetChannelCount();
 * @endcode
*/
int 
LIBMWCAPTURE_API
MWGetChannelCount(
	);

/**
 * @ingroup group_functions_common
 * @brief  Gets the channel info by its index.
 * @param[in] nIndex      			Channel index, ranges from 0 to ([MWGetChannelCount()](@ref MWGetChannelCount) - 1).
 * @param[out] pChannelInfo        	Channel infomation 
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code
 * MWCAP_CHANNEL_INFO t_info;
 * MWGetChannelInfoByIndex(k,&t_info);
 * @endcode
*/
MW_RESULT
LIBMWCAPTURE_API
MWGetChannelInfoByIndex(
	int								nIndex,
	MWCAP_CHANNEL_INFO *			pChannelInfo
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the product family based on the index.
 * @param[in] nIndex      			Channel index, from 0 to ([MWGetChannelCount()](@ref MWGetChannelCount) - 1)
 * @param[out] pFamilyInfo      	A pointer to the struct of #MWCAP_PRO_CAPTURE_INFO, #MWCAP_ECO_CAPTURE_INFO or #MWUSBCAP_CAPTURE_INFO that returns the product family of your device. 
 * @param[in] dwSize     			The size of the struct that the pFamilyInfo points to.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets the product family of the device based on the index.\n
 * It is supported by the Pro/Eco/USB family.\n
 * Code for Pro capture family:\n
 * @code
 * MWCAP_PRO_CAPTURE_INFO t_pro_info;
 * MWGetFamilyInfoByIndex(k,&t_pro_info,sizeof(MWCAP_PRO_CAPTURE_INFO));
 * @endcode
 * Code for Eco capture family:\n
 * @code
 * MWCAP_ECO_CAPTURE_INFO t_eco_info;
 * MWGetFamilyInfoByIndex(k,&t_t_eco_info,sizeof(MWCAP_ECO_CAPTURE_INFO));
 * @endcode
 * Code for USB capture family:\n
 * @code
 * MWUSBCAP_CAPTURE_INFO t_usb_info;
 * MWGetFamilyInfoByIndex(k,&t_usb_info,sizeof(MWUSBCAP_CAPTURE_INFO));
 * @endcode
*/
MW_RESULT
LIBMWCAPTURE_API
MWGetFamilyInfoByIndex(
	int								nIndex,
	LPVOID							pFamilyInfo,
	DWORD							dwSize
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the instance path of capture device based on the index.
 * @param[in] nIndex			Channel index, from 0 to ([MWGetChannelCount()](@ref MWGetChannelCount) - 1)
 * @param[out] pDevicePath      Path of the device
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets the instance path of capture device on its index\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetDevicePath(
	int								nIndex,
	char*							pDevicePath
);

/**
 * @ingroup group_functions_common
 * @brief Opens capture channel by device instance path
 * @param[in] pszDevicePath      Device instance path
 * @return  Returns channel handle if the API call succeeded, otherwise returns NULL.
 * @details Usage: \n
 * Opens capture channel according to device instance path. Gets ready for work.
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * @endcode
*/
HCHANNEL
LIBMWCAPTURE_API
MWOpenChannelByPath(
	const char*					pszDevicePath
	);

/**
 * @ingroup group_functions_common
 * @brief Closes capture channel.
 * @param[in] hChannel      The opened channel handle
 * @details Usage: \n
 * Closes the capture channel according to the channel handle of the capture device.
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
*/
void
LIBMWCAPTURE_API
MWCloseChannel(
	HCHANNEL						hChannel
	);

/**
 * @ingroup group_functions_common
 * @brief  Gets channel information
 * @param[in] hChannel      	The Channel handle
 * @param[out] pChannelInfo     Channel information
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_CHANNEL_INFO t_info;
 * MWGetChannelInfo(t_channel,&t_info);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode 
*/
MW_RESULT
LIBMWCAPTURE_API
MWGetChannelInfo(
	HCHANNEL						hChannel,
	MWCAP_CHANNEL_INFO *			pChannelInfo
	);

/**
 * @ingroup group_functions_common
 * @brief  Gets attributions of product family which the capture device belongs to 
 * @param[in] hChannel      	Channel handle
 * @param[out] pFamilyInfo     	Returns attributions of product family which the capture device belongs to.
 * @param[in] dwSize     		The size of the struct which pFamilyInfo points to.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets attributions of product family which the capture device belongs to, according to its channel handle.
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * //Pro:
 * MWCAP_PRO_CAPTURE_INFO t_pro_info;
 * MWGetFamilyInfo(t_channel,&t_pro_info,sizeof(MWCAP_PRO_CAPTURE_INFO));
 * //Eco:
 * MWCAP_ECO_CAPTURE_INFO t_eco_info;
 * MWGetFamilyInfo(t_channel,&t_t_eco_info,sizeof(MWCAP_ECO_CAPTURE_INFO));
 * //USB:
 * MWUSBCAP_CAPTURE_INFO t_usb_info;
 * MWGetFamilyInfo(t_channel,&t_usb_info,sizeof(MWUSBCAP_CAPTURE_INFO));
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
*/
MW_RESULT
LIBMWCAPTURE_API
MWGetFamilyInfo(
	HCHANNEL						hChannel,
	LPVOID							pFamilyInfo,
	DWORD							dwSize
	);

/**
 * @ingroup group_functions_common
 * @brief Gets video capture capability of the specified channel
 * @param[in] hChannel      	Channel handle
 * @param[out] pVideoCaps      	A pointer to struct #MWCAP_VIDEO_CAPS, which returns video capture capability of the channel
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_CAPS t_caps;
 * MWGetVideoCaps(t_channel,&t_caps);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
*/
MW_RESULT
LIBMWCAPTURE_API
MWGetVideoCaps(
	HCHANNEL						hChannel,
	MWCAP_VIDEO_CAPS*				pVideoCaps
	);
	
/**
 * @ingroup group_functions_common
 * @brief   Gets audio capture capability of the channel
 * @param[in] hChannel      	Channel handle
 * @param[out] pAudioCaps      	A pointer to struct #MWCAP_AUDIO_CAPS, which returns audio capture capability of the channel.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_AUDIO_CAPS t_caps;
 * MWGetAudioCaps(t_channel,&t_caps);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
*/
MW_RESULT
LIBMWCAPTURE_API
MWGetAudioCaps(
	HCHANNEL						hChannel,
	MWCAP_AUDIO_CAPS*				pAudioCaps
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the input video signal types supported by the channel.
 * @param[in] hChannel      			Channel handle
 * @param[out] pdwInputSource      		Returns the input video signal types supported by the channel. When being set to NULL, pdwInputCount returns the number of video signal types supported by the channel.
 * @param[in,out] pdwInputCount     	As an input parameter, it indicates the size of array that pdwInputSource points to. As an output parameter, it returns the number of video signal types supported by the channel.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code.
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * DWORD dwVideoInputCount = 0;
 * MW_RESULT xr = MWGetVideoInputSourceArray(hChannel, NULL, &dwVideoInputCount);
 * if (xr == MW_SUCCEEDED && dwVideoInputCount > 0) {
 * 	DWORD* pVideoInput = new DWORD[dwVideoInputCount];
 * 	xr=MWGetVideoInputSourceArray(hChannel,pVideoInput, &dwVideoInputCount);
 * 	if (xr == MW_SUCCEEDED) {
 * 		char szInputName[16] = { 0 };
 * 		for (DWORD i = 0; i < dwVideoInputCount; i++) {
 * 			GetVideoInputName(pVideoInput[i], szInputName, 16);
 * 			printf("[%d] %s\n", i, szInputName);
 * 		}
 * 	}
 * 	delete[] pVideoInput;
 * }
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
*/
MW_RESULT
LIBMWCAPTURE_API
MWGetVideoInputSourceArray(
	HCHANNEL						hChannel,
	DWORD*							pdwInputSource,
	DWORD*							pdwInputCount
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the input audio signal types supported by the channel
 * @param[in] hChannel      			Channel handle
 * @param[out] pdwInputSource      		Returns the input audio signal types supported by the channel. When being set to NULL, pdwInputCount returns the number of audio signal types supported by the channel.
 * @param[in,out] pdwInputCount     	As an input parameter, it indicates the size of array that pdwInputSource points to. As an output parameter, it returns the number of audio signal types supported by the channel.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * DWORD dwAudioInputCount = 0;
 * xr = MWGetAudioInputSourceArray(hChannel, NULL, &dwAudioInputCount);
 * if (xr == MW_SUCCEEDED && dwAudioInputCount > 0) {
 * 	DWORD* pAudioInput = new DWORD[dwAudioInputCount];
 * 	xr=MWGetAudioInputSourceArray(hChannel,pAudioInput,&dwAudioInputCount);
 * 	if (xr == MW_SUCCEEDED) {
 * 		char szInputName[16] = { 0 };
 * 		for (DWORD i = 0; i < dwAudioInputCount; i++) {
 * 			GetAudioInputName(pAudioInput[i], szInputName, 16);
 * ...
 * 		}
 * 	}
 * 	delete[] pAudioInput;
 * }
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetAudioInputSourceArray(
	HCHANNEL						hChannel,
	DWORD*							pdwInputSource,
	DWORD*							pdwInputCount
	);

	
/**
 * @ingroup group_functions_common
 * @brief Gets the scan state of input source.
 * @param[in] hChannel      Channel handle
 * @param[out] pbScan      	The return value indicates whether it is in scanning. 1 indicates true, AutoScan; 0 indicates false, not Autoscan.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets the scan state of input source. That is whether the input source is automatically scanned. If multiple sources are connected, the device will automatically capture the valid one.
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * BOOLEAN t_b_scan;
 * MWGetInputSourceScan(t_channel,&t_b_scan);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetInputSourceScan(
	HCHANNEL 						hChannel,
	BOOLEAN*						pbScan
	);

/**
 * @ingroup group_functions_common
 * @brief Sets the scan state of input source.
 * @param[in] hChannel      		Channel handle
 * @param[in] bScan      			Indicates the scanned states. 1 indicates true, AutoScan; 0 indicates false, not Autoscans.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets whether to automatically scan the input interface captured channel. \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * BOOLEAN t_b_scan;
 * MWSetInputSourceScan(t_channel,t_b_scan);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWSetInputSourceScan(
	HCHANNEL 						hChannel,
	BOOLEAN							bScan
	);

/**
 * @ingroup group_functions_common
 * @brief  Gets whether the input audio input source  is related to video input source 
 * @param[in] hChannel      		Channel handle
 * @param[out] pbLink      	    	Returns whether the audio input source is related to the video input source 
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets whether the audio input source is linked to video according to the channel handle. If it is TRUE, audio link video source is enabled by default.
 * Which means when there are multiple input sources, the video input source will automate link its audio. If it returns FALSE,
 * the video input would not match probably, you can use [MWSetVideoInputSource](@ref MWSetVideoInputSource) and  
 * [MWSetAudioInputSource](@ref MWSetAudioInputSource)
 * to set the related link state.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * BOOLEAN t_b_link;
 * MWGetAVInputSourceLink(t_channel,&t_b_link);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetAVInputSourceLink(
	HCHANNEL 						hChannel,
	BOOLEAN*						pbLink
	);

/**
 * @ingroup group_functions_common
 * @brief  Sets whether the input video source is linked to its audio automatically.
 * @param[in] hChannel      	Channel handle
 * @param[in] bLink      		Sets whether the audio input source link the video input source 
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets whether the audio input source link the video input source automatically.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * BOOLEAN t_b_link;
 * MWSetAVInputSourceLink(t_channel,t_b_link);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWSetAVInputSourceLink(
	HCHANNEL 						hChannel,
	BOOLEAN							bLink
	);

/**
 * @ingroup group_functions_common
 * @brief Gets current video input source of the channel.
 * @param[in] hChannel      		Channel handle
 * @param[out] pdwSource      		Returns current video input source
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets current video input source of the channel.\n
 * The definition of pdwSource refers to #MWCAP_VIDEO_INPUT_TYPE. 
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * DWORD dwVideoInput = 0;
 * MWGetVideoInputSource(t_channel, &dwVideoInput);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetVideoInputSource(
	HCHANNEL						hChannel,
	DWORD*							pdwSource
	);

/**
 * @ingroup group_functions_common
 * @brief Sets the video input source of the specified channel. 
 * @param[in] hChannel     Channel handle
 * @param[in] dwSource     Sets current video input source
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets the video input source of the specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * DWORD dwVideoInput = 0;
 * dwVideoInput=INPUT_SOURCE(MWCAP_VIDEO_INPUT_TYPE_HDMI, 0);
 * MWSetVideoInputSource(t_channel, &dwVideoInput);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWSetVideoInputSource(
	HCHANNEL						hChannel,
	DWORD							dwSource
	);

/**
 * @ingroup group_functions_common
 * @brief Gets current input audio source of the specified channel.
 * @param[in] hChannel      	Channel handle
 * @param[out] pdwSource      	Returns current input audio source.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets current input audio of the specified channel.
 * The definition of pdwSource refers to #INPUT_TYPE. \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * DWORD dwAudioInput = 0;
 * MWGetAudioInputSource(t_channel, &dwAudioInput);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetAudioInputSource(
	HCHANNEL						hChannel,
	DWORD*							pdwSource
	);

/**
 * @ingroup group_functions_common
 * @brief Sets current audio input source of specified channel.
 * @param[in] hChannel      Channel handle
 * @param[in] dwSource      Sets current audio input source
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets current audio input source of specified channel.\n
 * The definition of dwSource refers to #INPUT_TYPE. \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * DWORD dwAudioInput =INPUT_TYPE(MWCAP_AUDIO_INPUT_TYPE_HDMI, 0);
 * MWSetAudioInputSource(hChannel, dwAudioInput);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWSetAudioInputSource(
	HCHANNEL						hChannel,
	DWORD							dwSource
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the EDID of specified channel
 * @param[in] hChannel     Channel handle
 * @param[out] pbyData     Returns EDID
 * @param[in,out] pulSize  As input parameter, it indicates the memory size that pbyData points to. As output parameter, it returns the data length of EDID. 
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets the EDID of specified channel.\n
 * EDID is supplied by HDMI capture device. It is invalid for other capture devices.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * ULONG ulSize = 256;
 * BYTE byData[256];
 * MWGetEDID(t_channel, byData, &ulSize);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode 
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetEDID(
	HCHANNEL						hChannel,
	BYTE*							pbyData,
	ULONG*							pulSize
	);

/**
 * @ingroup group_functions_common
 * @brief Sets EDID of specified channel.
 * @param[in] hChannel     	Channel handle
 * @param[in] pbyData       New EDID
 * @param[in] ulSize     	Data length of EDID
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * EDID is supplied by HDMI capture device. The API is invalid for other capture devices when being called.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * ULONG ulSize = 256;
 * BYTE byData[256];
 * MWGetEDID(t_channel, byData, &ulSize);
 * ...
 * MWSetEDID(t_channel,byData,ulSize);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 * Make sure you are familiar with EDID when you use this API. Otherwise we do not recommend you to use it.\n
 */
MW_RESULT
LIBMWCAPTURE_API
MWSetEDID(
	HCHANNEL						hChannel,
	BYTE*							pbyData,
	ULONG							ulSize
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the specific status of input signal.
 * @param[in] hChannel      		Channel handle
 * @param[out] pInputStatus      	A pointer to struct #MWCAP_INPUT_SPECIFIC_STATUS, which returns the input signal state.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets the detailed state of specified input source.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_INPUT_SPECIFIC_STATUS t_status;
 * MWGetInputSpecificStatus(t_channel, &t_status);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetInputSpecificStatus(
	HCHANNEL						hChannel,
	MWCAP_INPUT_SPECIFIC_STATUS *	pInputStatus
	);

/**
 * @ingroup group_functions_common
 * @brief Gets video signal status of specified channel.
 * @param[in] hChannel      		Channel handle
 * @param[out] pSignalStatus      	A pointer to struct #MWCAP_VIDEO_SIGNAL_STATUS, which returns video signal status.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets the video signal status of specified channel.
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_SIGNAL_STATUS t_video_status;
 * MWGetVideoSignalStatus(t_channel, &t_video_status);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetVideoSignalStatus(
	HCHANNEL						hChannel,
	MWCAP_VIDEO_SIGNAL_STATUS *		pSignalStatus
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the audio signal status of specified channel.
 * @param[in] hChannel      		Channel handle
 * @param[out] pSignalStatus      	A pointer to struct #MWCAP_AUDIO_SIGNAL_STATUS, which returns the audio signal status.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets the audio signal status of specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_AUDIO_SIGNAL_STATUS t_audio_status;
 * MWGetAudioSignalStatus(t_channel, &t_audio_status);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetAudioSignalStatus(
	HCHANNEL						hChannel,
	MWCAP_AUDIO_SIGNAL_STATUS *		pSignalStatus
	);

/**
 * @ingroup group_functions_common
 * @brief Gets valid flag of HDMI InfoFrame.
 * @param[in] hChannel      	Channel handle
 * @param[out] pdwValidFlag     Returns valid flag of HDMI InfoFrame
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets valid flag of HDMI InfoFrame. Only supported by HDMI capture devices,
 * other devices are not supported.\n
 * The value of pdwValidFlag refers to #MWCAP_HDMI_INFOFRAME_MASK. \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * DWORD dwValidFlag = 0;
 * MWGetHDMIInfoFrameValidFlag(t_channel, &dwValidFlag);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetHDMIInfoFrameValidFlag(
	HCHANNEL						hChannel,
	DWORD*							pdwValidFlag
	);

/**
 * @ingroup group_functions_common
 * @brief Gets HDMI InfoFrame data.
 * @param[in] hChannel      Channel handle
 * @param[in] id      		HDMI InfoFrame ID
 * @param[out] pPacket     	A pointer to struct #HDMI_INFOFRAME_PACKET, which returns HDMI InfoFrame data.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets data of HDMI InfoFrame.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * DWORD dwValidFlag = 0;
 * MWGetHDMIInfoFrameValidFlag(t_channel, &dwValidFlag);
 * HDMI_INFOFRAME_PACKET packet;
 * if (dwValidFlag & MWCAP_HDMI_INFOFRAME_MASK_AVI) {
 * 		xr= MWGetHDMIInfoFramePacket(t_channel, MWCAP_HDMI_INFOFRAME_ID_AVI, &packet);
 * }
 * else if(dwValidFlag & MWCAP_HDMI_INFOFRAME_MASK_AUDIO){
 * 		...
 * }
 * ...
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetHDMIInfoFramePacket(
	HCHANNEL						hChannel,
	MWCAP_HDMI_INFOFRAME_ID			id,
	HDMI_INFOFRAME_PACKET*			pPacket
	);

/**
 * @ingroup group_functions_common
 * @brief  Sets aspect ratio of input video source
 * @param[in] hChannel     The opened channel handle
 * @param[in] nAspectX     width
 * @param[in] nAspectY     Height
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets aspect ratio of specified input video source. It works with the other video processing parameters. 
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * int t_aspect_x = 4;
 * int t_aspect_y = 3;
 * MWSetVideoInputAspectRatio(t_channel, t_aspect_x, t_aspect_y);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
*/
MW_RESULT
LIBMWCAPTURE_API
MWSetVideoInputAspectRatio(
	HCHANNEL 						hChannel,
	int								nAspectX,
	int								nAspectY
	);

/**
 * @ingroup group_functions_common
 * @brief Gets aspect ratio of input video source
 * @param[in] hChannel     The opened channel handle
 * @param[out] pnAspectX   The returned width of aspect ratio
 * @param[out] pnAspectY   The returned height of aspect ratio
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets aspect ratio of specified input video source.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * int t_aspect_x = 0;
 * int t_aspect_y = 0;
 * MWGetVideoInputAspectRatio(t_channel, &t_aspect_x, &t_aspect_y);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetVideoInputAspectRatio(
	HCHANNEL 						hChannel,
	int*							pnAspectX,
	int*							pnAspectY
	);

/**
 * @ingroup group_functions_common
 * @brief Sets color format of input video 
 * @param[in] hChannel      	The opened channel handle
 * @param[in] colorFormat     	Color format
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets color format of specified input channel. \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_COLOR_FORMAT t_colorformat;
 * t_colorformat=MWCAP_VIDEO_COLOR_FORMAT_YUV709;
 * MWSetVideoInputColorFormat (t_channel, t_colorformat);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWSetVideoInputColorFormat(
	HCHANNEL 						hChannel,
	MWCAP_VIDEO_COLOR_FORMAT		colorFormat
	);

/**
 * @ingroup group_functions_common
 * @brief Gets color format of input video.
 * @param[in] hChannel      		The opened channel handle
 * @param[out] pColorFormat      	A pointer to #MWCAP_VIDEO_COLOR_FORMAT, which returns color format value
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets color format of specified input channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_COLOR_FORMAT t_colorformat;
 * MWGetVideoInputColorFormat (t_channel,&t_colorformat);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetVideoInputColorFormat(
	HCHANNEL 						hChannel,
	MWCAP_VIDEO_COLOR_FORMAT *		pColorFormat
	);

/**
 * @ingroup group_functions_common
 * @brief Sets quantization range of input video
 * @param[in] hChannel     The opened channel handle
 * @param[in] quantRange   Quantization range
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets quantization range of specified input channel\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_QUANTIZATION_RANGE t_quantrange;
 * t_quantrange=MWCAP_VIDEO_QUANTIZATION_LIMITED
 * MWSetVideoInputQuantizationRange(t_channel,t_quantrange);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWSetVideoInputQuantizationRange(
	HCHANNEL 						hChannel,
	MWCAP_VIDEO_QUANTIZATION_RANGE	quantRange
	);

/**
 * @ingroup group_functions_common
 * @brief Gets quantization range of input video
 * @param[in] hChannel      		The opened channel handle
 * @param[out] pQuantRange      	A pointer to #MWCAP_VIDEO_QUANTIZATION_RANGE, which returns the quantization range value
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets quantization range of specified input channel. \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_QUANTIZATION_RANGE t_quantrange;
 * MWGetVideoInputQuantizationRange(t_channel,&t_quantrange);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetVideoInputQuantizationRange(
	HCHANNEL 						hChannel,
	MWCAP_VIDEO_QUANTIZATION_RANGE* pQuantRange
	);

/**
 * @ingroup group_functions_common
 * @brief Sets LED mode
 * @param[in] hChannel      	The opened channel handle
 * @param[in] dwMode      		LED mode. For details, see #MWCAP_LED_MODE.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets LED flash mode of specified channel.\n
 * For detailed information of dwMode value, see #MWCAP_LED_MODE. 
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * DWORD t_dw_mode=MWCAP_LED_DBL_BLINK;
 * MWSetLEDMode(t_channel,t_dw_mode);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWSetLEDMode(
	HCHANNEL 						hChannel,
	DWORD							dwMode
	);

/**
 * @ingroup group_functions_common
 * @brief Gets firmware storage information
 * @param[in] hChannel      			The opened channel handle
 * @param[out] pFirmwareStorageInfo     A pointer to #MWCAP_FIRMWARE_STORAGE, which returns firmware storage information
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets firmware storage information of specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_FIRMWARE_STORAGE t_storage_info;
 * MWGetFirmwareStorageInfo(t_channel,& t_storage_info);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWGetFirmwareStorageInfo(
	HCHANNEL 						hChannel,
	MWCAP_FIRMWARE_STORAGE *		pFirmwareStorageInfo
	);

/**
 * @ingroup group_functions_common
 * @brief  Erases firmware data
 * @param[in] hChannel     	The opened channel handle
 * @param[in] cbOffset     	The starting position of the data to erase
 * @param[in] cbErase     	The length of the data to erase
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Erases firmware data of specified channel/device. It is not recommended to call this API.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_FIRMWARE_STORAGE t_storage_info;
 * MWGetFirmwareStorageInfo(t_channel,& t_storage_info);
 * ...
 * MWEraseFirmwareData(t_channel, info.cbHeaderOffset, firmware.GetHeadLen());
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
*/
MW_RESULT
LIBMWCAPTURE_API
MWEraseFirmwareData(
	HCHANNEL 						hChannel,
	DWORD							cbOffset,
	DWORD							cbErase
	);

/**
 * @ingroup group_functions_common
 * @brief  Read firmware data from specified channel
 * @param[in] hChannel     The opened channel handle
 * @param[in] cbOffset     The starting position of the data to read
 * @param[out] pbyData     Returns the read data 
 * @param[in] cbToRead     The data length to read
 * @param[out] pcbRead     Returns the actual length of the read data 
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Reads the firmware data from specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_FIRMWARE_STORAGE t_storage_info;
 * MWGetFirmwareStorageInfo(t_channel,& t_storage_info);
 * ...
 * MWReadFirmwareData(t_channel,info.cbHeaderOffset+sizeof(MW_FIRMWARE_INFO_HEADER), (BYTE*)header.aSectionHeaders, cbSectionHeaders, &cbRead)
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWReadFirmwareData(
	HCHANNEL 						hChannel,
	DWORD							cbOffset,
	BYTE *							pbyData,
	DWORD							cbToRead,
	DWORD *							pcbRead
	);

/**
 * @ingroup group_functions_common
 * @brief Writes firmware data to specified channel.
 * @param[in] hChannel     The opened channel handle
 * @param[in] cbOffset     The starting position of the data to write
 * @param[in] pbyData      The data to write
 * @param[in] cbData       The data length to write
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Writes firmware data to specified channel(device). We do not recommend you to call this API.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_FIRMWARE_STORAGE t_storage_info;
 * MWGetFirmwareStorageInfo(t_channel,& t_storage_info);
 * ...
 * MWWriteFirmwareData(t_channel, info.cbHeaderOffset, (BYTE*)firmware.GetHead(), firmware.GetHeadLen())
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWWriteFirmwareData(
	HCHANNEL 						hChannel,
	DWORD							cbOffset,
	BYTE *							pbyData,
	DWORD							cbData
	);

/**
 * @ingroup group_functions_common
@brief  Uses the v4l function to create video capture
@param[in] hChannel			Channel handle opened
@param[in] nWidth			Width of video capture
@param[in] nHeight			Height of video capture
@param[in] nFourcc			Color format 
@param[in] nFrameDuration   Frame rate of video capture
@param[in] callback			Callback of video capture
@param[in] pParam			The parameter passed to the callback function
@return  Returns a HANDLE type handle if succeeded, otherwise returns NULL
 * <table>
 * 	<tr>
 * 		<td>Not null</td>
 * 		<td>Function call succeeded. The device is ready to start to capture videos.</td>
 * 	</tr>
 * 	<tr>
 * 		<td>NULL</td>
 * 		<td>Function call failed. Failed to start capturing.</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Captures videos from the specified channel.\n
 * @code
 * static void OnVideoCaptureCallback(BYTE *pbFrame, int cbFrame, UINT64 u64TimeStamp, void* pParam)
 * {
 * ...
 * }
 * ...
 * ...
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * HANDEL m_hVideo=NULL;
 * m_hVideo= MWCreateVideoCapture(t_channel,1920, 1080, MWFOURCC_YUY2, 166667, OnVideoCaptureCallback, this);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
*/
HANDLE
LIBMWCAPTURE_API
MWCreateVideoCapture(
	HCHANNEL 						hChannel,
	int								nWidth,
	int								nHeight,
	int								nFourcc,
	int								nFrameDuration,
	VIDEO_CAPTURE_CALLBACK			callback,
	void*							pParam
	);

/**
 * @ingroup group_functions_common
 * @brief Stops video capturing.
 * @param[in] hVideo			The opened video capture handle
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Stops video capturing. Works with 
 * [MWCreateVideoCapture](@ref MWCreateVideoCapture)
 * @code
 * static void OnVideoCaptureCallback(BYTE *pbFrame, int cbFrame, UINT64 u64TimeStamp, void* pParam)
 * {
 * ...
 * }
 * ...
 * ...
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * HANDEL m_hVideo=NULL;
 * m_hVideo= MWCreateVideoCapture(t_channel,1920, 1080, MWFOURCC_YUY2, 166667, OnVideoCaptureCallback, this);
 * ...
 * MWDestoryVideoCapture (m_hVideo);
 * ...
 * MWCloseChannel(t_channel);
 * @encode
*/
MW_RESULT
LIBMWCAPTURE_API
MWDestoryVideoCapture(
	HANDLE							hVideo
	);

/**
 * @ingroup group_functions_common
@brief  Create audio capture using the v4l function  
 * @param[in] hChannel			The opened channel handle
 * @param[in] captureNode	    Audio capture device type
 * @param[in] dwSamplesPerSec   Sampling rate
 * @param[in] wBitsPerSample    Depth
 * @param[in] wChannels			channels
 * @param[in] callback			The callback function
 * @param[in] pParam			The parameter passed to the callback function
 * @return  Returns the HANDLE value. Function return values are as follows.
 * <table>
 * 	<tr>
 * 		<td>Not null</td>
 * 		<td>Function call succeeded. The device is ready to start to capture audio.</td>
 * 	</tr>
 * 	<tr>
 * 		<td>NULL</td>
 * 		<td>Function call failed. Failed to start capturing.</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * use v4l2, just support one channel. It is supported by all capture devices.\n
 * @code
 * static void OnAudioCaptureCallback(const BYTE * pbFrame, int cbFrame, UINT64 u64TimeStamp, void* pParam)
 * {
 * ...
 * }
 * ...
 * ...
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * HANDEL m_hAudio=NULL;
 * m_hAudio=MWCreateAudioCapture(t_channel, MWCAP_AUDIO_CAPTURE_NODE_DEFAULT, 48000, 16, 2, OnAudioCaptureCallback, this);
 * ...
 * MWDestoryAudioCapture(m_hAudio);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */

HANDLE
LIBMWCAPTURE_API
MWCreateAudioCapture(
	HCHANNEL						hChannel,
	MWCAP_AUDIO_CAPTURE_NODE        captureNode,
	DWORD							dwSamplesPerSec,
	WORD							wBitsPerSample,
	WORD							wChannels,
	AUDIO_CAPTURE_CALLBACK			callback,
	void*							pParam
	);

/**
 * @ingroup group_functions_common
 * @brief Stops audio capturing.
 * @param[in] hAudio		Opened audio capture handle
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Works with [MWCreateAudioCapture](@ref MWCreateAudioCapture).\n
 * @code
 * static void OnAudioCaptureCallback(const BYTE * pbFrame, int cbFrame, UINT64 u64TimeStamp, void* pParam)
 * {
 * ...
 * }
 * ...
 * ...
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * HANDEL m_hAudio=NULL;
 * m_hAudio=MWCreateAudioCapture(t_channel, MWCAP_AUDIO_CAPTURE_NODE_DEFAULT, 48000, 16, 2, OnAudioCaptureCallback, this);
 * ...
 * MWDestoryAudioCapture(m_hAudio);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
*/
MW_RESULT
LIBMWCAPTURE_API
MWDestoryAudioCapture(
	HANDLE							hAudio
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the volume value of audio capture device
 * @param[in] hChannel					Channel handle
 * @param[in] audioNode					Audio device type
 * @param[out] pVolume					Returns the volume of audio capture device
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets volume of audio capture device.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_AUDIO_VOLUME t_volume;
 * MWGetAudioVolume(t_channel, MWCAP_AUDIO_CAPTURE_NODE_DEFAULT, &t_volume);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWGetAudioVolume(
	HCHANNEL						hChannel,
	MWCAP_AUDIO_NODE				audioNode,
	MWCAP_AUDIO_VOLUME*				pVolume
	);

/**
 * @ingroup group_functions_common
 * @brief Sets the volume of audio capture device 
 * @param[in] hChannel					Channel handle
 * @param[in] audioNode					Audio device type
 * @param[in] pVolume					The volume of audio capture device 
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets the volume of audio capture device.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_AUDIO_VOLUME t_volume;
 * MWGetAudioVolume(t_channel, MWCAP_AUDIO_CAPTURE_NODE_DEFAULT, &t_volume);
 * ...
 * for(int i=0;i<MWCAP_MAX_NUM_AUDIO_CHANNEL;i++){
 * 		t_volume.asVolume[i]=t_volume.sVolumeMax;
 * }
 * MWSetAudioVolume(t_channel, MWCAP_AUDIO_CAPTURE_NODE_DEFAULT, &t_volume);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWSetAudioVolume(
	HCHANNEL						hChannel,
	MWCAP_AUDIO_NODE				audioNode,
	MWCAP_AUDIO_VOLUME*				pVolume
	);

/**
 * @ingroup group_functions_common
 * @brief Gets whether to adjust horizontal alignment of the vga timing automatically.
 * @param[in] hChannel					Channel handle
 * @param[out] pbAutoHAlign				Whether to adjust horizontal automatically
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets whether to adjust horizontal alignment of the vga timing automatically.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * BOOLEAN t_auto_h=FALSE;
 * MWGetVideoAutoHAlign(t_channel, &t_auto_h);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWGetVideoAutoHAlign(
	HCHANNEL						hChannel,
	BOOLEAN*						pbAutoHAlign
	);

/**
 * @ingroup group_functions_common
 * @brief Sets whether to adjust horizontal alignment of the vga timing automatically.
 * @param[in] hChannel					Channel handle
 * @param[in] bAutoHAlign				Whether to adjust horizontal alignment of the vga timing automatically
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets whether to adjust horizontal alignment of the vga timing automatically.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * BOOLEAN t_auto_h=FALSE;
 * MWSetVideoAutoHAlign(t_channel, t_auto_h);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWSetVideoAutoHAlign(
	HCHANNEL						hChannel,
	BOOLEAN							bAutoHAlign
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the phase of the specified input vga timing.
 * @param[in] hChannel					The opened channel handle
 * @param[out] puSamplingPhase			Phase
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets the phase of the specified input vga timing.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * BYTE t_phase=0;
 * MWGetVideoSamplingPhase(t_channel, &t_phase);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWGetVideoSamplingPhase(
	HCHANNEL						hChannel,
	BYTE *							puSamplingPhase
	);

/**
 * @ingroup group_functions_common
 * @brief Sets the phase of the specified input vga timing.
 * @param[in] hChannel					Channel handle
 * @param[in] puSamplingPhase			Phase
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets the phase of the specified input vga timing.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * BYTE t_phase=0;
 * MWSetVideoSamplingPhase(t_channel, t_phase);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWSetVideoSamplingPhase(
	HCHANNEL						hChannel,
	BYTE							puSamplingPhase
	);

/**
 * @ingroup group_functions_common
 * @brief Gets whether to adjust the phase of the specified input vga timing automatically.
 * @param[in] hChannel					Channel handle
 * @param[out] pbAutoSamplingPhase		Returns whether to automatically adjust the phase of vga timing sampling
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets whether to adjust the phase of the specified vga timing automatically.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * BOOLEAN t_auto=FALSE;
 * MWGetVideoSamplingPhaseAutoAdjust(t_channel, &t_auto);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWGetVideoSamplingPhaseAutoAdjust(
	HCHANNEL						hChannel,
	BOOLEAN *						pbAutoSamplingPhase
	);

/**
 * @ingroup group_functions_common
 * @brief Sets whether to automatically adjust the phase of vga timing sampling
 * @param[in] hChannel					Channel handle
 * @param[in] bAutoSamplingPhase	    Whether to adjust the phase of the specified vga timing automatically
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets whether to automatically adjust the phase of vga timing sampling.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * BOOLEAN t_auto=FALSE;
 * MWSetVideoSamplingPhaseAutoAdjust(t_channel,t_auto);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWSetVideoSamplingPhaseAutoAdjust(
	HCHANNEL						hChannel,
	BOOLEAN							bAutoSamplingPhase
	);
	
/**
 * @ingroup group_functions_common
 * @brief Sets the vga timing of specified channel.
 * @param[in] hChannel					Channel handle
 * @param[in] pTiming					Timing
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets the vga timing of specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_TIMING_ARRAY t_array;
 * MWGetPreferredVideoTimings(t_channel, &t_array);
 * MWSetVideoTiming(t_channel,t_array.aTimings[0]);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWSetVideoTiming(
	HCHANNEL						hChannel,
	MWCAP_VIDEO_TIMING * 			pTiming
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the preffered vga timing array of specified channel.
 * @param[in] hChannel					Channel handle
 * @param[out] paTimings				Timing array
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets the preffered vga timing array of specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_TIMING_ARRAY t_array;
 * MWGetPreferredVideoTimings(t_channel, &t_array);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWGetPreferredVideoTimings(
	HCHANNEL						hChannel,
	MWCAP_VIDEO_TIMING_ARRAY * 		paTimings
	);

/**
 * @ingroup group_functions_common
 * @brief Sets the custom vga timing of specified channel
 * @param[in] hChannel					Channel handle
 * @param[in] pCustomTiming			Custom timing	
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets the custom vga timing of specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_CUSTOM_TIMING t_timing;
 * //set t_timing
 * ...
 * MWSetCustomVideoTiming(t_channel, &t_timing);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWSetCustomVideoTiming(
	HCHANNEL							hChannel,
	MWCAP_VIDEO_CUSTOM_TIMING *			pCustomTiming
	);

/**
 * @ingroup group_functions_common
 * @brief  Gets the custom vga timing of specified channel.
 * @param[in] hChannel					Channel handle
 * @param[out] paCustomTimings			Custom vga timing array
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets the custom vga timing of specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_CUSTOM_TIMING_ARRAY t_timing;
 * MWGetCustomVideoTimings(t_channel, &t_timing);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWGetCustomVideoTimings(
	HCHANNEL							hChannel,
	MWCAP_VIDEO_CUSTOM_TIMING_ARRAY *	paCustomTimings
	);

/**
 * @ingroup group_functions_common
 * @brief Sets the custom vga timing array of specified channel.
 * @param[in] hChannel					Channel handle
 * @param[out] paCustomTimings			Custom timings array
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets the custom vga timing array of specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_CUSTOM_TIMING_ARRAY t_timing;
 * t_timing.byNumCustomTimings=8;
 * for(int i=0;i<8;i++){
 * 	T_timing.aCustomTimings[i]=...;
 * ...
 * }
 * MWSetCustomVideoTimings(t_channel, &t_timing);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWSetCustomVideoTimings(
	HCHANNEL							hChannel,
	MWCAP_VIDEO_CUSTOM_TIMING_ARRAY *	paCustomTimings
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the custom resolutions in vga timing of specified channel.
 * @param[in] hChannel					Channel handle
 * @param[out] paCustomResolutions		Custom resolution array
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets the custom resolutions in vga timing of specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_CUSTOM_RESOLUTION_ARRAY  t_resolution;
 * MWGetCustomVideoResolutions(t_channel, &t_resolution);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWGetCustomVideoResolutions(
	HCHANNEL										hChannel,
	MWCAP_VIDEO_CUSTOM_RESOLUTION_ARRAY *			paCustomResolutions
	);

/**
 * @ingroup group_functions_common
 * @brief Sets the custom resolutions in vga timing of specified channel.
 * @param[in] hChannel					Channel handle
 * @param[in] paCustomResolutions		Custom resolution array
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets the custom resolutions in vga timing of specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_CUSTOM_RESOLUTION_ARRAY  t_resolution;
 * t_resolution.byNumCustomResolutions=8;
 * for(int i=0;i<8;i++){
 * 	t_resolution.aCustomResolutions[i].cx=...;
 * 	t_resolution.aCustomResolutions[i].cy=...;
 * }
 * MWSetCustomVideoResolutions(t_channel, &t_resolution);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWSetCustomVideoResolutions(
	HCHANNEL										hChannel,
	MWCAP_VIDEO_CUSTOM_RESOLUTION_ARRAY *			paCustomResolutions
	);
/**
 * @ingroup group_functions_common
 * @brief Sets the ANC data types to be captured for SDI signal.
 * @param[in] hChannel					The opened channel handle
 * @param[in] byIndex					Index of ANC data types, from 0 to 3.

 * @param[in] bHANC						Whether it is HANC
 * @param[in] bVANC						Whether it is VANC
 * @param[in] byDID						SMPTE ANC DID
 * @param[in] bySDID					SMPTE ANC SDID
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets the ANC data types of SDI signal, 4 types at most.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * //DID=0x61 and SDID=0x01 indicate to capture CC data.
 * MWCaptureSetSDIANCType(t_channel, 0, FALSE, TRUE, 0x61, 0x01);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWCaptureSetSDIANCType(
	HCHANNEL										hChannel,
	BYTE											byIndex,
	BOOLEAN											bHANC,
	BOOLEAN											bVANC,
	BYTE											byDID,
	BYTE											bySDID
	);

/**
 * @ingroup group_functions_common
 * @brief Captures specified SDI ANC data.
 * @param[in] hChannel					Channel handle
 * @param[in] pPacket					ANC data packet\n
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets capture cc data types of SDI signal and get ANC data packet.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCaptureSetSDIANCType(t_channel, 0, FALSE, TRUE, 0x61, 0x01);
 * ...
 * MWCAP_SDI_ANC_PACKET t_packet;
 * MWCaptureGetSDIANCPacket(t_channel,&t_packet);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWCaptureGetSDIANCPacket(
	HCHANNEL										hChannel,
	MWCAP_SDI_ANC_PACKET*							pPacket
	);

/**
 * @ingroup group_functions_common
 * @brief Gets resolution mode supported by devices, including #MWCAP_VIDEO_RESOLUTION_MODE_LIST when the resolutions are discrete values, and #MWCAP_VIDEO_RESOLUTION_MODE_RANGE when the resolutions are continuous values.
 * @param[in]	hChannel		The opened channel handle
 * @param[out]	pMode			Returns the device supported resolution mode: #MWCAP_VIDEO_RESOLUTION_MODE_LIST, #MWCAP_VIDEO_RESOLUTION_MODE_RANGE.
 * @param[out] pCount			Only available when the mode is #MWCAP_VIDEO_RESOLUTION_MODE_LIST,
 * 								indicates the device supported number of resolutions.
* @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * int t_n_count=0;
 * MWCAP_VIDEO_RESOLUTION_MODE t_mode;
 * MWGetVideoCaptureSupportResolutionMode(t_channel,&t_mode,&t_n_count);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */

MW_RESULT
	LIBMWCAPTURE_API
	MWGetVideoCaptureSupportResolutionMode(
		HCHANNEL						hChannel,
		MWCAP_VIDEO_RESOLUTION_MODE 	*pMode,
		int								*pCount
	);

/**
 * @ingroup group_functions_common
 * @brief Gets resolution range supported by the device, when the return mode of MWGetVideoCaptureSupportResolutionMode is #MWCAP_VIDEO_RESOLUTION_MODE_RANGE.
 * @param[in]	hChannel		The opened channel handle
 * @param[out]	pRange			Supported resolution range
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * int t_n_count=0;
 * MWCAP_VIDEO_RESOLUTION_MODE t_mode;
 * MWGetVideoCaptureSupportResolutionMode(t_channel,&t_mode,&t_n_count);
 * if(t_mode == MWCAP_VIDEO_RESOLUTION_MODE_RANGE){
 * 		MWCAP_VIDEO_RESOLUTION_RANGE t_range;
 * 		MWGetVideoCaptureSupportRangeResolution(hChannel,&t_range);
 * 		...
 * }
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */


	
MW_RESULT
	LIBMWCAPTURE_API
	MWGetVideoCaptureSupportRangeResolution(
		HCHANNEL						hChannel,
		MWCAP_VIDEO_RESOLUTION_RANGE*	pRange
	);

/**
 * @ingroup group_functions_common
 * @brief Gets resolutions supported by devices when the return mode of MWGetVideoCaptureSupportResolutionMode is #MWCAP_VIDEO_RESOLUTION_MODE_LIST.
 * @param[in]	hChannel		The opened channel handle
 * @param[out]	pList			Supported discrete resolution values
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * int t_n_count=0;
 * MWCAP_VIDEO_RESOLUTION_MODE t_mode;
 * MWGetVideoCaptureSupportResolutionMode(t_channel,&t_mode,&t_n_count);
 * if(t_mode == MWCAP_VIDEO_RESOLUTION_MODE_LIST){
 * 		MWCAP_VIDEO_RESOLUTION_LIST* t_p_list = new MWCAP_VIDEO_RESOLUTION_LIST[t_n_count];
 * 		MWGetVideoCaptureSupportListResolution(t_channel,t_p_list);
 * 		...
 * }
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */

MW_RESULT
	LIBMWCAPTURE_API
	MWGetVideoCaptureSupportListResolution(
		HCHANNEL						hChannel,
		MWCAP_VIDEO_RESOLUTION_LIST*	pList
	);


/**
 * @ingroup group_functions_common
 * @brief Uses v4l2 to get the device supported color spaces.
 * @param[in]	hChannel		The opened channel handle
 * @param[out]	pColorFourcc	Returns the device supported color spaces. For details, see MWFOURCC.h. When being set to NULL, the returned value is the number of device supported color spaces.
 * @param[out]  nCount			The number of color formats supported by the capture device.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets capture formats supported by devices.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * int t_n_count=0;
 * MWGetVideoCaptureSupportFormat(t_channel,NULL,&t_n_count);
 * if(t_n_count>0){
 * 		DWORD* t_p_format=new DWORD[t_n_count];
 * 		MWGetVideoCaptureSupportColorFormat(t_channel,t_p_format,&t_n_count);
 * }
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */

MW_RESULT
LIBMWCAPTURE_API
	MWGetVideoCaptureSupportColorFormat(
	HCHANNEL					hChannel,
	DWORD*						pColorFourcc,
	int*						nCount
    );

/**
 * @ingroup group_functions_common
 * @brief Gets range of video processing parameters
 * @param[in] hVideo      						The opened video capture handle
 * @param[in] videoProcParamType				Video processing parameter type, including brightness, contrast, hue, saturation.
 * @param[out] plParamValueMin					The returned minimum value
 * @param[out] plParamValueMax					The returned maximum value
 * @param[out]	plParamValueDef					The returned default value
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code
 * static void OnVideoCaptureCallback(BYTE *pbFrame, int cbFrame, UINT64 u64TimeStamp, void* pParam)
 * {
 * ...
 * }
 * ...
 * ...
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * HANDEL m_hVideo=NULL;
 * m_hVideo= MWCreateVideoCapture(t_channel,1920, 1080, MWFOURCC_YUY2, 166667, OnVideoCaptureCallback, this);
 * ...
 * long t_l_min=0;
 * long t_l_max=0;
 * long t_l_def=0;
 * MWGetVideoProcParamRange(m_hVideo,MWCAP_VIDEO_PROC_BRIGHTNESS,&t_l_min,&t_l_max,&t_l_def);
 * ...
 * MWDestoryVideoCapture (m_hVideo);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
*/
MW_RESULT
LIBMWCAPTURE_API
MWGetVideoProcParamRange(
	HANDLE hVideo,
	MWCAP_VIDEO_PROC_PARAM_TYPE videoProcParamType,
	long * plParamValueMin,
	long * plParamValueMax,
	long * plParamValueDef
	);

/**
 * @ingroup group_functions_common
 * @brief Gets current video processing settings.
 * @param[in] hVideo      						Opened video capture channel handle
 * @param[in] videoProcParamType      			Video processing parameters, including brightness, contrast, hue, saturation.
 * @param[out] plParamValue      				The returned default value
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code
 * static void OnVideoCaptureCallback(BYTE *pbFrame, int cbFrame, UINT64 u64TimeStamp, void* pParam)
 * {
 * ...
 * }
 * ...
 * ...
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * HANDEL m_hVideo=NULL;
 * m_hVideo= MWCreateVideoCapture(t_channel,1920, 1080, MWFOURCC_YUY2, 166667, OnVideoCaptureCallback, this);
 * ...
 * long t_l_val=0;
 * MWGetVideoProcParam(m_hVideo,MWCAP_VIDEO_PROC_BRIGHTNESS,&t_l_val);
 * ...
 * MWDestoryVideoCapture (m_hVideo);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
*/
MW_RESULT
	LIBMWCAPTURE_API
	MWGetVideoProcParam(
	HANDLE hVideo,
	MWCAP_VIDEO_PROC_PARAM_TYPE videoProcParamType,
	long * plParamValue
	);


/**
 * @ingroup group_functions_common
 * @brief Sets the specified video processing parameters
 * @param[in] hVideo      						The opened video channel handle
 * @param[in] videoProcParamType      			Video processing parameter type, including brightness, contrast, hue, saturation.
 * @param[in] lParamValue      					The set value, which should be within the range of parameters.
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code
 * static void OnVideoCaptureCallback(BYTE *pbFrame, int cbFrame, UINT64 u64TimeStamp, void* pParam)
 * {
 * ...
 * }
 * ...
 * ...
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * HANDEL m_hVideo=NULL;
 * m_hVideo= MWCreateVideoCapture(t_channel,1920, 1080, MWFOURCC_YUY2, 166667, OnVideoCaptureCallback, this);
 * ...
 * long t_l_min=0;
 * long t_l_max=0;
 * long t_l_def=0;
 * MWGetVideoProcParamRange(m_hVideo,MWCAP_VIDEO_PROC_BRIGHTNESS,&t_l_min,&t_l_max,&t_l_def);
 * long t_l_val=0;
 * MWGetVideoProcParam(m_hVideo,MWCAP_VIDEO_PROC_BRIGHTNESS,&t_l_val);
 * long t_l_setval = t_l_max;
 * MWSetVideoProcParam(m_hVideo,MWCAP_VIDEO_PROC_BRIGHTNESS,t_l_setval);
 * ...
 * MWDestoryVideoCapture (m_hVideo);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
*/
MW_RESULT
	LIBMWCAPTURE_API
	MWSetVideoProcParam(
	HANDLE hVideo,
	MWCAP_VIDEO_PROC_PARAM_TYPE videoProcParamType,
	long lParamValue
	);
	
	/**
	 * @ingroup group_functions_common
	 * @brief Sends instructions for rereading configurations to delay the execution.
	 * @param[in] hChannel			Opened channel handle
	 * @param[in] dwDelayMS 		Delay time in milliseconds
	 * @return Function return values are as follows
	 * <table>
	 *	<tr>
	 *		<td> #MW_SUCCEEDED </td>
	 *		<td> Function call succeeded.  </td>
	 *	</tr>
	 *	<tr>
	 *		<td> #MW_FAILED </td>
	 *		<td> Function call failed. </td>
	 *	</tr>
	 *	<tr>
	 *		<td> #MW_INVALID_PARAMS </td>
	 *		<td> Input invalid value(s).</td>
	 *	</tr>
	 * </table>
	 * @details Usage:\n
	 * Rereads configurations\n
	 * Be cautious when using it.\n
	 */

MW_RESULT
LIBMWCAPTURE_API
MWSetPostReconfig(
	HCHANNEL 						hChannel,
	DWORD							dwDelayMS
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the connection format of capture pin.
 * @param[in] hChannel					Channel handle
 * @param[out] paConnectionFormat		Connection format
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_CONNECTION_FORMAT t_format;
 * MWGetVideoCaptureConnectionFormat(t_channel, &t_format);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */

MW_RESULT 
LIBMWCAPTURE_API
MWGetVideoCaptureConnectionFormat(
    HCHANNEL                        hChannel,
    MWCAP_VIDEO_CONNECTION_FORMAT* pConnFormat
    );
/**
 * @ingroup group_functions_common
 * @brief Gets whether to scan the input signal source of specified channel automatically.
 * @param[in] hChannel					Channel handle
 * @param[out] pbInputSourceScanning	Whether to scan the input signal resource
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets whether to scan the input signal resources of specified channel automatically.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * BOOLEAN t_b_scan;
 * MWGetInputSourceScanState(t_channel, &t_b_scan);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT
	LIBMWCAPTURE_API
	MWGetInputSourceScanState(
	HCHANNEL										hChannel,
	BOOLEAN *										pbInputSourceScanning
	);

/**
 * @ingroup group_functions_common
 * @brief Gets the video process settings of specified channel.
 * @param[in] hChannel					Channel handle
 * @param[out] paProcessSettings		Video process settings
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Gets the video process parameters of specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_PROCESS_SETTINGS t_b_setting;
 * MWGetVideoCaptureProcessSettings(t_channel, &t_b_setting);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT 
	LIBMWCAPTURE_API
	MWGetVideoCaptureProcessSettings(
	HCHANNEL										hChannel,
	MWCAP_VIDEO_PROCESS_SETTINGS*					paProcessSettings
	);

/**
 * @ingroup group_functions_common
 * @brief Sets the video process parameters of specified channel.
 * @param[in] hChannel					Channel handle
 * @param[in] paProcessSettings			Video process parameters
 * @return Function return values are as follows:
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed.  </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s).</td>
 * 	</tr>
 * </table>
 * @details Usage: \n
 * Sets the video process parameters of specified channel.\n
 * @code
 * char path[128];
 * MWGetDevicePath(k,path);
 * HCHANNEL t_channel=MWOpenChannelByPath(path);
 * ...
 * MWCAP_VIDEO_PROCESS_SETTINGS t_b_setting;
 * t_b_setting.xx=...;
 * ...
 * ...
 * MWSetVideoCaptureProcessSettings(t_channel, &t_b_setting);
 * ...
 * MWCloseChannel(t_channel);
 * @endcode
 */
MW_RESULT 
	LIBMWCAPTURE_API
	MWSetVideoCaptureProcessSettings(
	HCHANNEL										hChannel,
	MWCAP_VIDEO_PROCESS_SETTINGS*					paProcessSettings
	);

#ifdef __cplusplus
}
#endif
