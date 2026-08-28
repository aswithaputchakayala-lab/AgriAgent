import os
import numpy as np
import tensorflow as tf
from PIL import Image


# ============================================================
# FIND THE TRAINED MODEL AUTOMATICALLY
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

print("Backend folder:", BASE_DIR)
print("Models folder:", MODELS_DIR)


if not os.path.exists(MODELS_DIR):
    raise FileNotFoundError(
        f"Models folder not found:\n{MODELS_DIR}"
    )


# Find any .keras / .h5 / .hdf5 model
model_files = []

for filename in os.listdir(MODELS_DIR):

    if filename.lower().endswith(
        (".keras", ".h5", ".hdf5")
    ):
        model_files.append(filename)


if len(model_files) == 0:

    raise FileNotFoundError(
        "No trained model found inside:\n"
        + MODELS_DIR
    )


# Use the first model found
MODEL_PATH = os.path.join(
    MODELS_DIR,
    model_files[0]
)

print("Model found:", MODEL_PATH)


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading plant disease model...")

model = tf.keras.models.load_model(
    MODEL_PATH
)

print("Model loaded successfully!")

print(
    "Model input shape:",
    model.input_shape
)


# ============================================================
# PLANTVILLAGE 38 CLASSES
# ============================================================

CLASS_NAMES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",

    "Blueberry___healthy",

    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",

    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",

    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",

    "Orange___Haunglongbing_(Citrus_greening)",

    "Peach___Bacterial_spot",
    "Peach___healthy",

    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",

    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",

    "Raspberry___healthy",

    "Soybean___healthy",

    "Squash___Powdery_mildew",

    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",

    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy"
]


print(
    "Number of classes:",
    len(CLASS_NAMES)
)


# ============================================================
# PREDICT IMAGE
# ============================================================

def predict_image(image_path):

    print("Predicting image:", image_path)

    # --------------------------------------------------------
    # Check uploaded image
    # --------------------------------------------------------

    if not os.path.exists(image_path):

        raise FileNotFoundError(
            f"Uploaded image not found:\n{image_path}"
        )


    # --------------------------------------------------------
    # Open image
    # --------------------------------------------------------

    image = Image.open(
        image_path
    ).convert("RGB")


    # --------------------------------------------------------
    # IMPORTANT
    #
    # Read the model's expected image size automatically.
    #
    # Your model expects:
    # (None, 160, 160, 3)
    #
    # Therefore this becomes:
    # (160, 160)
    # --------------------------------------------------------

    input_shape = model.input_shape

    height = input_shape[1]
    width = input_shape[2]


    if height is None:
        height = 160

    if width is None:
        width = 160


    print(
        "Resizing image to:",
        width,
        "x",
        height
    )


    image = image.resize(
        (width, height)
    )


    # --------------------------------------------------------
    # Convert to NumPy
    # --------------------------------------------------------

    image_array = np.array(
        image,
        dtype=np.float32
    )


    # --------------------------------------------------------
    # MobileNetV2 preprocessing
    # --------------------------------------------------------

    image_array = (
        tf.keras.applications.mobilenet_v2.preprocess_input(
            image_array
        )
    )


    # --------------------------------------------------------
    # Add batch dimension
    #
    # Example:
    #
    # (160,160,3)
    #
    # becomes:
    #
    # (1,160,160,3)
    # --------------------------------------------------------

    image_array = np.expand_dims(
        image_array,
        axis=0
    )


    print(
        "Image shape sent to model:",
        image_array.shape
    )


    # --------------------------------------------------------
    # Predict
    # --------------------------------------------------------

    predictions = model.predict(
        image_array,
        verbose=0
    )


    # --------------------------------------------------------
    # Get predicted class
    # --------------------------------------------------------

    predicted_index = int(
        np.argmax(predictions[0])
    )


    confidence = float(
        np.max(predictions[0]) * 100
    )


    # --------------------------------------------------------
    # Get disease name
    # --------------------------------------------------------

    if predicted_index < len(CLASS_NAMES):

        disease = CLASS_NAMES[
            predicted_index
        ]

    else:

        disease = "Unknown"


    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {
        "disease": disease,
        "confidence": round(
            confidence,
            2
        )
    }