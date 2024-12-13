/************************************************************************************************/
// MWUSBCapture.h : header file

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
#ifndef _MWUSB_CAPTURE_H_
#define _MWUSB_CAPTURE_H_

#ifdef LIBMWCAPTURE_EXPORTS
#define LIBMWCAPTURE_API __declspec(dllexport)
#elif LIBMWCAPTURE_DLL
#define LIBMWCAPTURE_API __declspec(dllimport)
#else
#define LIBMWCAPTURE_API 
#endif

#ifdef _WIN32
#include <Windows.h>
#endif
#include <stdint.h>
#include "MWUSBCaptureExtension.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @ingroup group_functions_usbcapture
 * @brief Registers hotplug callback function of USB capture device
 * @param[in] lpfnCallback	Callback function
 * @param[in] pParam		Callback parameter
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * Registers hotplug callback function of USB capture device to notify the plug states of USB capture devices.\n
 * @code
 * static void HotplugCheckCallback(MWUSBHOT_PLUG_EVETN event, const char *pszDevicePath, void* pParam)
 * {
 * 	...
 * }
 * ...
 * MWCaptureInitInstance();
 * ...
 * mr = MWUSBRegisterHotPlug(HotplugCheckCallback, NULL);
 * ...
 * mr = MWUSBUnRegisterHotPlug();
 * ...
 * MWCaptureExitInstance();
 * @endcode
*/
MW_RESULT
LIBMWCAPTURE_API
MWUSBRegisterHotPlug(
    LPFN_HOT_PLUG_CALLBACK lpfnCallback,
	void *				   pParam
    );

/**
 * @ingroup group_functions_usbcapture
 * @brief Unregisters hotplug callback function.
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * Unregisters hotplug callback function of USB capture device.\n
 * Refers to [MWUSBRegisterHotPlug](@ref MWUSBRegisterHotPlug) \n
*/
MW_RESULT
LIBMWCAPTURE_API
MWUSBUnRegisterHotPlug(
    );

/**
 * @ingroup group_functions_usbcapture
 * @brief Sets notification types for specified channel
 * @param[in] hChannel			Channel handle of the USB device
 * @param[in] pNotify			Notification
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * Sets notification types for the specified channel.\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_NOTIFY_ENABLE  t_notify;
 * t_notify.bInterrupt=false;
 * t_notify.ullEnableBits=MWCAP_NOTIFY_xxx|MWCAP_NOTIFY_xxx|...;
 * ...
 * MWUSBSetNotifyEnable(hChannel, &t_notify);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBSetNotifyEnable(
	HUSBCHANNEL						hChannel,
	MWCAP_NOTIFY_ENABLE *			pNotify
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Gets notification status of USB specified channel
 * @param[in] hChannel					Channel handle of USB device
 * @param[out] pullStatusBit			Notification mask
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 *  Gets notification status of USB specified channel.\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_NOTIFY_ENABLE  t_notify;
 * t_notify.bInterrupt=false;
 * t_notify.ullEnableBits=MWCAP_NOTIFY_xxx|MWCAP_NOTIFY_xxx|...;
 * ...
 * MWUSBSetNotifyEnable(hChannel, &t_notify);
 * ...
 * uint64_t t_status=0;
 * MWUSBGetNotifyStatus(hChannel, &t_status);
 * if(t_status & MWCAP_NOTIFY_xxx){
 * 	...
 * }
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBGetNotifyStatus(
	HUSBCHANNEL						hChannel,
	uint64_t *						pullStatusBit
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Erases firmware data from USB device
 * @param[in] hChannel					Channel handle of USB device
 * @param[in] cbOffset					Address offset
 * @param[in] cbErase					Erased size
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBSetFirmwareErase(
	HUSBCHANNEL 					hChannel,
	uint32_t						cbOffset,
	uint32_t						cbErase
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Gets read address of USB device firmware.
 * @param[in] hChannel					Channel handle of USB device
 * @param[out] pdwAddress				Read address of firmware
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * uint32_t t_address;
 * MWUSBGetFirmwareReadAddress(hChannel, &t_address);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBGetFirmwareReadAddress(
	HUSBCHANNEL 					hChannel,
	uint32_t *						pdwAddress
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Gets EDID of the loopthrough interface in the USB device, only supported by devices with loopthrough interface
 * @param[in] hChannel					Channel handle of USB device
 * @param[out] pbyEDID					EDID
 * @param[in,out] pcbEDID				As an input parameter, it indicates the size of the area which is pointed by the pbyEDID. As an output parameter, it indicates the size of the returned EDID. 
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * Gets EDID of the loopthrough interface in the USB device, which is only supported by devices with loopthrough interface.\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * uint32_t t_cd_edid=256;
 * unsigned char t_hc_edid[256];
 * MWUSBGetEDIDloopthrough(hChannel, t_hc_edid, &t_cd_edid);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBGetEDIDLoopThrough(
	HUSBCHANNEL						hChannel,
	char *							pbyEDID,
	uint32_t *						pcbEDID
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Gets whether the loopthrough interface in the USB device is valid.
 * @param[in] hChannel					Channel handle of USB device
 * @param[out] pbValid					Whether there is a valid loopthrough interface		
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * bool_t t_valid=false;
 * MWUSBGetloopthroughValid(hChannel, &t_valid);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBGetLoopThroughValid(
	HUSBCHANNEL						hChannel,
	bool_t *						pbValid
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Gets the volume of USB audio device.
 * @param[in] hChannel					Channel handle of USB device
 * @param[in] audioNode					Audio device
 * @param[out] pVolume					Volume of USB audio device
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * Gets the volume of USB audio device.\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_AUDIO_VOLUME t_vol;
 * MWUSBGetAudioVolume(hChannel, MWCAP_USB_AUDIO_EMBEDDED_CAPTURE, &t_vol);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBGetAudioVolume(
	HUSBCHANNEL						hChannel,
	MWCAP_USB_AUDIO_NODE			audioNode,
	MWCAP_AUDIO_VOLUME*				pVolume
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Sets the volume of USB audio device.
 * @param[in] hChannel					Channel handle of USB device
 * @param[in] audioNode					Audio device
 * @param[in] pVolume					Audio device volume
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * Sets the volume of USB audio device.\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_AUDIO_VOLUME t_vol;
 * MWUSBGetAudioVolume(hChannel, MWCAP_USB_AUDIO_EMBEDDED_CAPTURE, &t_vol);
 * t_vol.xx=...;
 * MWUSBSetAudioVolume(hChannel, MWCAP_USB_AUDIO_EMBEDDED_CAPTURE, &t_vol);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBSetAudioVolume(
	HUSBCHANNEL						hChannel,
	MWCAP_USB_AUDIO_NODE			audioNode,
	MWCAP_AUDIO_VOLUME*				pVolume
	);


/**
 * @ingroup group_functions_usbcapture
 * @brief Gets capture formats supported by the USB device.
 * @param[in] hChannel					Channel handle of USB device
 * @param[out] pOutputFourCC			Supported capture formats
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_VIDEO_OUTPUT_FOURCC t_fmt;
 * MWUSBGetVideoOutputFOURCC(hChannel, &t_fmt);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */

