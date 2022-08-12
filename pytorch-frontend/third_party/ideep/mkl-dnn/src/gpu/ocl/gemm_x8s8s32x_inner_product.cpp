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

#include "gpu/ocl/gemm_x8s8s32x_inner_product.hpp"

#include "gpu/gemm/gpu_gemm.hpp"
#include "gpu/ocl/ocl_utils.hpp"

namespace dnnl {
namespace impl {
namespace gpu {
namespace ocl {

status_t gemm_x8s8s32x_inner_product_fwd_t::execute_forward(
        const exec_ctx_t &ctx) const {
    using namespace memory_tracking::names;
    using namespace gemm_utils;

    gemm_exec_args_t gemm_args;
    gemm_args.a = &CTX_IN_STORAGE(DNNL_ARG_WEIGHTS);
    gemm_args.b = &CTX_IN_STORAGE(DNNL_ARG_SRC);

    std::unique_ptr<memory_storage_t> acc;
    if (pd()->use_scratchpad() || pd()->use_temp_dst())
        acc = ctx.get_scratchpad_grantor().get_memory_storage(
                key_iprod_int_dat_in_acc_dt);

    if (pd()->use_temp_dst()) {
        gemm_args.c = acc.get();
    } else {
        gemm_args.c = &CTX_OUT_STORAGE(DNNL_ARG_DST);
    }

    gemm_exec_ctx_t gemm_ctx(ctx, gemm_args);

    nested_scratchpad_t ns(ctx, key_nested, gemm_);
    gemm_ctx.set_scratchpad_grantor(ns.grantor());

    status_t gemm_exec_status = gpu_gemm(gemm_)->execute(gemm_ctx);
    if (gemm_exec_status != status::success) return gemm_exec_status;

    if (pd()->with_post_process()) {
        compute::kernel_arg_list_t arg_list;
        arg_list.set(0, CTX_OUT_STORAGE(DNNL_ARG_DST));
        arg_list.set(1, CTX_IN_STORAGE(DNNL_ARG_BIAS));
        arg_list.set(2, CTX_OUT_STORAGE(DNNL_ARG_DST));
        arg_list.set(3, pd()->attr_info_.eltwise_alpha);
        arg_list.set(4, pd()->attr_info_.eltwise_beta);
        arg_list.set(5, pd()->attr_info_.eltwise_scale);
        arg_list.set(6, pd()->attr_info_.sum_scale);
        arg_list.set(7,
                pd()->use_scratchpad() ? *acc
                                       : memory_storage_t::empty_storage());
        arg_list.set(8,
                pd()->attr_info_.with_oscales
                        ? CTX_GPU_RES_STORAGE(SCALES_)
                        : memory_storage_t::empty_storage());

        size_t mb = pd()->MB();
        size_t oc = pd()->OC();

        const size_t gws[] = {1, mb, oc};
        const size_t lws[] = {1, 1, 1};
        auto nd_range = compute::nd_range_t(gws, lws);

        status_t status
                = parallel_for(ctx, nd_range, post_process_kernel_, arg_list);
        if (status != status::success) return status;
    }

    return status::success;
}

} // namespace ocl
} // namespace gpu
} // namespace impl
} // namespace dnnl
