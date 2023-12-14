#ifndef MW_VENC_COMMON_H
#define MW_VENC_COMMON_H

////////////////////////////////////////////////////////////////////////////////
// Copyright (c) 2011-2020 Magewell Electronics Co., Ltd. (Nanjing)
//
// Permission is hereby granted, free of charge, to any person obtaining a
// copy of this software and associated documentation files (the "Software"),
// to deal in the Software without restriction, including without limitation
// the rights to use, copy, modify, merge, publish, distribute, sublicense,
// and/or sell copies of the Software, and to permit persons to whom the
// Software is furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included
// in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
// OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
////////////////////////////////////////////////////////////////////////////////

#include <stdint.h>

/**
 * @ingroup group_hwe_variables_enum
 * @brief mw_venc_frame_type_t
 * @details Defines the frame types to be encoded.\n
 * Related type(s):\n
 *  #mw_venc_frame_info_t \n
 * Related function(s):\n
 * 	[mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 *  [MW_ENCODER_CALLBACK](@ref MW_ENCODER_CALLBACK)
 */
typedef enum mw_venc_frame_type
{
    MW_VENC_FRAME_TYPE_UNKNOWN,							///<Unknown frame
    MW_VENC_FRAME_TYPE_IDR,								///<IDR frame
    MW_VENC_FRAME_TYPE_I,								///<I-frame
    MW_VENC_FRAME_TYPE_P,								///<P-frame
    MW_VENC_FRAME_TYPE_B,								///<B-frame
    MW_VENC_FRAME_TYPE_COUNT							///<Number of frame types enumerated
}mw_venc_frame_type_t;

/**
 * @ingroup group_hwe_variables_struct
 * @brief mw_venc_frame_info_t
 * @detials Defines the types infomation of frame to be encoded.\n
 * Related type(s):\n
 *  #mw_venc_frame_type_t \n
 * Related function(s):\n
 * 	[mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 */
typedef struct mw_venc_frame_info
{
    mw_venc_frame_type_t frame_type;					
    int32_t delay;										
    int64_t pts;										
}mw_venc_frame_info_t;

/**
 * @ingroup group_hwe_functions
 * @brief Callback functions
 * @details out code date.\n
 * Related function(s):\n
 * 	[mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 */
typedef void(*MW_ENCODER_CALLBACK)(void * user_ptr, const uint8_t * p_frame, uint32_t frame_len, mw_venc_frame_info_t *p_frame_info);

/**
 * @ingroup group_hwe_variables_enum
 * @brief mw_venc_platform_t
 * @details Defines the hardware types which is used to do hardware encoding.\n
 * Related function(s):\n
 * 	[mw_venc_create](@ref mw_venc_create) \n
 * 	[mw_venc_create_ex](@ref mw_venc_create_ex) \n
 * 	[mw_venc_get_default_param](@ref mw_venc_get_default_param) \n
 */
typedef enum mw_venc_platform
{
    MW_VENC_PLATFORM_UNKNOWN	=0,						///<Unknown hardware type, the binary value is 0000 0000
    MW_VENC_PLATFORM_AMD		=1,						///<AMD graphics, the binary value is 0000 0001
    MW_VENC_PLATFORM_INTEL		=2,						///<Intel graphics, the binary value is 0000 0010
	MW_VENC_PLATFORM_NVIDIA		=4,						///<Nvidia graphics, the binary value is 0000 0100
	MW_VENC_PLATFORM_COUNT								///<The maximum input value 
}mw_venc_platform_t;

/**
 * @ingroup group_hwe_variables_enum
 * @brief mw_venc_code_type_t
 * @details Defines code types.\n
 * Related type(s):\n
 * 	#mw_venc_param \n
 * Related function(s):\n
 *  [mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 * 	[mw_venc_get_default_param](@ref mw_venc_get_default_param) \n
 */
typedef enum mw_venc_code_type
{
    MW_VENC_CODE_TYPE_UNKNOWN,							///<Unknown
	MW_VENC_CODE_TYPE_AVC,								///<AVC/H264
    MW_VENC_CODE_TYPE_HEVC,								///<HEVC/H265
	MW_VENC_CODE_TYPE_H264 = MW_VENC_CODE_TYPE_AVC,		///<H264
	MW_VENC_CODE_TYPE_H265 = MW_VENC_CODE_TYPE_HEVC,	///<H265
	MW_VENC_CODE_TYPE_COUNT								///<The maximum input value 
}mw_venc_code_type_t;

