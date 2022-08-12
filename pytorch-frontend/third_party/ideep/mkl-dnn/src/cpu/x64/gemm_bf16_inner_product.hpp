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

#ifndef CPU_X64_GEMM_BF16_INNER_PRODUCT_HPP
#define CPU_X64_GEMM_BF16_INNER_PRODUCT_HPP

#include <assert.h>

#include <memory>

#include "common/c_types_map.hpp"
#include "common/memory_tracking.hpp"
#include "common/primitive.hpp"
#include "common/type_helpers.hpp"
#include "common/utils.hpp"

#include "cpu/cpu_engine.hpp"
#include "cpu/gemm/gemm.hpp"
#include "cpu/gemm_inner_product_utils.hpp"

namespace dnnl {
namespace impl {
namespace cpu {
namespace x64 {

template <data_type_t dst_data_type>
struct gemm_bf16_inner_product_fwd_t : public primitive_t {
    struct pd_t : public cpu_inner_product_fwd_pd_t {
        using cpu_inner_product_fwd_pd_t::cpu_inner_product_fwd_pd_t;

        DECLARE_COMMON_PD_T(GEMM_IMPL_STR, gemm_bf16_inner_product_fwd_t);

        status_t init(engine_t *engine) {
            using namespace utils;
            using namespace data_type;

            bool ok = true && mayiuse(avx512_core) && is_fwd()
                    && !has_zero_dim_memory()
                    && everyone_is(
                            bf16, src_md()->data_type, weights_md()->data_type)
                    && dst_data_type == dst_md()->data_type
                    && IMPLICATION(with_bias(),
                            one_of(weights_md(1)->data_type, f32, bf16))
                    && attr()->has_default_values(
                            primitive_attr_t::skip_mask_t::post_ops)
                    && post_ops_ok() && set_default_params() == status::success
                    && dense_gemm_consitency_check(
                            src_md(), weights_md(), dst_md());
            if (!ok) return status::unimplemented;

            dst_is_acc_ = dst_data_type == f32;

            init_scratchpad();

            return status::success;
        }

        bool dst_is_acc_;

    protected:
        bool post_ops_ok() const {
            auto const &po = attr()->post_ops_;
            auto is_eltwise
                    = [&](int idx) { return po.entry_[idx].is_eltwise(false); };
            auto is_sum = [&](int idx) { return po.entry_[idx].is_sum(false); };
            switch (po.len_) {
                case 0: return true; // no post_ops
                case 1: return is_eltwise(0) || is_sum(0); // sum OR eltwise
                case 2: return is_sum(0) && is_eltwise(1); // sum -> eltwise
                default: return false;
            }
            return false;
        }

        void init_scratchpad() {
            if (!dst_is_acc_) {
                auto scratchpad = scratchpad_registry().registrar();
                scratchpad.template book<acc_data_t>(
                        memory_tracking::names::key_iprod_int_dat_in_acc_dt,
                        MB() * OC());
            }
        }
    };

    gemm_bf16_inner_product_fwd_t(const pd_t *apd) : primitive_t(apd) {
        bool has_bias = pd()->with_bias(),
             has_eltwise
                = pd()->attr()->post_ops_.find(primitive_kind::eltwise) >= 0,
             has_sum_as_postops = !pd()->dst_is_acc_;
        postops_in_ip_ = false
                || !pd()->dst_is_acc_ /* includes has_sum_as_postops */
                || has_bias || has_eltwise;
        if (postops_in_ip_)
            pp_kernel_.reset(pp_kernel_t::create(pd(), !has_sum_as_postops));

        auto sum_idx = pd()->attr()->post_ops_.find(primitive_kind::sum);
        beta_ = sum_idx >= 0 && !has_sum_as_postops
                ? pd()->attr()->post_ops_.entry_[sum_idx].sum.scale
                : 0.0;
    }

    typedef typename prec_traits<dst_data_type>::type dst_data_t;
    typedef typename prec_traits<data_type::f32>::type acc_data_t;
    typedef typename prec_traits<data_type::bf16>::type src_data_t;
    typedef typename prec_traits<data_type::bf16>::type wei_data_t;

    status_t execute(const exec_ctx_t &ctx) const override {
        return execute_forward(ctx);
    }

private:
    using pp_kernel_t
            = inner_product_utils::pp_kernel_t<data_type::f32, dst_data_type>;
    std::unique_ptr<pp_kernel_t> pp_kernel_;
    bool postops_in_ip_;
    float beta_;

    status_t execute_forward(const exec_ctx_t &ctx) const;
    const pd_t *pd() const { return (const pd_t *)primitive_t::pd().get(); }
};

template <data_type_t diff_src_data_type>
struct gemm_bf16_inner_product_bwd_data_t : public primitive_t {
    struct pd_t : public cpu_inner_product_bwd_data_pd_t {
        using cpu_inner_product_bwd_data_pd_t::cpu_inner_product_bwd_data_pd_t;

