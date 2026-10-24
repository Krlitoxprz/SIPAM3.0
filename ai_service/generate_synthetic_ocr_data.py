"""
Generate synthetic OCR training data for CNN
Creates grayscale images of digits and characters for document OCR
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from pathlib import Path
import argparse

# Constants
IMAGE_SIZE = (128, 128)
CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
TRAIN_SAMPLES_PER_CLASS = 50  # Total: 50 * 36 = 1800 images
VAL_SAMPLES_PER_CLASS = 15    # Total: 15 * 36 = 540 images

def get_font(size=60):
    """Get a system font for text rendering."""
    # Try different fonts depending on OS
    fonts_to_try = [
        "arial.ttf",
        "Arial.ttf",
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf"
    ]
    
    for font_path in fonts_to_try:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
    
    # Fallback to default
    return ImageFont.load_default()

def generate_character_image(char, font, augment=True):
    """
    Generate a synthetic image of a single character.
    
    Args:
        char: Character to render
        font: PIL ImageFont
        augment: Whether to apply random augmentations
    
    Returns:
        PIL Image (grayscale, 128x128)
    """
    # Create blank grayscale image
    img = Image.new('L', IMAGE_SIZE, color=255)  # White background
    draw = ImageDraw.Draw(img)
    
    # Get text size
    bbox = draw.textbbox((0, 0), char, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    x = (IMAGE_SIZE[0] - text_width) // 2
    y = (IMAGE_SIZE[1] - text_height) // 2 - 10
    
    # Randomize text color (dark gray to black)
    text_color = random.randint(0, 60)
    
    # Draw character
    draw.text((x, y), char, fill=text_color, font=font)
    
    if augment:
        img = apply_augmentations(img)
    
    return img

def apply_augmentations(img):
    """
    Apply random augmentations to simulate real-world OCR conditions.
    
    Augmentations:
    - Rotation (slight)
    - Scaling
    - Gaussian blur
    - Noise
    - Brightness/contrast variation
    """
    # Random rotation (-10 to +10 degrees)
    angle = random.uniform(-10, 10)
    img = img.rotate(angle, fillcolor=255)
    
    # Random scaling (90% to 110%)
    scale = random.uniform(0.9, 1.1)
    new_size = (int(IMAGE_SIZE[0] * scale), int(IMAGE_SIZE[1] * scale))
    img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Crop or pad to maintain size
    if scale > 1:
        # Crop center
        left = (new_size[0] - IMAGE_SIZE[0]) // 2
        top = (new_size[1] - IMAGE_SIZE[1]) // 2
        img = img.crop((left, top, left + IMAGE_SIZE[0], top + IMAGE_SIZE[1]))
    elif scale < 1:
        # Pad with white
        new_img = Image.new('L', IMAGE_SIZE, color=255)
        left = (IMAGE_SIZE[0] - new_size[0]) // 2
        top = (IMAGE_SIZE[1] - new_size[1]) // 2
        new_img.paste(img, (left, top))
        img = new_img
    
    # Gaussian blur (occasional)
    if random.random() < 0.3:
        radius = random.uniform(0.5, 2.0)
        img = img.filter(ImageFilter.GaussianBlur(radius))
    
    # Add noise
    if random.random() < 0.5:
        img_array = np.array(img)
        noise = np.random.normal(0, random.uniform(5, 15), img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(img_array)
    
    # Adjust brightness/contrast
    if random.random() < 0.4:
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(random.uniform(0.8, 1.2))
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(random.uniform(0.8, 1.3))
    
    return img

def generate_dataset(output_dir, split='train', samples_per_class=50):
    """
    Generate complete OCR dataset.
    
    Args:
        output_dir: Root directory for dataset
        split: 'train' or 'val'
        samples_per_class: Number of samples per character
    """
    split_dir = Path(output_dir) / split
    split_dir.mkdir(parents=True, exist_ok=True)
    
    font = get_font(size=60)
    
    print(f"Generating {split} dataset...")
    print(f"Samples per class: {samples_per_class}")
    print(f"Total classes: {len(CHARSET)}")
    print(f"Total images: {samples_per_class * len(CHARSET)}")
    
    total_generated = 0
    
    for char in CHARSET:
        # Create directory for this character
        char_dir = split_dir / char
        char_dir.mkdir(exist_ok=True)
        
        # Generate samples
        for i in range(samples_per_class):
            img = generate_character_image(char, font, augment=(split == 'train'))
            
            # Save image
            filename = f"{char}_{i:04d}.png"
            img.save(char_dir / filename)
            
            total_generated += 1
            
            if total_generated % 100 == 0:
                print(f"  Generated {total_generated}/{samples_per_class * len(CHARSET)} images...")
    
    print(f"✓ {split} dataset complete: {total_generated} images")
    return total_generated

def create_info_file(output_dir):
    """Create dataset information file."""
    info = f"""OCR Dataset for CNN Training
