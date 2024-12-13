#ifndef MW708BASE_H
#define MW708BASE_H
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

#include <stdint.h>
#if (defined __linux__)
#include <stddef.h>
#endif
/**
 * @ingroup group_cc_variables_macro
 * @brief CC608 number of lines
 */
#define CC608_ROWS     15

/**
 * @ingroup group_cc_variables_macro
 * @brief CC608 number of columns
 */
#define CC608_COLUMNS  32

/**
 * @ingroup group_cc_variables_macro
 * @brief CC608 number of channels
 */
#define CC608_CHANNELS 4

typedef struct _cc708_decoder mw_cc708_decoder_t;
typedef struct _cc708_service_all_decoders mw_cc708_service_all_decoders_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief cc608 background colors
*/
typedef enum _cc608_background_color
{
    MW_BAC_WHITE,                       ///<  rgba(255,255,255,255)
    MW_BAC_WHITE_SEMI,                  ///<  rgba(255,255,255,122)
    MW_BAC_GREEN,                       ///<  rgba(0,255,0,255)
    MW_BAC_GREEN_SEMI,                  ///<  rgba(0,255,0,122)
    MW_BAC_BLUE,                        ///<  rgba(0,0,255,255)
    MW_BAC_BLUE_SEMI,                   ///<  rgba(0,0,255,122)
    MW_BAC_CYAN,                        ///<  rgba(0,255,255,255)
    MW_BAC_CYAN_SEMI,                   ///<  rgba(0,255,255,122)
    MW_BAC_RED,                         ///<  rgba(255,0,0,255)
    MW_BAC_RED_SEMI,                    ///<  rgba(255,0,0,122)
    MW_BAC_YELLOW,                      ///<  rgba(255,255,0,255)
    MW_BAC_YELLOW_SEMI,                 ///<  rgba(255,255,0,122)
    MW_BAC_MAGENTA,                     ///<  rgba(255,0,255,255)
    MW_BAC_MAGENTA_SEMI,                ///<  rgba(255,0,255,122)
    MW_BAC_BLACK,                       ///<  rgba(0,0,0,255)
    MW_BAC_BLACK_SEMI,                  ///<  rgba(0,0,0,122)
    MW_BAC_TRANSPARENT,                 ///<  rgba(0,0,0,0)
    MW_FAC_BLACK,                       ///< Black font
    MW_FAC_BLACK_UNDERLINE              ///< Black font with the underline
}mw_cc608_background_color_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief cc608 font colors
*/
typedef enum _cc608_foreground_color
{
    MW_FG_WHITE = 0,                    ///<  rgba(255,255,255,255)           
    MW_FG_GREEN,                        ///<  rgba(0,255,0,255)
    MW_FG_BLUE,                         ///<  rgba(0,0,255,255)
    MW_FG_CYAN,                         ///<  rgba(0,255,255,255)
    MW_FG_RED,                          ///<  rgba(255,0,0,255)
    MW_FG_YELLOW,                       ///<  rgba(255,255,0,255)
    MW_FG_MAGENTA,                      ///<  rgba(255,0,255,255)
    MW_FG_USERDEFINED,                  ///<  Custom color
    MW_FG_BLACK,                        ///<  rgba(0,0,0,255)
    MW_FG_TRANSPARENT                   ///<  rgba(0,0,0,0)
} mw_cc608_foreground_color_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief Enumeration of cc708 channels
*/
typedef enum _cc708_channel{
    MW_CC608_CC1=-1,                    ///< CC698 CC1
    MW_CC608_CC2=-2,                    ///< CC608 CC2
    MW_CC608_CC3=-3,                    ///< CC608 CC3
    MW_CC608_CC4=-4,                    ///< CC608 CC4
    MW_CC608_ALL=-5,                    ///< All CC608 channels

    MW_CC_ALL=0,                        ///< All CC608 and CC708 channels

    MW_CC708_SERVICE01=1,               ///< CC708 service01
    MW_CC708_SERVICE02,                 ///< CC708 service02
    MW_CC708_SERVICE03,                 ///< CC708 service03
    MW_CC708_SERVICE04,                 ///< CC708 service04
    MW_CC708_SERVICE05,                 ///< CC708 service05
    MW_CC708_SERVICE06,                 ///< CC708 service06
    MW_CC708_SERVICE07,                 ///< CC708 service07
    MW_CC708_SERVICE08,                 ///< CC708 service08
    MW_CC708_SERVICE09,                 ///< CC708 service09

    MW_CC708_SERVICE10,                 ///< CC708 service10
    MW_CC708_SERVICE11,                 ///< CC708 service11
    MW_CC708_SERVICE12,                 ///< CC708 service12
    MW_CC708_SERVICE13,                 ///< CC708 service13
    MW_CC708_SERVICE14,                 ///< CC708 service14
    MW_CC708_SERVICE15,                 ///< CC708 service15
    MW_CC708_SERVICE16,                 ///< CC708 service16
    MW_CC708_SERVICE17,                 ///< CC708 service17
    MW_CC708_SERVICE18,                 ///< CC708 service18
    MW_CC708_SERVICE19,                 ///< CC708 service19

    MW_CC708_SERVICE20,                 ///< CC708 service20
    MW_CC708_SERVICE21,                 ///< CC708 service21
    MW_CC708_SERVICE22,                 ///< CC708 service22
    MW_CC708_SERVICE23,                 ///< CC708 service23
    MW_CC708_SERVICE24,                 ///< CC708 service24
    MW_CC708_SERVICE25,                 ///< CC708 service25
    MW_CC708_SERVICE26,                 ///< CC708 service26
    MW_CC708_SERVICE27,                 ///< CC708 service27
    MW_CC708_SERVICE28,                 ///< CC708 service28
    MW_CC708_SERVICE29,                 ///< CC708 service29

    MW_CC708_SERVICE30,                 ///< CC708 service30
    MW_CC708_SERVICE31,                 ///< CC708 service31
    MW_CC708_SERVICE32,                 ///< CC708 service32
    MW_CC708_SERVICE33,                 ///< CC708 service33
    MW_CC708_SERVICE34,                 ///< CC708 service34
    MW_CC708_SERVICE35,                 ///< CC708 service35
    MW_CC708_SERVICE36,                 ///< CC708 service36
    MW_CC708_SERVICE37,                 ///< CC708 service37
    MW_CC708_SERVICE38,                 ///< CC708 service38
    MW_CC708_SERVICE39,                 ///< CC708 service39

    MW_CC708_SERVICE40,                 ///< CC708 service40
    MW_CC708_SERVICE41,                 ///< CC708 service41
    MW_CC708_SERVICE42,                 ///< CC708 service42
    MW_CC708_SERVICE43,                 ///< CC708 service43
    MW_CC708_SERVICE44,                 ///< CC708 service44
    MW_CC708_SERVICE45,                 ///< CC708 service45
    MW_CC708_SERVICE46,                 ///< CC708 service46
    MW_CC708_SERVICE47,                 ///< CC708 service47
    MW_CC708_SERVICE48,                 ///< CC708 service48
    MW_CC708_SERVICE49,                 ///< CC708 service49

    MW_CC708_SERVICE50,                 ///< CC708 service50
    MW_CC708_SERVICE51,                 ///< CC708 service51
    MW_CC708_SERVICE52,                 ///< CC708 service52
    MW_CC708_SERVICE53,                 ///< CC708 service53
    MW_CC708_SERVICE54,                 ///< CC708 service54
    MW_CC708_SERVICE55,                 ///< CC708 service55
    MW_CC708_SERVICE56,                 ///< CC708 service56
    MW_CC708_SERVICE57,                 ///< CC708 service57
    MW_CC708_SERVICE58,                 ///< CC708 service58
    MW_CC708_SERVICE59,                 ///< CC708 service59

    MW_CC708_SERVICE60,                 ///< CC708 service60
    MW_CC708_SERVICE61,                 ///< CC708 service61
    MW_CC708_SERVICE62,                 ///< CC708 service62
    MW_CC708_SERVICE63,                 ///< CC708 service63

    MW_CC708_ALL=64,                    ///< All CC708 services
}mw_cc708_channel_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc608_attributes_t cc608 font attribution
*/
typedef struct _cc608_attributes
{
    unsigned char italic;                              ///< Whether the font is italic, 0-false, 1-true
    unsigned char underline;                           ///< Whether there is underline, 0-false, 1-true
    mw_cc608_foreground_color_t foreground;            ///< Foreground color
    mw_cc608_background_color_t background;            ///< Background color
}mw_cc608_attributes_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc608_char_cell_t cc608 character
*/
typedef struct _cc608_char_cell
{
    uint32_t ch;                                        ///< Text unicode
    mw_cc608_attributes_t attributes;                   ///< Colors and fonts
    int inited;                                         ///< Whether the text is valid, 1-valid, 0-invalid
}mw_cc608_char_cell_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc608_row_t cc608 row
*/
typedef struct _cc608_row
{
    mw_cc608_char_cell_t cells[CC608_COLUMNS];          ///< Character line
    int16_t pos;                                        ///< Current cursor position
    int16_t num_chars;                                  ///< Number of characters
    mw_cc608_attributes_t pac_attr;                     ///< Current color and format
}mw_cc608_row_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc608_buffer_t cc608 single channel character
*/
typedef struct _cc608_buffer
{
    mw_cc608_row_t rows[CC608_ROWS];                    ///< Character Array
    int16_t rowpos;                                     ///< Cursor position
    mw_cc608_attributes_t pac_attr;                     ///< Current color and format

    mw_cc708_channel_t channel;                         ///< cc608 channel id

}mw_cc608_buffer_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc608_memory_t all cc608 channel characters
*/
typedef struct _cc608_memory
{
    mw_cc608_buffer_t channel[CC608_CHANNELS];          ///< All channel characters
    int channel_no;                                     ///< Current chosen channel
}mw_cc608_memory_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief cc608 display styles
*/
typedef enum _cc608_style
{
    MW_CC608_ROLLUP     = 1,                            //Rolling
    MW_CC608_PAINTON,                                   //Draw
    MW_CC608_POPON,                                     //Pop up
    MW_CC608_TEXT,                                      //Text
}mw_cc608_style_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc608_active_channel_t cc608 current active channel
*/
typedef struct _cc608_active_channel{
    int16_t m_active_channels[CC608_CHANNELS];          ///< Active channel
}mw_cc608_active_channel_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc608_decoder_t cc608 resolution structure
*/
typedef struct _cc608_decoder
{
    mw_cc608_memory_t buffer[2];                        ///< Before and after subtitle 
    mw_cc608_memory_t *on_buf;                          ///< Display subtitle 
    mw_cc608_memory_t *off_buf;                         ///< Background subtitle 
    mw_cc608_memory_t **active;                         ///< Active subtitle 

    mw_cc608_active_channel_t m_activeChannels;         ///< Active channels

    uint32_t lastcode;                                  ///< Last code

    uint16_t rollup_rows;                               ///< Number of roll up rows
    mw_cc608_style_t style;                             ///< Drawing style

    void *userdata;                                     ///< Callback object
    void(*callback)(int service, void *userdata);       ///< Callback function

    mw_cc708_decoder_t *parent;                         ///< MW_CC708_Decoder
    void(*cc708decodercallback)(mw_cc708_decoder_t *parent, bool t_b608, int t_nService);///< Callback function of MW_CC708_decoder

    char text[CC608_ROWS*CC608_COLUMNS + 1];            ///< Closed captions
    int textlen;                                        ///< Length of captions
}mw_cc608_decoder_t;

