from plato.tools.rbm import simple_rbm
from plato.tools.networks import StochasticLayer, FullyConnectedBridge
from plato.tools.optimizers import SimpleGradientDescent
from plotting.live_plotting import LiveStream
import theano
from utils.datasets.mnist import get_mnist_dataset
import numpy as np

__author__ = 'peter'


def demo_rbm():
    """
    In this demo we train an RBM on the MNIST input data (labels are ignored).  We plot the state of a markov chanin
    that is being simulaniously sampled from the RBM, and the parameters of the RBM.

    As learning progresses, we should see that the samples from the markov chain look increasingly like the data.

    TODO: Nicer way to access parameters.  Possibly just visualize persistent training chain instead of independent free
    sampling chain.
    """
    minibatch_size = 10

    dataset = get_mnist_dataset().process_with(inputs_processor=lambda (x, ): (x.reshape(x.shape[0], -1), ))

    rbm = simple_rbm(
        visible_layer = StochasticLayer('bernoulli'),
        bridge=FullyConnectedBridge(w = 0.001*np.random.randn(28*28, 500).astype(theano.config.floatX)),
        hidden_layer = StochasticLayer('bernoulli')
        )

    train_function = rbm.get_training_fcn(n_gibbs = 4, persistent = True, optimizer = SimpleGradientDescent(eta = 0.01)).compile()
    # sampling_function = rbm.get_free_sampling_fcn(init_visible_state = np.random.randn(9, 28*28), return_smooth_visible = True).compile()

    def debug_variable_setter():
        locvars = train_function.symbolic.locals()
        return {
            'hidden': locvars['hidden_layer'].reshape(-1, 25, 20),
            'visible': locvars['hidden_layer'].smooth(locvars['bridge'](locvars['sleep_hidden'])).reshape(-1, 28, 28),
            'w': locvars['bridge'].parameters[0],
            'b': locvars['bridge'].parameters[1],
            'b_rev': locvars['bridge'].parameters[2],
            }
    train_function.set_debug_variables(debug_variable_setter)

    stream = LiveStream(train_function.get_debug_values, update_every=10)
    for _, visible_data, _ in dataset.training_set.minibatch_iterator(minibatch_size = minibatch_size, epochs = 10, single_channel = True):
        # visible, hidden = sampling_function()
        train_function(visible_data)
        stream.update()


if __name__ == '__main__':

    demo_rbm()
