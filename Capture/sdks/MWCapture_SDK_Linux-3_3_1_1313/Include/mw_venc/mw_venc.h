#ifndef MW_VENC_H
#define MW_VENC_H

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

#ifdef _WIN32
#ifdef MWVENC_EXPORTS
#define MWVENC_API __declspec(dllexport)
#else
#define MWVENC_API __declspec(dllimport)
#endif
#endif

#include "mw_venc_common.h"

/**
 * @ingroup group_hwe_functions
 * @brief Initializes mw_venc
 * @return Returns #mw_venc_status_t, by default it is #MW_VENC_STATUS_SUCCESS.
 * @details Usage: 
 * The suggested API call:  
 * @code
 * // Call the function before other mw_venc modules. It initializes resources for the mw_venc.
 * mw_venc_init();
 * ...
 * int t_n_num = mw_venc_get_gpu_num();
 * ...
 * uint32 t_u32_platforms = mw_venc_get_support_platfrom()
 * ...
 * mw_venc_deinit();
 * @endcode
 */
#ifdef _WIN32
MWVENC_API
#endif
mw_venc_status_t mw_venc_init();

/**
 * @ingroup group_hwe_functions
 * @brief Destroys mw_venc
 * @return Returns #mw_venc_status_t, by default it is #MW_VENC_STATUS_SUCCESS.
 * @details Usage: 
 * Refers to [mw_venc_init](@ref mw_venc_init)
 */ 
#ifdef _WIN32
MWVENC_API
#endif
mw_venc_status_t mw_venc_deinit();

/**
 * @ingroup group_hwe_functions
 * @brief Obtains the number of GPUs for hardware video encoding and decoding
 * @return Returns the number of GPUs for hardware video encoding and decoding
 * @details Usage: 
 * Refers to [mw_venc_init](@ref mw_venc_init)  
 * Note: Call the function after [mw_venc_init](@ref mw_venc_init) 
 */ 
#ifdef _WIN32
MWVENC_API
#endif
int32_t mw_venc_get_gpu_num();

/**
 * @ingroup group_hwe_functions
 * @brief Obtains hardware information of GPU by index 
 * @return Returns #mw_venc_status_t. The possible return values are as follows.
 * <table>
 *  <tr>
 *      <td> #MW_VENC_STATUS_SUCCESS </td>
 *      <td> Function call succeeded. </td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_INVALID_PARAM </td>
 *      <td> Input invalid value(s). </td>
 *  </tr>
 * </table>
 * @details Related type(s):\n
 *  #mw_venc_gpu_info_t  
 * Usage:\n
 * @code
 * mw_venc_status_t t_status = MW_VENC_STATUS_SUCCESS;
 * mw_venc_init();
 * ...
 * int t_n_num = mw_venc_get_gpu_num();
 * ...
 * uint32 t_u32_platforms = mw_venc_get_support_platfrom();
 * for(int i=0;i<t_u32_platforms;i++){
 *     mw_venc_gpu_info_t t_gou_info;
 *     t_status = mw_venc_get_gpu_info_by_index(i,&t_gpu_info);
 *     if(t_status == MW_VENC_STATUS_SUCCESS){
 *          // ...
 *     } 
 * }
 * ...
 * mw_venc_deinit();
 * @endcode  
 * Call the function after [mw_venc_init](@ref mw_venc_init) 
 */ 
#ifdef _WIN32
MWVENC_API
#endif
mw_venc_status_t mw_venc_get_gpu_info_by_index(int32_t index, mw_venc_gpu_info_t *info);

typedef struct venc_handle *mw_venc_handle_t;

/**
 * @ingroup group_hwe_functions
 * @brief Gets the default value of encoding parameters
 * @param[out] p_param encoding parameters
 * @return The values of returned #mw_venc_status_t are as follows.
 * <table>
 *  <tr>
 *      <td> #MW_VENC_STATUS_SUCCESS </td>
 *      <td>  Function call succeeded. </td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_INVALID_PARAM </td>
 *      <td>  Input invalid value(s).</td>
 *  </tr>
 * </table>
 * @details Related type(s):\n
 * #mw_venc_param_t \n
 * Sets the default value of the parameters.\n
 * @code
 * p_param->code_type = MW_VENC_CODE_TYPE_UNKNOWN;
 * p_param->fourcc = MW_VENC_FOURCC_UNKNOWN;
 * p_param->targetusage = MW_VENC_TARGETUSAGE_BALANCED;
 * p_param->rate_control.mode = MW_VENC_RATECONTROL_UNKNOWN;
 * p_param->rate_control.target_bitrate = 0;
 * p_param->rate_control.max_bitrate = 0;
 * p_param->width = 0;
 * p_param->height = 0;
 * p_param->fps.num = 60;
 * p_param->fps.den = 1;
 * p_param->slice_num = 1;
 * p_param->gop_pic_size = 60;
 * p_param->gop_ref_size = 1;
 * p_param->profile = MW_VENC_PROFILE_UNKNOWN;
 * p_param->level = MW_VENC_LEVEL_5_1;
 * p_param->amd_mem_reserved = MW_VENC_AMD_MEM_DX11;
 * @endcode
 */
