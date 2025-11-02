# Hunyuan 3D is licensed under the TENCENT HUNYUAN NON-COMMERCIAL LICENSE AGREEMENT
"""
Image enhancement and geometric transformations using kornia.
Provides GPU-accelerated image processing for better input quality.
"""

try:
    import kornia
    import kornia.augmentation as K
    KORNIA_AVAILABLE = True
except ImportError:
    KORNIA_AVAILABLE = False
    print("Warning: kornia not installed. Image enhancement disabled.")

import torch
import numpy as np
from PIL import Image


class ImageEnhancer:
    """
    Image enhancement using kornia for GPU-accelerated transformations.
    Useful for preprocessing images before 3D generation.
    """
    
    def __init__(self, device='cuda'):
        """
        Args:
            device: 'cuda' or 'cpu'
        """
        if not KORNIA_AVAILABLE:
            raise ImportError("kornia is not installed. Install with: pip install kornia")
        
        self.device = device
    
    def pil_to_tensor(self, image):
        """Convert PIL Image to kornia tensor"""
        if isinstance(image, Image.Image):
            img_np = np.array(image.convert('RGB'))
            img_tensor = torch.from_numpy(img_np).float() / 255.0
            img_tensor = img_tensor.permute(2, 0, 1).unsqueeze(0)  # [1, C, H, W]
        else:
            img_tensor = image
        
        return img_tensor.to(self.device)
    
    def tensor_to_pil(self, tensor):
        """Convert kornia tensor to PIL Image"""
        if tensor.dim() == 4:
            tensor = tensor.squeeze(0)
        tensor = tensor.permute(1, 2, 0).cpu()
        tensor = torch.clamp(tensor, 0, 1)
        img_np = (tensor.numpy() * 255).astype(np.uint8)
        return Image.fromarray(img_np)
    
    def enhance_sharpness(self, image, factor=1.5):
        """
        Enhance image sharpness using kornia filters.
        
        Args:
            image: PIL Image
            factor: Sharpness factor (1.0 = no change, >1.0 = sharper)
            
        Returns:
            PIL Image: Sharpened image
        """
        img_tensor = self.pil_to_tensor(image)
        
        # Apply unsharp masking for sharpness
        kernel = torch.tensor([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]], dtype=torch.float32).to(self.device)
        kernel = kernel.unsqueeze(0).unsqueeze(0)
        
        # Convolve with sharpening kernel
        sharpened = kornia.filters.filter2d(img_tensor, kernel)
        
        # Blend with original
        enhanced = img_tensor * (1 - factor) + sharpened * factor
        
        return self.tensor_to_pil(enhanced)
    
    def correct_perspective(self, image, angle=0.0):
        """
        Correct perspective/distortion.
        
        Args:
            image: PIL Image
            angle: Rotation angle in degrees
            
        Returns:
            PIL Image: Corrected image
        """
        img_tensor = self.pil_to_tensor(image)
        
        # Rotation transformation
        center = torch.tensor([[image.size[0] / 2, image.size[1] / 2]]).to(self.device)
        angle_rad = torch.tensor([angle * np.pi / 180.0]).to(self.device)
        scale = torch.tensor([1.0]).to(self.device)
        
        M = kornia.geometry.get_rotation_matrix2d(center, angle_rad, scale)
        transformed = kornia.geometry.transform.warp_affine(
            img_tensor, M, dsize=(image.size[1], image.size[0])
        )
        
        return self.tensor_to_pil(transformed)
    
    def normalize_illumination(self, image):
        """
        Normalize illumination for more consistent results.
        
        Args:
            image: PIL Image
            
        Returns:
            PIL Image: Illumination-normalized image
        """
        img_tensor = self.pil_to_tensor(image)
        
        # Convert to LAB color space for better illumination handling
        lab = kornia.color.rgb_to_lab(img_tensor)
        
        # Normalize L channel (illumination)
        L = lab[:, 0:1, :, :]
        L_mean = L.mean()
        L_normalized = (L - L_mean) * 0.5 + L_mean  # Gentle normalization
        
        lab_normalized = torch.cat([L_normalized, lab[:, 1:, :, :]], dim=1)
        rgb_normalized = kornia.color.lab_to_rgb(lab_normalized)
        
        return self.tensor_to_pil(rgb_normalized)
    
    def augment_for_robustness(self, image, brightness=0.1, contrast=0.1):
        """
        Apply light augmentation for more robust 3D generation.
        
        Args:
            image: PIL Image
            brightness: Brightness adjustment range
            contrast: Contrast adjustment range
            
        Returns:
            PIL Image: Augmented image
        """
        img_tensor = self.pil_to_tensor(image)
        
        # Kornia augmentation
        aug = K.AugmentationSequential(
            K.ColorJitter(brightness=brightness, contrast=contrast, saturation=0.05, hue=0.01),
            data_keys=['input'],
            same_on_batch=False,
        )
        
        augmented = aug(img_tensor)
        return self.tensor_to_pil(augmented)
    
    def enhance_for_3d(self, image, sharpen=True, normalize_illum=True):
        """
        Complete enhancement pipeline optimized for 3D generation.
        
        Args:
            image: PIL Image
            sharpen: Whether to apply sharpening
            normalize_illum: Whether to normalize illumination
            
        Returns:
            PIL Image: Enhanced image ready for 3D generation
        """
        img = image
        
        if normalize_illum:
            img = self.normalize_illumination(img)
        
        if sharpen:
            img = self.enhance_sharpness(img, factor=1.3)
        
        return img
    
    def __call__(self, image, mode='enhance_for_3d', **kwargs):
        """
        Convenience method for image enhancement.
        
        Args:
            image: PIL Image
            mode: 'sharpen', 'perspective', 'illumination', 'augment', or 'enhance_for_3d'
            **kwargs: Additional arguments for specific modes
            
        Returns:
            PIL Image: Enhanced image
        """
        if mode == 'sharpen':
            return self.enhance_sharpness(image, kwargs.get('factor', 1.5))
        elif mode == 'perspective':
            return self.correct_perspective(image, kwargs.get('angle', 0.0))
        elif mode == 'illumination':
            return self.normalize_illumination(image)
        elif mode == 'augment':
            return self.augment_for_robustness(image, 
                                             kwargs.get('brightness', 0.1),
                                             kwargs.get('contrast', 0.1))
        elif mode == 'enhance_for_3d':
            return self.enhance_for_3d(image,
                                      kwargs.get('sharpen', True),
                                      kwargs.get('normalize_illum', True))
        else:
            raise ValueError(f"Unknown mode: {mode}")

