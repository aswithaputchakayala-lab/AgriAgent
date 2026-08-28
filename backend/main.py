from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


import tempfile
import os
import requests

from model import predict_image

# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AgriAgent API",
    description="AI-powered Smart Agriculture Decision Support System",
    version="1.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# LOAD PLANT DISEASE MODEL
# ============================================================

from model import predict_image


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "success": True,
        "message": "AgriAgent Backend is working!"
    }


# ============================================================
# PLANT DISEASE PREDICTION
# ============================================================

@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    if not file:

        return {
            "success": False,
            "error": "No image uploaded"
        }


    suffix = os.path.splitext(file.filename)[1]


    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp_file:

        contents = await file.read()

        temp_file.write(contents)

        temp_path = temp_file.name


    try:

        result = predict_image(temp_path)


        disease = result.get(
            "disease",
            "Unknown"
        )

        confidence = result.get(
            "confidence",
            0
        )


        # ----------------------------------------------------
        # XAI explanation for disease prediction
        # ----------------------------------------------------

        if "healthy" in disease.lower():

            disease_explanation = (
                "The model classified the uploaded leaf as healthy. "
                "The prediction is based on visual patterns learned "
                "from healthy and diseased plant leaf images."
            )

        else:

            disease_explanation = (
                f"The model identified {disease.replace('_', ' ')} "
                f"with a confidence of {confidence}%. "
                "The prediction is based on visual features and "
                "patterns learned from the plant disease training dataset."
            )


        return {

            "success": True,

            "filename": file.filename,

            "prediction": {

                "class_index":
                    result.get("class_index"),

                "disease":
                    disease,

                "confidence":
                    confidence

            },

            "xai": {

                "explanation":
                    disease_explanation,

                "model_reason":
                    "The trained MobileNetV2 model analyzes visual characteristics of the uploaded leaf and selects the disease class with the highest prediction probability."

            }

        }


    except Exception as e:

        return {

            "success": False,

            "error": str(e)

        }


    finally:

        if os.path.exists(temp_path):

            os.remove(temp_path)


# ============================================================
# FARM INPUT MODEL
# ============================================================

class FarmInput(BaseModel):

    crop: str

    soil_moisture: float

    temperature: float

    humidity: float


# ============================================================
# FARM ANALYSIS
# ============================================================

@app.post("/farm")
def farm_analysis(data: FarmInput):


    # --------------------------------------------------------
    # SOIL MOISTURE ANALYSIS
    # --------------------------------------------------------

    if data.soil_moisture < 30:

        soil_status = "Low"

        irrigation_advice = "Irrigation recommended"

        soil_explanation = (
            "Soil moisture is below 30%, indicating that "
            "the soil may require additional water."
        )


    elif data.soil_moisture <= 70:

        soil_status = "Optimal"

        irrigation_advice = "Soil moisture is suitable"

        soil_explanation = (
            "Soil moisture is within the suitable range, "
            "so immediate irrigation may not be necessary."
        )


    else:

        soil_status = "High"

        irrigation_advice = "Reduce irrigation"

        soil_explanation = (
            "Soil moisture is above 70%, so excessive "
            "irrigation should be avoided."
        )


    # --------------------------------------------------------
    # TEMPERATURE ANALYSIS
    # --------------------------------------------------------

    if data.temperature < 15:

        temperature_status = "Low"

    elif data.temperature <= 35:

        temperature_status = "Suitable"

    else:

        temperature_status = "High"


    # --------------------------------------------------------
    # HUMIDITY ANALYSIS
    # --------------------------------------------------------

    if data.humidity < 40:

        humidity_status = "Low"

    elif data.humidity <= 80:

        humidity_status = "Suitable"

    else:

        humidity_status = "High"


    # --------------------------------------------------------
    # CROP RECOMMENDATION
    # --------------------------------------------------------

    if (
        data.temperature >= 20
        and data.temperature <= 35
        and data.soil_moisture >= 40
        and data.humidity >= 50
    ):

        recommended_crop = "Rice"

        crop_reason = (
            "Temperature, soil moisture and humidity "
            "are suitable for a water-demanding crop."
        )


    elif (
        data.temperature >= 20
        and data.temperature <= 30
        and data.soil_moisture < 40
    ):

        recommended_crop = "Millet"

        crop_reason = (
            "Soil moisture is low while the temperature "
            "is suitable for a relatively drought-tolerant crop."
        )


    elif data.temperature < 20:

        recommended_crop = "Potato"

        crop_reason = (
            "The temperature is relatively low, "
            "making potato a suitable recommendation."
        )


    else:

        recommended_crop = "Maize"

        crop_reason = (
            "The current combination of environmental "
            "conditions makes maize a reasonable recommendation."
        )


    # --------------------------------------------------------
    # OVERALL XAI
    # --------------------------------------------------------

    overall_explanation = (
        f"The recommendation was generated using the supplied "
        f"soil moisture ({data.soil_moisture}%), temperature "
        f"({data.temperature}°C), and humidity "
        f"({data.humidity}%). "
        f"Based on these conditions, {recommended_crop} "
        f"was selected."
    )


    return {

        "success": True,

        "input": {

            "crop":
                data.crop,

            "soil_moisture":
                data.soil_moisture,

            "temperature":
                data.temperature,

            "humidity":
                data.humidity

        },

        "soil_analysis": {

            "status":
                soil_status,

            "irrigation_advice":
                irrigation_advice,

            "explanation":
                soil_explanation

        },

        "climate_analysis": {

            "temperature_status":
                temperature_status,

            "humidity_status":
                humidity_status

        },

        "crop_recommendation":
            recommended_crop,

        "crop_recommendation_explanation":
            crop_reason,

        "xai_explanation":
            overall_explanation

    }


