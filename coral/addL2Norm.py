import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Layer
from pathlib import Path

# Custom L2Normalization layer
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

def add_l2norm_to_tflite(input_tflite_path, output_tflite_path):
    # Load existing TFLite model
    interpreter = tf.lite.Interpreter.from_file(input_tflite_path)
    interpreter.allocate_tensors()

    # Convert TFLite model to Keras model
    keras_model = tf.lite.TFLiteConverter.from_concrete_functions([interpreter.signatures["serving_default"]]).convert()
    keras_model = tf.lite.Interpreter(model_content=keras_model)

    # Add L2Normalization layer to the Keras model
    keras_model.add(L2Normalization())

    # Convert the modified Keras model back to TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(keras_model)
    tflite_model = converter.convert()

    # Save the modified TFLite model
    with open(output_tflite_path, 'wb') as f:
        f.write(tflite_model)

if __name__ == "__main__":
    # Specify the paths for the input and output TFLite models
    script_dir = Path(__file__).parent.resolve()
    input_tflite_path = script_dir/'base'/'mobilenet_v2.tflite'
    output_tflite_path = script_dir/'base'/'mobilenet_v2_L2Norm.tflite'

    # Add L2Normalization layer to the existing TFLite model
    add_l2norm_to_tflite(input_tflite_path, output_tflite_path)

    print(f"Modified TFLite model saved to: {output_tflite_path}")