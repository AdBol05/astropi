import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Input, Layer, Activation, GlobalAveragePooling2D, Dense, L2Normalization
from tensorflow.keras.models import Model

# Load MobileNetV2 model without top layers (include_top=False)
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# Add L2 normalization layer
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(128)(x)  # You can adjust the number of units as needed
x = L2Normalization()(x)  # Add L2 normalization layer

# Add additional layers if needed
x = Activation('relu')(x)
x = Dense(6, activation='softmax')(x)  # Replace num_classes with the number of classes in your dataset

# Create a new model with the modified architecture
model = Model(inputs=base_model.input, outputs=x)

# Compile the model and specify the optimizer, loss function, and metrics
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Print the model summary to verify the architecture
model.summary()
