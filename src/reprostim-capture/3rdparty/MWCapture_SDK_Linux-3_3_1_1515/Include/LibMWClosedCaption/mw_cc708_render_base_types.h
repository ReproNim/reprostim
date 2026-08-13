#ifndef MWCCREBDER_H
#define MWCCREBDER_H
////////////////////////////////////////////////////////////////////////////////
// Copyright (c) 2011-2019 Magewell Electronics Co., Ltd. (Nanjing)
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
#pragma once

#define MW_FONT_PATH_MAX_LEN 128

typedef struct  _cc_color{
    unsigned char r;
    unsigned char g;
    unsigned char b;
    unsigned char a;
}mw_cc_color_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief Color formats
*/
typedef enum _color_format{
    MW_RGBA,                                    ///< RGBA
    MW_BGRA,                                    ///< BGRA
    MW_ARGB,                                    ///< ARGB
    MW_ABGR                                     ///< ABGR
}mw_color_format_t;

typedef struct _cc_font{
    void *pft_lib;
    void *pft_face;
    int16_t nft_error;
    char csfont_path[MW_FONT_PATH_MAX_LEN];
    void *pdefault_font;
    int32_t ndefault_font_mem_size;
    int16_t nfont_height;
    int16_t nfont_width;
    int16_t nfont_ratio;						//50-100;

    mw_cc_color_t mccfont_color;
    mw_cc_color_t mccbacl_color;
    bool bitalic;
    bool bunderline;
    bool bdefault;

    mw_cc_color_t mcccustom_font_color;
    mw_cc_color_t mcccustom_back_color;
    bool bcustom_font_color;
    bool bcustom_back_color;
}mw_cc_font_t;

typedef struct _cc_screen{
    int16_t nwidth;
    int16_t nheight;
    int32_t nsize;
    unsigned char *pscreen_buffer;
}mw_cc_screen_t;

typedef struct _cc_render{
    void* pft_libary;
    void* phresource;
    void *pdefault_font;
    int32_t ndefault_font_mem_size;
}mw_cc_render_t;
#endif