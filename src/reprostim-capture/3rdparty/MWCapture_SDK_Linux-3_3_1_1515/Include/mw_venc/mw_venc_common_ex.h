#ifndef MW_VENC_COMMON_EX_H
#define MW_VENC_COMMON_EX_H

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

#include "mw_venc_common.h"

/**
 * @ingroup group_hwe_ex_variables_enum
 * @brief mw_venc_inframe_mode_t
 * @details Defines the data type entered by the encoder.\n
 * Related function(s): \n
 * [mw_venc_create_ex](@ref mw_venc_create_ex)
 */
typedef enum mw_venc_inframe_mode
{
    MW_VENC_INFRAME_MODE_UNKNOWN,							///<Inputs unknown data type
    MW_VENC_INFRAME_MODE_OPENGL_TEXTURE,					///<Inputs OpenGL texture 
    MW_VENC_INFRAME_MODE_COUNT								///<Number of input data types 
}mw_venc_inframe_mode_t;

/**
 * @ingroup group_hwe_ex_variables_struct
 * @brief mw_venc_amd_opengl_param_t
 * @details Defines AMD OpenGL parameters.\n
 * Related types:\n
 * #mw_venc_param_ex_t \n
 * Related function(s): \n
 * [mw_venc_create_ex](@ref mw_venc_create_ex)
 */
typedef struct mw_venc_amd_opengl_param {
	void*						m_p_opengl_context;			///<OpenGL context
	void*						m_p_window;					///<Window handle
	void*						m_p_dc;						///<DC handle
}mw_venc_amd_opengl_param_t;

/**
 * @ingroup group_hwe_ex_variables_struct
 * @brief mw_venc_param_ex_t
 * @details Defines the extended parameters of encoder to support OpenGL texture.\n
 * Related type(s):\n
 * #mw_venc_param_t\n
 * #mw_venc_amd_opengl_param_t\n
 * Related function(s): \n
 * [mw_venc_create_ex](@ref mw_venc_create_ex)
 */
typedef struct mw_venc_param_ex {
	mw_venc_param_t				m_venc_param;				///<Encoder	configurations 		
	mw_venc_amd_opengl_param_t	m_amd_opengl_reserved;		///<AMD OpenGL parameters which are valid if an AMD device is used.	                                                            
}mw_venc_param_ex_t;

#endif