/**
 * @ingroup group_hwe_variables_enum
 * @brief mw_venc_targetusage_t
 * @details Defines the preset of quality and speed mode for your encoder.\n
 * Related type(s):\n
 * 	#mw_venc_param \n
 * Related function(s):\n
 *  [mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 * 	[mw_venc_get_default_param](@ref mw_venc_get_default_param) \n
 */
typedef enum mw_venc_targetusage
{
    MW_VENC_TARGETUSAGE_UNKNOWN,						///<Unknown
    MW_VENC_TARGETUSAGE_BEST_QUALITY,					///<Quality first
    MW_VENC_TARGETUSAGE_BALANCED,						///<Balance the coding quality and speed
    MW_VENC_TARGETUSAGE_BEST_SPEED,						///<Speed first
    MW_VENC_TARGETUSAGE_COUNT							///<The maximum input value 
}mw_venc_targetusage_t;

/**
 * @ingroup group_hwe_variables_enum
 * @brief mw_venc_rate_control_mode_t
 * @details Defines the bitrate controlling types.\n
 * Related type(s):\n
 * 	#mw_venc_param \n
 *  #mw_venc_rate_control \n
 *  #MW_VENC_PROPERTY_RATE_CONTROL \n
 * Related function(s):\n
 *  [mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 * 	[mw_venc_get_default_param](@ref mw_venc_get_default_param) \n
 */
typedef enum mw_venc_rate_control_mode
{
    MW_VENC_RATECONTROL_UNKNOWN,						///<Unknown
    MW_VENC_RATECONTROL_CBR,							///<Constant Bit Rate
    MW_VENC_RATECONTROL_VBR,							///<Variable Bit Rate
    MW_VENC_RATECONTROL_CQP,							///<Constant Quantization Parameter
    MW_VENC_RATECONTROL_COUNT							///<The maximum input value 
}mw_venc_rate_control_mode_t;

/**
 * @ingroup group_hwe_variables_enum
 * @brief mw_venc_profile_t
 * @details Defines the profile type.\n
 * Related type(s):\n
 * 	#mw_venc_param \n
 * Related function(s):\n
 *  [mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 * 	[mw_venc_get_default_param](@ref mw_venc_get_default_param) \n
 */
typedef enum mw_venc_profile
{
    MW_VENC_PROFILE_UNKNOWN,							///<Unknown
    MW_VENC_PROFILE_H264_BASELINE,						///<H264 baseline
    MW_VENC_PROFILE_H264_MAIN,							///<H264 main
    MW_VENC_PROFILE_H264_HIGH,							///<H264 high
	MW_VENC_PROFILE_H265_MAIN,							///<H265 main
	MW_VENC_PROFILE_COUNT								///<The maximum input value 
}mw_venc_profile_t;

/**
 * @ingroup group_hwe_variables_enum
 * @brief mw_venc_level_t
 * @details Defines the video encoding level. The higher the level is, the higher the bitrate, resolution, frame rate are being supported.\n
 * Related type(s):\n
 * 	#mw_venc_param \n
 * Related function(s):\n
 *  [mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 * 	[mw_venc_get_default_param](@ref mw_venc_get_default_param) \n
 */
typedef enum mw_venc_level
{
    MW_VENC_LEVEL_UNKNOWN,								///<Unknown
    MW_VENC_LEVEL_2_1,									///<Level 2.1
    MW_VENC_LEVEL_3_1,									///<Level 3.1
    MW_VENC_LEVEL_4_1,									///<Level 4.1
	MW_VENC_LEVEL_5_1,									///<Level 5.1
	MW_VENC_LEVEL_5_2,									///<Level 5.2
	MW_VENC_LEVEL_6_1,									///<Level 6.1
	MW_VENC_LEVEL_6_2,									///<Level 6.2
	MW_VENC_LEVEL_COUNT									///<The maximum input value 
}mw_venc_level_t;

/**
 * @ingroup group_hwe_variables_enum
 * @brief mw_venc_fourcc_t
 * @details Defines the color format.\n
 * Related type(s):\n
 * 	#mw_venc_param \n
 * Related function(s):\n
 *  [mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 * 	[mw_venc_get_default_param](@ref mw_venc_get_default_param) \n
 */
