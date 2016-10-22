// The MIT License (MIT)
//
// Copyright (c) 2016 WUSTL ZPLAB
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
//
// Authors: Erik Hvatum <ice.rikh@gmail.com>

template<typename BitmapMaskCursor, typename T, BitmapMaskDimensionVsImage T_W, BitmapMaskDimensionVsImage T_H>
struct BitmapMaskCursorScanlineAdvanceAspect;

template<typename BitmapMaskCursor, typename T, BitmapMaskDimensionVsImage T_W>
struct BitmapMaskCursorScanlineAdvanceAspect<BitmapMaskCursor, T, T_W, BitmapMaskDimensionVsImage::Smaller>
{
    const std::uint8_t*const mask_scanlines_end;
    const SampleLutPtr im_to_mask_scanline_idx_lut;
    const std::uint64_t* im_to_mask_scanline_lut_element;
    const SampleLutPtr mask_to_im_scanline_idx_lut;
    const std::uint64_t* mask_to_im_scanline_lut_element;

    BitmapMaskCursorScanlineAdvanceAspect(PyArrayView& data_view, BitmapMask<T, T_W, BitmapMaskDimensionVsImage::Smaller>& mask_)
      : mask_scanlines_end(static_cast<std::uint8_t*>(mask_.bitmap_view.buf) + mask_.bitmap_view.shape[1] * mask_.bitmap_view.strides[1]),
        im_to_mask_scanline_idx_lut(sampleLuts.getLut(data_view.shape[1], mask_.bitmap_view.shape[1])),
        mask_to_im_scanline_idx_lut(sampleLuts.getLut(mask_.bitmap_view.shape[1], data_view.shape[1])) {}

    inline void seek_front_scanline()
    {
        BitmapMaskCursor& S = *static_cast<BitmapMaskCursor*>(this);
        S.mask_scanline = S.mask_scanlines_origin;
        im_to_mask_scanline_lut_element = im_to_mask_scanline_idx_lut->m_data.data();
        mask_to_im_scanline_lut_element = mask_to_im_scanline_idx_lut->m_data.data();
        for(;;)
        {
            S.seek_front_pixel_of_scanline();
            if(S.pixel_valid) break;
            S.mask_scanline += S.mask_scanline_stride;
            ++mask_to_im_scanline_lut_element;
        }
    }

//  void quick_advance_scanline()
//  {
//      mask_scanline_lut_element = im_to_mask_scanline_idx_lut->m_data.data();
//      im_scanline_lut_element = mask_to_im_scanline_idx_lut->m_data.data();
//      static_cast<BitmapMaskCursor*>(this)->mask_scanline = static_cast<BitmapMaskCursor*>(this)->mask_scanlines_origin[*mask_scanline_lut_element];
//  }

    inline void advance_scanline() {}
};

template<typename BitmapMaskCursor, typename T, BitmapMaskDimensionVsImage T_W>
struct BitmapMaskCursorScanlineAdvanceAspect<BitmapMaskCursor, T, T_W, BitmapMaskDimensionVsImage::Same>
{
    BitmapMaskCursorScanlineAdvanceAspect(PyArrayView& data_view, BitmapMask<T, T_W, BitmapMaskDimensionVsImage::Same>& mask_) {}
    inline void seek_front_scanline() {}
    inline void advance_scanline() {}
};

template<typename BitmapMaskCursor, typename T, BitmapMaskDimensionVsImage T_W>
struct BitmapMaskCursorScanlineAdvanceAspect<BitmapMaskCursor, T, T_W, BitmapMaskDimensionVsImage::Larger>
{
    const SampleLutPtr im_to_mask_scanline_idx_lut;
    const std::uint64_t* lut_element;

    BitmapMaskCursorScanlineAdvanceAspect(PyArrayView& data_view, BitmapMask<T, T_W, BitmapMaskDimensionVsImage::Larger>& mask_)
      : im_to_mask_scanline_idx_lut(sampleLuts.getLut(data_view.shape[1], mask_.bitmap_view.shape[1])),
        lut_element(im_to_mask_scanline_idx_lut->m_data.data()) {}
    
    inline void seek_front_scanline() {}
    inline void advance_scanline() {}
};


template<typename BitmapMaskCursor, typename T, BitmapMaskDimensionVsImage T_W, BitmapMaskDimensionVsImage T_H>
struct BitmapMaskCursorPixelAdvanceAspect;

template<typename BitmapMaskCursor, typename T, BitmapMaskDimensionVsImage T_H>
struct BitmapMaskCursorPixelAdvanceAspect<BitmapMaskCursor, T, BitmapMaskDimensionVsImage::Smaller, T_H>
{
    const std::uint8_t* mask_elements_end;
    const SampleLutPtr mask_to_im_pixel_idx_lut;
    const std::uint64_t* lut_element;

    BitmapMaskCursorPixelAdvanceAspect(PyArrayView& data_view, BitmapMask<T, BitmapMaskDimensionVsImage::Smaller, T_H>& mask_)
      : mask_to_im_pixel_idx_lut(sampleLuts.getLut(mask_.bitmap_view.shape[0], data_view.shape[0])) {}

    inline void seek_front_pixel_of_scanline() {}
    inline void advance_pixel() {}
};

template<typename BitmapMaskCursor, typename T, BitmapMaskDimensionVsImage T_H>
struct BitmapMaskCursorPixelAdvanceAspect<BitmapMaskCursor, T, BitmapMaskDimensionVsImage::Same, T_H>
{
    BitmapMaskCursorPixelAdvanceAspect(PyArrayView& data_view, BitmapMask<T, BitmapMaskDimensionVsImage::Same, T_H>& mask_) {}

    inline void seek_front_pixel_of_scanline() {}
    inline void advance_pixel() {}
};

template<typename BitmapMaskCursor, typename T, BitmapMaskDimensionVsImage T_H>
struct BitmapMaskCursorPixelAdvanceAspect<BitmapMaskCursor, T, BitmapMaskDimensionVsImage::Larger, T_H>
{
    const SampleLutPtr im_to_mask_pixel_idx_lut;
    const std::uint64_t* lut_element;

    BitmapMaskCursorPixelAdvanceAspect(PyArrayView& data_view, BitmapMask<T, BitmapMaskDimensionVsImage::Larger, T_H>& mask_)
      : im_to_mask_pixel_idx_lut(sampleLuts.getLut(data_view.shape[0], mask_.bitmap_view.shape[0])) {}

    inline void seek_front_pixel_of_scanline() {}
    inline void advance_pixel() {}
};