==============================
Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Dataset Structure:
- Image size: {IMAGE_SIZE[0]}x{IMAGE_SIZE[1]} pixels
- Color mode: Grayscale (1 channel)
- Character set: {CHARSET}
- Number of classes: {len(CHARSET)}

Splits:
- Train: {TRAIN_SAMPLES_PER_CLASS} samples per class = {TRAIN_SAMPLES_PER_CLASS * len(CHARSET)} images
- Validation: {VAL_SAMPLES_PER_CLASS} samples per class = {VAL_SAMPLES_PER_CLASS * len(CHARSET)} images
- Total: {TRAIN_SAMPLES_PER_CLASS * len(CHARSET) + VAL_SAMPLES_PER_CLASS * len(CHARSET)} images

Augmentations (train only):
- Rotation: ±10 degrees
- Scaling: 90-110%
- Gaussian blur: 30% probability
- Noise: 50% probability
- Brightness/contrast: 40% probability

Course Compliance:
- CNN input: 128x128x1 (grayscale)
- Classification: 36 classes (0-9, A-Z)
- Use case: Document OCR (cédulas, RUT)
"""
    
    info_path = Path(output_dir) / "dataset_info.txt"
    with open(info_path, 'w') as f:
        f.write(info)
    
    print(f"\nDataset info saved to: {info_path}")

def verify_dataset(output_dir):
    """Verify generated dataset."""
    print("\nVerifying dataset...")
    
    train_dir = Path(output_dir) / 'train'
    val_dir = Path(output_dir) / 'val'
    
    # Count images
    train_count = sum(1 for _ in train_dir.rglob('*.png'))
    val_count = sum(1 for _ in val_dir.rglob('*.png'))
    
    print(f"  Train images: {train_count}")
    print(f"  Val images: {val_count}")
    print(f"  Total: {train_count + val_count}")
    
    # Check class distribution
    train_classes = len(list(train_dir.iterdir()))
    val_classes = len(list(val_dir.iterdir()))
    
    print(f"  Train classes: {train_classes}")
    print(f"  Val classes: {val_classes}")
    
    # Sample a few images
    print("\n  Sample images:")
    for i, img_path in enumerate(train_dir.rglob('*.png')):
        if i >= 5:
            break
        print(f"    - {img_path.relative_to(output_dir)}")

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic OCR dataset')
    parser.add_argument('--output', '-o', type=str, default='data/ocr_dataset',
                       help='Output directory for dataset')
    parser.add_argument('--train-samples', type=int, default=50,
                       help='Samples per class for training')
    parser.add_argument('--val-samples', type=int, default=15,
                       help='Samples per class for validation')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("OCR DATASET GENERATION FOR CNN TRAINING")
    print("=" * 60)
    print(f"Output directory: {args.output}")
    print()
    
    # Generate datasets
    global TRAIN_SAMPLES_PER_CLASS, VAL_SAMPLES_PER_CLASS
    TRAIN_SAMPLES_PER_CLASS = args.train_samples
    VAL_SAMPLES_PER_CLASS = args.val_samples
    
    train_total = generate_dataset(args.output, 'train', args.train_samples)
    val_total = generate_dataset(args.output, 'val', args.val_samples)
    
    # Create info file
    create_info_file(args.output)
    
    # Verify
    verify_dataset(args.output)
    
    print("\n" + "=" * 60)
    print(f"✓ Dataset generation complete!")
    print(f"  Total images: {train_total + val_total}")
    print(f"  Location: {Path(args.output).absolute()}")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Train CNN: python cnn_ocr.py")
    print("  2. Test OCR: python test_ocr.py")
    print("  3. Integrate with backend")

if __name__ == "__main__":
    main()
