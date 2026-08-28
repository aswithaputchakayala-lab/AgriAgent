from model import predict_image


IMAGE_PATH = r"C:\Users\HASINI RAVULA\OneDrive\Documents\ml\datasets\village dataset\Plant Village Dataset\Test\Apple - Apple Scab\03354abb-aa1c-4f9d-a1ef-9f40505cd539___FREC_Scab 3355.JPG"


result = predict_image(IMAGE_PATH)


print("\n========== PREDICTION RESULT ==========")
print("Class Index :", result["class_index"])
print("Disease     :", result["disease"])
print("Confidence  :", result["confidence"], "%")
print("=======================================\n")