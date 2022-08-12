from __future__ import absolute_import, division, print_function, unicode_literals
from test_pytorch_common import TestCase, run_tests

import torch
import torch.onnx
from torch.onnx import utils, OperatorExportTypes, TrainingMode
from torch.onnx.symbolic_helper import _set_opset_version, _set_operator_export_type
import torch.utils.cpp_extension
from test_pytorch_common import skipIfUnsupportedMinOpsetVersion
import caffe2.python.onnx.backend as backend
from verify import verify

import torchvision

import onnx
import onnxruntime  # noqa

import io
import copy
import unittest

import numpy as np


skip = unittest.skip


class TestUtilityFuns(TestCase):
    opset_version = 9

    def setUp(self):
        torch.manual_seed(0)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(0)

    def test_is_in_onnx_export(self):
        test_self = self

        class MyModule(torch.nn.Module):
            def forward(self, x):
                test_self.assertTrue(torch.onnx.is_in_onnx_export())
                raise ValueError
                return x + 1

        x = torch.randn(3, 4)
        f = io.BytesIO()
        try:
            torch.onnx.export(MyModule(), x, f, opset_version=self.opset_version)
        except ValueError:
            self.assertFalse(torch.onnx.is_in_onnx_export())

    def test_validate_dynamic_axes_invalid_input_output_name(self):
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            utils._validate_dynamic_axes({'input1': {}, 'output': {},
                                         'invalid_name1': {}, 'invalid_name2': {}},
                                         None, ['input1', 'input2'], ['output'])
            messages = [str(warning.message) for warning in w]
        assert "Provided key invalid_name1 for dynamic axes is not a valid input/output name" in messages
        assert "Provided key invalid_name2 for dynamic axes is not a valid input/output name" in messages
        assert len(messages) == 2

    @skipIfUnsupportedMinOpsetVersion(11)
    def test_split_to_slice(self):
        class SplitModule(torch.nn.Module):
            def forward(self, x, y, t):
                splits = (x.size(1), y.size(1))
                out, out2 = torch.split(t, splits, dim=1)
                return out, out2

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        x = torch.randn(2, 3)
        y = torch.randn(2, 4)
        t = torch.randn(2, 7)
        graph, _, _ = utils._model_to_graph(SplitModule(), (x, y, t))
        for node in graph.nodes():
            assert node.kind() != "onnx::SplitToSequence"

    def test_constant_fold_transpose(self):
        class TransposeModule(torch.nn.Module):
            def forward(self, x):
                a = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
                b = torch.transpose(a, 1, 0)
                return b + x

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        x = torch.ones(3, 2)
        graph, _, __ = utils._model_to_graph(TransposeModule(), (x, ),
                                             do_constant_folding=True,
                                             _disable_torch_constant_prop=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Transpose"
            assert node.kind() != "onnx::Cast"
            assert node.kind() != "onnx::Constant"
        assert len(list(graph.nodes())) == 1

    def test_constant_fold_reduceL2(self):
        class TransposeModule(torch.nn.Module):
            def forward(self, x):
                a = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
                b = torch.norm(a, p=2, dim=-2, keepdim=False)
                return b + x

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        x = torch.ones(2, 3)
        graph, _, __ = utils._model_to_graph(TransposeModule(), (x, ),
                                             do_constant_folding=True,
                                             _disable_torch_constant_prop=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::ReduceL2"
        assert len(list(graph.nodes())) == 1

    def test_constant_fold_reduceL1(self):
        class NormModule(torch.nn.Module):
            def forward(self, x):
                a = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
                b = torch.norm(a, p=1, dim=-2)
                return b + x

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        x = torch.ones(2, 3)
        graph, _, __ = utils._model_to_graph(NormModule(), (x, ),
                                             do_constant_folding=True,
                                             _disable_torch_constant_prop=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::ReduceL1"
        assert len(list(graph.nodes())) == 1

    def test_constant_fold_slice(self):
        class NarrowModule(torch.nn.Module):
            def forward(self, x):
                a = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
                b = torch.narrow(a, 0, 0, 1)
                return b + x

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        x = torch.ones(1, 3)
        graph, _, __ = utils._model_to_graph(NarrowModule(), (x, ),
                                             do_constant_folding=True,
                                             _disable_torch_constant_prop=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Slice"
            assert node.kind() != "onnx::Cast"
            assert node.kind() != "onnx::Constant"
        assert len(list(graph.nodes())) == 1

    def test_constant_fold_slice_index_exceeds_dim(self):
        class SliceIndexExceedsDimModule(torch.nn.Module):
            def forward(self, x):
                a = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
                b = a[1:10]         # index exceeds dimension
                return b + x

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        x = torch.ones(1, 3)
        graph, _, __ = utils._model_to_graph(SliceIndexExceedsDimModule(), (x, ),
                                             do_constant_folding=True,
                                             _disable_torch_constant_prop=True,
                                             operator_export_type=OperatorExportTypes.ONNX)

        for node in graph.nodes():
            assert node.kind() != "onnx::Slice"
            assert node.kind() != "onnx::Cast"
            assert node.kind() != "onnx::Constant"
        assert len(list(graph.nodes())) == 1

    def test_constant_fold_slice_negative_index(self):
        class SliceNegativeIndexModule(torch.nn.Module):
            def forward(self, x):
                a = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
                b = a[0:-1]        # index relative to the end
                c = torch.select(a, dim=-1, index=-2)
                d = torch.select(a, dim=1, index=0)
                return b + x, c + d

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        x = torch.ones(1, 3)
        graph, _, __ = utils._model_to_graph(SliceNegativeIndexModule(), (x, ),
                                             do_constant_folding=True,
                                             _disable_torch_constant_prop=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Slice"
            assert node.kind() != "onnx::Cast"
            assert node.kind() != "onnx::Constant"

    def test_constant_fold_gather(self):
        class GatherModule(torch.nn.Module):
            def forward(self, x):
                a = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
                b = torch.select(a, dim=1, index=-2)
                c = torch.index_select(a, dim=-2, index=torch.tensor([0, 1]))
                return b + 1, c + x

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        x = torch.ones(1, 3)
        model = GatherModule()
        model(x)
        graph, _, __ = utils._model_to_graph(GatherModule(), (x, ),
                                             do_constant_folding=True,
                                             _disable_torch_constant_prop=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Gather"

    def test_constant_fold_unsqueeze(self):
        class UnsqueezeModule(torch.nn.Module):
            def forward(self, x):
                a = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
                b = torch.unsqueeze(a, 0)
                return b + x

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        x = torch.ones(1, 2, 3)
        graph, _, __ = utils._model_to_graph(UnsqueezeModule(), (x, ),
                                             do_constant_folding=True,
                                             _disable_torch_constant_prop=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Unsqueeeze"
            assert node.kind() != "onnx::Cast"
            assert node.kind() != "onnx::Constant"
        assert len(list(graph.nodes())) == 1

    def test_constant_fold_concat(self):
        class ConcatModule(torch.nn.Module):
            def forward(self, x):
                # Why did I insert a Cast here?  There appears to be intentional
                # behavior in ONNX constant folding where constant tensors which
                # are not attached to any known to be foldable onnx
                # operations don't get extracted into the initializer graph.  So
                # without these casts, we will actually fail to pull out one of
                # the constants, thus failing constant folding.  I think the
                # test is wrong but I don't have time to write a more correct
                # test (I think the right way to go about the test is to setup
                # a predicate for what invariant graphs should hold after
                # constant folding, and then verify this predicate holds.
                # I think the asserts below are an attempt at this predicate,
                # but it is not right!)
                #
                # More commentary at
                # https://github.com/pytorch/pytorch/pull/18698/files#r340107552
                a = torch.tensor([[1., 2., 3.]]).to(torch.float)
                b = torch.tensor([[4., 5., 6.]]).to(torch.float)
                c = torch.cat((a, b), 0)
                d = b + c
                return x + d

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        x = torch.ones(2, 3)
        graph, _, __ = utils._model_to_graph(ConcatModule(), (x, ),
                                             do_constant_folding=True,
                                             _disable_torch_constant_prop=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Concat"
            assert node.kind() != "onnx::Cast"
            assert node.kind() != "onnx::Constant"
        assert len(list(graph.nodes())) == 1

    def test_constant_fold_lstm(self):
        class GruNet(torch.nn.Module):
            def __init__(self):
                super(GruNet, self).__init__()
                self.mygru = torch.nn.GRU(7, 3, 1, bidirectional=False)

            def forward(self, input, initial_state):
                return self.mygru(input, initial_state)

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        input = torch.randn(5, 3, 7)
        h0 = torch.randn(1, 3, 3)
        graph, _, __ = utils._model_to_graph(GruNet(), (input, h0),
                                             do_constant_folding=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Slice"
            assert node.kind() != "onnx::Concat"
            assert node.kind() != "onnx::Unsqueeze"
        assert len(list(graph.nodes())) == 3

    def test_constant_fold_transpose_matmul(self):
        class MatMulNet(torch.nn.Module):
            def __init__(self):
                super(MatMulNet, self).__init__()
                self.B = torch.nn.Parameter(torch.ones(5, 3))

            def forward(self, A):
                return torch.matmul(A, torch.transpose(self.B, -1, -2))

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        A = torch.randn(2, 3)
        graph, _, __ = utils._model_to_graph(MatMulNet(), (A),
                                             do_constant_folding=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Transpose"
        assert len(list(graph.nodes())) == 1

    def test_constant_fold_reshape(self):
        class ReshapeModule(torch.nn.Module):
            def __init__(self, ):
                super(ReshapeModule, self).__init__()
                self.register_buffer("weight", torch.ones(5))

            def forward(self, x):
                b = self.weight.reshape(1, -1, 1, 1)
                return x * b

        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        x = torch.randn(4, 5)
        graph, _, __ = utils._model_to_graph(ReshapeModule(), (x, ), do_constant_folding=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Reshape"
        assert len(list(graph.nodes())) == 1

    def test_constant_fold_div(self):
        class Module(torch.nn.Module):
            def __init__(self, ):
                super(Module, self).__init__()
                self.register_buffer("weight", torch.ones(5))

            def forward(self, x):
                div = self.weight.div(torch.tensor([1, 2, 3, 4, 5]))
                return div * x

        x = torch.randn(2, 5)
        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        graph, _, __ = utils._model_to_graph(Module(), (x, ), do_constant_folding=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Div"
        assert len(list(graph.nodes())) == 1

    def test_constant_fold_mul(self):
        class Module(torch.nn.Module):
            def __init__(self, ):
                super(Module, self).__init__()
                self.register_buffer("weight", torch.ones(5))

            def forward(self, x):
                mul = self.weight.mul(torch.tensor([1, 2, 3, 4, 5]))
                return mul / x

        x = torch.randn(2, 5)
        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        graph, _, __ = utils._model_to_graph(Module(), (x, ), do_constant_folding=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Mul"
        assert len(list(graph.nodes())) == 1

    def test_constant_fold_add(self):
        class Module(torch.nn.Module):
            def __init__(self, ):
                super(Module, self).__init__()
                self.register_buffer("weight", torch.ones(5))

            def forward(self, x):
                add = self.weight + torch.tensor([1, 2, 3, 4, 5])
                return add - x

        x = torch.randn(2, 5)
        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        graph, params_dict, __ = utils._model_to_graph(
            Module(), (x, ), do_constant_folding=True,
            operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            self.assertTrue(node.kind() != "onnx::Add")
        self.assertEqual(len(list(graph.nodes())), 1)
        params = list(params_dict.values())
        self.assertEqual(len(params), 1)
        weight = params[0]
        # TODO(#38095): Replace assertEqualIgnoreType. See issue #38095
        self.assertEqualIgnoreType(weight, torch.tensor([2, 3, 4, 5, 6]))

    def test_constant_fold_sub(self):
        class Module(torch.nn.Module):
            def __init__(self, ):
                super(Module, self).__init__()
                self.register_buffer("weight", torch.ones(5))

            def forward(self, x):
                sub = self.weight - torch.tensor([1, 2, 3, 4, 5])
                return sub + x

        x = torch.randn(2, 5)
        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        graph, params_dict, __ = utils._model_to_graph(
            Module(), (x, ), do_constant_folding=True,
            operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Sub"
        self.assertEqual(len(list(graph.nodes())), 1)
        params = list(params_dict.values())
        self.assertEqual(len(params), 1)
        weight = params[0]
        # TODO(#38095): Replace assertEqualIgnoreType. See issue #38095
        self.assertEqualIgnoreType(weight, torch.tensor([0, -1, -2, -3, -4]))

    def test_constant_fold_sqrt(self):
        class Module(torch.nn.Module):
            def __init__(self, ):
                super(Module, self).__init__()
                self.register_buffer("weight", torch.ones(5))

            def forward(self, x):
                sqrt = torch.sqrt(self.weight)
                return sqrt / x

        x = torch.randn(2, 5)
        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        graph, _, __ = utils._model_to_graph(Module(), (x, ), do_constant_folding=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        for node in graph.nodes():
            assert node.kind() != "onnx::Sqrt"
        assert len(list(graph.nodes())) == 1

    def test_constant_fold_shape(self):
        class ShapeModule(torch.nn.Module):
            def __init__(self):
                super(ShapeModule, self).__init__()
                self.register_buffer("weight", torch.ones(5))

            def forward(self, x):
                shape = self.weight.shape[0]
                return x + shape

        x = torch.randn(2, 5)
        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        graph, _, __ = utils._model_to_graph(ShapeModule(), (x, ), do_constant_folding=True,
                                             _disable_torch_constant_prop=True,
                                             operator_export_type=OperatorExportTypes.ONNX)

        for node in graph.nodes():
            assert node.kind() != "onnx::Shape"
        assert len(list(graph.nodes())) == 1

    def test_strip_doc_string(self):
        class MyModule(torch.nn.Module):
            def forward(self, input):
                return torch.exp(input)
        x = torch.randn(3, 4)

        def is_model_stripped(f, strip_doc_string=None):
            if strip_doc_string is None:
                torch.onnx.export(MyModule(), x, f, opset_version=self.opset_version)
            else:
                torch.onnx.export(MyModule(), x, f, strip_doc_string=strip_doc_string,
                                  opset_version=self.opset_version)
            model = onnx.load(io.BytesIO(f.getvalue()))
            model_strip = copy.copy(model)
            onnx.helper.strip_doc_string(model_strip)
            return model == model_strip

        # test strip_doc_string=True (default)
        self.assertTrue(is_model_stripped(io.BytesIO()))
        # test strip_doc_string=False
        self.assertFalse(is_model_stripped(io.BytesIO(), False))

    # NB: remove this test once DataParallel can be correctly handled
    def test_error_on_data_parallel(self):
        model = torch.nn.DataParallel(torch.nn.ReflectionPad2d((1, 2, 3, 4)))
        x = torch.randn(1, 2, 3, 4)
        f = io.BytesIO()
        with self.assertRaisesRegex(ValueError,
                                    'torch.nn.DataParallel is not supported by ONNX '
                                    'exporter, please use \'attribute\' module to '
                                    'unwrap model from torch.nn.DataParallel. Try '):
            torch.onnx.export(model, x, f, opset_version=self.opset_version)

    def test_export_mode(self):
        class MyModule(torch.nn.Module):
            def forward(self, x):
                y = x + 1
                return y

        model = MyModule()
        x = torch.randn(10, 3, 128, 128)
        f = io.BytesIO()

        # set mode to in inference mode and export in training mode
        model.eval()
        old_state = model.training
        torch.onnx.export(model, (x,), f,
                          opset_version=self.opset_version, training=torch.onnx.TrainingMode.TRAINING)
        # verify that the model state is preserved
        assert model.training == old_state

        # set mode to training mode and export in inference mode
        model.train()
        old_state = model.training
        torch.onnx.export(model, (x,), f,
                          opset_version=self.opset_version, training=torch.onnx.TrainingMode.EVAL)
        # verify that the model state is preserved
        assert model.training == old_state

    def test_diagnose_export_mode(self):
        class MyModule(torch.nn.Module):
            def forward(self, x):
                return torch.cumsum(x, dim=0)

        model = MyModule()
        x = torch.randn(2, 3, 4)
        f = io.BytesIO()

        # run export in diagnose mode
        graph, unsupported_ops = torch.onnx._diagnose_export(model, (x,), f,
                                                             opset_version=9)
        iter = graph.nodes()
        assert next(iter).kind() == "onnx::Constant"
        assert next(iter).kind() == "prim::Constant"
        assert next(iter).kind() == "aten::cumsum"
        assert len(unsupported_ops) == 1
        assert unsupported_ops == ['aten::cumsum']

    def test_dropout_training(self):
        class MyModule(torch.nn.Module):
            def __init__(self):
                super(MyModule, self).__init__()
                self.dropout = torch.nn.Dropout(0.4)

            def forward(self, x):
                dropout = self.dropout(x)
                return dropout

        model = MyModule()
        x = torch.randn(10, 3, 128, 128)

        model.train()

        f = io.BytesIO()
        torch.onnx.export(model, (x,), f,
                          opset_version=self.opset_version, training=torch.onnx.TrainingMode.TRAINING)
        ort_sess = onnxruntime.InferenceSession(f.getvalue())
        ort_inputs = {ort_sess.get_inputs()[0].name: x.cpu().numpy()}
        ort_outs = ort_sess.run(None, ort_inputs)
        assert x != ort_outs[0]

    def test_aten_fallthrough(self):
        # Test aten export of op with no symbolic
        class Module(torch.nn.Module):
            def forward(self, x):
                return torch.triu(x)

        x = torch.randn(2, 3, 4)
        _set_opset_version(self.opset_version)
        graph, _, __ = utils._model_to_graph(Module(), (x, ),
                                             operator_export_type=OperatorExportTypes.ONNX_FALLTHROUGH)
        iter = graph.nodes()
        assert next(iter).kind() == "onnx::Constant"
        assert next(iter).kind() == "aten::triu"

    def test_custom_op_fallthrough(self):
        # Test custom op
        op_source = """
        #include <torch/script.h>

        torch::Tensor custom_add(torch::Tensor self, torch::Tensor other) {
          return self + other;
        }

        static auto registry =
          torch::RegisterOperators("custom_namespace::custom_op", &custom_add);
        """

        torch.utils.cpp_extension.load_inline(
            name="custom_add",
            cpp_sources=op_source,
            is_python_module=False,
            verbose=True,
        )

        class FooModel(torch.nn.Module):
            def forward(self, input, other):
                # Calling custom op
                return torch.ops.custom_namespace.custom_op(input, other)

        x = torch.randn(2, 3, 4, requires_grad=False)
        y = torch.randn(2, 3, 4, requires_grad=False)
        model = FooModel()
        graph, _, __ = torch.onnx.utils._model_to_graph(model, (x, y),
                                                        operator_export_type=torch.onnx.OperatorExportTypes.ONNX_FALLTHROUGH)
        iter = graph.nodes()
        assert next(iter).kind() == "custom_namespace::custom_op"

    def test_onnx_fallthrough(self):
        # Test aten export of op with symbolic for aten
        x = torch.randn(100, 128)
        y = torch.randn(100, 128)
        model = torch.nn.CosineSimilarity(dim=1, eps=1e-6)

        graph, _, __ = utils._model_to_graph(model, (x, y),
                                             operator_export_type=OperatorExportTypes.ONNX_FALLTHROUGH)
        iter = graph.nodes()
        assert next(iter).kind() == "onnx::Constant"
        assert next(iter).kind() == "onnx::Constant"
        assert next(iter).kind() == "aten::cosine_similarity"

    def test_quantized_fallthrough(self):
        # Test Quantized op
        class QModule(torch.nn.Module):
            def __init__(self):
                super(QModule, self).__init__()
                self.quant1 = torch.quantization.QuantStub()
                self.dequant = torch.quantization.DeQuantStub()

            def forward(self, x):
                res = self.quant1(x)
                return self.dequant(res)

        model = QModule()
        torch.backends.quantized.engine = "qnnpack"
        pt_inputs = (torch.randn(1, 2, 3, 4))
        model.qconfig = torch.quantization.default_qconfig
        q_model = torch.quantization.prepare(model, inplace=False)
        q_model = torch.quantization.convert(q_model, inplace=False)

        q_model.eval()
        output = q_model(*pt_inputs)

        graph, _, __ = utils._model_to_graph(q_model, pt_inputs, example_outputs=output,
                                             operator_export_type=OperatorExportTypes.ONNX_FALLTHROUGH)

        iter = graph.nodes()
        assert next(iter).kind() == "onnx::Constant"
        assert next(iter).kind() == "onnx::Constant"
        assert next(iter).kind() == "onnx::Constant"
        assert next(iter).kind() == "aten::quantize_per_tensor"
        assert next(iter).kind() == "aten::dequantize"

    def test_prim_fallthrough(self):
        # Test prim op
        class PrimModule(torch.jit.ScriptModule):
            @torch.jit.script_method
            def forward(self, x):
                if isinstance(x, list):
                    y = x
                else:
                    y = [x]
                return y

        x = torch.tensor([2])
        model = PrimModule()
        output = model(x)
        graph, _, __ = utils._model_to_graph(model, (x,), example_outputs=output,
                                             operator_export_type=OperatorExportTypes.ONNX_FALLTHROUGH)
        iter = graph.nodes()
        assert next(iter).kind() == "prim::ListConstruct"

    def test_custom_layer_tuple(self):
        class CustomFunction(torch.autograd.Function):
            @staticmethod
            def symbolic(g, input):
                return g.op('CustomNamespace::Custom', input, outputs=2)

            @staticmethod
            def forward(ctx, input):
                return input, input

        class Custom(torch.nn.Module):
            def forward(self, input):
                return CustomFunction.apply(input)

        model = Custom()
        batch = torch.FloatTensor(1, 3)

        graph, _, _ = utils._model_to_graph(model, batch)
        iter = graph.nodes()
        assert next(iter).kind() == "CustomNamespace::Custom"

    @skipIfUnsupportedMinOpsetVersion(12)
    def test_dropout_training_zero(self):
        class MyModule(torch.nn.Module):
            def __init__(self):
                super(MyModule, self).__init__()
                self.dropout = torch.nn.Dropout(0.5)

            def forward(self, x):
                dropout = self.dropout(x)
                return dropout

        torch.manual_seed(0)
        onnxruntime.set_seed(0)

        model = MyModule()

        # ensure there are no zeros in the input
        x = torch.randn(10, 3, 128, 128)
        y = x.numpy()
        y_mask = np.where(y == 0, 1, y)
        input = torch.from_numpy(y_mask)
        nb_elements = torch.numel(input)

        model.train()

        f = io.BytesIO()
        torch.onnx.export(model, (input,), f,
                          opset_version=self.opset_version, training=torch.onnx.TrainingMode.TRAINING)
        ort_sess = onnxruntime.InferenceSession(f.getvalue())
        ort_inputs = {ort_sess.get_inputs()[0].name : input.cpu().numpy()}
        ort_outs = ort_sess.run(None, ort_inputs)
        y = model(input)
        output = y.cpu().numpy()

        ort_mask = np.where(ort_outs[0] != 0, 1, 0)
        pyt_mask = np.where(output != 0, 1, 0)

        ratio_pytorch = np.sum(pyt_mask) / nb_elements
        ratio_ort = np.sum(ort_mask) / nb_elements

        np.testing.assert_allclose(ratio_pytorch, ratio_ort, rtol=0.01, atol=0.01)

    def test_unused_initializers(self):
        class Model(torch.nn.Module):
            def __init__(self):
                super(Model, self).__init__()
                self.conv2 = torch.nn.ConvTranspose2d(16, 33, (3, 5), stride=(2, 1), padding=(4, 2), dilation=(1, 1))
                self.k_proj = torch.nn.Linear(5, 5, bias=True)

            def forward(self, x):
                x = self.conv2(x)
                return x

        x = torch.randn(20, 16, 50, 100)
        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        _, params_dict, __ = utils._model_to_graph(Model(), (x, ), do_constant_folding=False,
                                                   operator_export_type=OperatorExportTypes.ONNX)

        assert len(params_dict) == 2

    def test_modifying_params(self):
        class MyModel(torch.nn.Module):
            def __init__(self):
                super(MyModel, self).__init__()
                self.param = torch.nn.Parameter(torch.tensor([2.0]))

            def forward(self, x):
                y = x * x
                self.param.data.add_(1.0)
                return y

        x = torch.tensor([1, 2])
        verify(MyModel(), x, backend, do_constant_folding=False)

    def test_fuse_conv_bn(self):
        class Fuse(torch.nn.Module):
            def __init__(self):
                super(Fuse, self).__init__()
                self.conv = torch.nn.Conv2d(3, 2, kernel_size=1, stride=2, padding=3, bias=True)
                self.bn = torch.nn.BatchNorm2d(2)

            def forward(self, x):
                out = self.conv(x)
                return self.bn(out)

        x = torch.randn(2, 3, 2, 2, requires_grad=True)
        graph, _, __ = utils._model_to_graph(Fuse(), (x, ),
                                             do_constant_folding=True,
                                             training=TrainingMode.EVAL)
        for node in graph.nodes():
            assert node.kind() != "onnx::BatchNormalization"
            assert node.kind() == "onnx::Conv"

        assert len(list(graph.nodes())) == 1

    def test_fuse_resnet18(self):
        model = torchvision.models.resnet18(pretrained=True)
        x = torch.randn(2, 3, 224, 224, requires_grad=True)
        graph, _, __ = utils._model_to_graph(model, (x, ),
                                             do_constant_folding=True)

        for node in graph.nodes():
            assert node.kind() != "onnx::BatchNormalization"

    def test_conv_bn(self):
        class MyModule(torch.nn.Module):
            def __init__(self):
                super(MyModule, self).__init__()
                self.conv = torch.nn.Conv2d(3, 16, kernel_size=1, stride=2, padding=3, bias=True)
                self.bn = torch.nn.BatchNorm2d(16, affine=True)

            def forward(self, x):
                x = self.conv(x)
                bn = self.bn(x)
                return bn

        model = MyModule()
        x = torch.randn(10, 3, 128, 128)

        f = io.BytesIO()
        torch.onnx.export(model, (x,), f,
                          opset_version=self.opset_version, training=torch.onnx.TrainingMode.TRAINING)
        ort_sess = onnxruntime.InferenceSession(f.getvalue())
        ort_inputs = {ort_sess.get_inputs()[0].name: x.cpu().numpy()}
        ort_outs1 = ort_sess.run(None, ort_inputs)

        f = io.BytesIO()
        torch.onnx.export(model, (x,), f,
                          opset_version=self.opset_version, training=torch.onnx.TrainingMode.EVAL)
        ort_sess = onnxruntime.InferenceSession(f.getvalue())
        ort_inputs = {ort_sess.get_inputs()[0].name: x.cpu().numpy()}
        ort_outs2 = ort_sess.run(None, ort_inputs)
        [np.testing.assert_allclose(ort_out1, ort_out2, atol=1e-7, rtol=0.001) for ort_out1, ort_out2 in zip(ort_outs1, ort_outs2)]

    def test_multiple_conv_bn(self):
        class MyModule(torch.nn.Module):
            def __init__(self):
                super(MyModule, self).__init__()
                self.conv1 = torch.nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
                self.conv2 = torch.nn.Conv2d(64, 2, kernel_size=1, stride=1, padding=0, bias=False)
                self.conv3 = torch.nn.Conv2d(2, 2, kernel_size=3, stride=1, padding=1, bias=False)
                self.bn = torch.nn.BatchNorm2d(64)
                self.bn2 = torch.nn.BatchNorm2d(2)
                self.relu = torch.nn.ReLU(inplace=True)
                self.maxpool = torch.nn.MaxPool2d(kernel_size=3, stride=2, padding=1)


            def forward(self, x):
                x = self.conv1(x)
                x = self.bn(x)
                x = self.relu(x)
                x = self.maxpool(x)
                x = self.conv2(x)
                x = self.bn2(x)
                x = self.relu(x)
                x = self.conv3(x)
                x = self.bn2(x)
                x = self.relu(x)
                return x

        model = MyModule()
        x = torch.randn(2, 3, 224, 224)

        f = io.BytesIO()
        torch.onnx.export(model, (x,), f,
                          opset_version=self.opset_version, training=torch.onnx.TrainingMode.TRAINING)
        ort_sess = onnxruntime.InferenceSession(f.getvalue())
        ort_inputs = {ort_sess.get_inputs()[0].name: x.cpu().numpy()}
        ort_outs1 = ort_sess.run(None, ort_inputs)
        f = io.BytesIO()
        torch.onnx.export(model, (x,), f,
                          opset_version=self.opset_version, training=torch.onnx.TrainingMode.EVAL)
        ort_sess = onnxruntime.InferenceSession(f.getvalue())
        ort_inputs = {ort_sess.get_inputs()[0].name: x.cpu().numpy()}
        ort_outs2 = ort_sess.run(None, ort_inputs)
        [np.testing.assert_allclose(ort_out1, ort_out2, atol=1e-7, rtol=0.001) for ort_out1, ort_out2 in zip(ort_outs1, ort_outs2)]

    def test_onnx_function_substitution_pass(self):

        @torch.jit.script
        def f(x : torch.Tensor, y : torch.Tensor):
            z = x - y
            return x + z

        class MyModule(torch.nn.Module):
            def __init__(self):
                super(MyModule, self).__init__()

            def forward(self, x, y):
                return f(x, y)

        model = MyModule()
        input_1 = torch.tensor(11)
        input_2 = torch.tensor(12)
        _set_opset_version(self.opset_version)
        _set_operator_export_type(OperatorExportTypes.ONNX)
        graph, _, __ = utils._model_to_graph(MyModule(), (input_1, input_2), do_constant_folding=True,
                                             operator_export_type=OperatorExportTypes.ONNX)
        # Check that the prim::Constant node in the graph for representing the
        # scripted function `f` is removed and the following prim::CallFunction
        # is replced by inline graph, with onnx::Sub and onnx::Add nodes.
        for node in graph.nodes():
            assert node.kind() != "prim::Constant"
        assert len(list(graph.nodes())) == 2  # onnx::Sub and onnx::Add nodes only.

# opset 10 tests
TestUtilityFuns_opset10 = type(str("TestUtilityFuns_opset10"),
                               (TestCase,),
                               dict(TestUtilityFuns.__dict__, opset_version=10))


# opset 11 tests
TestUtilityFuns_opset11 = type(str("TestUtilityFuns_opset11"),
                               (TestCase,),
                               dict(TestUtilityFuns.__dict__, opset_version=11))

# opset 12 tests
TestUtilityFuns_opset12 = type(str("TestUtilityFuns_opset12"),
                               (TestCase,),
                               dict(TestUtilityFuns.__dict__, opset_version=12))


if __name__ == '__main__':
    run_tests()