/**
 * @ingroup group_cc_variables_macro
 * @brief Max length of CC708
 */
#define MAX_708_PACKET_LENGTH           128

/**
 * @ingroup group_cc_variables_macro
 * @brief Mac services of CC708
 */
#define CCX_DECODERS_708_MAX_SERVICES   63

/**
 * @ingroup group_cc_variables_macro
 * @brief Max lines of CC708
 */
#define I708_MAX_ROWS                   15

/**
 * @ingroup group_cc_variables_macro
 * @brief Max columns of CC708
 */
#define I708_MAX_COLUMNS                42

/**
 * @ingroup group_cc_variables_macro
 * @brief Max columns of CC708
 */
#define I708_MAX_COLUMNS_2				32	

/**
 * @ingroup group_cc_variables_macro
 * @brief Lines of CC708 
 */
#define I708_SCREENGRID_ROWS            75

/**
 * @ingroup group_cc_variables_macro
 * @brief Columns of CC708 
 */
#define I708_SCREENGRID_COLUMNS         210

/**
 * @ingroup group_cc_variables_macro
 * @brief Max lines of CC708 
 */
#define I708_MAX_WINDOWS                8

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cea708_time_code_t CC708 time code
*/
typedef struct _cea708_time_code//0x71
{
	unsigned char m_csTimeCode[4];      ///< Time code
    int16_t n10hour;                    ///< The 10-digit number of hours
    int16_t n1hour;                     ///< The unit-digits number of hours
    int16_t n10min;                     ///< The 10-digit number of minutes
    int16_t n1min;                      ///< The unit-digits number of minutes
    int16_t n10sec;                     ///< The 10-digit number of seconds
    int16_t n1sec;                      ///< The unit-digits number of seconds
    int16_t n10fra;                     ///< The 10-digit number of frames
    int16_t n1fra;                      ///< The unit-digits number of frames
    bool bdropfra;                      ///< Whether there are drop frames
}mw_cea708_time_code_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief  Window caption alignment
*/
typedef enum _cea708_windows_attrib_justify
{
    MW_CC708_WA_LEFT = 0,                       ///< Left-aligned text
    MW_CC708_WA_RIGHT,                          ///< Right-aligned text
    MW_CC708_WA_CENTER,                         ///< Centered text
    MW_CC708_WA_FULL,                           ///< Justified text
}mw_cea708_windows_attrib_justify_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief CC708 print direction
*/
typedef enum _cea708_windows_attrib_print_direction
{
    MW_CC708_PD_LEFT_TO_RIGHT = 0,              ///< Drawing from Left to right 
    MW_CC708_PD_RIGHT_TO_LEFT,                  ///< Drawing from right to left
    MW_CC708_PD_TOP_TO_BOTTOM,                  ///< Drawing from top to bottom
    MW_CC708_PD_BOTTOM_TO_TOP,                  ///< Drawing from bottom to top
}mw_cea708_windows_attrib_print_direction_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief CC708 scrolling directions
*/
typedef enum _cea708_windows_attrib_scroll_direction
{
    MW_CC708_SD_LEFT_TO_RIGHT = 0,              ///< Scrolling from left to right
    MW_CC708_SD_RIGHT_TO_LEFT,                  ///< Scrolling from right to left
    MW_CC708_SD_TOP_TO_BOTTOM,                  ///< Scrolling from top to bottom
    MW_CC708_SD_BOTTOM_TO_TOP,                  ///< Scrolling from bottom to top
}mw_cea708_windows_attrib_scroll_direction_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief Scrolling effect of CC708
*/
typedef enum _cea708_windows_attrib_scroll_display_effect
{
    MW_CC708_SDE_SNAP = 0,
    MW_CC708_SDE_FADE,
    MW_CC708_SDE_WIPE,
}mw_cea708_windows_attrib_scroll_display_effect_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief Window effect direction of CC708
*/
typedef enum _cea708_windows_attrib_effect_direction
{
    MW_CC708_ED_LEFT_TO_RIGHT = 0,              ///<  From left to right
    MW_CC708_ED_RIGHT_TO_LEFT,                  ///<  From right to left
    MW_CC708_ED_TOP_TO_BOTTOM,                  ///<  From top to bottom
    MW_CC708_ED_BOTTOM_TO_TOP,                  ///<  From bottom to top
}mw_cea708_windows_attrib_effect_direction_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief Sets filling opacity of CC708 box 
*/
typedef enum _cea708_windows_attrib_fill_opacity
{
    MW_CC708_FO_SOLID = 0,                      ///< Solid
    MW_CC708_FO_FLASH,                          ///< Flashing
    MW_CC708_FO_TRANSLUENT,                     ///< Gradient
    MW_CC708_FO_TRANSPARENT,                    ///< Opacity
}mw_cea708_windows_attrib_fill_opacity_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief Frame types of CC708 window
*/
typedef enum _cea708_windows_attrib_border_type
{
    MW_CC708_BT_NONE = 0,                       ///< None
    MW_CC708_BT_RAISED,                         ///< Raised border
    MW_CC708_BT_DEPRESSED,                      ///< Depression border
    MW_CC708_BT_UNIFORM,                        ///< Uniform border
    MW_CC708_BT_SHADOW_LEFT,                    ///< Left shadow border
    MW_CC708_BT_SHADOW_RIGHT,                   ///< Right shadow border
}mw_cea708_windows_attrib_border_type_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief CC708 pen size
 */
