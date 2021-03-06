import pytest

import tensorflow as tf
from tensorflow.keras import layers

import numpy as np
from numpy.testing import assert_allclose

import nfp

def test_slice():

    connectivity = layers.Input(shape=[None, 2], dtype=tf.int64, name='connectivity')

    out0 = nfp.Slice(np.s_[:, :, 0])(connectivity)
    out1 = nfp.Slice(np.s_[:, :, 1])(connectivity)

    model = tf.keras.Model([connectivity], [out0, out1])
    inputs = np.array([[1, 2, 3, 4, 5], [6, 7, 8, 9, 0]]).T
    inputs = inputs[np.newaxis, :, :]

    out = model(inputs)

    assert_allclose(out[0], inputs[:, :, 0])
    assert_allclose(out[1], inputs[:, :, 1])


def test_gather():

    in1 = layers.Input(shape=[None], dtype='float', name='data')
    in2 = layers.Input(shape=[None], dtype=tf.int64, name='indices')

    gather = nfp.Gather()([in1, in2])

    model = tf.keras.Model([in1, in2], [gather])

    data = np.random.rand(2, 10).astype(np.float32)
    indices = np.array([[2, 6, 3], [5, 1, 0]])
    out = model([data, indices])

    assert_allclose(out, np.vstack([data[0, indices[0]], data[1, indices[1]]]))


@pytest.mark.parametrize('method', ['sum', 'mean', 'max', 'min', 'prod'])
def test_reduce(smiles_inputs, method):

    preprocessor, inputs = smiles_inputs
    func = getattr(np, method)

    atom_class = layers.Input(shape=[None], dtype=tf.int64, name='atom')
    bond_class = layers.Input(shape=[None], dtype=tf.int64, name='bond')
    connectivity = layers.Input(shape=[None, 2], dtype=tf.int64, name='connectivity')

    atom_embed = layers.Embedding(preprocessor.atom_classes, 16, mask_zero=True)(atom_class)
    bond_embed = layers.Embedding(preprocessor.bond_classes, 16, mask_zero=True)(bond_class)

    reduced = nfp.Reduce(method)([
        bond_embed, nfp.Slice(np.s_[:, :, 0])(connectivity), atom_embed])

    model = tf.keras.Model([atom_class, bond_class, connectivity],
                           [atom_embed, bond_embed, reduced])

    atom_state, bond_state, atom_reduced =  model([inputs['atom'], inputs['bond'],
                                                   inputs['connectivity']])

    assert_allclose(atom_reduced[0, 0, :], func(bond_state[0, :4, :], 0))
    assert_allclose(atom_reduced[0, 1, :], func(bond_state[0, 4:8, :], 0))
    assert_allclose(atom_reduced[0, 2, :], bond_state[0, 9, :], 0)
    assert_allclose(atom_reduced[0, 3, :], bond_state[0, 10, :], 0)
    assert_allclose(atom_reduced[0, 4, :], bond_state[0, 11, :], 0)
    assert_allclose(atom_reduced[0, 5, :], bond_state[0, 12, :], 0)
    # assert_allclose(atom_reduced[0, 8:, :], 0.)
