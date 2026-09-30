import os
import torch
import timm
from torchvision import transforms
from PIL import Image
import csv
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def load_model(path, device):
    model = timm.create_model('efficientnet_b0', pretrained=False, num_classes=2)
    model.load_state_dict(torch.load(path, map_location=device, weights_only=True))
    model.to(device)
    model.eval()
    return model

class SimpleDataset(torch.utils.data.Dataset):
    def __init__(self, csv_file, transform=None):
        self.data = []
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.data.append((row['filepath'], 1 if row['label'] == 'LEAF' else 0))
        self.transform = transform
    def __len__(self): return len(self.data)
    def __getitem__(self, idx):
        path, label = self.data[idx]
        image = Image.open(path).convert('RGB')
        if self.transform: image = self.transform(image)
        return image, label

def evaluate_thresholds(model, loader, device):
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)[:, 1]
            all_preds.extend(probs.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
    print("--- VALIDATION THRESHOLD ANALYSIS ---")
    thresholds = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90]
    print(f"{'Threshold':<10}| {'TP':<5}| {'TN':<5}| {'FP':<5}| {'FN':<5}| {'Prec':<7}| {'Rec':<7}| {'F1':<7}| {'False Acc':<10}| {'False Rej':<10}")
    for t in thresholds:
        preds = [1 if p >= t else 0 for p in all_preds]
        cm = confusion_matrix(all_labels, preds)
        if cm.shape == (2,2):
            tn, fp, fn, tp = cm.ravel()
        else:
            tn, fp, fn, tp = 0, 0, 0, 0
        prec = precision_score(all_labels, preds, zero_division=0)
        rec = recall_score(all_labels, preds, zero_division=0)
        f1 = f1_score(all_labels, preds, zero_division=0)
        false_acc = fp / (fp + tn) if (fp + tn) > 0 else 0
        false_rej = fn / (fn + tp) if (fn + tp) > 0 else 0
        print(f"{t:<10.2f}| {tp:<5}| {tn:<5}| {fp:<5}| {fn:<5}| {prec:<7.4f}| {rec:<7.4f}| {f1:<7.4f}| {false_acc:<10.4f}| {false_rej:<10.4f}")

def test_image(model, path, device, transform):
    print(f"\n--- TESTING IMAGE: {os.path.basename(path)} ---")
    if not os.path.exists(path):
        print("Image not found locally.")
        return
        
    image = Image.open(path).convert('RGB')
    input_tensor = transform(image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(input_tensor)
        probs = torch.softmax(outputs, dim=1)[0]
    
    prob_non_leaf = probs[0].item()
    prob_leaf = probs[1].item()
    
    pred_class = "LEAF" if prob_leaf >= 0.50 else "NON_LEAF"
    
    print(f"Predicted class (thresh 0.50): {pred_class}")
    print(f"Raw logits: {outputs[0].cpu().numpy()}")
    print(f"Softmax P(leaf): {prob_leaf:.4f}")
    print(f"Softmax P(non_leaf): {prob_non_leaf:.4f}")

if __name__ == "__main__":
    device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
    model = load_model("models/student_v3_leaf_verifier.pth", device)
    
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    val_ds = SimpleDataset("data/student_v3_dataset/val.csv", transform=transform)
    val_loader = torch.utils.data.DataLoader(val_ds, batch_size=32, shuffle=False)
    
    evaluate_thresholds(model, val_loader, device)
    
    test_image(model, "tests/ml/test_images/G_blurry_leaf.jpg", device, transform)
    test_image(model, "tests/ml/test_images/D_non_leaf_object.jpg", device, transform)
    test_image(model, "tests/ml/test_images/A_clear_leaf.jpg", device, transform)
