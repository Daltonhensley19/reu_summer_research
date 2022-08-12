/*******************************************************************************
* Copyright 2019-2020 Intel Corporation
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/

#include "gpu/ocl/ocl_types.h"

#if IS_FWD
KERNEL_ATTR
__kernel void ref_pooling_fwd(
        __global DATA_T *src, __global int *ws, __global DATA_T *dst) {
    const int mb = GWS_GET_MB();
    const int oc = GWS_GET_OC();

    for (int od = 0; od < OD; ++od)
        for (int oh = 0; oh < OH; ++oh)
            for (int ow = 0; ow < OW; ++ow) {
                const uint dst_off = DST_OFF(mb, oc, od, oh, ow);
#if ALG_MAX && IS_TRAINING
                ws[dst_off] = -1;
#endif
#if ALG_MAX
#if DT_BF16
                DEF_ACC_DATA_T d = DATA_MIN;
#else // DT_BF16
                DATA_T d = DATA_MIN;
#endif
                for (int kd = 0; kd < KD; ++kd)
                    for (int kh = 0; kh < KH; ++kh) {
                        for (int kw = 0; kw < KW; ++kw) {
                            const int id = od * SD - PD + kd;
                            const int ih = oh * SH - PH + kh;
                            const int iw = ow * SW - PW + kw;

                            if (id < 0 || id >= ID) continue;
                            if (ih < 0 || ih >= IH) continue;
                            if (iw < 0 || iw >= IW) continue;

#if ALG_MAX && IS_TRAINING
                            if (ws[dst_off] < 0)
                                ws[dst_off] = kd * KH * KW + kh * KW + kw;
#endif
                            int src_off = SRC_OFF(mb, oc, id, ih, iw);
#if DT_BF16
                            DEF_ACC_DATA_T s = DATA_TO_REF(src[src_off]);
#else // DT_BF16 == 0
                            DATA_T s = src[src_off];
#endif
                            if (s > d) {
                                d = s;
#if ALG_MAX && IS_TRAINING
                                ws[dst_off] = kd * KH * KW + kh * KW + kw;
#endif
                            }
                        }
                    }
                dst[dst_off] = CONVERT_DATA_T(d);
#if ALG_MAX && IS_TRAINING
                if (ws[dst_off] < 0) ws[dst_off] = 0;
#endif
#else
                const int id_start = max(od * SD - PD, 0);
                const int ih_start = max(oh * SH - PH, 0);
                const int iw_start = max(ow * SW - PW, 0);
                const int id_end = min(od * SD - PD + KD, ID);
                const int ih_end = min(oh * SH - PH + KH, IH);
                const int iw_end = min(ow * SW - PW + KW, IW);

#if ALG_AVG_P
                const int num_summands = KD * KW * KH;
#else
                const int num_summands = (ih_end - ih_start)
                        * (iw_end - iw_start) * (id_end - id_start);
#endif
                float d = 0;
                for (int id = id_start; id < id_end; ++id)
                    for (int ih = ih_start; ih < ih_end; ++ih) {
                        for (int iw = iw_start; iw < iw_end; ++iw) {
                            int src_off = SRC_OFF(mb, oc, id, ih, iw);
                            d += DATA_TO_REF(src[src_off]);
                        }
                    }
                dst[dst_off] = CONVERT_DATA_T(ROUND(d / num_summands));
#endif
            }
}
#endif

#if IS_BWD
KERNEL_ATTR
__kernel void ref_pooling_bwd(__global DATA_T *diff_src, __global int *ws,
        __global DATA_T *diff_dst) {
    const int mb = GWS_GET_MB();
    const int oc = GWS_GET_OC();

    for (int id = 0; id < ID; ++id)
        for (int ih = 0; ih < IH; ++ih)
            for (int iw = 0; iw < IW; ++iw) {
                uint diff_src_offset = SRC_OFF(mb, oc, id, ih, iw);
                diff_src[diff_src_offset] = 0;
            }

#if DT_BF16
    // For bfloat16, iterate over input to use a temporary float accumulator
    for (int id = 0; id < ID; ++id)
        for (int ih = 0; ih < IH; ++ih)
            for (int iw = 0; iw < IW; ++iw) {
                float s = 0;
                for (int kd = 0; kd < KD; ++kd)
                    for (int kh = 0; kh < KH; ++kh)
                        for (int kw = 0; kw < KW; ++kw) {
                            int _od = id + PD - kd;
                            int _oh = ih + PH - kh;
                            int _ow = iw + PW - kw;
                            if (_od % SD != 0 || _oh % SH != 0 || _ow % SW != 0)
                                continue;

                            int od = _od / SD;
                            int oh = _oh / SH;
                            int ow = _ow / SW;

                            if (od < 0 || od >= OD) continue;
                            if (oh < 0 || oh >= OH) continue;
                            if (ow < 0 || ow >= OW) continue;

                            const uint dst_off = DST_OFF(mb, oc, od, oh, ow);

#if ALG_MAX
                            const int index = ws[dst_off];

                            const int hw = index % (KW * KH);
                            const int w_kd = index / (KW * KH);
                            const int w_kw = hw % KW;
                            const int w_kh = hw / KW;
                            if (w_kd != kd || w_kh != kh || w_kw != kw)
                                continue;
#endif

#if ALG_MAX
                            const int denom = 1;
#elif ALG_AVG_P
                            const int denom = KD * KH * KW;
#elif ALG_AVG_NP
                            const int id_start = max(od * SD - PD, 0);
                            const int ih_start = max(oh * SH - PH, 0);
                            const int iw_start = max(ow * SW - PW, 0);
                            const int id_end = min(od * SD - PD + KD, ID);
                            const int ih_end = min(oh * SH - PH + KH, IH);
                            const int iw_end = min(ow * SW - PW + KW, IW);
                            const int denom = (ih_end - ih_start)
                                    * (iw_end - iw_start) * (id_end - id_start);
#endif
                            s += DATA_TO_REF(diff_dst[dst_off]) / denom;
                        }
                uint diff_src_offset = SRC_OFF(mb, oc, id, ih, iw);
                diff_src[diff_src_offset] = CONVERT_DATA_T(s);
            }
#else // DT_BF16
    for (int od = 0; od < OD; ++od)
        for (int oh = 0; oh < OH; ++oh)
            for (int ow = 0; ow < OW; ++ow) {
                const uint dst_off = DST_OFF(mb, oc, od, oh, ow);
                const float d = diff_dst[dst_off];

#if ALG_MAX
                const int index = ws[dst_off];
                const int kd = index / (KW * KH);
                const int hw = index % (KW * KH);
                const int kw = hw % KW;
                const int kh = hw / KW;

                const int id = od * SD - PD + kd;
                const int ih = oh * SH - PH + kh;
                const int iw = ow * SW - PW + kw;

                if (id < 0 || id >= ID) continue;
                if (ih < 0 || ih >= IH) continue;
                if (iw < 0 || iw >= IW) continue;

                uint diff_src_offset = SRC_OFF(mb, oc, id, ih, iw);
                diff_src[diff_src_offset] += d;
#else
                const int id_start = max(od * SD - PD, 0);
                const int ih_start = max(oh * SH - PH, 0);
                const int iw_start = max(ow * SW - PW, 0);
                const int id_end = min(od * SD - PD + KD, ID);
                const int ih_end = min(oh * SH - PH + KH, IH);
                const int iw_end = min(ow * SW - PW + KW, IW);

#if ALG_AVG_P
                const int num_summands = KD * KW * KH;
#else
                const int num_summands = (ih_end - ih_start)
                        * (iw_end - iw_start) * (id_end - id_start);
#endif
                for (int id = id_start; id < id_end; ++id)
                    for (int ih = ih_start; ih < ih_end; ++ih)
                        for (int iw = iw_start; iw < iw_end; ++iw) {
                            const uint diff_src_offset
                                    = SRC_OFF(mb, oc, id, ih, iw);
                            diff_src[diff_src_offset] += d / num_summands;
                        }
#endif
            }
#endif
}
#endif
