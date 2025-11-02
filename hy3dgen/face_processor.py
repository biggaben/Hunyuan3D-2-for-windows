# Hunyuan 3D is licensed under the TENCENT HUNYUAN NON-COMMERCIAL LICENSE AGREEMENT
"""
Face detection and alignment processor using facexlib.
Integrates face detection and alignment for better 3D generation of portraits.
"""

try:
    from facexlib import detection, alignment, parsing
    from facexlib.utils import face_align
    FACEXLIB_AVAILABLE = True
except ImportError:
    FACEXLIB_AVAILABLE = False
    print("Warning: facexlib not installed. Face processing disabled.")

import cv2
import numpy as np
from PIL import Image
import torch


class FaceProcessor:
    """
    Face detection, alignment, and enhancement processor.
    Useful for portrait 3D generation to ensure faces are properly centered and aligned.
    """
    
    def __init__(self, device='cuda', detection_model='retinaface', enable_alignment=True, enable_parsing=False):
        """
        Args:
            device: 'cuda' or 'cpu'
            detection_model: 'retinaface' (default) or 'yolov5'
            enable_alignment: Whether to align faces
            enable_parsing: Whether to enable face parsing (segmentation)
        """
        if not FACEXLIB_AVAILABLE:
            raise ImportError("facexlib is not installed. Install with: pip install facexlib")
        
        self.device = device
        self.enable_alignment = enable_alignment
        self.enable_parsing = enable_parsing
        
        # Initialize face detection
        self.detector = detection.init_detection_model(detection_model, half=False, device=device)
        
        # Initialize face alignment
        if enable_alignment:
            self.alignment_net = alignment.init_alignment_model('awing_fan', device=device)
        
        # Initialize face parsing (optional)
        if enable_parsing:
            self.parser = parsing.init_parsing_model('parsenet', device=device)
    
    def detect_faces(self, image):
        """
        Detect faces in an image.
        
        Args:
            image: PIL Image or numpy array (BGR)
            
        Returns:
            list: List of detected faces with bounding boxes and landmarks
        """
        if isinstance(image, Image.Image):
            img_np = np.array(image.convert('RGB'))
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = image
        
        faces, _ = self.detector.align_detect(
            img=img_bgr,
            threshold=0.5
        )
        
        return faces
    
    def align_face(self, image, face_landmarks=None):
        """
        Align face using landmarks for better 3D generation.
        
        Args:
            image: PIL Image or numpy array
            face_landmarks: Optional pre-detected landmarks
            
        Returns:
            PIL Image: Aligned face image
        """
        if isinstance(image, Image.Image):
            img_np = np.array(image.convert('RGB'))
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = image
        
        if face_landmarks is None:
            faces = self.detect_faces(img_bgr)
            if len(faces) == 0:
                return Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
            face_landmarks = faces[0]['kps']
        
        # Align face
        aligned_face = face_align.norm_crop(img_bgr, landmark=face_landmarks)
        aligned_rgb = cv2.cvtColor(aligned_face, cv2.COLOR_BGR2RGB)
        
        return Image.fromarray(aligned_rgb)
    
    def center_on_face(self, image, padding=0.3):
        """
        Center the image on the detected face with padding.
        Useful for portrait 3D generation.
        
        Args:
            image: PIL Image
            padding: Padding ratio around face (0.3 = 30% padding)
            
        Returns:
            PIL Image: Recentered image
        """
        faces = self.detect_faces(image)
        
        if len(faces) == 0:
            # No face detected, return original
            return image
        
        if isinstance(image, Image.Image):
            img_np = np.array(image)
            h, w = img_np.shape[:2]
        else:
            h, w = image.shape[:2]
        
        # Get bounding box of first face
        face_box = faces[0]['bbox']  # [x1, y1, x2, y2]
        x1, y1, x2, y2 = face_box
        
        # Calculate face center and size
        face_center_x = (x1 + x2) / 2
        face_center_y = (y1 + y2) / 2
        face_width = x2 - x1
        face_height = y2 - y1
        
        # Calculate crop box with padding
        crop_size = max(face_width, face_height) * (1 + 2 * padding)
        crop_x1 = max(0, int(face_center_x - crop_size / 2))
        crop_y1 = max(0, int(face_center_y - crop_size / 2))
        crop_x2 = min(w, int(face_center_x + crop_size / 2))
        crop_y2 = min(h, int(face_center_y + crop_size / 2))
        
        # Crop and resize to square
        if isinstance(image, Image.Image):
            cropped = image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
            # Resize to original dimensions
            return cropped.resize((w, h), Image.Resampling.LANCZOS)
        else:
            cropped = image[crop_y1:crop_y2, crop_x1:crop_x2]
            return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LANCZOS4)
    
    def enhance_portrait(self, image, align=True, center=True):
        """
        Complete portrait enhancement pipeline:
        1. Detect face
        2. Center on face (optional)
        3. Align face (optional)
        
        Args:
            image: PIL Image
            align: Whether to align the face
            center: Whether to center on face
            
        Returns:
            PIL Image: Enhanced portrait
        """
        if isinstance(image, Image.Image):
            img = image
        else:
            img = Image.fromarray(image)
        
        # Center on face first
        if center:
            img = self.center_on_face(img)
        
        # Align face
        if align:
            img = self.align_face(img)
        
        return img
    
    def __call__(self, image, mode='enhance'):
        """
        Convenience method for face processing.
        
        Args:
            image: PIL Image
            mode: 'detect', 'align', 'center', or 'enhance'
            
        Returns:
            PIL Image or detection results
        """
        if mode == 'detect':
            return self.detect_faces(image)
        elif mode == 'align':
            return self.align_face(image)
        elif mode == 'center':
            return self.center_on_face(image)
        elif mode == 'enhance':
            return self.enhance_portrait(image)
        else:
            raise ValueError(f"Unknown mode: {mode}")

