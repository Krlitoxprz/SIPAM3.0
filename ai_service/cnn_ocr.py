"""
CNN-OCR-01 - Convolutional Neural Network for Document OCR
Extracts text from ID cards and documents uploaded by students.
"""
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
import cv2
from pathlib import Path

class DocumentOCR:
    """
    CNN for Optical Character Recognition on student documents.
    Architecture: Conv -> Pool -> Conv -> Pool -> Dense -> Output
    """
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.input_shape = (128, 128, 1)  # Grayscale images
        self.num_classes = 37  # 0-9 digits + A-Z letters + blank
        
        if model_path and Path(model_path).exists():
            self.model = tf.keras.models.load_model(model_path)
        else:
            self.build_model()
    
    def build_model(self):
        """
        Build CNN architecture following course requirements:
        - Multiple Conv2D layers with ReLU
        - MaxPooling for dimensionality reduction
        - BatchNormalization for stability
        - Dropout for regularization
        """
        self.model = models.Sequential([
            # Block 1: Feature extraction (edges, corners)
            layers.Conv2D(32, (3, 3), activation='relu', 
                         input_shape=self.input_shape,
                         padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),
            
            # Block 2: Higher level features (shapes)
            layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),
            
            # Block 3: Complex patterns (character parts)
            layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),
            
            # Block 4: Deep features
            layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),
            
            # Classification head
            layers.Flatten(),
            layers.Dense(512, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            layers.Dense(256, activation='relu'),
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        # Compile with appropriate optimizer for course requirements
        self.model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy', tf.keras.metrics.Precision(), 
                    tf.keras.metrics.Recall()]
        )
        
        print("CNN-OCR Model built successfully")
        self.model.summary()
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for CNN input.
        """
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (128, 128))
        img = img / 255.0  # Normalize
        img = np.expand_dims(img, axis=-1)  # Add channel dimension
        return img
    
    def extract_text(self, image_path: str) -> dict:
        """
        Extract text from document image.
        Returns extracted text and confidence scores.
        """
        if self.model is None:
            return {"error": "Model not loaded"}
        
        img = self.preprocess_image(image_path)
        img_batch = np.expand_dims(img, axis=0)
        
        predictions = self.model.predict(img_batch)
        
        # Decode predictions to text
        # (Simplified - in production would use CTC decoder)
        return {
            "extracted_text": self._decode_predictions(predictions),
            "confidence": float(np.max(predictions)),
            "model": "CNN-OCR-v1"
        }
    
    def _decode_predictions(self, predictions: np.ndarray) -> str:
        """Decode model predictions to characters."""
        charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
        decoded = ""
        for pred in predictions[0]:
            idx = np.argmax(pred)
            decoded += charset[idx]
        return decoded[:10]  # Return first 10 chars
    
    def train(self, train_dir: str, val_dir: str, epochs: int = 50):
        """
        Train CNN with data augmentation (course requirement).
        """
        # Data augmentation for better generalization
        train_datagen = ImageDataGenerator(
            rotation_range=10,
            width_shift_range=0.1,
            height_shift_range=0.1,
            zoom_range=0.1,
            brightness_range=[0.8, 1.2]
        )
        
        # Load data
        train_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=(128, 128),
            color_mode='grayscale',
            batch_size=32,
            class_mode='categorical'
        )
        
        val_generator = ImageDataGenerator().flow_from_directory(
            val_dir,
            target_size=(128, 128),
            color_mode='grayscale',
            batch_size=32,
            class_mode='categorical'
        )
        
        # Train with callbacks
        callbacks = [
            tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            tf.keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5),
            tf.keras.callbacks.ModelCheckpoint('cnn_ocr_best.keras', save_best_only=True)
        ]
        
        history = self.model.fit(
            train_generator,
            validation_data=val_generator,
            epochs=epochs,
            callbacks=callbacks
        )
        
        return history


# Factory function for Flask integration
def get_ocr_model() -> DocumentOCR:
    """Get or initialize OCR model singleton."""
    # Try modern .keras format first, then .h5 for compatibility
    model_dir = Path(__file__).parent / "saved"
    # Try final model first, then best, then h5 versions
    for model_name in ["cnn_ocr_final.keras", "cnn_ocr_best.keras", 
                       "cnn_ocr_final.h5", "cnn_ocr_best.h5"]:
        model_path = model_dir / model_name
        if model_path.exists():
            print(f"Loading CNN OCR model: {model_name}")
            return DocumentOCR(str(model_path))
    
    print("No trained CNN OCR model found. Building new model.")
    return DocumentOCR(None)


if __name__ == "__main__":
    # Demo/test
    ocr = DocumentOCR()
    print("CNN-OCR model initialized for course compliance")
    print(f"Input shape: {ocr.input_shape}")
    print(f"Number of classes: {ocr.num_classes}")
