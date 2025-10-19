import os
import cv2
import numpy as np
from paddleocr import PaddleOCR
# ----------------------------
# OCR Text Extraction


def run_ocr_extraction(image_path: str, visualize: bool = False) -> str:
    """Extract text from an image using PaddleOCR, compatible with all versions."""
    print("Initializing PaddleOCR...")

    ocr = PaddleOCR(lang='en')

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        # ✅ For PaddleOCR v4.x (newer)
        img = cv2.imread(image_path)
        results = ocr.predict(img)
    except Exception:
        # ✅ Fallback for older versions
        results = ocr.ocr(image_path)

    all_text = []
    extracted_data = []

    # Newer dict-based output
    if isinstance(results, list) and results and isinstance(results[0], dict):
        for res in results:
            texts = res.get("rec_texts", [])
            scores = res.get("rec_scores", [])
            boxes = res.get("rec_polys", [])
            for i in range(len(texts)):
                extracted_data.append({
                    "text": texts[i],
                    "confidence": float(scores[i]),
                    "bbox": np.array(boxes[i]).astype(int).tolist()
                })
                all_text.append(texts[i])
    else:
        # Legacy nested list format
        for line in results:
            for item in line:
                txt = item[1][0]
                conf = float(item[1][1])
                all_text.append(txt)
                extracted_data.append({"text": txt, "confidence": conf})

    extracted_text = " ".join(all_text).strip()

    if not extracted_text:
        extracted_text = "No text detected."

    print(f"🧾 Extracted text: {extracted_text}")
    return extracted_text 

if __name__ == "__main__":
    test_image = R"C:\Users\praga\OneDrive\Desktop\news_dataset\fake_image3.png"  # Replace with your test image path
    extracted_text = run_ocr_extraction(test_image, visualize=False)
    print(f"\nFinal Extracted Text:\n{extracted_text}\n")