MW_RESULT
LIBMWCAPTURE_API
MWUSBGetVideoOutputFOURCC(
	HUSBCHANNEL 					hChannel,
	MWCAP_VIDEO_OUTPUT_FOURCC*		pOutputFourCC
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Sets capture formats supported by the USB device, 3 at most.
 * @param[in] hChannel					Channel handle of USB device
 * @param[in] pOutputFourCC				Supported capture formats
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * Sets capture formats supported by the USB device, which is 3 at most. The function must work with MWUSBSaveOptions, 
 * and plugs and reconnects the USB device after setting, then the function will work.\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_VIDEO_OUTPUT_FOURCC t_fmt;
 * MWUSBGetVideoOutputFOURCC(hChannel ,&t_fmt);
 * t_fmt.xx=...;
 * MWUSBSetVideoOutputFOURCC(hChannel ,&t_fmt);
 * ...
 * MWUSBSaveOptions(hChannel);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBSetVideoOutputFOURCC(
	HUSBCHANNEL 					hChannel,
	MWCAP_VIDEO_OUTPUT_FOURCC*		pOutputFourCC
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Gets resolutions of captured images supported by the USB device
 * @param[in] hChannel					Channel handle of USB device
 * @param[out] pFrameSize				Resolutions of captured images supported by the USB device
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_VIDEO_OUTPUT_FRAME_SIZE t_fsize;
 * MWUSBGetVideoOutputFrameSize(hChannel ,& t_fsize);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBGetVideoOutputFrameSize(
	HUSBCHANNEL 						hChannel,
	MWCAP_VIDEO_OUTPUT_FRAME_SIZE*		pFrameSize
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Sets resolutions supported by the USB device
 * @param[in] hChannel					Channel handle of USB device
 * @param[in] pFrameSize				Resolutions supported by the USB device
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_VIDEO_OUTPUT_FRAME_SIZE t_fsize;
 * MWUSBGetVideoOutputFrameSize(hChannel, &t_fsize);
 * ...
 * t_fsize.xx=...;
 * ...
 * MWUSBSetVideoOutputFrameSize(hChannel, &t_fsize);
 * ...
 * MWUSBSaveOptions(hChannel);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBSetVideoOutputFrameSize(
	HUSBCHANNEL 						hChannel,
	MWCAP_VIDEO_OUTPUT_FRAME_SIZE*		pFrameSize
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Gets capture intervals supported by USB device
 * @param[in] hChannel					Channel handle of USB device
 * @param[out] pFrameInterval			Capture intervals supported by USB device
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_VIDEO_OUTPUT_FRAME_INTERVAL t_internal;
 * MWUSBGetVideoOutputFrameInterval(hChannel, &t_internal);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBGetVideoOutputFrameInterval(
	HUSBCHANNEL 							hChannel,
	MWCAP_VIDEO_OUTPUT_FRAME_INTERVAL*		pFrameInterval
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Sets capture intervals supported by USB device
 * @param[in] hChannel					Channel handle of USB device
 * @param[in] pFrameInterval			Capture intervals
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_VIDEO_OUTPUT_FRAME_INTERVAL t_internal;
 * MWUSBGetVideoOutputFrameInterval(hChannel, &t_internal);
 * ...
 * t_internal.xx=...;
 * ...
 * MWUSBSetVideoOutputFrameInterval(hChannel, &t_internal);
 * ...
 * MWUSBSaveOptions(hChannel);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBSetVideoOutputFrameInterval(
	HUSBCHANNEL 							hChannel,
	MWCAP_VIDEO_OUTPUT_FRAME_INTERVAL*		pFrameInterval
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Gets the image pattern showed when there is not a valid input signal.
 * @param[in] hChannel					Channel handle of USB device
 * @param[out] pImageMode				The image pattern showed when there is not a valid input signal
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * Gets the image pattern showed when there is not a valid input signal.\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_STATUS_IMAGE_MODE t_mode;
 * MWUSBGetStatusImageMode(hChannel, &t_mode);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBGetStatusImageMode(
	HUSBCHANNEL						hChannel,
	MWCAP_STATUS_IMAGE_MODE *		pImageMode
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Sets the image pattern showed when there is not a valid input signal
 * @param[in] hChannel					Channel handle of USB device
 * @param[in] pImageMode				The image pattern showed when there is not a valid input signal
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * Sets the image pattern showed when there is not a valid input signal.\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_STATUS_IMAGE_MODE t_mode=MWCAP_STATUS_IMAGE_BLUE;
 * MWUSBSetStatusImageMode(hChannel, &t_mode);
 * ...
 * MWUSBSaveOptions(hChannel);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBSetStatusImageMode(
	HUSBCHANNEL						hChannel,
	MWCAP_STATUS_IMAGE_MODE *		pImageMode
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Gets device name pattern of USB device 
 * @param[in] hChannel					Channel handle of USB device
 * @param[out] pNameMode				Device name pattern
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_DEVICE_NAME_MODE t_mode;
 * MWUSBGetDeviceNameMode(hChannel, &t_mode);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBGetDeviceNameMode(
	HUSBCHANNEL						hChannel,
	MWCAP_DEVICE_NAME_MODE *		pNameMode
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Sets device name pattern of USB device
 * @param[in] hChannel					Channel handle of USB device
 * @param[in] pNameMode					Device name pattern 
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWCAP_DEVICE_NAME_MODE t_mode=MWCAP_DEVICE_NAME_SERIAL_NUMBER;
 * MWUSBSetDeviceNameMode(hChannel, &t_mode);
 * ...
 * MWUSBSaveOptions(hChannel);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBSetDeviceNameMode(
	HUSBCHANNEL						hChannel,
	MWCAP_DEVICE_NAME_MODE *		pNameMode
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Saves configurations
 * @param[in] hChannel					Channel handle of USB device 
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * The detailed usage refers to the following functions:\n
 *  [MWUSBSetVideoOutputFOURCC](@ref MWUSBSetVideoOutputFOURCC) \n
 *  [MWUSBSetVideoOutputFrameSize](@ref MWUSBSetVideoOutputFrameSize) \n
 *  [MWUSBSetVideoOutputFrameInterval](@ref MWUSBSetVideoOutputFrameInterval) \n
 *  [MWUSBSetStatusImageMode](@ref MWUSBSetStatusImageMode) \n
 *  [MWUSBSetDeviceNameMode](@ref MWUSBSetDeviceNameMode) \n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWUSBSaveOptions(hChannel);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBSaveOptions(
	HUSBCHANNEL		hChannel 
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Loads the saved configurations
 * @param[in] hChannel					Channel handle of USB device
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWUSBLoadOptions(hChannel);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBLoadOptions(
	HUSBCHANNEL		hChannel
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Restores to the default settings
 * @param[in] hChannel					Channel handle of USB device
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * MWUSBResetOptions(hChannel);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBResetOptions(
	HUSBCHANNEL		hChannel
	);

/**
 * @ingroup group_functions_usbcapture
 * @brief Gets extended Hid interfaces supported by USB device
 * @param[in] hChannel					Channel handle of USB device
 * @param[out] pdwFlag					Flag of the extended supported Hid interfaces 
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * The meaning of the pdwFlag refers to MWCAP_HID_EXTENSION_XX.\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * uint32_t t_flag=0;
 * MWUSBGetExtensionSupported(hChannel, &t_flag);
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */

MW_RESULT
LIBMWCAPTURE_API
MWUSBGetExtensionSupported(
	HUSBCHANNEL				hChannel,
	uint32_t *				pdwFlag
	);


/**
 * @ingroup group_functions_usbcapture
@brief Gets current edid mode
@param[in] 	hChannel      	Channel handle of USB device
@param[out] 	pMode      	The edid mode of device
@return Returns MW_SUCCEED if succeeded, otherwise returns MW_FAILED or NW_INVALID_PARAMS
*/
MW_RESULT
LIBMWCAPTURE_API
MWUSBGetEDIDMode(HUSBCHANNEL hChannel, MWCAP_EDID_MODE * pMode);
/**
 * @ingroup group_functions_usbcapture
@brief Sets the edid mode
@param[in] 	hChannel      	Channel handle of USB device
@param[out] 	mode      	The edid mode set to device
@return Returns MW_SUCCEED if succeeded, otherwise returns MW_FAILED or NW_INVALID_PARAMS
*/
MW_RESULT
LIBMWCAPTURE_API
MWUSBSetEDIDMode(HUSBCHANNEL hChannel, MWCAP_EDID_MODE mode);


/**
 * @ingroup group_functions_usbcapture
 * @brief Gets frame rates supported by USB device based on v4l.
 * @param[in]		hChannel		Channel handle of USB device
 * @param[out]		pFramerate		Frame rates supported by USB device. When it is set to NULL, only the number of supported frame rates is returned.
 * @param[in,out]	nCount			As an input parameter, it indicates the pointer points to the size of pFramerate array. As an output parameter, it indicates the number of capture frame rates supported by USB device.
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * int t_n_count = 0;
 * MWUSBGetVideoCaptureSupportFrameRate(hChannel, NULL, &t_n_count);
 * if(t_n_count > 0){
 * 	MWCAP_VIDEO_FRAMERATE* t_p_rate=new MWCAP_VIDEO_FRAMERATE[t_n_count];
 * 	MWUSBGetVideoCaptureSupportFrameRate(hChannel,t_p_rate,&t_n_count);
 * }
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */

MW_RESULT
LIBMWCAPTURE_API
MWUSBGetVideoCaptureSupportFrameRate(
	HCHANNEL					hChannel,
	MWCAP_VIDEO_FRAMERATE*		pFramerate,
	int*						nCount
);


/**
 * @ingroup group_functions_usbcapture
 * @brief Gets frame rates supported by USB device based on v4l.
 * @param[in]	hChannel		Channel handle of USB device
 * @param[out]	pFramerate		Capture frame rates supported by USB device
 * @param[in,out]	nCount		As an input parameter, it indicates the pointer points to the size of pFramerate array. As an output parameter, it indicates the number of capture frame rates supported by USB device.
 * @return Function return values are as follows
 * <table>
 * 	<tr>
 * 		<td> #MW_SUCCEEDED </td>
 * 		<td> Function call succeeded. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_FAILED </td>
 * 		<td> Function call failed. </td>
 * 	</tr>
 * 	<tr>
 * 		<td> #MW_INVALID_PARAMS </td>
 * 		<td> Input invalid value(s). </td>
 * 	</tr>
 * </table>
 * @details Usage:\n
 * @code
 * char pDevicePath[128] = {0};
 * mr = MWGetDevicePath(i, pDevicePath);
 * ...
 * HCHANNEL hChannel = MWOpenChannelByPath(pDevicePath);
 * ...
 * int t_n_count = 0;
 * MWUSBGetVideoCaptureSupportFrameRateEx(hChannel, NULL, &t_n_count);
 * if(t_n_count > 0){
 * 	MWCAP_VIDEO_FRAMERATE_EX* t_p_rate=new MWCAP_VIDEO_FRAMERATE_EX[t_n_count];
 * 	MWUSBGetVideoCaptureSupportFrameRateEx(hChannel, t_p_rate, &t_n_count);
 * }
 * ...
 * MWCloseChannel(hChannel);
 * @endcode
 */
MW_RESULT
LIBMWCAPTURE_API
MWUSBGetVideoCaptureSupportFrameRateEx(
	HCHANNEL					hChannel,
	MWCAP_VIDEO_FRAMERATE_EX*	pFramerate,
	int*						nCount
);

#ifdef __cplusplus
}
#endif


#endif //_MWUSB_CAPTURE_H_
