"""
convolutional nodes
"""

from __future__ import division, absolute_import
from __future__ import print_function, unicode_literals

import toolz
import numpy as np
import theano
import theano.tensor as T

from .. import core


def conv_output_length(input_size, conv_size, stride, pad):
    """
    calculates the output size along a single axis for a conv operation
    """
    if input_size is None:
        return None
    without_stride = input_size + 2 * pad - conv_size + 1
    # equivalent to np.ceil(without_stride / stride)
    output_size = (without_stride + stride - 1) // stride
    return output_size


def conv_output_shape(input_shape,
                      num_filters,
                      axes,
                      conv_shape,
                      strides,
                      pads):
    """
    compute output shape for a conv
    """
    output_shape = list(input_shape)
    assert 1 not in axes
    output_shape[1] = num_filters
    for axis, conv_size, stride, pad in zip(axes,
                                            conv_shape,
                                            strides,
                                            pads):
        output_shape[axis] = conv_output_length(input_shape[axis],
                                                conv_size,
                                                stride,
                                                pad)
    return tuple(output_shape)


def conv_parse_pad(filter_size, pad):
    if pad == "valid":
        return (0,) * len(filter_size)
    elif pad == "full":
        return tuple([x - 1 for x in filter_size])
    elif pad == "same":
        new_pad = []
        for f in filter_size:
            assert f % 2
            new_pad += [f // 2]
        return tuple(new_pad)
    else:
        assert len(pad) == len(filter_size)
        return pad


@core.register_node("conv_2d")
class Conv2DNode(core.NodeImpl):

    """
    node for 2D convolution
    """

    hyperparameter_names = ("inits",
                            "num_filters",
                            "filter_size",
                            "conv_stride",
                            "stride",
                            "conv_pad",
                            "pad")

    def compute_output(self, network, in_vw):
        # gather hyperparameters
        num_filters = network.find_hyperparameter(["num_filters"])
        filter_size = network.find_hyperparameter(["filter_size"])
        stride = network.find_hyperparameter(["conv_stride", "stride"],
                                             (1, 1))
        pad = network.find_hyperparameter(["conv_pad", "pad"], "valid")
        inits = list(toolz.concat(network.find_hyperparameters(
            ["inits"],
            [])))
        assert len(filter_size) == 2
        assert pad in ["valid", "full"]

        # create weight
        num_channels = in_vw.shape[1]
        filter_shape = (num_filters, num_channels) + tuple(filter_size)
        W = network.create_variable(
            name="weight",
            is_shared=True,
            shape=filter_shape,
            tags={"parameter", "weight"},
            inits=inits,
        ).variable

        out_var = T.nnet.conv2d(input=in_vw.variable,
                                filters=W,
                                image_shape=in_vw.shape,
                                filter_shape=filter_shape,
                                border_mode=pad,
                                subsample=stride)

        out_shape = conv_output_shape(input_shape=in_vw.shape,
                                      num_filters=num_filters,
                                      axes=(2, 3),
                                      conv_shape=filter_size,
                                      strides=stride,
                                      pads=conv_parse_pad(filter_size, pad))

        network.create_variable(
            "default",
            variable=out_var,
            shape=out_shape,
            tags={"output"},
        )