# ============================================================
# CURRENT LOCATION WEATHER
# ============================================================

@app.get("/weather/current")
def get_current_weather(
    latitude: float,
    longitude: float
):

    try:

        # ----------------------------------------------------
        # Open-Meteo current weather API
        # ----------------------------------------------------

        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            "&current=temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "rain,"
            "wind_speed_10m"
        )


        response = requests.get(
            url,
            timeout=10
        )


        if response.status_code != 200:

            return {

                "success": False,

                "message":
                    "Unable to get weather data"

            }


        weather_data = response.json()


        current = weather_data["current"]


        temperature = current[
            "temperature_2m"
        ]

        humidity = current[
            "relative_humidity_2m"
        ]

        rain = current[
            "rain"
        ]

        precipitation = current[
            "precipitation"
        ]

        wind_speed = current[
            "wind_speed_10m"
        ]


        # ----------------------------------------------------
        # TEMPERATURE STATUS
        # ----------------------------------------------------

        if temperature < 15:

            temperature_status = "Low"

        elif temperature <= 35:

            temperature_status = "Suitable"

        else:

            temperature_status = "High"


        # ----------------------------------------------------
        # HUMIDITY STATUS
        # ----------------------------------------------------

        if humidity < 40:

            humidity_status = "Low"

        elif humidity <= 80:

            humidity_status = "Suitable"

        else:

            humidity_status = "High"


        # ----------------------------------------------------
        # RAIN STATUS
        # ----------------------------------------------------

        if rain > 0:

            rain_status = "Rain detected"

        else:

            rain_status = "No rain currently"


        # ----------------------------------------------------
        # WEATHER XAI
        # ----------------------------------------------------

        weather_explanation = (
            f"Current temperature is {temperature}°C "
            f"({temperature_status}), humidity is {humidity}% "
            f"({humidity_status}), and rainfall is {rain} mm "
            f"({rain_status.lower()}). These conditions can "
            "be considered when planning irrigation and crop "
            "management."
        )


        return {

            "success": True,

            "location": {

                "latitude":
                    latitude,

                "longitude":
                    longitude

            },

            "weather": {

                "temperature_c":
                    temperature,

                "humidity_percent":
                    humidity,

                "rain_mm":
                    rain,

                "precipitation_mm":
                    precipitation,

                "wind_speed_kmh":
                    wind_speed

            },

            "climate_analysis": {

                "temperature_status":
                    temperature_status,

                "humidity_status":
                    humidity_status,

                "rain_status":
                    rain_status

            },

            "xai_explanation":
                weather_explanation

        }


    except Exception as e:

        return {

            "success": False,

            "message":
                "Weather service unavailable",

            "error":
                str(e)

        }
# ============================================================
# IoT SENSOR DATA
# ============================================================

class IoTData(BaseModel):
    soil_moisture: float
    temperature: float
    humidity: float


@app.post("/iot/sensor-data")
def receive_iot_data(data: IoTData):

    # Soil moisture analysis
    if data.soil_moisture < 30:
        soil_status = "Low"
        irrigation_advice = "Irrigation recommended"

    elif data.soil_moisture <= 70:
        soil_status = "Optimal"
        irrigation_advice = "Soil moisture is suitable"

    else:
        soil_status = "High"
        irrigation_advice = "Reduce irrigation"


    # Temperature analysis
    if data.temperature < 15:
        temperature_status = "Low"

    elif data.temperature <= 35:
        temperature_status = "Suitable"

    else:
        temperature_status = "High"


    # Humidity analysis
    if data.humidity < 40:
        humidity_status = "Low"

    elif data.humidity <= 80:
        humidity_status = "Suitable"

    else:
        humidity_status = "High"


    # Crop recommendation
    if (
        data.temperature >= 20
        and data.temperature <= 35
        and data.soil_moisture >= 40
        and data.humidity >= 50
    ):
        recommended_crop = "Rice"

    elif (
        data.temperature >= 20
        and data.temperature <= 30
        and data.soil_moisture < 40
    ):
        recommended_crop = "Millet"

    elif data.temperature < 20:
        recommended_crop = "Potato"

    else:
        recommended_crop = "Maize"


    return {
        "success": True,

        "sensor_data": {
            "soil_moisture": data.soil_moisture,
            "temperature": data.temperature,
            "humidity": data.humidity
        },

        "soil_analysis": {
            "status": soil_status,
            "irrigation_advice": irrigation_advice
        },

        "climate_analysis": {
            "temperature_status": temperature_status,
            "humidity_status": humidity_status
        },

        "crop_recommendation": recommended_crop
    }
# ==================================================
# FRONTEND
# ==================================================

frontend_path = os.path.join(
    os.path.dirname(__file__),
    "frontend"
)

from pathlib import Path
from fastapi.responses import FileResponse


@app.get("/app")
def serve_app():
    index_file = Path(__file__).resolve().parent.parent / "index.html"

    if not index_file.exists():
        return {
            "success": False,
            "error": f"index.html not found at {index_file}"
        }

    return FileResponse(index_file)