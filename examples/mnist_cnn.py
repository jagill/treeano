from __future__ import division, absolute_import
from __future__ import print_function, unicode_literals

import time
import numpy as np
import sklearn.datasets
import sklearn.cross_validation
import sklearn.metrics
import theano
import theano.tensor as T
import treeano
import treeano.nodes as tn
import treeano.lasagne.nodes as tl
import canopy

fX = theano.config.floatX

# ############################### prepare data ###############################

mnist = sklearn.datasets.fetch_mldata('MNIST original')
# theano has a constant float type that it uses (float32 for GPU)
# also rescaling to [0, 1] instead of [0, 255]
X = mnist['data'].reshape(-1, 1, 28, 28).astype(fX) / 255.0
y = mnist['target'].astype("int32")
X_train, X_valid, y_train, y_valid = sklearn.cross_validation.train_test_split(
    X, y, random_state=42)
in_train = {"x": X_train, "y": y_train}
in_valid = {"x": X_valid, "y": y_valid}

# ############################## prepare model ##############################
# architecture:
# - 5x5 conv, 32 filters
# - ReLU
# - 2x2 maxpool
# - 5x5 conv, 32 filters
# - ReLU
# - 2x2 maxpool
# - fully connected layer - 256 units
# - 50% dropout
# - fully connected layer- 10 units
# - softmax

# - the batch size can be provided as `None` to make the network
#   work for multiple different batch sizes
model = tn.HyperparameterNode(
    "model",
    tn.SequentialNode(
        "seq",
        [tn.InputNode("x", shape=(None, 1, 28, 28)),
         tl.Conv2DNode("conv1"),
         tn.ReLUNode("relu1"),
         tl.MaxPool2DNode("mp1"),
         tl.Conv2DNode("conv2"),
         tn.ReLUNode("relu2"),
         tl.MaxPool2DNode("mp2"),
         tn.DenseNode("fc1"),
         tn.DropoutNode("do1"),
         tn.DenseNode("fc2", num_units=10),
         tn.SoftmaxNode("pred"),
         ]),
    num_filters=32,
    filter_size=(5, 5),
    pool_size=(2, 2),
    num_units=256,
    dropout_probability=0.5,
    inits=[treeano.inits.XavierNormalInit()],
)

with_updates = tn.HyperparameterNode(
    "with_updates",
    tn.AdamNode(
        "adam",
        {"subtree": model,
         "cost": tn.PredictionCostNode("cost", {
             "pred": tn.ReferenceNode("pred_ref", reference="model"),
             "target": tn.InputNode("y", shape=(None,), dtype="int32")},
         )}),
    loss_function=treeano.utils.categorical_crossentropy_i32,
)
network = with_updates.network()
network.build()  # build eagerly to share weights

BATCH_SIZE = 500
train_fn = canopy.handled_fn(
    network,
    [canopy.handlers.chunk_variables(batch_size=BATCH_SIZE,
                                     variables=["x", "y"])],
    {"x": "x", "y": "y"},
    {"cost": "cost"},
    include_updates=True)

valid_fn = canopy.handled_fn(
    network,
    [canopy.handlers.override_hyperparameters(dropout_probability=0),
     canopy.handlers.chunk_variables(batch_size=BATCH_SIZE,
                                     variables=["x", "y"])],
    {"x": "x", "y": "y"},
    {"cost": "cost", "pred": "pred"})


# ################################# training #################################

print("Starting training...")

NUM_EPOCHS = 25
for epoch_num in range(NUM_EPOCHS):
    start_time = time.time()
    train_loss = train_fn(in_train)["cost"]
    valid_out = valid_fn(in_valid)
    valid_loss, probabilities = valid_out["cost"], valid_out["pred"]
    predicted_classes = np.argmax(probabilities, axis=1)
    # calculate accuracy for this epoch
    accuracy = sklearn.metrics.accuracy_score(y_valid, predicted_classes)
    total_time = time.time() - start_time
    print("Epoch: %d, train_loss=%f, valid_loss=%f, accuracy=%f, time=%fs"
          % (epoch_num + 1, train_loss, valid_loss, accuracy, total_time))
