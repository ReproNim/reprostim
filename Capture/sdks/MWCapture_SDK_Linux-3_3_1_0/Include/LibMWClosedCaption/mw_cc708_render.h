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
 * @brief MWCreateRender
 *        Create a render
 * @return Returns NULL if failed
 */
LIBCCRENDER_FREETYPE_API
mw_cc_render_t *MWCreateRender();

/**
 * @brief MWDestoryRender
 *        Destory the render
 * @param[in] pRender       Pointer of the render
 */
LIBCCRENDER_FREETYPE_API
void MWDestoryRender(mw_cc_render_t *pRender);

/**
 * @brief MWLoadFont
 *        Load font
 * @param[in] t_pmcfFont    Pointer of the font to be loaded
 * @param[in] pRender       Pointer of the render
 * @return  Returns true if success
 */
LIBCCRENDER_FREETYPE_API
bool MWLoadFont(mw_cc_font_t *t_pmcfFont, mw_cc_render_t *pRender);

/**
 * @brief MWUnLoadFont
 *        Unload font
 * @param[in] t_pmcfFont    Pointer of the font to be unloaded
 * @param[in] pRender       Pointer of the render
 */
LIBCCRENDER_FREETYPE_API
void MWUnLoadFont(mw_cc_font_t *t_pmcfFont, mw_cc_render_t *pRender);

/**
 * @brief MWCreateCCScreen
 *        Create the screen to be rendered
 * @param[in] t_nWidth      Width of the screen
 * @param[in] t_nHeight     Height of the screen
 * @return Returns NULL if failed
 */
LIBCCRENDER_FREETYPE_API
mw_cc_screen_t *MWCreateCCScreen(int t_nWidth, int t_nHeight);

/**
 * @brief MWDestoryCCScreen
 *        Destory the screen
 * @param[in] t_pScreen     Pointer of the screen to be destroy
 */
LIBCCRENDER_FREETYPE_API
void MWDestoryCCScreen(mw_cc_screen_t *t_pScreen);

/**
 * @brief MWRenderCC608Screen
 *        Render the screen with cc608 buffer
 * @param[out] t_pScreen         Pointer of the screen to be rendered
 * @param[in] t_pCC608Buffer    Pointer of the cc608 buffer to be rendered
 * @param[in] t_pmcfFont        Pointer of the font render with
 * @param[in] pRender           Pointer of render
 * @return Returns MW_CC_NO_ERROR if seccess
 */
LIBCCRENDER_FREETYPE_API
MW_CC_RESULT MWRenderCC608Screen(
        mw_cc_screen_t *t_pScreen,
        mw_cc608_buffer_t *t_pCC608Buffer,
        mw_cc_font_t *t_pmcfFont,
        mw_cc_render_t *pRender);

/**
 * @brief MWRenderCC608Buffer
 *        Render the cc608 buffer to a given memory
 * @param[out] t_pScreen		Pointer of the screen to be rendered
 * @param[in] t_nWidth			Width of the given memory
 * @param[in] t_nHeight			Height of the given memory
 * @param[in] t_nSize			Size of the memory
 * @param[in] t_pCC608Buffer            Pointer of the cc608 buffer to be rendered
 * @param[in] t_pmcfFont		Pointer of the font render with
 * @param[in] pRender			Pointer of render
 * @return Returns MW_CC_NO_ERROR if success
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
 * @brief MWRenderCC608BufferArea
 *        Render the cc608 buffer to the certain area of the given memeory
 * @param[out] t_pScreen		Pointer of the screen to be rendered
 * @param[in] t_nWidth			Width of the given memory
 * @param[in] t_nHeight			Height of the given memory
 * @param[in] t_nSize			Size of the memory
 * @param[in] t_nX			X position of the area in the given memory
 * @param[in] t_nY			Y position of the area in the given memory
 * @param[in] t_nAWidth			Width of the area in the given memory
 * @param[in] t_nAHeight		Height of the area in the given memory
 * @param[in] t_pCC608Buffer            Pointer of the cc608 buffer to be rendered
 * @param[in] t_pmcfFont		Pointer of the font render with
 * @param[in] pRender			Pointer of render
 * @return Returns MW_CC_NO_ERROR if success
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
 * @brief MWRenderCC708Screen
 *        Render the screen with cc708 tv_window_screen
 * @param[out] t_pScreen         Pointer of the screen to be rendered
 * @param[in] t_pWindowScreen   Pointer of the cc708 tv_window_screen to be rendered
 * @param[in] t_pmcfFont        Pointer of the font render with
 * @param[in] pRender           Pointer of render
 * @return Returns MW_CC_NO_ERROR if success
 */
LIBCCRENDER_FREETYPE_API
MW_CC_RESULT MWRenderCC708Screen(mw_cc_screen_t *t_pScreen, mw_cc708_tv_window_screen_t *t_pWindowScreen, mw_cc_font_t *t_pmcfFont, mw_cc_render_t *pRender);

/**
 * @brief MWRenderCC708Buffer
 *        Render the cc708 tv_window_screen to given memory
 * @param[out] t_pScreen		Pointer of the screen to be rendered
 * @param[in] t_nWidth			Width of the given memory
 * @param[in] t_nHeight			Height of the given memory
 * @param[in] t_nSize			Size of the memory
 * @param[in] t_pWindowScreen           Pointer of the cc708 tv_window_screen to be rendered
 * @param[in] t_pmcfFont		Pointer of the font render with
 * @param[in] pRender			Pointer of the render
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
 * @brief MWRenderCC708BufferArea
 *	  Render the cc708 tv_window_screen to the certain area of the given memeory
 * @param[out] t_pScreen		Pointer of the screen to be rendered
 * @param[in] t_nWidth			Width of the given memory
 * @param[in] t_nHeight			Height of the given memory
 * @param[in] t_nSize			Size of the memory
 * @param[in] t_nX			X position of the area in the given memory
 * @param[in] t_nY			Y position of the area in the given memory
 * @param[in] t_nAWidth			Width of the area in the given memory
 * @param[in] t_nAHeight		Height of the area in the given memory
 * @param[in] t_pWindowScreen           Pointer of the cc708 tv_window_screen to be rendered
 * @param[in] t_pmcfFont		Pointer of the font render with
 * @param[in] pRender			Pointer of the render
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
 * @brief MWRenderCCSetBackgroundColor
 *        Set the caption with default background color or custom background color
 * @param[in] t_pFont           Pointer of the font
 * @param[in] t_bSet            True if use custom background color
 * @param[in] t_mccColor        Color value to be setted
 */
LIBCCRENDER_FREETYPE_API
void MWRenderCCSetBackgroundColor(mw_cc_font_t *t_pFont, bool t_bSet, mw_cc_color_t t_mccColor);

/**
 * @brief MWRenderCCSetFontColor
 *        Set the caption with default font color or custom font color
 * @param[in] t_pFont            Pointer of the font
 * @param[in] t_bSet             True if use custom font color
 * @param[in] t_mccColor         Color value to be setted
 */
LIBCCRENDER_FREETYPE_API
void MWRenderCCSetFontColor(mw_cc_font_t *t_pFont, bool t_bSet, mw_cc_color_t t_mccColor);

#endif