typedef enum _cea_pen_attrib_size
{
    MW_CC708_PENSIZE_SMALL = 0,                 ///< Small
    MW_CC708_PENSIZE_STANDARD,                  ///< Standard
    MW_CC708_PENSIZE_LARGE,                     ///< Large
}mw_cea_pen_attrib_size_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief CC708 fonts
*/
typedef enum _cea708_pen_attrib_font_style
{
    MW_CC708_FS_DEFAULT_OR_DEFINED=0,                       ///< Default or custom font style
    MW_CC708_FS_MONOSPACED_WITH_SERIFS,                     ///< Monospaced, serif fonts
    MW_CC708_FS_PROPORTIONALLY_SPACED_WITH_SERIFS,          ///< Proportionally spaced font with serifs
    MW_CC708_FS_MONOSPACED_WITHOUT_SERIFS,                  ///< Monospaced, sans-serif fonts
    MW_CC708_FS_PROPORTIONALLY_SPACED_WITHOUT_SERIFS,       ///< Proportionally spaced font without serifs
    MW_CC708_FS_CAUSAL_FONT_TYPE,                           ///< At this state, you can custom the font
    MW_CC708_FS_CURISVE_FONT_TYPE,                          ///< Cursive
    MW_CC708_FS_SMALL_CAPTIALS,                             ///< Lowercase letters
}mw_cea708_pen_attrib_font_style_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief CC708 text labels which indicate different lines sources
*/
typedef enum _cea708_pen_attrib_texttag
{
    MW_CC708_PTEXTTAG_DIALOG = 0,                           ///< Dialog
    MW_CC708_PTEXTTAG_SOURCE_OR_SPEAKER_ID,                 ///< Source
    MW_CC708_PTEXTTAG_ELECTRONIC_VOICE,                     ///< Electronic sound
    MW_CC708_PTEXTTAG_FOREIGN_LAUNGUANGE,                   ///< Foreign language
    MW_CC708_PTEXTTAG_VOICEOVER,                            ///< Voice over
    MW_CC708_PTEXTTAG_AUDIBLE_TRANSLATION,                  ///< Audible translation
    MW_CC708_PTEXTTAG_SUBTITLE_TRANSLATION,                 ///< Subtitle translation
    MW_CC708_PTEXTTAG_VOICE_QUALITY_DESCRIPTION,            ///< Description of voice quality       
    MW_CC708_PTEXTTAG_SONG_LYRICS,                          ///< Lyrics
    MW_CC708_PTEXTTAG_SOUND_EFFECT_DESCRIPTION,             ///< Sound effects description
    MW_CC708_PTEXTTAG_MUSICAL_SCORE_DESCRIPTION,            ///< Score description
    MW_CC708_PTEXTTAG_EXPLETIVE,                            ///< Exclamations
    MW_CC708_PTEXTTAG_UNDEFINED_12,                         ///< Reserved
    MW_CC708_PTEXTTAG_UNDEFINED_13,                         ///< Reserved
    MW_CC708_PTEXTTAG_UNDEFINED_14,                         ///< Reserved
    MW_CC708_PTEXTTAG_NOT_TO_BE_DISPLAYED,                  ///< Don't display lines
}mw_cea708_pen_attrib_texttag_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief CC708 text position
*/
typedef enum _cea_pen_attrib_offset
{
    MW_CC708_POF_SUBSCRIPT=0,                               ///< Subscript
    MW_CC708_POF_NORMAL,                                    ///< Regular
    MW_CC708_POF_SUPERSCRIPT,                               ///< Superscript
}mw_cea_pen_attrib_offset_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief Edge type of CC708 pen 
*/
typedef enum _cea_pen_attrib_edgetype
{
    MW_CC708_PET_NONE = 0,                                  ///< None
    MW_CC708_PET_RAISED,                                    ///< Embossed
    MW_CC708_PET_DEPRESSED,                                 ///< Engrave
    MW_CC708_PET_UNIFORM,                                   ///< Uniform edge
    MW_CC708_PET_LEFT_DROP_SHADOW,                          ///< Left drop shadow
    MW_CC708_PET_RIGHT_DROP_SHADOW,                         ///< Right drop shadow
}mw_cea_pen_attrib_edgetype_t;

