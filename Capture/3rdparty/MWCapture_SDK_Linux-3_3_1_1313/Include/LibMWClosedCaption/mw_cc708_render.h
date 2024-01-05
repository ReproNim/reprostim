#ifndef CCREBDER_FT
#define CCREBDER_FT
////////////////////////////////////////////////////////////////////////////////
// Copyright (c) 2011-2018 Magewell Electronics Co., Ltd. (Nanjing)
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


#include "mw_cc708_render_base_types.h"
#include "mw_cc708_base_types.h"
#include "mw_error_code.h"
#pragma once

#ifdef LIBCCRENDER_FREETYPE_EXPORTS
#define LIBCCRENDER_FREETYPE_API __declspec(dllexport)
#elif LIBCCRENDER_FREETYPE_DLL
#define LIBCCRENDER_FREETYPE_API __declspec(dllimport)
#else
#define LIBCCRENDER_FREETYPE_API
#endif

/**
 * @ingroup group_cc_functions_render
 * @brief MWCreateRender
 *        Creates a CC renderer
 * @return If succeeded, it returns cc renderer; otherwise, it returns null.
 */
LIBCCRENDER_FREETYPE_API
mw_cc_render_t *MWCreateRender();

/**
 * @ingroup group_cc_functions_render
 * @brief MWDestoryRender
 *        Destroys a cc renderer
 * @param[in] pRender       cc renderer
 */
LIBCCRENDER_FREETYPE_API
void MWDestoryRender(mw_cc_render_t *pRender);

/**
 * @ingroup group_cc_functions_render
 * @brief MWLoadFont
 *        Uploads fonts
 * @param[in] t_pmcfFont    Font
 * @param[in] pRender       cc renderer
 * @return  Returns true if succeeded.
 */
LIBCCRENDER_FREETYPE_API
bool MWLoadFont(mw_cc_font_t *t_pmcfFont, mw_cc_render_t *pRender);

/**
 * @ingroup group_cc_functions_render
 * @brief MWUnLoadFont
 *        Unloads fonts
 * @param[in] t_pmcfFont    Font
 * @param[in] pRender       cc renderer
 */
LIBCCRENDER_FREETYPE_API
void MWUnLoadFont(mw_cc_font_t *t_pmcfFont, mw_cc_render_t *pRender);

/**
 * @ingroup group_cc_functions_render
 * @brief MWCreateCCScreen
 *        Creates a CC screen
 * @param[in] t_nWidth      Width of the screen
 * @param[in] t_nHeight     Height of the screen
 * @return Returns NULL if failed.
 */
LIBCCRENDER_FREETYPE_API
mw_cc_screen_t *MWCreateCCScreen(int t_nWidth, int t_nHeight);

/**
 * @ingroup group_cc_functions_render
 * @brief MWDestoryCCScreen
 *       Destroys a CC Screen
 * @param[in] t_pScreen    Screen
 */
LIBCCRENDER_FREETYPE_API
void MWDestoryCCScreen(mw_cc_screen_t *t_pScreen);

/**
 * @ingroup group_cc_functions_render
 * @brief MWRenderCC608Screen
 *        Renders on screens with cc608 buffer
 * @param[out] t_pScreen         	Screen
 * @param[in] t_pCC608Buffer    	cc608 buffer
 * @param[in] t_pmcfFont        	Font
 * @param[in] pRender           	Renderer
 * @return Returns #MW_CC_NO_ERROR if succeeded.
 */
LIBCCRENDER_FREETYPE_API
MW_CC_RESULT MWRenderCC608Screen(
        mw_cc_screen_t *t_pScreen,
        mw_cc608_buffer_t *t_pCC608Buffer,
        mw_cc_font_t *t_pmcfFont,
        mw_cc_render_t *pRender);

/**
 * @ingroup group_cc_functions_render
 * @brief MWRenderCC608Buffer
 *        Render cc608 buffer to the specified memory
 * @param[out] t_pScreen		the specified memory
 * @param[in] t_nWidth			Memory width
 * @param[in] t_nHeight			Memory height
 * @param[in] t_nSize			Memory size
 * @param[in] t_pCC608Buffer    cc608 buffer
 * @param[in] t_pmcfFont		Font
 * @param[in] pRender			Renderer
 * @return If succeeded, it returns #MW_CC_NO_ERROR.
 */
LIBCCRENDER_FREETYPE_API
MW_CC_RESULT MWRenderCC608Buffer(
        unsigned char *t_pScreen,
        int t_nWidth,
        int t_nHeight,
        int t_nSize,
        mw_cc608_buffer_t *t_pCC608Buffer,
        mw_cc_font_t *t_pmcfFont,
        mw_cc_render_t *pRender);