typedef enum mw_venc_fourcc
{
    MW_VENC_FOURCC_UNKNOWN,								///<Unknown
    MW_VENC_FOURCC_NV12,								///<NV12 equals #MWFOURCC_NV12
    MW_VENC_FOURCC_NV21,								///<NV21 equals #MWFOURCC_NV21
    MW_VENC_FOURCC_YV12,								///<YV12 equals #MWFOURCC_YV12
    MW_VENC_FOURCC_I420,								///<I420 equals #MWFOURCC_I420
    MW_VENC_FOURCC_YUY2,								///<YUY2 equals #MWFOURCC_YUY2
    MW_VENC_FOURCC_P010,								///<P010 equals #MWFOURCC_P010
	MW_VENC_FOURCC_BGRA,								///<BGRA equals #MWFOURCC_BGRA
	MW_VENC_FOURCC_RGBA,								///<RGBA equals #MWFOURCC_RGBA
    MW_VENC_FOURCC_ARGB,								///<ARGB equals #MWFOURCC_ARGB
    MW_VENC_FOURCC_ABGR,								///<ABGR equals #MWFOURCC_ABGR
	MW_VENC_FOURCC_COUNT								///<The maximum input value 
}mw_venc_fourcc_t;

/**
 * @ingroup group_hwe_variables_struct
 * @brief mw_venc_rate_control_t
 * @details Defines the parameters of bitrate controlling.\n
 * Related type(s):\n
 * 			#mw_venc_rate_control_mode_t \n
 * 			#MW_VENC_PROPERTY_RATE_CONTROL \n
 * Related function(s):\n
 *  [mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 * 	[mw_venc_get_default_param](@ref mw_venc_get_default_param) \n
 *  [mw_venc_get_property](@ref mw_venc_get_property)
 *  [mw_venc_set_property](@ref mw_venc_set_property)
 */
typedef struct mw_venc_rate_control
{
	mw_venc_rate_control_mode_t mode;					///<Bitrate controlling methods
	union{
        struct {
            uint32_t target_bitrate;					///<Target bitrate: only valid when the bitrate is variable or constant.
            uint32_t max_bitrate;						///<The maximun bitrate: only valid when the bitrate is variable.
        };
		struct {
		    uint8_t qpi;								///<I-Frame QP
			uint8_t qpb;								///<B-Frame QP
			uint8_t qpp;								///<P-Frame QP
            uint8_t reserved;							///<Reserved      
		};
	};
}mw_venc_rate_control_t;

/**
 * @ingroup group_hwe_variables_struct
 * @brief mw_venc_fps_t
 * @details Sets the frame rate.\n
 * Related type(s):\n
 * 	#MW_VENC_PROPERTY_FPS \n
 * Related function(s):\n
 *  [mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 * 	[mw_venc_get_default_param](@ref mw_venc_get_default_param) \n
 *  [mw_venc_get_property](@ref mw_venc_get_property)
 *  [mw_venc_set_property](@ref mw_venc_set_property)
 */
typedef struct mw_venc_fps{
		int32_t num;									///<Numerator of frames
		int32_t den;									///<Denominator of frames
}mw_venc_fps_t;

/**
 * @ingroup group_hwe_variables_struct
 * @brief mw_venc_extdata_t
 * @details Defines the extended encoding data.\n
 * Related type(s):\n
 * 	#MW_VENC_PROPERTY_EXTDATA \n
 * Related function(s):\n
 *  [mw_venc_get_property](@ref mw_venc_get_property)
 *  [mw_venc_set_property](@ref mw_venc_set_property)
 */
typedef struct mw_venc_extdata {
    uint8_t *p_extdata;									///<Extended data pointer. The data includes vps(Video Parameter Set),sps(Sequence Parameter Set) and pps(Picture Parameter Set).
    uint32_t extdata_len;								///<The total length of entended data
    uint32_t len[3];									///<len[0] vps_len;len[1] sps_len;len[2] pps_len
}mw_venc_extdata_t;

/**
 * @ingroup group_hwe_variables_enum
 * @brief mw_venc_property_t
 * @details Defines the encoder properties.\n
 * Related function(s):\n
 *  [mw_venc_get_property](@ref mw_venc_get_property)
 *  [mw_venc_set_property](@ref mw_venc_set_property)
 */
