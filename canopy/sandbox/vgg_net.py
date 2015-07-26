"""
see http://www.vlfeat.org/matconvnet/pretrained/ for model files
"""
import numpy as np
import scipy.io
import treeano
import treeano.nodes as tn
import treeano.lasagne.nodes as tl


def vgg_16_nodes(conv_only):
    """
    conv_only:
    whether or not to only return conv layers (before FC layers)
    """
    assert conv_only

    # NOTE: using Conv2DDNNNode's because the network uses "same" convs
    return tn.HyperparameterNode(
        "vgg16",
        tn.SequentialNode(
            "vgg16_seq",
            [tn.HyperparameterNode(
                "conv_group_1",
                tn.SequentialNode(
                    "conv_group_1_seq",
                    [tl.Conv2DDNNNode("conv1_1"),
                     tn.ReLUNode("relu1_1"),
                     tl.Conv2DDNNNode("conv1_2"),
                     tn.ReLUNode("relu1_2")]),
                num_filters=64),
             tl.MaxPool2DNode("pool1"),
             tn.HyperparameterNode(
                "conv_group_2",
                tn.SequentialNode(
                    "conv_group_2_seq",
                    [tl.Conv2DDNNNode("conv2_1"),
                     tn.ReLUNode("relu2_1"),
                     tl.Conv2DDNNNode("conv2_2"),
                     tn.ReLUNode("relu2_2")]),
                 num_filters=128),
             tl.MaxPool2DNode("pool2"),
             tn.HyperparameterNode(
                "conv_group_3",
                tn.SequentialNode(
                    "conv_group_3_seq",
                    [tl.Conv2DDNNNode("conv3_1"),
                     tn.ReLUNode("relu3_1"),
                     tl.Conv2DDNNNode("conv3_2"),
                     tn.ReLUNode("relu3_2"),
                     tl.Conv2DDNNNode("conv3_3"),
                     tn.ReLUNode("relu3_3")]),
                 num_filters=256),
             tl.MaxPool2DNode("pool3"),
             tn.HyperparameterNode(
                "conv_group_4",
                tn.SequentialNode(
                    "conv_group_4_seq",
                    [tl.Conv2DDNNNode("conv4_1"),
                     tn.ReLUNode("relu4_1"),
                     tl.Conv2DDNNNode("conv4_2"),
                     tn.ReLUNode("relu4_2"),
                     tl.Conv2DDNNNode("conv4_3"),
                     tn.ReLUNode("relu4_3")]),
                 num_filters=512),
             tl.MaxPool2DNode("pool4"),
             tn.HyperparameterNode(
                "conv_group_5",
                tn.SequentialNode(
                    "conv_group_5_seq",
                    [tl.Conv2DDNNNode("conv5_1"),
                     tn.ReLUNode("relu5_1"),
                     tl.Conv2DDNNNode("conv5_2"),
                     tn.ReLUNode("relu5_2"),
                     tl.Conv2DDNNNode("conv5_3"),
                     tn.ReLUNode("relu5_3")]),
                 num_filters=512),
             tl.MaxPool2DNode("pool5"),
             # TODO add dense nodes
             ]),
        border_mode="same",
        filter_size=(3, 3),
        pool_size=(2, 2),
    )


idx_dict = {
    16: [0, 2, 5, 7, 10, 12, 14, 17, 19, 21, 24, 26, 28,  # convs
         31, 33, 35],  # fcs
    19: [0, 2, 5, 7, 10, 12, 14, 16, 19, 21, 23, 25, 28, 30, 32, 34,  # convs
         37, 39, 41],  # fcs
}


def vgg_value_dict(mat_file="imagenet-vgg-verydeep-16.mat", model=16):
    """
    based on:
    https://github.com/317070/Twitch-plays-LSD-neural-net/blob/master/mat2npy.py
    """
    idxs = idx_dict[model]

    data = scipy.io.loadmat(mat_file)

    # TODO do something with this?
    classes = data["classes"][0][0].tolist()[1][0]

    # TODO do something with this?
    mean = data['normalization'][0][0][0]

    value_dict = {}
    for idx in idxs:
        layer_name = data['layers'][0][idx][0][0][-2][0]
        W = data['layers'][0][idx][0][0][0][0][0]
        # FIXME test this that it matches up with an actual model
        W = np.transpose(W, (3, 2, 0, 1))
        # W = W[:,:,::-1,::-1]
        b = data['layers'][0][idx][0][0][0][0][1][0]
        print(dict(
            idx=idx,
            name=layer_name,
            W_shape=W.shape,
            b_shape=b.shape,
        ))
        value_dict[layer_name + ":W"] = W
        value_dict[layer_name + ":b"] = b

    return {"values": value_dict}