#ifdef _WIN32
MWVENC_API 
#endif
mw_venc_status_t mw_venc_get_default_param(mw_venc_param_t *p_param);

/**
 * @ingroup group_hwe_functions
 * @brief Gets supported encoding hardware platform.
 * @return Returns mask of supported hardware encoding platform. The detailed information refers to #mw_venc_platform_t.
 * @details Usage: \n
 * The recommended way of calling function:
 * @code
 * ...
 * mw_venc_init();
 * ...
 * uint32 t_u32_platfrom = mw_venc_get_support_platfrom();
 * if(t_u32_platfrom & MW_VENC_PLATFORM_AMD){
 *  //For AMD hardware encoding
 * }
 * if(t_u32_platform & MW_VENC_PLATFORM_INTEL){
 *  //For Intel hardware encoding
 * }
 * if(t_u32_platform & MW_VENC_PLATFORM_NVIDIA){
 *  //For Nvidia hardware encoding
 * }
 * ...
 * mw_venc_deinit();
 * ...
 * @endcode
 */
#ifdef _WIN32
MWVENC_API
#endif
uint32_t mw_venc_get_support_platfrom();

/**
 * @ingroup group_hwe_functions
 * @brief Creates an encoder.
 * @param[in] platform                Hardware encoding platform
 * @param[in] p_param                 Encoder parameters
 * @param[in] frame_callback          Encoder callback function
 * @param[in] user_ptr                Callback parameter
 * @return Returns the encoder handle if succeeded, otherwise returns NULL.
 * @details Usage: \n
 * The recommended way to call the function is as follows.
 * @code
 * ....
 * // Callback function
 * void encode_callback(
 *      void * user_ptr, 
 *      const uint8_t * p_frame, 
 *      uint32_t frame_len, 
 *      mw_venc_frame_info_t *p_frame_info)
 * {
 *      // Processes data
 * }
 * ...
 * mw_venc_init();
 * ...
 * mw_venc_handle_t t_handle = NULL;
 * mw_venc_platform_t t_platfrom = MW_VENC_PLATFORM_UNKNOWN;
 * mw_venc_param_t t_venc_param;
 * mw_venc_status_t t_venc_stat = MW_VENC_STATUS_SUCCESS;
 * mw_venc_get_default_param(&t_venc_param);
 * uint32 t_u32_platfrom = mw_venc_get_support_platfrom();
 * if(t_u32_platfrom & MW_VENC_PLATFORM_AMD){
 *  //For AMD
 *  t_platfrom = MW_VENC_PLATFORM_AMD;
 * }
 * if(t_u32_platform & MW_VENC_PLATFORM_INTEL){
 *  //For Intel
 *  t_platfrom = MW_VENC_PLATFORM_INTEL;
 * }
 * if(t_u32_platform & MW_VENC_PLATFORM_NVIDIA){
 *  //For Nvidia
 *  t_platfrom = MW_VENC_PLATFORM_NVIDIA;
 * }
 * t_venc_param.code_type = MW_VENC_CODE_TYPE_H264;
 * t_venc_param.fourcc = MW_VENC_FOURCC_NV12;
 * t_venc_param.targetusage = MW_VENC_TARGETUSAGE_BALANCED;
 * t_venc_param.rate_control.mode = MW_VENC_RATECONTROL_CBR;
 * t_venc_param.rate_control.target_bitrate = 4096;
 * t_venc_param.width = 1920;
 * t_venc_param.height = 1080;
 * t_venc_param.profile = MW_VENC_PROFILE_H264_MAIN;
 * ...
 * // Creates an encoder
 * t_handle = mw_venc_create(t_platfrom,&t_venc_param,encode_callback,NULL);
 * ...
 * // Inputs data char* t_p_data;
 * t_venc_stat = mw_venc_put_frame(t_handle,t_p_data);
 * ...
 * // Gets parameters of encoder
 * mw_venc_property_t t_property = MW_VENC_PROPERTY_FPS;
 * mw_venc_fps_t t_fps;
 * t_venc_stat = mw_venc_get_property(t_handle,t_property,&t_fps);
 * ...
 * //Modifies parameters of encoder
 * t_fps.num = 30;
 * t_fps.den = 1;
 * t_venc_stat = mw_venc_set_property(t_handle,t_property,&t_fps);
 * ...
 * // Destroys the encoder
 * t_venc_stat = mw_venc_destory(t_handle);
 * t_handle = NULL;
 * ...
* mw_venc_deinit();
 * ...
 * @endcode
 */
