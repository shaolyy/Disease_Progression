# coding=utf-8
import numpy as np
import tensorflow as tf
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import math_ops
from tensorflow.python.ops import nn_ops


class RevisedGRUCell(object):
    """
    compared to standard rnn cell, this version of gru can accept time information directly
    """

    def __init__(self, hidden_state, initial_strategy_map, name, activation):
        """
        :param hidden_state
        :param initial_strategy_map: should contain initializer objects with key gate_weight, gate_bias,
        candidate_weight, candidate_bias
        :param name:
        :param activation: name of activation function
        """
        self.__hidden_state = hidden_state
        self.__name = name
        self.__initial_strategy_map = initial_strategy_map
        self.__activation_name = activation
        if self.__activation_name == 'tanh':
            self.__activation = tf.tanh
        elif self.__activation_name == 'sigmoid':
            self.__activation_name = tf.sigmoid
        elif self.__activation_name == 'relu':
            self.__activation = tf.nn.relu
        else:
            raise ValueError('The activation should be "tanh", "sigmoid" or "relu"')

        self.__parameter_check()

    def __call__(self, input_x, input_t, previous_sate):
        """
        :param input_x: tf.placeholder with shape [batch_size, input_x_depth], dtype=tf.float64
        :param input_t: tf.placeholder a matrix with shape [batch_size, input_t_depth], dtype=tf.float64
        :param previous_sate: the previous hidden states is a tensor with size [batch_size, hidden_state],
        dtype=tf.float64. if the previous state is the zero state, the size should be [batch_size,], dtype=tf.float64.
        :return: new hidden state with size [batch_size, hidden_state], dtype=tf.float64.
        """
        if (previous_sate.shape.dims == 1 and previous_sate.shape[0].value != self.__hidden_state) or \
                (previous_sate.shape.dims == 2 and previous_sate.shape[1].value != self.__hidden_state):
            raise ValueError('previous state/ zero state size incompatible')

        # get predefined variable
        td = input_t.shape[1].value
        hs = self.__hidden_state
        xd = input_x.shape[1].value
        gw = self.__initial_strategy_map['gate_weight']
        gb = self.__initial_strategy_map['gate_bias']
        cw = self.__initial_strategy_map['candidate_weight']
        cb = self.__initial_strategy_map['candidate_bias']

        # define the parameter a GRU cell
        with tf.variable_scope("cell_para", reuse=tf.AUTO_REUSE):
            gate_weight = tf.get_variable(name='gate_weight', shape=[td, hs * 2], initializer=gw, dtype=tf.float64)
            gate_bias = tf.get_variable(name='gate_bias', shape=[hs * 2], initializer=gb, dtype=tf.float64)
            candidate_weight = tf.get_variable(name='candidate_weight', shape=[xd + hs, hs], initializer=cw,
                                               dtype=tf.float64)
            candidate_bias = tf.get_variable(name='candidate_bias', shape=[hs], initializer=cb, dtype=tf.float64)

        with tf.name_scope('gate_calc'):
            gate_value = math_ops.matmul(input_t, gate_weight)
            gate_value = nn_ops.bias_add(gate_value, gate_bias)
            gate_value = math_ops.sigmoid(gate_value)

        with tf.name_scope('gate_split'):
            r, u = array_ops.split(value=gate_value, num_or_size_splits=2, axis=1)
            r_state = r * previous_sate

        with tf.name_scope('candidate_calc'):
            concat = array_ops.concat([input_x, r_state], axis=1)
            candidate = math_ops.matmul(concat, candidate_weight, name='candidate_matmul')
            candidate = nn_ops.bias_add(candidate, candidate_bias, name='candidate_bias_add')
            c = self.__activation(candidate)

        with tf.name_scope('new_state'):
            new_h = u * previous_sate + (1 - u) * c

        return new_h

    def __parameter_check(self):
        """
        This function is used to examine whether the parameters are legal
        """
        legal_flag = True

        hidden_state = self.__hidden_state
        name = self.__name

        if hidden_state < 0 or not isinstance(hidden_state, int):
            legal_flag = False

        if name is not None and not isinstance(name, str):
            legal_flag = False

        if not legal_flag:
            raise Exception('the format of parameter is not right')


def unit_test():
    """
    :return:
    """
    time_stamp = 5
    batch_size = None
    x_depth = 4
    t_depth = 1
    hidden_state = 16
    activation = 'tanh'
    name = 'revised_gru'
    x = tf.placeholder(name='x', shape=[time_stamp, batch_size, x_depth], dtype=tf.float64)
    t = tf.placeholder(name='x', shape=[time_stamp, batch_size, t_depth], dtype=tf.float64)
    zero_state = tf.convert_to_tensor(np.random.normal(0, 1, [hidden_state]))
    init = dict()
    init['gate_weight'] = tf.random_normal_initializer(0, 1)
    init['gate_bias'] = tf.random_normal_initializer(0, 1)
    init['candidate_weight'] = tf.random_normal_initializer(0, 1)
    init['candidate_bias'] = tf.random_normal_initializer(0, 1)
    x_list = tf.unstack(x, axis=0)
    t_list = tf.unstack(t, axis=0)
    rgru_cell = RevisedGRUCell(hidden_state=hidden_state, initial_strategy_map=init, name=name, activation=activation)
    state = zero_state

    for i in range(0, len(x_list)):
        state = rgru_cell(input_x=x_list[i], input_t=t_list[i], previous_sate=state)


if __name__ == '__main__':
    unit_test()