/**
 * @ingroup group_cc_variables_enum
 * @brief  Anchor location of CC708 window
*/
typedef enum _cea_anchor_points
{
    MW_CC708_ANCHORPOINT_TOP_LEFT = 0,                      ///< Top left
    MW_CC708_ANCHORPOINT_TOP_CENTER,                        ///< Top center
    MW_CC708_ANCHORPOINT_TOP_RIGHT,                         ///< Top right
    MW_CC708_ANCHORPOINT_MIDDLE_LEFT,                       ///< Middle left
    MW_CC708_ANCHORPOINT_MIDDLE_CENTER,                     ///< Middle center
    MW_CC708_ANCHORPOINT_MIDDLE_RIGHT,                      ///< Middle right
    MW_CC708_ANCHORPOINT_BOTTOM_LEFT,                       ///< Bottom left
    MW_CC708_ANCHORPOINT_BOTTOM_CENTER,                     ///< Bottom center
    MW_CC708_ANCHORPOINT_BOTTOM_RIGHT,                      ///< Bottom right
}mw_cea_anchor_points_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc708_cell_t cc708 character unit
*/
typedef struct _cc708_cell
{
    uint16_t sym;                   ///< Characters, Unicode-16 character sets
    uint16_t init;                  ///< Whether the character is valid
} mw_cc708_cell_t;