#ifdef _WIN32
MWVENC_API 
#endif
mw_venc_handle_t 
mw_venc_create(
    mw_venc_platform_t platform, 
    mw_venc_param_t *p_param,
    MW_ENCODER_CALLBACK frame_callback, 
    void *user_ptr);


/**
 * @ingroup group_hwe_functions
 * @brief Ctreats an encoder
 * @param[in] index                   index of GPU used for hardware encoding
 * @param[in] p_param                 parameters of the encoder
 * @param[in] frame_callback          callback 
 * @param[in] user_ptr                callback parameters 
 * @return If succeeded, it returns the encoder handle; otherwise, it returns NULL.
 * @details Usage: \n
 *  The recommended way to call the function is as follows.
 * @code
 * ....
 * // callback
 * void encode_callback(
 *      void * user_ptr, 
 *      const uint8_t * p_frame, 
 *      uint32_t frame_len, 
 *      mw_venc_frame_info_t *p_frame_info)
 * {
 *      // Processes data
 * }
 * ...
 * mw_venc_init();
 * ...
 * mw_venc_handle_t t_handle = NULL;
 * mw_venc_platform_t t_platfrom = MW_VENC_PLATFORM_UNKNOWN;
 * mw_venc_param_t t_venc_param;
 * mw_venc_status_t t_venc_stat = MW_VENC_STATUS_SUCCESS;
 * mw_venc_get_default_param(&t_venc_param);
 * int t_n_num = mw_venc_get_gpu_num();
 * int t_n_index = -1;
 * if(t_n_num>0)
 *    t_n_index = 0;  
 * t_venc_param.code_type = MW_VENC_CODE_TYPE_H264;
 * t_venc_param.fourcc = MW_VENC_FOURCC_NV12;
 * t_venc_param.targetusage = MW_VENC_TARGETUSAGE_BALANCED;
 * t_venc_param.rate_control.mode = MW_VENC_RATECONTROL_CBR;
 * t_venc_param.rate_control.target_bitrate = 4096;
 * t_venc_param.width = 1920;
 * t_venc_param.height = 1080;
 * t_venc_param.profile = MW_VENC_PROFILE_H264_MAIN;
 * ...
 * // Creates an encoder
 * t_handle = mw_venc_create_by_index(t_n_index,&t_venc_param,encode_callback,NULL);
 * ...
 * // Inputs data char* t_p_data;
 * t_venc_stat = mw_venc_put_frame(t_handle,t_p_data);
 * ...
 * // Obtains encoder parameters
 * mw_venc_property_t t_property = MW_VENC_PROPERTY_FPS;
 * mw_venc_fps_t t_fps;
 * t_venc_stat = mw_venc_get_property(t_handle,t_property,&t_fps);
 * ...
 * // Modifys encoder parameters
 * t_fps.num = 30;
 * t_fps.den = 1;
 * t_venc_stat = mw_venc_set_property(t_handle,t_property,&t_fps);
 * ...
 * // Destroys the encoder
 * t_venc_stat = mw_venc_destory(t_handle);
 * t_handle = NULL;
 * ...
 * mw_venc_deinit();
 * ...
 * @endcode
 */
#ifdef _WIN32
MWVENC_API
#endif
mw_venc_handle_t
mw_venc_create_by_index(
    int32_t index,
    mw_venc_param_t *p_param,
    MW_ENCODER_CALLBACK frame_callback,
    void *user_ptr);

/**
 * @ingroup group_hwe_functions
 * @brief Imports data to encoders.
 * @param[in] handle        Encoder handle
 * @param[in] p_frame       Frame data
 * @return The possible return values of #mw_venc_status_t are as follows.
 * <table>
 *  <tr>
 *      <td> #MW_VENC_STATUS_SUCCESS </td>
 *      <td>  Function call succeeded. </td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_INVALID_PARAM </td>
 *      <td>  Input invalid value(s).</td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_FAIL </td>
 *      <td> Function call failed.</td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_UNKNOWN_ERROR </td>
 *      <td> Function call failed with unknown errors.</td>
 *  </tr>
 * </table>
 * @details Usage: \n
 * The usage refers to [mw_venc_create](@ref mw_venc_create) \n
 *         [mw_venc_create_by_index](@ref mw_venc_create_by_index)
 */