typedef enum mw_venc_property
{
    MW_VENC_PROPERTY_UNKNOWN,							///<Unknown
	MW_VENC_PROPERTY_RATE_CONTROL,						///<Rate: #mw_venc_rate_control_t default MW_VENC_RATECONTROL_CBR 4096k
	MW_VENC_PROPERTY_FPS,								///<Frame rate: #mw_venc_fps_t default 60/1
	MW_VENC_PROPERTY_GOP_SIZE,							///<GOP: int32_t default 60
	MW_VENC_PROPERTY_SLICE_NUM,							///<Number of slices: int32_t default 1
	MW_VENC_PROPERTY_GOP_REF_SIZE,						///<GOP reference size: int32_t defalut  0, if = 1 -> no b-frame
    MW_VENC_PROPERTY_EXTDATA,       					///<Extened data: #mw_venc_extdata_t just get vps sps pps
    MW_VENC_PROPERTY_FORCE_IDR,     					///<Force IDR 
	MW_VENC_PROPERTY_COUNT								///<The maximum input value 
}mw_venc_property_t;

/**
 * @ingroup group_hwe_variables_enum
 * @brief mw_venc_status_t
 * @details Return status of coding APIs
 */
typedef enum mw_venc_status
{
	MW_VENC_STATUS_SUCCESS,								///<Success
	MW_VENC_STATUS_FAIL,								///<Fail
	MW_VENC_STATUS_UNSUPPORT,							///<Not supported
    MW_VENC_STATUS_BUSY,								///<Busy
	MW_VENC_STATUS_INVALID_PARAM,						///<Invalid parameter
	MW_VENC_STATUS_UNKNOWN_ERROR,						///<Unknown error
	MW_VENC_STATUS_COUNT								///<The maximum input value 
}mw_venc_status_t;

/**
 * @ingroup group_hwe_variables_enum
 * @brief mw_venc_amd_mem_type_t
 * @details Defines types when encoding with AMD\n
 * Related function(s):\n
 *  [mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 */
typedef enum mw_venc_amd_mem_type {
	MW_VENC_AMD_MEM_AUTO,								///<Uses memory determined by system
	MW_VENC_AMD_MEM_CPU,								///<Uses memory
	MW_VENC_AMD_MEM_DX9,								///<Uses DX9
	MW_VENC_AMD_MEM_DX11,								///<Uses DX11
	MW_VENC_AMD_MEM_OPENGL,								///<Uses OpenGL
    MW_VENC_AMD_MEM_VULKAN,								///<Uses Vulkan
	MW_VENC_AMD_MEM_COUNT								///<The maximum input value 
}mw_venc_amd_mem_type_t;

//

/**
* @ingroup group_hwe_variables_enum
* @brief mw_venc_color_primaries_t
* Chromaticity coordinates of the source primaries.
* These values match the ones defined by ISO/IEC 23001-8_2013 7.1.
*/
typedef enum mw_venc_color_primaries {
    MW_VENC_COLOR_PRI_RESERVED0 = 0,
    MW_VENC_COLOR_PRI_BT709 = 1,  ///< also ITU-R BT1361 / IEC 61966-2-4 / SMPTE RP177 Annex B
    MW_VENC_COLOR_PRI_UNSPECIFIED = 2,
    MW_VENC_COLOR_PRI_RESERVED = 3,
    MW_VENC_COLOR_PRI_BT470M = 4,  ///< also FCC Title 47 Code of Federal Regulations 73.682 (a)(20)

    MW_VENC_COLOR_PRI_BT470BG = 5,  ///< also ITU-R BT601-6 625 / ITU-R BT1358 625 / ITU-R BT1700 625 PAL & SECAM
    MW_VENC_COLOR_PRI_SMPTE170M = 6,  ///< also ITU-R BT601-6 525 / ITU-R BT1358 525 / ITU-R BT1700 NTSC
    MW_VENC_COLOR_PRI_SMPTE240M = 7,  ///< functionally identical to above
    MW_VENC_COLOR_PRI_FILM = 8,  ///< colour filters using Illuminant C
    MW_VENC_COLOR_PRI_BT2020 = 9,  ///< ITU-R BT2020
    MW_VENC_COLOR_PRI_SMPTE428 = 10, ///< SMPTE ST 428-1 (CIE 1931 XYZ)
    MW_VENC_COLOR_PRI_SMPTEST428_1 = MW_VENC_COLOR_PRI_SMPTE428,
    MW_VENC_COLOR_PRI_SMPTE431 = 11, ///< SMPTE ST 431-2 (2011) / DCI P3
    MW_VENC_COLOR_PRI_SMPTE432 = 12, ///< SMPTE ST 432-1 (2010) / P3 D65 / Display P3
    MW_VENC_COLOR_PRI_JEDEC_P22 = 22, ///< JEDEC P22 phosphors
    MW_VENC_COLOR_PRI_COUNT                ///< Not part of ABI
}mw_venc_color_primaries_t;

