# A Tutorial on Autoencoders
# Copyright (C) 2020  Abien Fred Agarap and Richard Ralph Ricardo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Also add information on how to contact you by electronic and paper mail.
#
# If your software can interact with users remotely through a computer
# network, you should also make sure that it provides a way for users to
# get its source.  For example, if your program is a web application, its
# interface could display a "Source" link that leads users to an archive
# of the code.  There are many ways you could offer source, and different
# solutions will be better for different programs; see section 13 for the
# specific requirements.
#
# You should also get your employer (if you work as a programmer) or school,
# if any, to sign a "copyright disclaimer" for the program, if necessary.
# For more information on this, and how to apply and follow the GNU AGPL, see
# <http://www.gnu.org/licenses/>.
"""TensorFlow 2.0 implementation of LeNet-based variational autoencoder"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__version__ = "1.0.0"
__author__ = "Abien Fred Agarap"

import tensorflow as tf


class CVAE(tf.keras.Model):
    def __init__(self, **kwargs):
        super(CVAE, self).__init__()
        self.encoder = Encoder(
            input_shape=kwargs["input_shape"], latent_dim=kwargs["latent_dim"]
        )
        self.decoder = Decoder(latent_dim=kwargs["latent_dim"])

    @tf.function
    def call(self, features):
        z_mean, z_log_var, z = self.encoder(features)
        reconstructed = self.decoder(z)
        kl_divergence = -5e-2 * tf.reduce_sum(
            tf.exp(z_log_var) + tf.square(z_mean) - 1 - z_log_var
        )
        self.add_loss(kl_divergence)
        return reconstructed


class Encoder(tf.keras.layers.Layer):
    def __init__(self, **kwargs):
        super(Encoder, self).__init__()
        self.input_layer = tf.keras.layers.InputLayer(input_shape=kwargs["input_shape"])
        self.conv_layer_1 = tf.keras.layers.Conv2D(
            filters=6, kernel_size=5, strides=(2, 2), activation=tf.nn.relu
        )
        self.conv_layer_2 = tf.keras.layers.Conv2D(
            filters=16, kernel_size=5, strides=(2, 2), activation=tf.nn.relu
        )
        self.flatten = tf.keras.layers.Flatten()
        self.z_mean_layer = tf.keras.layers.Dense(units=kwargs["latent_dim"])
        self.z_log_var_layer = tf.keras.layers.Dense(units=kwargs["latent_dim"])
        self.sampling = Sampling()

    def call(self, features):
        features = self.input_layer(features)
        activation = self.conv_layer_1(features)
        activation = self.conv_layer_2(activation)
        activation = self.flatten(activation)
        z_mean = self.z_mean_layer(activation)
        z_log_var = self.z_log_var_layer(activation)
        z = self.sampling((z_mean, z_log_var))
        return z_mean, z_log_var, z


class Decoder(tf.keras.layers.Layer):
    def __init__(self, **kwargs):
        super(Decoder, self).__init__()
        self.input_layer = tf.keras.layers.InputLayer(
            input_shape=(kwargs["latent_dim"],)
        )
        self.hidden_layer_1 = tf.keras.layers.Dense(
            units=(7 * 7 * 6), activation=tf.nn.relu
        )
        self.reshape_layer = tf.keras.layers.Reshape(target_shape=(7, 7, 6))
        self.convt_layer_1 = tf.keras.layers.Conv2DTranspose(
            filters=16,
            kernel_size=5,
            strides=(2, 2),
            padding="same",
            activation=tf.nn.relu,
        )
        self.convt_layer_2 = tf.keras.layers.Conv2DTranspose(
            filters=6,
            kernel_size=5,
            strides=(2, 2),
            padding="same",
            activation=tf.nn.relu,
        )
        self.output_layer = tf.keras.layers.Conv2DTranspose(
            filters=1,
            kernel_size=5,
            strides=(1, 1),
            padding="same",
            activation=tf.nn.sigmoid,
        )

    def call(self, features):
        features = self.input_layer(features)
        activation = self.hidden_layer_1(features)
        activation = self.reshape_layer(activation)
        activation = self.convt_layer_1(activation)
        activation = self.convt_layer_2(activation)
        output = self.output_layer(activation)
        return output


class Sampling(tf.keras.layers.Layer):
    def call(self, args):
        z_mean, z_log_var = args
        batch = tf.shape(z_mean)[0]
        dimension = tf.shape(z_mean)[1]
        epsilon = tf.random.normal(shape=(batch, dimension), mean=0.0, stddev=1.0)
        return z_mean + epsilon + tf.exp(5e-1 * z_log_var)