#define MW_708CELL_SYM_SET(x, c) {x.init = 1; x.sym = c;}
#define MW_708CELL_SYM_SET_16(x, c1, c2) {x.init = 1; x.sym = (c1 << 8) | c2;}
#define MW_708CELL_SYM(x) ((unsigned char)(x.sym))
#define MW_708CELL_SYM_IS_EMPTY(x) (x.init == 0)
#define MW_708CELL_SYM_IS_SET(x) (x.init == 1)
#define MW_708CELL_MUSICAL_NOTE_CHAR 9836	// Unicode Character 'BEAMED SIXTEENTH NOTES'

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc708_pen_color_t cc708 pen color
*/
typedef struct _cc708_pen_color  
{
    int16_t fg_color;                                           ///< Foreground color & 0x3f 2 bit r, 2 bit g, 2 bit b, 2 bit a
    mw_cea708_windows_attrib_fill_opacity_t fg_opacity;         ///< Foreground opacity
    int16_t bg_color;                                           ///< Background & 0x3f 2 bit r, 2 bit g, 2 bit b, 2 bit a
    mw_cea708_windows_attrib_fill_opacity_t bg_opacity;         ///< Background opacity
    int16_t edge_color;                                         ///< Edge color & 0x3f 2 bit r, 2 bit g, 2 bit b, 2 bit a
}mw_cc708_pen_color_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc708_pen_attrib_t cc708 pen property
*/
typedef struct _cc708_pen_attrib //adjust
{
    mw_cea_pen_attrib_size_t pen_size;                          ///< Pen size
    mw_cea_pen_attrib_offset_t offset;                          ///< Pen mode
    mw_cea708_pen_attrib_texttag_t text_tag;                    ///< Pen tag
    mw_cea708_pen_attrib_font_style_t font_tag;                 ///< Pen fonts
    mw_cea_pen_attrib_edgetype_t edge_type;                     ///< Pen edge types
    int16_t underline;                                          ///< Whether there is underline; 1 indicates true, 0 indicates false
    int16_t italic;                                             ///< Whether it is italic; 1 indicates true, 0 indicates false
}mw_cc708_pen_attrib_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief Property of mw_cc708_window_attrib_t  Attribution of the cc708 captions window 
*/
typedef struct _cc708_window_attrib
{
    mw_cea708_windows_attrib_justify_t justify;                     ///< Caption alignment
    mw_cea708_windows_attrib_print_direction_t print_dir;           ///< Caption print direction
    mw_cea708_windows_attrib_scroll_direction_t scroll_dir;         ///< Caption scroll direction
    int16_t word_wrap;                                              ///< Word wrap, 0-not wrap, 1-wrap
    mw_cea708_windows_attrib_scroll_display_effect_t display_eff;   ///< Display effect
    mw_cea708_windows_attrib_effect_direction_t effect_dir;         ///< Effect direction
    int16_t effect_speed;                                           ///< Effect speed, which ranges from 1 to 15 (x*0.5 seconds)
    int16_t fill_color;                                             ///< Filling color & 0x3f 2 bit r, 2 bit g, 2 bit b, 2 bit a
    mw_cea708_windows_attrib_fill_opacity_t fill_opacity;           ///< Fill opacity
    mw_cea708_windows_attrib_border_type_t border_type;             ///< Frame type
    int16_t border_color;                                           ///< Frame color & 0x3f 2 bit r, 2 bit g, 2 bit b, 2 bit a
    int16_t border_type01;                                          ///< Calculates the border type
}mw_cc708_window_attrib_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc708_window_t cc708 captions window 
*/
typedef struct _cc708_window
{
    int16_t is_defined;                                                             ///< Whether a window is established; 0-false, 1-true
    int16_t number;                                                                 ///< Window index
    int16_t priority;                                                               ///< Window priority
    int16_t col_lock;                                                               ///< Whether to lock the column; 0-false, 1-true
    int16_t row_lock;                                                               ///< Whether to lock the row; 0-false, 1-true
    int16_t visible;                                                                ///< Whether it is visible; 0-false, 1-true
    int16_t anchor_vertical;                                                        ///< Vertical anchor
    int16_t relative_pos;                                                           ///< Whether it is relative position; 0-false, 1-true
    int16_t anchor_horizontal;                                                      ///< Horizontal anchor
    int16_t row_count;                                                              ///< Number of rows
    mw_cea_anchor_points_t anchor_point;                                            ///< Anchor point
    int16_t col_count;                                                              ///< Number of column
    int16_t pen_style;                                                              ///< Pen style index
    int16_t win_style;                                                              ///< window style index
    unsigned char commands[6];                                                      ///< Aviods repeated commands
    mw_cc708_window_attrib_t window_attrib;                                         ///< window property
    mw_cc708_pen_attrib_t pen_attric;                                               ///< Pen attribution
    mw_cc708_pen_color_t pen_color;                                                 ///< Pen color
    int16_t pen_row;                                                                ///< Row position of pen 
    int16_t pen_coloumn;                                                            ///< Column position of pen

    mw_cc708_cell_t *cell_rows[I708_MAX_ROWS];                                      ///< Characters
    mw_cc708_pen_color_t pen_colors[I708_MAX_ROWS][I708_SCREENGRID_COLUMNS];        ///< Defines specified character pen color
    mw_cc708_pen_attrib_t pen_attribs[I708_MAX_ROWS][I708_SCREENGRID_COLUMNS];      ///< Defines specified character pen attribution
    int16_t memory_reserved;                                                        ///< Whether there is memory assigned; 1-true, 0-false
    int16_t is_empty;                                                               ///< Whether there is content; 1-true, 0-false
}mw_cc708_window_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc708_tv_window_screen_t display of closed captions 
*/
typedef struct _cc708_tv_window_screen{
    mw_cc708_window_t windows[I708_MAX_WINDOWS];                                    ///< Captions window 
    int16_t nwindow_num;                                                            ///< Window counts
}mw_cc708_tv_window_screen_t;


