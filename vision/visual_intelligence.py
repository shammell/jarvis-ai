#!/usr/bin/env python3
"""
JARVIS Visual Intelligence Module - INTERMEDIATE LEVEL
Advanced computer vision and AI-powered screen analysis
"""

import cv2
import numpy as np
from PIL import Image
import pytesseract
import io
import base64
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VisualIntelligence:
    """
    Advanced visual intelligence for screen analysis
    - OCR text extraction
    - Object detection
    - Color analysis
    - Pattern recognition
    - UI element detection
    """

    def __init__(self):
        self.last_analysis = None
        logger.info("🧠 Visual Intelligence Module initialized")

    def extract_text_from_image(self, image_base64: str) -> Dict[str, Any]:
        """
        Extract all text from screenshot using OCR

        Returns:
            {
                "text": "extracted text",
                "words": [{"text": "word", "confidence": 95, "bbox": [x, y, w, h]}],
                "lines": ["line1", "line2"]
            }
        """
        try:
            # Decode base64 image
            img_data = base64.b64decode(image_base64)
            img = Image.open(io.BytesIO(img_data))

            # Extract text with details
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

            # Parse results
            words = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:
                    words.append({
                        'text': data['text'][i],
                        'confidence': int(data['conf'][i]),
                        'bbox': [
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        ]
                    })

            # Get full text
            full_text = pytesseract.image_to_string(img)
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]

            logger.info(f"📝 Extracted {len(words)} words from screen")

            return {
                'success': True,
                'text': full_text,
                'words': words,
                'lines': lines,
                'word_count': len(words)
            }

        except Exception as e:
            logger.error(f"❌ OCR failed: {e}")
            return {'success': False, 'error': str(e)}

    def find_text_on_screen(self, image_base64: str, search_text: str) -> Optional[Tuple[int, int]]:
        """
        Find specific text on screen and return its center position

        Args:
            image_base64: Screenshot as base64
            search_text: Text to find

        Returns:
            (x, y) center position or None
        """
        try:
            result = self.extract_text_from_image(image_base64)

            if not result['success']:
                return None

            search_lower = search_text.lower()

            for word in result['words']:
                if search_lower in word['text'].lower():
                    bbox = word['bbox']
                    center_x = bbox[0] + bbox[2] // 2
                    center_y = bbox[1] + bbox[3] // 2

                    logger.info(f"🔍 Found '{search_text}' at ({center_x}, {center_y})")
                    return (center_x, center_y)

            logger.warning(f"⚠️ Text '{search_text}' not found on screen")
            return None

        except Exception as e:
            logger.error(f"❌ Text search failed: {e}")
            return None

    def detect_ui_elements(self, image_base64: str) -> Dict[str, Any]:
        """
        Detect UI elements (buttons, text fields, etc) on screen

        Returns:
            {
                "buttons": [{"bbox": [x, y, w, h], "confidence": 0.9}],
                "text_fields": [...],
                "icons": [...]
            }
        """
        try:
            # Decode image
            img_data = base64.b64decode(image_base64)
            img = Image.open(io.BytesIO(img_data))
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

            # Convert to grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

            # Detect edges
            edges = cv2.Canny(gray, 50, 150)

            # Find contours (potential UI elements)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filter and classify contours
            buttons = []
            text_fields = []

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h

                # Filter by size (ignore very small/large)
                if 100 < area < 50000:
                    aspect_ratio = w / h if h > 0 else 0

                    # Classify based on aspect ratio
                    if 0.8 < aspect_ratio < 1.2:  # Square-ish = button
                        buttons.append({
                            'bbox': [x, y, w, h],
                            'center': (x + w//2, y + h//2),
                            'area': area
                        })
                    elif aspect_ratio > 2:  # Wide = text field
                        text_fields.append({
                            'bbox': [x, y, w, h],
                            'center': (x + w//2, y + h//2),
                            'area': area
                        })

            logger.info(f"🎯 Detected {len(buttons)} buttons, {len(text_fields)} text fields")

            return {
                'success': True,
                'buttons': buttons[:20],  # Top 20
                'text_fields': text_fields[:10],  # Top 10
                'total_elements': len(buttons) + len(text_fields)
            }

        except Exception as e:
            logger.error(f"❌ UI detection failed: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_colors(self, image_base64: str) -> Dict[str, Any]:
        """
        Analyze dominant colors on screen

        Returns:
            {
                "dominant_colors": [(r, g, b), ...],
                "color_distribution": {...}
            }
        """
        try:
            # Decode image
            img_data = base64.b64decode(image_base64)
            img = Image.open(io.BytesIO(img_data))
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

            # Resize for faster processing
            img_small = cv2.resize(img_cv, (100, 100))

            # Reshape to list of pixels
            pixels = img_small.reshape(-1, 3)
            pixels = np.float32(pixels)

            # K-means clustering to find dominant colors
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            k = 5
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

            # Convert to RGB
            dominant_colors = centers.astype(int).tolist()
            dominant_colors = [(int(c[2]), int(c[1]), int(c[0])) for c in dominant_colors]

            logger.info(f"🎨 Analyzed colors: {dominant_colors}")

            return {
                'success': True,
                'dominant_colors': dominant_colors,
                'num_colors': k
            }

        except Exception as e:
            logger.error(f"❌ Color analysis failed: {e}")
            return {'success': False, 'error': str(e)}

    def compare_screenshots(self, img1_base64: str, img2_base64: str) -> Dict[str, Any]:
        """
        Compare two screenshots and find differences

        Returns:
            {
                "similarity": 0.95,
                "differences": [{"bbox": [x, y, w, h], "change": "significant"}]
            }
        """
        try:
            # Decode images
            img1_data = base64.b64decode(img1_base64)
            img2_data = base64.b64decode(img2_base64)

            img1 = cv2.imdecode(np.frombuffer(img1_data, np.uint8), cv2.IMREAD_COLOR)
            img2 = cv2.imdecode(np.frombuffer(img2_data, np.uint8), cv2.IMREAD_COLOR)

            # Resize to same size if needed
            if img1.shape != img2.shape:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

            # Calculate difference
            diff = cv2.absdiff(img1, img2)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

            # Threshold to find significant changes
            _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)

            # Find contours of changes
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            differences = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w * h > 100:  # Ignore tiny changes
                    differences.append({
                        'bbox': [x, y, w, h],
                        'area': w * h
                    })

            # Calculate similarity
            similarity = 1.0 - (np.sum(gray_diff) / (gray_diff.size * 255))

            logger.info(f"📊 Similarity: {similarity:.2%}, {len(differences)} changes")

            return {
                'success': True,
                'similarity': float(similarity),
                'differences': differences[:10],  # Top 10 changes
                'num_changes': len(differences)
            }

        except Exception as e:
            logger.error(f"❌ Screenshot comparison failed: {e}")
            return {'success': False, 'error': str(e)}


# Test
if __name__ == "__main__":
    vi = VisualIntelligence()
    print("Visual Intelligence Module - INTERMEDIATE LEVEL")
    print("Ready for advanced screen analysis!")