        DECLARE_COMMON_PD_T(GEMM_IMPL_STR, gemm_bf16_inner_product_bwd_data_t);

        status_t init(engine_t *engine) {
            using namespace data_type;

            bool ok = true && mayiuse(avx512_core)
                    && desc()->prop_kind == prop_kind::backward_data
                    && !has_zero_dim_memory()
                    && utils::everyone_is(bf16, weights_md()->data_type,
                            diff_dst_md()->data_type)
                    && diff_src_data_type == diff_src_md()->data_type
                    && attr()->has_default_values()
                    && this->set_default_params() == status::success
                    && dense_gemm_consitency_check(
                            diff_src_md(), weights_md(), diff_dst_md());
            if (!ok) return status::unimplemented;

            diff_src_is_acc_ = diff_src_data_type == data_type::f32;

            init_scratchpad();

            return status::success;
        }

        bool diff_src_is_acc_;

    private:
        void init_scratchpad() {
            if (!diff_src_is_acc_) {
                auto scratchpad = scratchpad_registry().registrar();
                scratchpad.template book<acc_data_t>(
                        memory_tracking::names::key_iprod_int_dat_in_acc_dt,
                        MB() * IC_total_padded());
            }
        }
    };

    gemm_bf16_inner_product_bwd_data_t(const pd_t *apd) : primitive_t(apd) {}

    typedef typename prec_traits<data_type::bf16>::type diff_dst_data_t;
    typedef typename prec_traits<data_type::f32>::type acc_data_t;
    typedef typename prec_traits<diff_src_data_type>::type diff_src_data_t;
    typedef typename prec_traits<data_type::bf16>::type wei_data_t;

    status_t execute(const exec_ctx_t &ctx) const override {
        return execute_backward_data(ctx);
    }

private:
    status_t execute_backward_data(const exec_ctx_t &ctx) const;
    const pd_t *pd() const { return (const pd_t *)primitive_t::pd().get(); }
};

template <data_type_t diff_wei_data_type>
struct gemm_bf16_inner_product_bwd_weights_t : public primitive_t {
    struct pd_t : public cpu_inner_product_bwd_weights_pd_t {
        using cpu_inner_product_bwd_weights_pd_t::
                cpu_inner_product_bwd_weights_pd_t;

        DECLARE_COMMON_PD_T(
                GEMM_IMPL_STR, gemm_bf16_inner_product_bwd_weights_t);

        status_t init(engine_t *engine) {
            using namespace utils;
            using namespace data_type;

            bool ok = true && mayiuse(avx512_core)
                    && desc()->prop_kind == prop_kind::backward_weights
                    && !has_zero_dim_memory()
                    && everyone_is(
                            bf16, src_md()->data_type, diff_dst_md()->data_type)
                    && diff_wei_data_type == diff_weights_md()->data_type
                    && IMPLICATION(with_bias(),
                            one_of(diff_weights_md(1)->data_type, f32, bf16))
                    && attr()->has_default_values()
                    && set_default_params() == status::success
                    && dense_gemm_consitency_check(
                            src_md(), diff_weights_md(), diff_dst_md());

            if (!ok) return status::unimplemented;

            diff_wei_is_acc_ = diff_wei_data_type == f32;
            diff_bias_is_acc_
                    = with_bias() && diff_weights_md(1)->data_type == f32;

            init_scratchpad();

            return status::success;
        }

        bool diff_wei_is_acc_, diff_bias_is_acc_;

    private:
        void init_scratchpad() {
            auto scratchpad = scratchpad_registry().registrar();
            if (!diff_wei_is_acc_)
                scratchpad.template book<acc_data_t>(
                        memory_tracking::names::key_iprod_int_dat_in_acc_dt,
                        OC() * IC_total_padded());
            if (with_bias() && !diff_bias_is_acc_)
                scratchpad.template book<acc_data_t>(
                        memory_tracking::names::key_iprod_bias_bf16_convert_wsp,
                        OC());
        }
    };

    gemm_bf16_inner_product_bwd_weights_t(const pd_t *apd) : primitive_t(apd) {}

    typedef typename prec_traits<data_type::bf16>::type diff_dst_data_t;
    typedef typename prec_traits<data_type::f32>::type acc_data_t;
    typedef typename prec_traits<data_type::bf16>::type src_data_t;
    typedef typename prec_traits<diff_wei_data_type>::type diff_wei_data_t;

    status_t execute(const exec_ctx_t &ctx) const override {
        return execute_backward_weights(ctx);
    }

private:
    status_t execute_backward_weights(const exec_ctx_t &ctx) const;
    const pd_t *pd() const { return (const pd_t *)primitive_t::pd().get(); }
};

} // namespace x64
} // namespace cpu
} // namespace impl
} // namespace dnnl

#endif

// vim: et ts=4 sw=4 cindent cino+=l0,\:4,N-s