/**
  * @ingroup group_cc_variables_struct
  * @brief mw_cc708_service_decoder_t cc708 service decoder
*/
typedef struct _cc708_service_decoder
{
    mw_cc708_window_t windows[I708_MAX_WINDOWS];                                            ///< CC708 captions window 
    int16_t current_window;                                                                 ///< Current active window 
    int16_t inited;                                                                         ///< Whether to initialize
    int16_t service;                                                                        ///< CC708 service index

    mw_cc708_tv_window_screen_t m_win_screen;                                               ///< CC708 content dispayed 

    void *userdata;                                                                         ///< Callback object
    void(*callback)(int service, void *userdata);                                           ///< Callback function
    mw_cc708_decoder_t *parent;                                                             ///< Callback object of cc708 decoder
    void(*cc708decodercallback)(mw_cc708_decoder_t *parent, bool t_b608, int t_nService);   ///< Callback function of cc708 decoder

    mw_cc708_service_all_decoders_t *m_pSADParent;                                          ///< Father pointer of all cc708 service decoder
}mw_cc708_service_decoder_t;

/**
  * @ingroup group_cc_variables_struct
  * @brief _cc708_service_all_decoders All cc708 service decoders
*/
struct _cc708_service_all_decoders
{
    mw_cc708_service_decoder_t **cc708_service_decoder;                                     ///< CC708 service decoder
    int16_t  nactive_service_count;                                                         ///< Active service number
    int16_t  nis_active;                                                                    ///< Active service id
    int16_t  service_active[CCX_DECODERS_708_MAX_SERVICES];                                 ///< Active service id record
    mw_cc708_decoder_t *parent;
};