/**
* @ingroup group_hwe_variables_enum
* @brief mw_venc_color_transfer_characteristic_t
* Color Transfer Characteristic.
* These values match the ones defined by ISO/IEC 23001-8_2013 7.2.
*/
typedef enum mw_venc_color_transfer_characteristic {
    MW_VENC_COLOR_TRC_RESERVED0 = 0,
    MW_VENC_COLOR_TRC_BT709 = 1,  ///< also ITU-R BT1361
    MW_VENC_COLOR_TRC_UNSPECIFIED = 2,
    MW_VENC_COLOR_TRC_RESERVED = 3,
    MW_VENC_COLOR_TRC_GAMMA22 = 4,  ///< also ITU-R BT470M / ITU-R BT1700 625 PAL & SECAM
    MW_VENC_COLOR_TRC_GAMMA28 = 5,  ///< also ITU-R BT470BG
    MW_VENC_COLOR_TRC_SMPTE170M = 6,  ///< also ITU-R BT601-6 525 or 625 / ITU-R BT1358 525 or 625 / ITU-R BT1700 NTSC
    MW_VENC_COLOR_TRC_SMPTE240M = 7,
    MW_VENC_COLOR_TRC_LINEAR = 8,  ///< "Linear transfer characteristics"
    MW_VENC_COLOR_TRC_LOG = 9,  ///< "Logarithmic transfer characteristic (100:1 range)"
    MW_VENC_COLOR_TRC_LOG_SQRT = 10, ///< "Logarithmic transfer characteristic (100 * Sqrt(10) : 1 range)"
    MW_VENC_COLOR_TRC_IEC61966_2_4 = 11, ///< IEC 61966-2-4
    MW_VENC_COLOR_TRC_BT1361_ECG = 12, ///< ITU-R BT1361 Extended Colour Gamut
    MW_VENC_COLOR_TRC_IEC61966_2_1 = 13, ///< IEC 61966-2-1 (sRGB or sYCC)
    MW_VENC_COLOR_TRC_BT2020_10 = 14, ///< ITU-R BT2020 for 10-bit system
    MW_VENC_COLOR_TRC_BT2020_12 = 15, ///< ITU-R BT2020 for 12-bit system
    MW_VENC_COLOR_TRC_SMPTE2084 = 16, ///< SMPTE ST 2084 for 10-, 12-, 14- and 16-bit systems
    MW_VENC_COLOR_TRC_SMPTEST2084 = MW_VENC_COLOR_TRC_SMPTE2084,
    MW_VENC_COLOR_TRC_SMPTE428 = 17, ///< SMPTE ST 428-1
    MW_VENC_COLOR_TRC_SMPTEST428_1 = MW_VENC_COLOR_TRC_SMPTE428,
    MW_VENC_COLOR_TRC_ARIB_STD_B67 = 18, ///< ARIB STD-B67, known as "Hybrid log-gamma"
    MW_VENC_COLOR_TRC_COUNT                 ///< Not part of ABI
}mw_venc_color_transfer_characteristic_t;

