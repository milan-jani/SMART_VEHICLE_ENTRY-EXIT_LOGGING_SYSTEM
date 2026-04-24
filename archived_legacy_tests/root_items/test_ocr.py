import cv2
import numpy as np
import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
import logging
logging.getLogger("ppocr").setLevel(logging.WARNING)

from paddleocr import PaddleOCR

# Create dummy text image
img = np.zeros((100, 300, 3), dtype=np.uint8)
cv2.putText(img, 'MH20EE7602', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)

ocr_reader = PaddleOCR(use_angle_cls=True, lang='en')
results = ocr_reader.ocr(img)

print("====== OCR STRUCTURE ======")
print(str(results))
print("===========================")