#ifdef _WIN32
MWVENC_API 
#endif
mw_venc_status_t 
mw_venc_put_frame(
    mw_venc_handle_t handle, 
    uint8_t *p_frame);

/**
* @ingroup group_hwe_functions
* @brief Imports data to encoders.
* @param[in] handle        Encoder handle
* @param[in] p_frame       Frame data
* @param[in] pts           timestamp
* @return The possible return values of #mw_venc_status_t are as follows.
* <table>
*  <tr>
*      <td> #MW_VENC_STATUS_SUCCESS </td>
*      <td> Function call succeeded  </td>
*  </tr>
*  <tr>
*      <td> #MW_VENC_STATUS_INVALID_PARAM </td>
*      <td> Input invalid value(s). </td>
*  </tr>
*  <tr>
*      <td> #MW_VENC_STATUS_FAIL </td>
*      <td> Function call failed. </td>
*  </tr>
*  <tr>
*      <td> #MW_VENC_STATUS_UNKNOWN_ERROR </td>
*      <td> Function call failed with unknown errors. </td>
*  </tr>
* </table>
* @details Usage: \n
* The usage refers to [mw_venc_put_frame](@ref mw_venc_put_frame)
*/
#ifdef _WIN32
MWVENC_API
#endif
mw_venc_status_t
mw_venc_put_frame_ex(
    mw_venc_handle_t handle,
    uint8_t *p_frame,
    int64_t pts);

/**
 * @ingroup group_hwe_functions
 * @brief Destroys encoders.
 * @param[in] handle    Encoder handle  
 * @return The possible return values of #mw_venc_status_t are as follows.
 * <table>
 *  <tr>
 *      <td> #MW_VENC_STATUS_SUCCESS </td>
 *      <td> Function call succeeded.  </td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_INVALID_PARAM </td>
 *      <td> Input invalid value(s).</td>
 *  </tr>
 * </table>
 * @details Usage: \n
 * The usage refers to [mw_venc_create](@ref mw_venc_create)
 *         [mw_venc_create_by_index](@ref mw_venc_create_by_index)
 */
#ifdef _WIN32
MWVENC_API 
#endif
mw_venc_status_t 
mw_venc_destory(mw_venc_handle_t handle);

/**
 * @ingroup group_hwe_functions
 * @brief Gets encoder parameters.
 * @param[in] handle    Encoder handle
 * @param[in] param     Parameter type
 * @param[out] args     Parameter values
 * @return The possible return values of #mw_venc_status_t are as follows.
 * <table>
 *  <tr>
 *      <td> #MW_VENC_STATUS_SUCCESS </td>
 *      <td> Function call succeeded.  </td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_INVALID_PARAM </td>
 *      <td>  Input invalid value(s). </td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_FAIL </td>
 *      <td> Failed to get encoder parameters. </td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_UNSUPPORT </td>
 *      <td> Unsupported parameter type. </td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_UNKNOWN_ERROR </td>
 *      <td> Failed to get encoder parameters with unknown error. </td>
 *  </tr>
 * </table>
 * @details Usage: \n
 * The usage refers to [mw_venc_create](@ref mw_venc_create)
 *         [mw_venc_create_by_index](@ref mw_venc_create_by_index)
 */
#ifdef _WIN32
MWVENC_API 
#endif
mw_venc_status_t 
mw_venc_get_property(
    mw_venc_handle_t handle,
    mw_venc_property_t param, 
    void *args);

/**
 * @ingroup group_hwe_functions
 * @brief Sets encoder parameters.
 * @param[in]   handle  Encoder handle
 * @parma[in]   param   Parameter type
 * @param[in]   args    Parameter values
 * @return The possible return values of #mw_venc_status_t are as follows.
 * <table>
 *  <tr>
 *      <td> #MW_VENC_STATUS_SUCCESS </td>
 *      <td> Function call succeeded.</td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_INVALID_PARAM </td>
 *      <td> Input invalid value(s).</td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_FAIL </td>
 *      <td> Function call failed.</td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_UNSUPPORT </td>
 *      <td> Unsupported parameter type. </td>
 *  </tr>
 * </table>
 * @details Usage: \n
 * The usage refers to [mw_venc_create](@ref mw_venc_create)
 *         [mw_venc_create_by_index](@ref mw_venc_create_by_index)
 */
#ifdef _WIN32
MWVENC_API 
#endif
mw_venc_status_t
mw_venc_set_property(
    mw_venc_handle_t handle,
    mw_venc_property_t param,
    void *args);

#endif