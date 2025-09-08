import os
import cv2
import easyocr
import pandas as pd
import joblib
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Paths
RESULTS_FILE = "results/predictions.csv"
MODEL_PATH = "member1/models/fake_news_model.pkl"

# Create results folder if it doesn't exist
os.makedirs("results", exist_ok=True)

# Initialize EasyOCR readers safely
reader_en_hi = easyocr.Reader(['en', 'hi'], gpu=False)  # English + Hindi
reader_te_en = easyocr.Reader(['te', 'en'], gpu=False)  # Telugu + English

# Load model if exists, else use dummy
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    print(f"⚠️ Model not found at {MODEL_PATH}. Using dummy model for testing.")
    class DummyModel:
        def predict(self, texts):
            return ["Real" if "news" in t.lower() else "Fake" for t in texts]
    model = DummyModel()

# Initialize results CSV if not exists
if not os.path.exists(RESULTS_FILE):
    pd.DataFrame(columns=['image_path', 'language_detected', 'extracted_text', 'prediction']).to_csv(RESULTS_FILE, index=False)

def process_image(img_path):
    """Process a single image and save result to CSV."""
    img = cv2.imread(img_path)
    if img is None:
        print(f"❌ Could not read image: {img_path}")
        return

    # Try Telugu reader first
    try:
        ocr_result = reader_te_en.readtext(img)
        if not ocr_result:  # if nothing detected, fallback to English+Hindi
            ocr_result = reader_en_hi.readtext(img)
    except Exception:
        ocr_result = reader_en_hi.readtext(img)

    extracted_text = " ".join([str(res[1]) for res in ocr_result])  # ensure string

    # Confidence scores (EasyOCR returns float) → string for CSV
    detected_langs = [str(res[2]) for res in ocr_result] if ocr_result else ["unknown"]
    language_detected = ", ".join(detected_langs)

    # Predict fake/real
    prediction = model.predict([extracted_text])[0]

    # Save to CSV
    df = pd.read_csv(RESULTS_FILE)
    df = pd.concat([df, pd.DataFrame([{
        'image_path': img_path,
        'language_detected': language_detected,
        'extracted_text': extracted_text,
        'prediction': prediction
    }])], ignore_index=True)
    df.to_csv(RESULTS_FILE, index=False)

    # Print results
    print(f"✅ Processed {img_path}")
    print(f"Extracted Text: {extracted_text}")
    print(f"Detected Language: {language_detected}")
    print(f"Prediction: {prediction}\n")

if __name__ == "__main__":
    # Hide main tkinter window
    Tk().withdraw()
    # Ask user to select an image
    user_image = askopenfilename(title="Select an image for fake news detection",
                                 filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
    if user_image:
        process_image(user_image)
        print(f"All done! Results saved at: {RESULTS_FILE}")
    else:
        print("❌ No image selected.")