/**
  * @ingroup group_cc_variables_struct
  * @brief _cc708_decoder cc708 decoder
*/
struct _cc708_decoder
{
    bool binited;                                                                           ///< Whether to initialize

    mw_cc708_service_all_decoders_t *cc708_sad_decoders;                                    ///< All cc708 service decoder
    mw_cc608_decoder_t *cc608_decoder;                                                      ///< cc608 decoder

    unsigned char current_packet[MAX_708_PACKET_LENGTH];                                    ///< Current data
    int16_t ncurrent_packet_length;                                                         ///< Current date length    
    int16_t nlast_seq;                                                                      ///< The last sequence

    bool btrans_cc708;                                                                      ///< Whether to decode cc708; the default value is true. If false, cc708 will not be decoded.
    bool btrans_cc608;                                                                      ///< Whether to decode cc608; the default value is true. If false, cc708 will not be decoded.
    mw_cc608_buffer_t cc608_buffer;                                                         ///< cc608 decode structure

    mw_cc708_tv_window_screen_t cc708_window_screen;                                        ///< cc708 content displayed


    bool bshow_cc708;                                                                       ///< Whether to display cc708
    bool bshow_cc608;                                                                       ///< Whether to display cc608

    bool bhas_cc708;                                                                        ///< Whether there is cc608 input
    bool bhas_cc608;                                                                        ///< Whether there is cc708 input

    bool bcc608_output[4];                                                                  ///< Hides channel 0-3 of cc608
    bool bcc708_output[63];                                                                 ///< Hides service 0-63 of cc708

	void *userdata;                                                                         ///< Callback object
	void(*callback)(int service, void *userdata);                                           ///< Callback function

	int nlast_cdp_counter;                                                                  ///< The last count of cdp
	int ncurrent_cdp_counter;                                                               ///< Current count of cdp
};

#endif
