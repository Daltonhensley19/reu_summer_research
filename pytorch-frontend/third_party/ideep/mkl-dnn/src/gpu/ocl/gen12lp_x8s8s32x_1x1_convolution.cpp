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
#include <algorithm>
#include "gpu/ocl/gen12lp_x8s8s32x_1x1_convolution.hpp"
#include "gpu/ocl/ocl_stream.hpp"

namespace dnnl {
namespace impl {
namespace gpu {
namespace ocl {

status_t gen12lp_x8s8s32x_1x1_convolution_fwd_t::pd_t::init_conf(
        engine_t *engine) {
    using namespace format_tag;

    const convolution_desc_t &cd = *desc();
    const memory_desc_wrapper src_mdw(src_md());
    const memory_desc_wrapper weights_mdw(weights_md());
    const memory_desc_wrapper dst_mdw(dst_md());
    const memory_desc_wrapper bias_mdw(weights_md(1));
    auto dev_info = utils::downcast<compute::compute_engine_t *>(engine)
                            ->device_info();

    set_default_conf(conf, cd, *src_md(), *weights_md(), *dst_md(),
            *weights_md(1), *attr());

    if (conf.is_depthwise || conf.kh != 1 || conf.kw != 1
            || (conf.with_groups && conf.ngroups > 1
                    && (conf.oc % 32 != 0 || conf.ic % 32 != 0)))
        return status::unimplemented;

    conf.src_data_type = src_mdw.data_type();
    conf.dst_data_type = dst_mdw.data_type();

    conf.mb_block = 32;
    conf.oc_block = 32;
    conf.ic_block = 32;
    conf.nchunk = utils::div_up(conf.oc * conf.ngroups, conf.oc_block);

    if (conf.mb == 8 || conf.mb % 16 == 0) {
        conf.mb_block = 32;
        conf.sp_block = 1;
    } else {
        if (conf.stride_h != 1 || conf.stride_w != 1)
            return status::unimplemented;
        conf.mb_block = 1;
        conf.sp_block = 4;
        auto approx_clocks = [&](const int block) {
            int ic_chunks = utils::div_up(conf.ic, conf.ic_block);
            bool use_slm = (utils::div_up(conf.ow * conf.oh, block)) % 8 == 0;
            int mem_clocks = ic_chunks * (16 - use_slm * 6)
                    + block / 2 * (ic_chunks + 1);
            int compute_clocks = 32 * block * ic_chunks;
            return utils::div_up(conf.nchunk * conf.mb
                                   * utils::div_up(conf.ow * conf.oh, block),
                           dev_info->hw_threads())
                    * (compute_clocks + mem_clocks);
        };
        auto clock_compare = [&](const int &block1, const int &block2) {
            return approx_clocks(block1) < approx_clocks(block2);
        };
        std::vector<int> sorted_blocks = {4, 8, 12, 16};
        std::sort(sorted_blocks.begin(), sorted_blocks.end(), clock_compare);
        conf.sp_block = sorted_blocks[0];
    }
    conf.src_data_type = src_mdw.data_type();
    conf.dst_data_type = dst_mdw.data_type();

    int ow_group
            = ((utils::div_up(conf.ow * conf.oh, conf.sp_block)) % 8) ? 1 : 8;

    conf.sub_group_size = 8;
    conf.lws_d[0] = conf.sub_group_size;
    conf.lws_d[1] = ow_group;
    conf.lws_d[2] = 1;

    conf.gws_d[0] = utils::rnd_up(conf.nchunk * 8, conf.lws_d[0]);
    conf.gws_d[1] = utils::rnd_up(
            utils::div_up(conf.ow * conf.oh, conf.sp_block), conf.lws_d[1]);

    conf.gws_d[2] = utils::div_up(conf.mb, utils::div_up(conf.mb_block, 2));

    conf.with_bias = cd.bias_desc.format_kind != format_kind::undef;

    format_tag_t src_tag, dst_tag, wei_tag;

    if (conf.mb_block == 32) {
        src_tag = utils::pick(conf.ndims - 3, NCw32n32c, NChw32n32c);
        dst_tag = utils::pick(conf.ndims - 3, NCw32n32c, NChw32n32c);
    } else {
        src_tag = utils::pick(conf.ndims - 3, nCw32c, nChw32c);
        dst_tag = utils::pick(conf.ndims - 3, nCw32c, nChw32c);
    }

    wei_tag = conf.with_groups
            ? utils::pick(conf.ndims - 3, gOIw4o8i8o4i, gOIhw4o8i8o4i)
            : utils::pick(conf.ndims - 3, OIw4o8i8o4i, OIhw4o8i8o4i);

    conf.src_tag = src_mdw.format_kind() == format_kind::any
            ? src_tag
            : src_mdw.matches_one_of_tag(src_tag);
    conf.wei_tag = weights_mdw.format_kind() == format_kind::any
            ? wei_tag
            : weights_mdw.matches_one_of_tag(wei_tag);
    conf.dst_tag = dst_mdw.format_kind() == format_kind::any
            ? dst_tag
            : dst_mdw.matches_one_of_tag(dst_tag);

    if (conf.src_tag != src_tag || conf.wei_tag != wei_tag
            || conf.dst_tag != dst_tag)
        return status::unimplemented;

    return status::success;
}

status_t gen12lp_x8s8s32x_1x1_convolution_fwd_t::pd_t::init_kernel_ctx(
        compute::kernel_ctx_t &kernel_ctx) const {
    kernel_ctx.define_int("G", conf.ngroups);
    kernel_ctx.define_int("MB", conf.mb);
    kernel_ctx.define_int("IC", conf.ic_without_padding);
    kernel_ctx.define_int("IH", conf.ih);
    kernel_ctx.define_int("IW", conf.iw);
    kernel_ctx.define_int("OC", conf.oc_without_padding);
    kernel_ctx.define_int("OH", conf.oh);
    kernel_ctx.define_int("OW", conf.ow);
    kernel_ctx.define_int("KH", conf.kh);
    kernel_ctx.define_int("KW", conf.kw);
    kernel_ctx.define_int("SH", conf.stride_h);
    kernel_ctx.define_int("SW", conf.stride_w);

    kernel_ctx.define_int("SP_BLOCK", conf.sp_block);
    kernel_ctx.define_int("MB_BLOCK", conf.mb_block);
    kernel_ctx.define_int("OC_BLOCK", conf.oc_block);
    kernel_ctx.define_int("IC_BLOCK", conf.ic_block);

    kernel_ctx.define_int("WITH_BIAS", conf.with_bias);
    kernel_ctx.define_int("WITH_POST_SUM_ELTWISE",
            conf.attr_info.with_eltwise && conf.attr_info.with_sum
                    && conf.attr_info.eltwise_idx > conf.attr_info.sum_idx);
    def_attr_info(kernel_ctx, conf.attr_info);
    kernel_ctx.define_int("SCALES_COMMON", conf.attr_info.with_common_oscales);
    kernel_ctx.define_int("SCALES_PER_OC", conf.attr_info.with_per_oc_oscales);

    kernel_ctx.define_int("SUB_GROUP_SIZE", conf.sub_group_size);

    kernel_ctx.define_int("LWS_0", conf.lws_d[0]);
    kernel_ctx.define_int("LWS_1", conf.lws_d[1]);
    kernel_ctx.define_int("LWS_2", conf.lws_d[2]);

    kernel_ctx.define_int("OC_NCHUNK", utils::div_up(conf.oc, conf.oc_block));
    kernel_ctx.define_int("IC_NCHUNK", utils::div_up(conf.ic, conf.ic_block));

    kernel_ctx.define_int("INT8_WEI_SLM",
            utils::div_up(conf.ow * conf.oh, conf.sp_block) % 8 == 0);
    kernel_ctx.define_int("SP_TAIL",
            utils::div_up(conf.ow * conf.oh, conf.sp_block) % conf.lws_d[1]
                    == 0);
    kernel_ctx.define_int("OUT_SP_TAIL", (conf.ow * conf.oh) % conf.sp_block);

    kernel_ctx.set_data_type(conf.dst_data_type);
    def_data_type(kernel_ctx, conf.src_data_type, "SRC");
    def_data_type(kernel_ctx, conf.dst_data_type, "DST");

    kernel_ctx.add_option("-Dcl_intel_subgroups_char");

    return status::success;
}

status_t gen12lp_x8s8s32x_1x1_convolution_fwd_t::execute_forward(
        const exec_ctx_t &ctx) const {
    auto &src = CTX_IN_STORAGE(DNNL_ARG_SRC);
    auto &weights = CTX_IN_STORAGE(DNNL_ARG_WEIGHTS);
    auto &bias = CTX_IN_STORAGE(DNNL_ARG_BIAS);
    auto &oscales = CTX_IN_STORAGE(DNNL_ARG_ATTR_OUTPUT_SCALES);
    auto &dst = CTX_OUT_STORAGE(DNNL_ARG_DST);

    const auto &conf = pd()->conf;

    compute::kernel_arg_list_t arg_list;
    arg_list.set(0, src);
    arg_list.set(1, weights);
    arg_list.set(2, bias);
    arg_list.set(3, dst);
    arg_list.set(4, conf.attr_info.eltwise_alpha);
    arg_list.set(5, conf.attr_info.eltwise_beta);
    arg_list.set(6, conf.attr_info.eltwise_scale);
    arg_list.set(7, conf.attr_info.sum_scale);

    if (conf.attr_info.common_oscales) {
        float scales = pd()->attr()->output_scales_.scales_[0];
        arg_list.set(8, scales);
    } else {
        arg_list.set(8, 1.0f);
    }

    if (conf.attr_info.with_per_oc_oscales) {
        if (conf.attr_info.with_runtime_oscales)
            arg_list.set(9, oscales);
        else
            arg_list.set(9, CTX_GPU_RES_STORAGE(SCALES_));
    } else {
        arg_list.set(9, memory_storage_t::empty_storage());
    }

    auto nd_range = compute::nd_range_t(conf.gws_d, conf.lws_d);
    status_t status = parallel_for(ctx, nd_range, kernel_, arg_list);

    return status;
}

} // namespace ocl
} // namespace gpu
} // namespace impl
} // namespace dnnl
