import os
import shutil
import random
from pathlib import Path
from PIL import Image

try:
    from datasets import load_dataset
except ImportError:
    print("Please install datasets")
    import sys
    sys.exit(1)

def main():
    base_dir = Path("data/student_v3_dataset")
    leaf_dir = base_dir / "LEAF"
    non_leaf_dir = base_dir / "NON_LEAF"
    
    if base_dir.exists():
        shutil.rmtree(base_dir)
        
    leaf_dir.mkdir(parents=True, exist_ok=True)
    non_leaf_dir.mkdir(parents=True, exist_ok=True)
    
    print("Downloading LEAF images from HuggingFace (beans dataset)...")
    leaf_ds = load_dataset("AI-Lab-Makerere/beans", split="train")
    
    leaf_count = 0
    for i, item in enumerate(leaf_ds):
        if leaf_count >= 750:
            break
        img = item['image']
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(leaf_dir / f"hf_beans_{i}.jpg")
        leaf_count += 1
        
    print(f"Saved {leaf_count} LEAF images.")

    print("Downloading NON_LEAF images from HuggingFace (flowers)...")
    flower_ds = load_dataset("nelorth/oxford-flowers", split="train")
    
    non_leaf_count = 0
    for i, item in enumerate(flower_ds):
        if non_leaf_count >= 350:
            break
        img = item['image']
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(non_leaf_dir / f"hf_flower_{i}.jpg")
        non_leaf_count += 1
        
    print("Downloading NON_LEAF images from HuggingFace (cats/dogs)...")
    try:
        pet_ds = load_dataset("Bingsu/Cat_and_Dog", split="train")
        for i, item in enumerate(pet_ds):
            if non_leaf_count >= 700:
                break
            img = item['image']
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(non_leaf_dir / f"hf_pet_{i}.jpg")
            non_leaf_count += 1
    except Exception as e:
        print(f"Failed to load cats and dogs: {e}")
        
    # Copy FieldMind evaluation images
    print("Copying FieldMind test images...")
    fieldmind_test_dir = Path("tests/ml/test_images")
    fm_images = []
    if fieldmind_test_dir.exists():
        for p in fieldmind_test_dir.glob("*.jpg"):
            target = non_leaf_dir if "non_leaf" in p.name.lower() or "sky" in p.name.lower() or "human" in p.name.lower() else leaf_dir
            shutil.copy(p, target / p.name)
            fm_images.append(p.name)
            
    # Gather all images
    leaf_images = list(leaf_dir.glob("*.jpg"))
    non_leaf_images = list(non_leaf_dir.glob("*.jpg"))
    
    print(f"Total LEAF: {len(leaf_images)}")
    print(f"Total NON_LEAF: {len(non_leaf_images)}")
    
    # Simple deduplication by filename (and exact file size)
    # Since we are using fresh datasets, we assume minimal duplicates.
    
    # Splits (70/15/15)
    random.seed(42)
    random.shuffle(leaf_images)
    random.shuffle(non_leaf_images)
    
    def write_split(name, leaves, non_leaves):
        lines = ["filepath,label\n"]
        for p in leaves: lines.append(f"{p.absolute()},LEAF\n")
        for p in non_leaves: lines.append(f"{p.absolute()},NON_LEAF\n")
        with open(base_dir / f"{name}.csv", "w") as f:
            f.writelines(lines)
            
    # Keep FM images strictly in test set
    fm_leaves = [p for p in leaf_images if p.name in fm_images]
    fm_non_leaves = [p for p in non_leaf_images if p.name in fm_images]
    
    rem_leaves = [p for p in leaf_images if p.name not in fm_images]
    rem_non_leaves = [p for p in non_leaf_images if p.name not in fm_images]
    
    tl = int(len(rem_leaves) * 0.7)
    vl = int(len(rem_leaves) * 0.85)
    
    tn = int(len(rem_non_leaves) * 0.7)
    vn = int(len(rem_non_leaves) * 0.85)
    
    train_l, val_l, test_l = rem_leaves[:tl], rem_leaves[tl:vl], rem_leaves[vl:]
    train_n, val_n, test_n = rem_non_leaves[:tn], rem_non_leaves[tn:vn], rem_non_leaves[vn:]
    
    # Add FM images to test
    test_l.extend(fm_leaves)
    test_n.extend(fm_non_leaves)
    
    write_split("train", train_l, train_n)
    write_split("val", val_l, val_n)
    write_split("test", test_l, test_n)
    
    print("Dataset setup complete.")
    print(f"Train: {len(train_l) + len(train_n)}")
    print(f"Val: {len(val_l) + len(val_n)}")
    print(f"Test: {len(test_l) + len(test_n)}")

if __name__ == "__main__":
    main()
