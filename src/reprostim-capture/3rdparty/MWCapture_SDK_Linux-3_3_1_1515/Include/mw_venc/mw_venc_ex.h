#ifndef MW_VENC_EX_H
#define MW_VENC_EX_H

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

#include "mw_venc_common_ex.h"
#include "mw_venc.h"

/**
 * @ingroup group_hwe_ex_functions
 * @brief Creates extended encoders which support to input OpenGL texture.
 * @param[in]   platform        Hardware coding platform
 * @param[in]   inframe_mode    Input type of coding data
 * @param[in]   p_param         Extended parameters of encoder
 * @param[in]   frame_callback  Callback function
 * @param[in]   user_ptr        Callback parameters
 * @return Returns encoder handle if succeeded, otherwise, returns NULL.
 * @details Usage: \n
 * The recommended way to call the function is as follows.
 * @code
 * ....
 * // Encodes callback functions
 * void encode_callback(
 *      void * user_ptr, 
 *      const uint8_t * p_frame, 
 *      uint32_t frame_len, 
 *      mw_venc_frame_info_t *p_frame_info)
 * {
 *      // Processes data
 * }
 * ....
 * mw_venc_handle_t t_handle = NULL;
 * mw_venc_platform_t t_platfrom = MW_VENC_PLATFORM_UNKNOWN;
 * mw_venc_param_ex_t t_venc_param;
 * mw_venc_status_t t_venc_stat = MW_VENC_STATUS_SUCCESS;
 * mw_venc_get_default_param(&t_venc_param.m_venc_param);
 * mw_venc_inframe_mode_t t_mode = MW_VENC_INFRAME_MODE_OPENGL_TEXTURE;
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
 * t_venc_param.m_venc_param.code_type = MW_VENC_CODE_TYPE_H264;
 * t_venc_param.m_venc_param.fourcc = MW_VENC_FOURCC_NV12;
 * t_venc_param.m_venc_param.targetusage = MW_VENC_TARGETUSAGE_BALANCED;
 * t_venc_param.m_venc_param.rate_control.mode = MW_VENC_RATECONTROL_CBR;
 * t_venc_param.m_venc_param.rate_control.target_bitrate = 4096;
 * t_venc_param.m_venc_param.width = 1920;
 * t_venc_param.m_venc_param.height = 1080;
 * t_venc_param.m_venc_param.profile = MW_VENC_PROFILE_H264_MAIN;
 * ...
 * // Sets AMD OpenGL parameters including HDC g_hdc, HGLRC g_hrc, HWND g_window.
 * if(t_platfrom == MW_VENC_PLATFORM_AMD){
 *  t_venc_param.m_amd_opengl_reserved.m_p_opengl_context = g_hrc;
 *  t_venc_param.m_amd_opengl_reserved.m_p_window = g_window;
 *  t_venc_param.m_amd_opengl_reserved.m_p_dc = g_hdc;
 * }
 * ...
 * // Creates encoders
 * t_handle = mw_venc_create_ex(
 *              t_platfrom,
 *              t_mode,
 *              &t_venc_param,
 *              encode_callback,
 *              NULL);
 * ...
 * // Inputs data GLuint t_glui_texture[];
 * t_venc_stat = mw_venc_put_opengl_texture(t_handle, t_glui_texture);
 * ...
 * // Gets encoder parameters
 * mw_venc_property_t t_property = MW_VENC_PROPERTY_FPS;
 * mw_venc_fps_t t_fps;
 * t_venc_stat = mw_venc_get_property(t_handle,t_property,&t_fps);
 * ...
 * // Modifies encoder parameters
 * t_fps.num = 30;
 * t_fps.den = 1;
 * t_venc_stat = mw_venc_get_property(t_handle,t_property,&t_fps);
 * ...
 * // Destroys encoders
 * t_venc_stat = mw_venc_destory_ex(t_handle);
 * t_handle = NULL;
 * ...
 * @endcode
 */
#ifdef _WIN32
MWVENC_API 
#endif
mw_venc_handle_t 
mw_venc_create_ex(
    mw_venc_platform_t platform,
    mw_venc_inframe_mode_t inframe_mode,
    mw_venc_param_ex_t *p_param,
    MW_ENCODER_CALLBACK frame_callback, 
    void *user_ptr);

/**
 * @ingroup group_hwe_ex_functions
 * @brief Imports OpenGL texture into encoders
 * @param[in] handle    Encoder handle
 * @param[in] texture   Index of OpenGL texture
 * @return The possible return values of #mw_venc_status_t are as follows.
 * <table>
 *  <tr>
 *      <td> #MW_VENC_STATUS_SUCCESS </td>
 *      <td> Function call succeeded.</td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_INVALID_PARAM </td>
 *      <td> Input invalid value(s). </td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_UNKNOWN_ERROR </td>
 *      <td> Function call failed caused by unknown reasons.</td>
 *  </tr>
 *  <tr>
 *      <td> #MW_VENC_STATUS_FAIL </td>
 *      <td>Function call failed. </td>
 *  </tr>
 * </table>
 * @details Usage: \n
 * The usage refers to  [mw_venc_create_ex](@ref mw_venc_create_ex)
 */
#ifdef _WIN32
MWVENC_API 
#endif
mw_venc_status_t 
mw_venc_put_opengl_texture(
    mw_venc_handle_t handle, 
    uint32_t texture[]);

/**
 * @ingroup group_hwe_ex_functions
 * @brief Destroys the extended encoders.
 * @param[in] handle    Encoder handle
 * @return The possible return values of #mw_venc_status_t are as follows.
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
 * @details Usage: \n
 * The usage refers to [mw_venc_create_ex](@ref mw_venc_create_ex)
 */
#ifdef _WIN32
MWVENC_API
#endif
mw_venc_status_t
mw_venc_destory_ex(mw_venc_handle_t handle);

#endif