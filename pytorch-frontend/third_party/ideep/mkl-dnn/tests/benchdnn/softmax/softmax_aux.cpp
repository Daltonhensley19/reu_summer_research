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

#include "dnnl_common.hpp"
#include "dnnl_debug.hpp"

#include "softmax/softmax.hpp"

namespace softmax {

alg_t str2alg(const char *str) {
#define CASE(_alg) \
    if (!strcasecmp(STRINGIFY(_alg), str)) return _alg
    CASE(SOFTMAX);
    CASE(LOGSOFTMAX);
#undef CASE
    assert(!"unknown algorithm");
    return UNDEF;
}

const char *alg2str(alg_t alg) {
    if (alg == SOFTMAX) return "SOFTMAX";
    if (alg == LOGSOFTMAX) return "LOGSOFTMAX";
    assert(!"unknown algorithm");
    return "UNDEF";
}

std::ostream &operator<<(std::ostream &s, const prb_t &p) {
    dump_global_params(s);
    settings_t def;

    if (canonical || p.dir != def.dir[0]) s << "--dir=" << p.dir << " ";
    if (canonical || p.dt != def.dt[0]) s << "--dt=" << p.dt << " ";
    if (canonical || p.tag != def.tag[0]) s << "--tag=" << p.tag << " ";
    if (canonical || p.alg != def.alg[0])
        s << "--alg=" << alg2str(p.alg) << " ";
    if (canonical || p.axis != def.axis[0]) s << "--axis=" << p.axis << " ";
    if (canonical || p.inplace != def.inplace[0])
        s << "--inplace=" << bool2str(p.inplace) << " ";

    s << p.dims;

    return s;
}

} // namespace softmax
