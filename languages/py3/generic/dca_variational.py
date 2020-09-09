import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

from keras.datasets import fashion_mnist


# Set random seed for reproducibility
np.random.seed(1000)
tf.set_random_seed(1000)


nb_samples = 1000
nb_epochs = 400
batch_size = 200
code_length = 256


if __name__ == '__main__':
    # Load the dataset
    (X_train, _), (_, _) = fashion_mnist.load_data()
    X_train = X_train.astype(np.float32)[0:nb_samples] / 255.0

    width = X_train.shape[1]
    height = X_train.shape[2]

    graph = tf.Graph()

    with graph.as_default():
        input_images = tf.placeholder(tf.float32, shape=(batch_size, width, height, 1))

        # Encoder
        conv_0 = tf.layers.conv2d(inputs=input_images,
                                  filters=32,
                                  kernel_size=(3, 3),
                                  strides=(2, 2),
                                  activation=tf.nn.relu,
                                  padding='same')

        conv_1 = tf.layers.conv2d(inputs=conv_0,
                                  filters=64,
                                  kernel_size=(3, 3),
                                  strides=(2, 2),
                                  activation=tf.nn.relu,
                                  padding='same')

        conv_2 = tf.layers.conv2d(inputs=conv_1,
                                  filters=128,
                                  kernel_size=(3, 3),
                                  activation=tf.nn.relu,
                                  padding='same')

        # Code layer
        code_input = tf.layers.flatten(inputs=conv_2)

        code_mean = tf.layers.dense(inputs=code_input,
                                    units=width * height)

        code_log_variance = tf.layers.dense(inputs=code_input,
                                            units=width * height)

        code_std = tf.sqrt(tf.exp(code_log_variance))

        # Normal samples
        normal_samples = tf.random_normal(mean=0.0, stddev=1.0, shape=(batch_size, width * height))

        # Sampled code
        sampled_code = (normal_samples * code_std) + code_mean

        # Decoder
        decoder_input = tf.reshape(sampled_code, (-1, 7, 7, 16))

        convt_0 = tf.layers.conv2d_transpose(inputs=decoder_input,
                                             filters=64,
                                             kernel_size=(3, 3),
                                             strides=(2, 2),
                                             activation=tf.nn.relu,
                                             padding='same')

        convt_1 = tf.layers.conv2d_transpose(inputs=convt_0,
                                             filters=32,
                                             kernel_size=(3, 3),
                                             strides=(2, 2),
                                             activation=tf.nn.relu,
                                             padding='same')

        convt_2 = tf.layers.conv2d_transpose(inputs=convt_1,
                                             filters=1,
                                             kernel_size=(3, 3),
                                             padding='same')

        convt_output = tf.nn.sigmoid(convt_2)

        # Loss
        reconstruction = tf.nn.sigmoid_cross_entropy_with_logits(logits=convt_2, labels=input_images)
        kl_divergence = 0.5 * tf.reduce_sum(
            tf.square(code_mean) + tf.square(code_std) - tf.log(1e-8 + tf.square(code_std)) - 1, axis=1)

        loss = tf.reduce_sum(reconstruction) + kl_divergence

        # Training step
        training_step = tf.train.AdamOptimizer(0.001).minimize(loss)

    # Train the model
    session = tf.InteractiveSession(graph=graph)
    tf.global_variables_initializer().run()

    for e in range(nb_epochs):
        np.random.shuffle(X_train)

        total_loss = 0.0

        for i in range(0, nb_samples - batch_size, batch_size):
            X = np.zeros((batch_size, width, height, 1), dtype=np.float32)
            X[:, :, :, 0] = X_train[i:i + batch_size, :, :]

            _, n_loss = session.run([training_step, loss],
                                    feed_dict={
                                        input_images: X
                                    })
            total_loss += n_loss

        print('Epoch {}) Total loss: {}'.format(e + 1, total_loss))

    # Show some results
    Xs = np.reshape(X_train[0:batch_size], (batch_size, width, height, 1))

    Ys = session.run([convt_output],
                     feed_dict={
                         input_images: Xs
                     })

    Ys = np.squeeze(Ys[0] * 255.0)

    fig, ax = plt.subplots(2, 10, figsize=(18, 4))

    for i in range(10):
        ax[0, i].imshow(Ys[i], cmap='gray')
        ax[0, i].set_xticks([])
        ax[0, i].set_yticks([])

        ax[1, i].imshow(Ys[i + 10], cmap='gray')
        ax[1, i].set_xticks([])
        ax[1, i].set_yticks([])

    plt.show()

    session.close()
