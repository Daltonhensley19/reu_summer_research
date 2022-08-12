#include <torch/csrc/jit/mobile/module.h>
#include <torch/csrc/jit/mobile/interpreter.h>
#include <torch/csrc/jit/mobile/observer.h>
#include <torch/csrc/jit/runtime/jit_exception.h>
#include <exception>

#include <ATen/record_function.h>

namespace torch {
namespace jit {
std::ostream& operator<<(std::ostream& out, Instruction inst);
namespace mobile {

const c10::QualifiedName& Function::qualname() const {
  return name_;
}

const std::string& Function::name() const {
  return name_.name();
}

void CompilationUnit::register_function(std::unique_ptr<Function> fn) {
  methods_.emplace_back(std::move(fn));
}

Function* CompilationUnit::find_function(const c10::QualifiedName& qn) {
  for (auto& fn : methods_) {
    if (fn->qualname() == qn) {
      return fn.get();
    }
  }
  return nullptr;
}

c10::IValue Module::run_method(const std::string& method_name, Stack stack) {
  auto observer = torch::observerConfig().getModuleObserver();
  if (observer) {
    observer->onEnterRunMethod(name(), method_name);
  }

  auto debug_info = std::make_shared<MobileDebugInfo>();
  debug_info->setModelName(name());
  debug_info->setMethodName(method_name);
  at::DebugInfoGuard guard(at::DebugInfoKind::MOBILE_RUNTIME_INFO, debug_info);

  auto m = find_method(method_name);
  if (m == nullptr) {
    if (observer) {
      std::string cancellation_reason =
          "Method '" + method_name + "' is not defined";
      observer->onCancelRunMethod(cancellation_reason);
    }
    AT_ERROR("Method '", method_name, "' is not defined.");
  }
  try {
    stack.insert(stack.begin(), object_);
    m->run(stack);
    c10::IValue result = stack.front();
    if (observer) {
      observer->onExitRunMethod();
    }
    return result;
  } catch (const std::exception& ex) {
    if (observer) {
      observer->onFailRunMethod(
          "Error occured during model running entry point: " +
          (std::string)ex.what());
    }
    TORCH_CHECK(false, ex.what());
  } catch (...) {
    if (observer) {
      observer->onFailRunMethod("unknown exception");
    }
    TORCH_CHECK(false, "unknown exception");
  }
}

Function* Module::find_method(const std::string& basename) const {
  for (auto& fn : cu_->methods()) {
    if (fn->name() == basename) {
      return fn.get();
    }
  }
  return nullptr;
}

namespace {
void set_train_recurse(
    const c10::intrusive_ptr<c10::ivalue::Object>& obj,
    bool on) {
  if (auto slot = obj->type()->findAttributeSlot("training")) {
    obj->setSlot(*slot, on);
  } else {
    TORCH_INTERNAL_ASSERT(false, "'training' attribute not found");
  }
  for (const auto& slot : obj->slots()) {
    if (slot.isObject()) {
      set_train_recurse(slot.toObject(), on);
    }
  }
}

void slot_params_recurse(
    const c10::intrusive_ptr<c10::ivalue::Object>& obj,
    std::vector<at::Tensor>* params) {
  for (const auto& slot : obj->slots()) {
    if (slot.isTensor()) {
      params->emplace_back(slot.toTensor());
    } else if (slot.isObject()) {
      slot_params_recurse(slot.toObject(), params);
    }
  }
}

void slot_named_params_recurse(
    const c10::intrusive_ptr<c10::ivalue::Object>& obj,
    std::map<std::string, at::Tensor>* params,
    const std::string& parent_name) {
  auto slots = obj->slots();
  size_t nslots = slots.size();
  for (size_t i = 0; i < nslots; ++i) {
    auto slot = slots[i];
    std::string name =
        parent_name.size() == 0 ? parent_name : parent_name + ".";
    name += obj->type()->getAttributeName(i);
    if (slot.isTensor()) {
      (*params)[name] = slot.toTensor();
    } else if (slot.isObject()) {
      slot_named_params_recurse(slot.toObject(), params, name);
    }
  }
}
} // namespace

const std::vector<at::Tensor> Module::parameters() const {
  std::vector<at::Tensor> params;
  slot_params_recurse(object_, &params);
  return params;
}

const std::map<std::string, at::Tensor> Module::named_parameters() const {
  std::map<std::string, at::Tensor> params;
  const std::string name = "";
  slot_named_params_recurse(object_, &params, name);
  return params;
}

std::string Module::get_forward_method_debug_info(size_t pc) const {
  return find_method("forward")->get_module_debug_info(pc);
}

void Module::train(bool on) {
  set_train_recurse(object_, on);
}

bool Module::is_training() const {
  if (auto slot = object_->type()->findAttributeSlot("training")) {
    return object_->getSlot(*slot).toBool();
  }
  return true;
}
} // namespace mobile
} // namespace jit
} // namespace torch
