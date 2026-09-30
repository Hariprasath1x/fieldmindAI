import os
import csv
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import timm

class LeafDataset(Dataset):
    def __init__(self, csv_file, transform=None):
        self.data = []
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.data.append((row['filepath'], 1 if row['label'] == 'LEAF' else 0))
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        path, label = self.data[idx]
        image = Image.open(path).convert('RGB')
        if self.transform:
            image = self.transform(image)
        return image, label

def evaluate(model, loader, device, thresholds=[0.5]):
    model.eval()
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)[:, 1] # Probability of LEAF
            all_preds.extend(probs.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
    metrics = {}
    for t in thresholds:
        preds = [1 if p >= t else 0 for p in all_preds]
        metrics[t] = {
            'accuracy': accuracy_score(all_labels, preds),
            'precision': precision_score(all_labels, preds, zero_division=0),
            'recall': recall_score(all_labels, preds, zero_division=0),
            'f1': f1_score(all_labels, preds, zero_division=0)
        }
    return metrics, all_preds, all_labels

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # 8. Simple realistic augmentation
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    eval_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    base_dir = "data/student_v3_dataset"
    train_ds = LeafDataset(f"{base_dir}/train.csv", transform=train_transform)
    val_ds = LeafDataset(f"{base_dir}/val.csv", transform=eval_transform)
    test_ds = LeafDataset(f"{base_dir}/test.csv", transform=eval_transform)
    
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False)
    
    # 7. EfficientNet-B0
    model = timm.create_model('efficientnet_b0', pretrained=True, num_classes=2)
    model = model.to(device)
    
    # 9. Train normally
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    
    epochs = 3 # Keep it fast for student project iteration
    
    print("Starting training...")
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{epochs} - Loss: {running_loss/len(train_loader):.4f}")
        
    print("\nEvaluating on Validation Set...")
    # 11. Threshold analysis on VALIDATION
    thresholds = [0.50, 0.60, 0.70, 0.80, 0.90]
    val_metrics, _, _ = evaluate(model, val_loader, device, thresholds)
    
    best_t = 0.5
    best_f1 = 0
    print("Validation Threshold Analysis:")
    for t, m in val_metrics.items():
        print(f"  Threshold {t:.2f} -> Acc: {m['accuracy']:.4f}, Prec: {m['precision']:.4f}, Rec: {m['recall']:.4f}, F1: {m['f1']:.4f}")
        if m['f1'] > best_f1:
            best_f1 = m['f1']
            best_t = t
            
    print(f"\nSelected Threshold (based on Val F1): {best_t:.2f}")
    
    print("\nEvaluating on locked Test Set...")
    # 13. Evaluate once on locked test set
    test_metrics, test_preds, test_labels = evaluate(model, test_loader, device, [best_t])
    tm = test_metrics[best_t]
    
    preds_binary = [1 if p >= best_t else 0 for p in test_preds]
    cm = confusion_matrix(test_labels, preds_binary)
    
    print(f"Test Accuracy:  {tm['accuracy']:.4f}")
    print(f"Test Precision: {tm['precision']:.4f}")
    print(f"Test Recall:    {tm['recall']:.4f}")
    print(f"Test F1-Score:  {tm['f1']:.4f}")
    print("Confusion Matrix:")
    print(cm)
    
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), "models/student_v3_leaf_verifier.pth")
    print("Model saved to models/student_v3_leaf_verifier.pth")

if __name__ == "__main__":
    main()