/**
* @ingroup group_hwe_variables_enum
* @brief mw_venc_color_space_t
* YUV colorspace type.
* These values match the ones defined by ISO/IEC 23001-8_2013 7.3.
*/
typedef enum mw_venc_color_space {
    MW_VENC_COLOR_SPACE_RGB = 0,  ///< order of coefficients is actually GBR, also IEC 61966-2-1 (sRGB)
    MW_VENC_COLOR_SPACE_BT709 = 1,  ///< also ITU-R BT1361 / IEC 61966-2-4 xvYCC709 / SMPTE RP177 Annex B
    MW_VENC_COLOR_SPACE_UNSPECIFIED = 2,
    MW_VENC_COLOR_SPACE_RESERVED = 3,
    MW_VENC_COLOR_SPACE_FCC = 4,  ///< FCC Title 47 Code of Federal Regulations 73.682 (a)(20)
    MW_VENC_COLOR_SPACE_BT470BG = 5,  ///< also ITU-R BT601-6 625 / ITU-R BT1358 625 / ITU-R BT1700 625 PAL & SECAM / IEC 61966-2-4 xvYCC601
    MW_VENC_COLOR_SPACE_SMPTE170M = 6,  ///< also ITU-R BT601-6 525 / ITU-R BT1358 525 / ITU-R BT1700 NTSC
    MW_VENC_COLOR_SPACE_SMPTE240M = 7,  ///< functionally identical to above
    MW_VENC_COLOR_SPACE_YCGCO = 8,  ///< Used by Dirac / VC-2 and H.264 FRext, see ITU-T SG16
    MW_VENC_COLOR_SPACE_YCOCG = MW_VENC_COLOR_SPACE_YCGCO,
    MW_VENC_COLOR_SPACE_BT2020_NCL = 9,  ///< ITU-R BT2020 non-constant luminance system
    MW_VENC_COLOR_SPACE_BT2020_CL = 10, ///< ITU-R BT2020 constant luminance system
    MW_VENC_COLOR_SPACE_SMPTE2085 = 11, ///< SMPTE 2085, Y'D'zD'x
    MW_VENC_COLOR_SPACE_CHROMA_DERIVED_NCL = 12, ///< Chromaticity-derived non-constant luminance system
    MW_VENC_COLOR_SPACE_CHROMA_DERIVED_CL = 13, ///< Chromaticity-derived constant luminance system
    MW_VENC_COLOR_SPACE_ICTCP = 14, ///< ITU-R BT.2100-0, ICtCp
    MW_VENC_COLOR_SPACE_COUNT                ///< Not part of ABI
}mw_venc_color_space_t;


/**
 * @ingroup group_hwe_variables_struct
 * @brief mw_venc_param_t
 * @details Encoder configurations\n
 * Related type(s):\n
 * 			#mw_venc_code_type_t \n
 * 			#mw_venc_fourcc_t \n
 * 			#mw_venc_targetusage_t \n 
 * 			#mw_venc_rate_control_t \n
 * 			#mw_venc_fps_t \n
 * 			#mw_venc_profile_t \n 
 * 			#mw_venc_level_t \n
 * 			#mw_venc_amd_mem_type_t \n
 * Related function(s):\n
 *  [mw_venc_create](@ref mw_venc_create) \n
 *  [mw_venc_create_ex](@ref mw_venc_create_ex) \n
 * 	[mw_venc_get_default_param](@ref mw_venc_get_default_param) \n
 */
typedef struct mw_venc_param {
	mw_venc_code_type_t code_type;						///<Code type, H264 or H265 
	mw_venc_fourcc_t fourcc;							///<Color format of input data 
	mw_venc_targetusage_t targetusage;					///<Preset
	mw_venc_rate_control_t rate_control;				///<Frame control 
	int32_t width;										///<width of input video
	int32_t height;										///<Height of input video
	mw_venc_fps_t fps;									///<Frame rate 
	int32_t slice_num;									///<Slice number 
	int32_t gop_pic_size;								///<GOP size
	int32_t gop_ref_size;								///<Referenced GOP size 
	mw_venc_profile_t profile;							///<Profile
	mw_venc_level_t level;								///<Level
    int32_t intel_async_depth;
	mw_venc_amd_mem_type_t amd_mem_reserved;			///<AMD storage type, which are valid only if you are using AMD to encode. 
    int32_t yuv_is_full_range;
    mw_venc_color_primaries_t color_primaries;
    mw_venc_color_transfer_characteristic_t color_trc;
    mw_venc_color_space_t color_space;
}mw_venc_param_t;

/**
 * @ingroup group_hwe_variables_struct
 * @brief mw_venc_gpu_info_t
 * @details hardware codec information\n
 *  Related type(s):\n
 * 			#mw_venc_platform_t \n
 * Related function(s):\n
 *  [mw_venc_get_gpu_info_by_index](@ref mw_venc_get_gpu_info_by_index) \n
 *  [mw_venc_create_by_index](@ref mw_venc_create_by_index) \n
 */
typedef struct mw_venc_gpu_info {
	char gpu_name[128];									///gpu name
	mw_venc_platform_t platform;						///gpu platform
}mw_venc_gpu_info_t;

#endif