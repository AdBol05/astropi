import tensorflow as tf
from tensorflow.keras.layers import Layer

class L2Normalization(Layer):
    def __init__(self, epsilon=1e-12, **kwargs):
        self.epsilon = epsilon
        super(L2Normalization, self).__init__(**kwargs)

    def build(self, input_shape):
        super(L2Normalization, self).build(input_shape)

    def call(self, x):
        return x / (tf.norm(x, axis=-1, keepdims=True) + self.epsilon)

    def compute_output_shape(self, input_shape):
        return input_shape

# Example usage
base_model = tf.keras.applications.MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
x = base_model.output
x = tf.keras.layers.GlobalAveragePooling2D()(x)
x = tf.keras.layers.Dense(128)(x)
x = L2Normalization()(x)

# Add additional layers if needed
x = tf.keras.layers.Activation('relu')(x)
output = tf.keras.layers.Dense(6, activation='softmax')(x)

model = tf.keras.models.Model(inputs=base_model.input, outputs=output)
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.summary()

converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with open('mobilenet_v2_L2Norm', 'wb') as f:
    f.write(tflite_model)