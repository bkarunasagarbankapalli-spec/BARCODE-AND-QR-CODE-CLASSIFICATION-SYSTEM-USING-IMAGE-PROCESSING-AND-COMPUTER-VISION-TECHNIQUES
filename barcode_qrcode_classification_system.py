"""
Barcode and QR Code Classification System
Classifies barcode and QR code images using image processing and computer vision
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image, ImageDraw
import cv2
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score, roc_curve
import warnings
warnings.filterwarnings('ignore')

# Set style for visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

def generate_barcode_image(width=200, height=80, code_type='barcode'):
    """Generate synthetic barcode image"""
    img = Image.new('L', (width, height), color=255)
    draw = ImageDraw.Draw(img)
    
    # Draw barcode pattern (vertical lines)
    bar_width = 3
    for i in range(0, width, bar_width * 2):
        thickness = np.random.randint(2, 4)
        draw.rectangle([i, 10, i + thickness, height - 10], fill=0)
    
    return np.array(img)

def generate_qrcode_image(width=200, height=200, code_type='qrcode'):
    """Generate synthetic QR code image"""
    img = Image.new('L', (width, height), color=255)
    draw = ImageDraw.Draw(img)
    
    # Draw position markers (3 corners)
    marker_size = 40
    positions = [(0, 0), (width - marker_size, 0), (0, height - marker_size)]
    
    for x, y in positions:
        # Outer square
        draw.rectangle([x, y, x + marker_size, y + marker_size], outline=0, width=2)
        # Inner square
        draw.rectangle([x + 8, y + 8, x + marker_size - 8, y + marker_size - 8], fill=0)
        # Center square
        draw.rectangle([x + 12, y + 12, x + marker_size - 12, y + marker_size - 12], fill=255)
    
    # Fill QR code area with random pattern
    for i in range(50, width - 50, 5):
        for j in range(50, height - 50, 5):
            if np.random.rand() > 0.5:
                draw.rectangle([i, j, i + 4, j + 4], fill=0)
    
    return np.array(img)

def extract_features(image):
    """Extract features from barcode/QR code image"""
    # Resize image to standard size
    img = cv2.resize(image, (100, 100))
    
    # Convert to grayscale if needed
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    features = {}
    
    # Basic statistics
    features['mean_intensity'] = np.mean(img)
    features['std_intensity'] = np.std(img)
    features['min_intensity'] = np.min(img)
    features['max_intensity'] = np.max(img)
    
    # Edge detection
    edges = cv2.Canny(img, 100, 200)
    features['edge_density'] = np.sum(edges) / (100 * 100)
    
    # Contour analysis
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    features['contour_count'] = len(contours)
    
    # Histogram analysis
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    features['histogram_variance'] = np.var(hist)
    
    # Horizontal and vertical projections
    h_projection = np.sum(edges, axis=1)
    v_projection = np.sum(edges, axis=0)
    features['h_projection_variance'] = np.var(h_projection)
    features['v_projection_variance'] = np.var(v_projection)
    
    # Aspect ratio
    features['aspect_ratio'] = 100 / 100  # Square
    
    # Line detection
    lines = cv2.HoughLines(edges, 1, np.pi/180, 50)
    features['line_count'] = len(lines) if lines is not None else 0
    
    # Moments
    M = cv2.moments(edges)
    if M['m00'] != 0:
        features['centroid_x'] = M['m10'] / M['m00']
        features['centroid_y'] = M['m01'] / M['m00']
    else:
        features['centroid_x'] = 50
        features['centroid_y'] = 50
    
    return features

def generate_dataset(n_samples=200, random_state=42):
    """Generate synthetic dataset of barcode and QR code images"""
    np.random.seed(random_state)
    
    images = []
    labels = []
    feature_list = []
    
    # Generate barcodes
    for i in range(n_samples // 2):
        img = generate_barcode_image()
        images.append(img)
        labels.append('Barcode')
        features = extract_features(img)
        feature_list.append(features)
    
    # Generate QR codes
    for i in range(n_samples // 2):
        img = generate_qrcode_image()
        images.append(img)
        labels.append('QR Code')
        features = extract_features(img)
        feature_list.append(features)
    
    # Create feature dataframe
    features_df = pd.DataFrame(feature_list)
    features_df['Label'] = labels
    
    return images, labels, features_df

def train_classifiers(X_train, X_test, y_train, y_test):
    """Train multiple classification models"""
    models = {}
    results = []
    
    # Random Forest
    print("Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    y_proba_rf = rf.predict_proba(X_test)[:, 1]
    
    models['Random Forest'] = rf
    results.append({
        'Model': 'Random Forest',
        'Accuracy': accuracy_score(y_test, y_pred_rf),
        'Precision': precision_score(y_test, y_pred_rf, average='weighted'),
        'Recall': recall_score(y_test, y_pred_rf, average='weighted'),
        'F1-Score': f1_score(y_test, y_pred_rf, average='weighted'),
        'ROC-AUC': roc_auc_score((y_test == 'QR Code').astype(int), y_proba_rf)
    })
    
    # Support Vector Machine
    print("Training SVM...")
    svm = SVC(kernel='rbf', probability=True, random_state=42)
    svm.fit(X_train, y_train)
    y_pred_svm = svm.predict(X_test)
    y_proba_svm = svm.predict_proba(X_test)[:, 1]
    
    models['SVM'] = svm
    results.append({
        'Model': 'SVM',
        'Accuracy': accuracy_score(y_test, y_pred_svm),
        'Precision': precision_score(y_test, y_pred_svm, average='weighted'),
        'Recall': recall_score(y_test, y_pred_svm, average='weighted'),
        'F1-Score': f1_score(y_test, y_pred_svm, average='weighted'),
        'ROC-AUC': roc_auc_score((y_test == 'QR Code').astype(int), y_proba_svm)
    })
    
    # Neural Network
    print("Training Neural Network...")
    nn = MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
    nn.fit(X_train, y_train)
    y_pred_nn = nn.predict(X_test)
    y_proba_nn = nn.predict_proba(X_test)[:, 1]
    
    models['Neural Network'] = nn
    results.append({
        'Model': 'Neural Network',
        'Accuracy': accuracy_score(y_test, y_pred_nn),
        'Precision': precision_score(y_test, y_pred_nn, average='weighted'),
        'Recall': recall_score(y_test, y_pred_nn, average='weighted'),
        'F1-Score': f1_score(y_test, y_pred_nn, average='weighted'),
        'ROC-AUC': roc_auc_score((y_test == 'QR Code').astype(int), y_proba_nn)
    })
    
    return models, pd.DataFrame(results)

def plot_code_samples(images, labels):
    """Plot sample barcode and QR code images"""
    fig, axes = plt.subplots(2, 5, figsize=(14, 6))
    
    barcode_count = 0
    qrcode_count = 0
    
    for idx, (img, label) in enumerate(zip(images[:10], labels[:10])):
        row = idx // 5
        col = idx % 5
        
        axes[row, col].imshow(img, cmap='gray')
        axes[row, col].set_title(label, fontsize=11, fontweight='bold')
        axes[row, col].axis('off')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/barcode_qrcode_samples.png', dpi=300, bbox_inches='tight')
    print("Saved: barcode_qrcode_samples.png")
    plt.close()

def plot_feature_distributions(features_df):
    """Plot feature distributions by code type"""
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    
    features_to_plot = ['mean_intensity', 'edge_density', 'contour_count', 
                       'h_projection_variance', 'v_projection_variance', 'line_count']
    
    for idx, feature in enumerate(features_to_plot):
        row = idx // 3
        col = idx % 3
        
        for label in ['Barcode', 'QR Code']:
            data = features_df[features_df['Label'] == label][feature]
            axes[row, col].hist(data, alpha=0.6, label=label, bins=15, edgecolor='black', linewidth=1.5)
        
        axes[row, col].set_xlabel(feature, fontsize=10, fontweight='bold')
        axes[row, col].set_ylabel('Frequency', fontsize=10, fontweight='bold')
        axes[row, col].set_title(f'{feature} Distribution', fontsize=11, fontweight='bold')
        axes[row, col].legend()
        axes[row, col].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/barcode_qrcode_feature_distributions.png', dpi=300, bbox_inches='tight')
    print("Saved: barcode_qrcode_feature_distributions.png")
    plt.close()

def plot_model_comparison(results_df):
    """Plot model performance comparison"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'ROC-AUC']
    x = np.arange(len(results_df))
    width = 0.15
    
    for idx, metric in enumerate(metrics):
        axes[0].bar(x + idx * width, results_df[metric], width, label=metric, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    axes[0].set_xlabel('Model', fontsize=11, fontweight='bold')
    axes[0].set_ylabel('Score', fontsize=11, fontweight='bold')
    axes[0].set_title('Model Performance Comparison', fontsize=12, fontweight='bold')
    axes[0].set_xticks(x + width * 2)
    axes[0].set_xticklabels(results_df['Model'], fontsize=10)
    axes[0].legend(fontsize=9)
    axes[0].grid(axis='y', alpha=0.3)
    axes[0].set_ylim([0, 1.1])
    
    # Radar-like comparison
    models = results_df['Model'].tolist()
    accuracy_scores = results_df['Accuracy'].tolist()
    
    colors = ['#3498db', '#e74c3c', '#2ecc71']
    axes[1].bar(models, accuracy_scores, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    axes[1].set_ylabel('Accuracy', fontsize=11, fontweight='bold')
    axes[1].set_title('Model Accuracy Comparison', fontsize=12, fontweight='bold')
    axes[1].grid(axis='y', alpha=0.3)
    axes[1].set_ylim([0, 1.1])
    
    for i, v in enumerate(accuracy_scores):
        axes[1].text(i, v + 0.02, f'{v:.3f}', ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/barcode_qrcode_model_comparison.png', dpi=300, bbox_inches='tight')
    print("Saved: barcode_qrcode_model_comparison.png")
    plt.close()

def plot_confusion_matrices(models, X_test, y_test):
    """Plot confusion matrices for all models"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    
    for idx, (model_name, model) in enumerate(models.items()):
        y_pred = model.predict(X_test)
        cm = confusion_matrix(y_test, y_pred, labels=['Barcode', 'QR Code'])
        
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx], 
                   xticklabels=['Barcode', 'QR Code'], yticklabels=['Barcode', 'QR Code'],
                   cbar=False, annot_kws={'fontsize': 11, 'fontweight': 'bold'})
        axes[idx].set_title(f'{model_name} Confusion Matrix', fontsize=12, fontweight='bold')
        axes[idx].set_ylabel('True Label', fontsize=10, fontweight='bold')
        axes[idx].set_xlabel('Predicted Label', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/barcode_qrcode_confusion_matrices.png', dpi=300, bbox_inches='tight')
    print("Saved: barcode_qrcode_confusion_matrices.png")
    plt.close()

def plot_roc_curves(models, X_test, y_test):
    """Plot ROC curves for all models"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = ['#3498db', '#e74c3c', '#2ecc71']
    
    for idx, (model_name, model) in enumerate(models.items()):
        y_proba = model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve((y_test == 'QR Code').astype(int), y_proba)
        auc = roc_auc_score((y_test == 'QR Code').astype(int), y_proba)
        
        ax.plot(fpr, tpr, color=colors[idx], lw=2, label=f'{model_name} (AUC = {auc:.3f})', marker='o', markersize=4)
    
    ax.plot([0, 1], [0, 1], 'k--', lw=2, label='Random Classifier')
    ax.set_xlabel('False Positive Rate', fontsize=11, fontweight='bold')
    ax.set_ylabel('True Positive Rate', fontsize=11, fontweight='bold')
    ax.set_title('ROC Curves - Barcode vs QR Code Classification', fontsize=12, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/barcode_qrcode_roc_curves.png', dpi=300, bbox_inches='tight')
    print("Saved: barcode_qrcode_roc_curves.png")
    plt.close()

def main():
    print("="*80)
    print("BARCODE AND QR CODE CLASSIFICATION SYSTEM - IMAGE PROCESSING")
    print("="*80)
    
    # Generate dataset
    print("\n[1] Generating synthetic barcode and QR code dataset...")
    images, labels, features_df = generate_dataset(n_samples=200)
    features_df.to_csv('/home/ubuntu/barcode_qrcode_features.csv', index=False)
    print(f"Dataset generated: {len(images)} images")
    print(f"Class distribution: {pd.Series(labels).value_counts().to_dict()}")
    
    # Prepare features for classification
    print("\n[2] Preparing features for classification...")
    X = features_df.drop('Label', axis=1).values
    y = features_df['Label'].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"Training set: {len(X_train)}, Test set: {len(X_test)}")
    
    # Train models
    print("\n[3] Training classification models...")
    models, results_df = train_classifiers(X_train, X_test, y_train, y_test)
    results_df.to_csv('/home/ubuntu/barcode_qrcode_model_results.csv', index=False)
    print("\nModel Results:")
    print(results_df.to_string(index=False))
    
    # Generate visualizations
    print("\n[4] Generating visualizations...")
    plot_code_samples(images, labels)
    plot_feature_distributions(features_df)
    plot_model_comparison(results_df)
    plot_confusion_matrices(models, X_test, y_test)
    plot_roc_curves(models, X_test, y_test)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE - All visualizations saved")
    print("="*80)

if __name__ == "__main__":
    main()