/**
 * @ingroup group_cc_functions_render
 * @brief MWRenderCC608BufferArea
 *        Renders cc608 buffer to specified area of specified memory
 * @param[out] t_pScreen		Specified memory
 * @param[in] t_nWidth			Width of memory 
 * @param[in] t_nHeight			Height of memory 
 * @param[in] t_nSize			Size of memory 
 * @param[in] t_nX				x coordinates of the specified area 
 * @param[in] t_nY				y coordinates of the specified area y coordinates
 * @param[in] t_nAWidth			width of the specified area
 * @param[in] t_nAHeight		Height of the specified area
 * @param[in] t_pCC608Buffer    cc608 buffer
 * @param[in] t_pmcfFont		Font
 * @param[in] pRender			Renderer
 * @return If succeeded, it returns #MW_CC_NO_ERROR
 */
LIBCCRENDER_FREETYPE_API
MW_CC_RESULT MWRenderCC608BufferArea(
		unsigned char *t_pScreen,
		int t_nWidth,
		int t_nHeight,
		int t_nSize,
		int t_nX,
		int t_nY,
		int t_nAWidth,
		int t_nAHeight,
		mw_cc608_buffer_t *t_pCC608Buffer,
		mw_cc_font_t *t_pmcfFont,
		mw_cc_render_t *pRender
);

/**
 * @ingroup group_cc_functions_render
 * @brief MWRenderCC708Screen
 *        Renders cc708 tv_window_screen to screen
 * @param[out] t_pScreen        Screen
 * @param[in] t_pWindowScreen   cc708 tv_window_screen
 * @param[in] t_pmcfFont        Font
 * @param[in] pRender           Renderer
 * @return If succeeded, it returns #MW_CC_NO_ERROR.
 */
LIBCCRENDER_FREETYPE_API
MW_CC_RESULT MWRenderCC708Screen(mw_cc_screen_t *t_pScreen, mw_cc708_tv_window_screen_t *t_pWindowScreen, mw_cc_font_t *t_pmcfFont, mw_cc_render_t *pRender);

/**
 * @ingroup group_cc_functions_render
 * @brief MWRenderCC708Buffer
 *        Renders cc708 tv_window_screen to the specified memory
 * @param[out] t_pScreen		Specified memory
 * @param[in] t_nWidth			Width of memory 
 * @param[in] t_nHeight			Height of memory 
 * @param[in] t_nSize			Size of memory 
 * @param[in] t_pWindowScreen   cc708 tv_window_screen
 * @param[in] t_pmcfFont		Font
 * @param[in] pRender			Renderer
 * @return If succeeded, it returns #MW_CC_NO_ERROR
 */
LIBCCRENDER_FREETYPE_API
MW_CC_RESULT MWRenderCC708Buffer(
        unsigned char *t_pScreen,
        int t_nWidth,
        int t_nHeight,
        int t_nSize,
        mw_cc708_tv_window_screen_t *t_pWindowScreen,
        mw_cc_font_t *t_pmcfFont,
        mw_cc_render_t *pRender);

/**
 * @ingroup group_cc_functions_render
 * @brief MWRenderCC708BufferArea
 *	  Renders cc708 tv_window_screen to the specified area of specified memory 
 * @param[out] t_pScreen		Specified memory
 * @param[in] t_nWidth			Memory width
 * @param[in] t_nHeight			Memory height
 * @param[in] t_nSize			Memory size
 * @param[in] t_nX				Specified area x coordinates
 * @param[in] t_nY				Specified area y coordinates
 * @param[in] t_nAWidth			Area width
 * @param[in] t_nAHeight		Area height
 * @param[in] t_pWindowScreen   cc708 tv_window_screen
 * @param[in] t_pmcfFont		Font
 * @param[in] pRender			Renderer
 * @return If succeeded, it returns #MW_CC_NO_ERROR
 */
LIBCCRENDER_FREETYPE_API
MW_CC_RESULT MWRenderCC708BufferArea(
		unsigned char *t_pScreen,
		int t_nWidth,
		int t_nHeight,
		int t_nSize,
		int t_nX,
		int t_nY,
		int t_nAWidth,
		int t_nAHeight,
		mw_cc708_tv_window_screen_t *t_pWindowScreen,
		mw_cc_font_t *t_pmcfFont,
		mw_cc_render_t *pRender);
/**
 * @ingroup group_cc_functions_render
 * @brief MWRenderCCSetBackgroundColor
 *        Sets the default or custom background color
 * @param[in] t_pFont           Font
 * @param[in] t_bSet            Whether to use the custom color
 * @param[in] t_mccColor        Color
 */
LIBCCRENDER_FREETYPE_API
void MWRenderCCSetBackgroundColor(mw_cc_font_t *t_pFont, bool t_bSet, mw_cc_color_t t_mccColor);

/**
 * @ingroup group_cc_functions_render
 * @brief MWRenderCCSetFontColor
 *         Sets the default or custom Font color
 * @param[in] t_pFont            Font
 * @param[in] t_bSet             Whether to use the custom color
 * @param[in] t_mccColor         Font color
 */
LIBCCRENDER_FREETYPE_API
void MWRenderCCSetFontColor(mw_cc_font_t *t_pFont, bool t_bSet, mw_cc_color_t t_mccColor);

#endif
