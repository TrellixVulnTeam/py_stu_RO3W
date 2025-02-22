import tensorflow as tf
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
from tensorflow.keras import datasets, layers, optimizers, Sequential, metrics, regularizers

from tensorflow.keras.applications.resnet50 import ResNet50
from tensorflow.keras.preprocessing.image import ImageDataGenerator

gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=0.4)

cpu_num = 16
config = tf.compat.v1.ConfigProto(device_count={"CPU": cpu_num},
                                  gpu_options=gpu_options,
                                  inter_op_parallelism_threads=cpu_num,
                                  intra_op_parallelism_threads=cpu_num,
                                  log_device_placement=True)
session = tf.compat.v1.Session(config=config)

tf.random.set_seed(23554)


def preprocess(x, y):
    x = tf.cast(x, dtype=tf.float32) / 255.
    y = tf.cast(y, dtype=tf.int32)
    return x, y


# (x, y), (x_test, y_test) = datasets.cifar100.load_data()
(x, y), (x_test, y_test) = datasets.cifar10.load_data()

y = tf.squeeze(y, axis=1)
y_test = tf.squeeze(y_test, axis=1)
image_gen_train = ImageDataGenerator(  # 数据增强
    rescale=1.0/255,  # 归至0～1
    rotation_range=90,  # 随机0度旋转
    width_shift_range=0.6,  # 宽度偏移
    height_shift_range=0.6,  # 高度偏移
    horizontal_flip=True,  # 水平翻转
    zoom_range=0.8  # 将图像随机缩放到100％
)
image_gen_train.fit(x)

print(x.shape, y.shape, x_test.shape, y_test.shape)

# train_db = tf.images.Dataset.from_tensor_slices((x, y))
# train_db = train_db.shuffle(10000).map(preprocess).batch(128)
# test_db = tf.images.Dataset.from_tensor_slices((x_test, y_test))
# test_db = test_db.map(preprocess).batch(128)

import matplotlib.pyplot as plt
import pandas as pd


def plot_learning_curves(history, label, epochs, min_value, max_value):
    data = {}
    data[label] = history.history[label]
    data['val_' + label] = history.history['val_' + label]
    pd.DataFrame(data).plot(figsize=(8, 5))
    plt.grid(True)
    plt.axis([0, epochs, min_value, max_value])
    plt.savefig(os.path.basename(__file__) + '_' + label + '.jpg')
    plt.show()


epochs = 200


def main():
    model = ResNet50(
        weights=None,
        classes=10,
        input_shape=(32, 32, 3)
    )
    model.compile(optimizer=tf.keras.optimizers.SGD(learning_rate=1e-4),
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    model.build(input_shape=(None, 32, 32, 3))
    model.summary()
    history = model.fit(image_gen_train.flow(x, y, batch_size=64),
                        batch_size=128, epochs=epochs,
                        validation_data=(x_test, y_test),
                        validation_freq=1, verbose=1, shuffle=True)

    plot_learning_curves(history, 'accuracy', epochs, 0, 1)
    plot_learning_curves(history, 'loss', epochs, 0, 10)


main()
