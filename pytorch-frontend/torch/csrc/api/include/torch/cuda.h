#pragma once

#include <torch/csrc/WindowsTorchApiMacro.h>

#include <cstdint>
#include <cstddef>

namespace torch {
namespace cuda {

/// Returns the number of CUDA devices available.
size_t TORCH_API device_count();

/// Returns true if at least one CUDA device is available.
bool TORCH_API is_available();

/// Returns true if CUDA is available, and CuDNN is available.
bool TORCH_API cudnn_is_available();

/// Sets the seed for the current GPU.
void TORCH_API manual_seed(uint64_t seed);

/// Sets the seed for all available GPUs.
void TORCH_API manual_seed_all(uint64_t seed);

} // namespace cuda
} // namespace torch