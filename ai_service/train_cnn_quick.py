"""
Quick CNN Training Script for Course Demonstration
Trains CNN on synthetic OCR data in ~10-15 minutes
"""
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import numpy as np
from pathlib import Path
import json
import time

def train_cnn_quick(epochs=15, batch_size=32):
    """
    Train CNN quickly for course demonstration.
    
    Args:
        epochs: Number of training epochs (default: 15, enough for demo)
        batch_size: Batch size for training
    
    Returns:
        model: Trained CNN model
        history: Training history
    """
    
    print("=" * 60)
    print("CNN OCR TRAINING - COURSE DEMONSTRATION")
    print("=" * 60)
    print(f"Epochs: {epochs}")
    print(f"Batch size: {batch_size}")
    print()
    
    # Check for dataset
    dataset_dir = Path("data/ocr_dataset")
    if not dataset_dir.exists():
        print("ERROR: Dataset not found!")
        print("Run first: python generate_synthetic_ocr_data.py")
        return None, None
    
    # Data augmentation for training
    train_datagen = ImageDataGenerator(
        rescale=1./255,  # Normalize to [0,1]
        rotation_range=10,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.1,
        brightness_range=[0.8, 1.2],
        fill_mode='nearest'
    )
    
    # Only rescaling for validation
    val_datagen = ImageDataGenerator(rescale=1./255)
    
    # Load training data
    print("Loading training data...")
    train_generator = train_datagen.flow_from_directory(
        dataset_dir / 'train',
        target_size=(128, 128),
        color_mode='grayscale',
        batch_size=batch_size,
        class_mode='categorical',
        shuffle=True
    )
    
    # Load validation data
    print("Loading validation data...")
    val_generator = val_datagen.flow_from_directory(
        dataset_dir / 'val',
        target_size=(128, 128),
        color_mode='grayscale',
        batch_size=batch_size,
        class_mode='categorical',
        shuffle=False
    )
    
    num_classes = len(train_generator.class_indices)
    print(f"\nClasses: {num_classes}")
    print(f"Training samples: {train_generator.samples}")
    print(f"Validation samples: {val_generator.samples}")
    
    # Build CNN model
    print("\nBuilding CNN architecture...")
    model = tf.keras.Sequential([
        # Block 1
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu', 
                            input_shape=(128, 128, 1),
                            padding='same'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Dropout(0.25),
        
        # Block 2
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Dropout(0.25),
        
        # Block 3
        tf.keras.layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Dropout(0.25),
        
        # Block 4
        tf.keras.layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Dropout(0.25),
        
        # Classification head
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(512, activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(num_classes, activation='softmax')
    ])
    
    # Compile model
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy', 
                tf.keras.metrics.Precision(name='precision'),
                tf.keras.metrics.Recall(name='recall')]
    )
    
    # Model summary
    model.summary()
    print()
    
    # Callbacks
    callbacks = [
        EarlyStopping(
            monitor='val_accuracy',
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1
        ),
        ModelCheckpoint(
            'models/saved/cnn_ocr_best.h5',
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        )
    ]
    
    # Train
    print("Starting training...")
    print("=" * 60)
    start_time = time.time()
    
    history = model.fit(
        train_generator,
        epochs=epochs,
        validation_data=val_generator,
        callbacks=callbacks,
        verbose=1
    )
    
    training_time = time.time() - start_time
    
    # Evaluate
    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)
    
    val_loss, val_acc, val_precision, val_recall = model.evaluate(val_generator)
    
    print(f"\nValidation Accuracy: {val_acc:.4f}")
    print(f"Validation Precision: {val_precision:.4f}")
    print(f"Validation Recall: {val_recall:.4f}")
    print(f"Training time: {training_time/60:.1f} minutes")
    
    # Save model in multiple formats
    print("\nSaving models...")
    
    # 1. Native Keras format (recommended for Keras 3.x)
    model.save('models/saved/cnn_ocr_final.keras')
    print("  ✓ Saved: cnn_ocr_final.keras")
    
    # 2. Legacy H5 format (for compatibility)
    model.save('models/saved/cnn_ocr_final.h5')
    print("  ✓ Saved: cnn_ocr_final.h5")
    
    # 3. SavedModel format for TensorFlow Serving (Keras 3.x)
    model.export('models/saved/cnn_ocr_savedmodel')
    print("  ✓ Saved: cnn_ocr_savedmodel/")
    
    # 3. Save class indices
    with open('models/saved/cnn_ocr_classes.json', 'w') as f:
        json.dump(train_generator.class_indices, f, indent=2)
    print("  ✓ Saved: cnn_ocr_classes.json")
    
    # 4. Save training history
    history_dict = {
        'accuracy': [float(x) for x in history.history['accuracy']],
        'val_accuracy': [float(x) for x in history.history['val_accuracy']],
        'loss': [float(x) for x in history.history['loss']],
        'val_loss': [float(x) for x in history.history['val_loss']],
        'training_time_seconds': training_time
    }
    
    with open('models/saved/cnn_ocr_history.json', 'w') as f:
        json.dump(history_dict, f, indent=2)
    print("  ✓ Saved: cnn_ocr_history.json")
    
    # Print course compliance summary
    print("\n" + "=" * 60)
    print("COURSE COMPLIANCE SUMMARY")
    print("=" * 60)
    print("✓ CNN Architecture:")
    print("  - 4 Conv2D blocks (32, 64, 128, 256 filters)")
    print("  - BatchNormalization after each conv")
    print("  - MaxPooling2D for downsampling")
    print("  - Dropout for regularization (0.25-0.5)")
    print("  - Dense classification head (512, 256, 36)")
    print()
    print("✓ Training Features:")
    print("  - Data augmentation (rotation, shift, zoom)")
    print("  - Early stopping")
    print("  - Learning rate reduction on plateau")
    print("  - Model checkpointing")
    print()
    print(f"✓ Results: {val_acc:.1%} validation accuracy")
    print(f"✓ Training time: {training_time/60:.1f} minutes")
    print("=" * 60)
    
    return model, history

if __name__ == "__main__":
    import sys
    
    # Check if dataset exists
    if not Path("data/ocr_dataset").exists():
        print("Dataset not found. Generating first...")
        import subprocess
        subprocess.run([sys.executable, "generate_synthetic_ocr_data.py"])
    
    # Train model
    model, history = train_cnn_quick(epochs=15, batch_size=32)
    
    if model:
        print("\n✓ CNN training complete!")
        print("\nNext steps:")
        print("  1. Test the model: python test_cnn.py")
        print("  2. Integrate with Flask API")
        print("  3. Update documentation")
