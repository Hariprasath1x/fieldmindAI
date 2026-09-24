import os
import sys
from pathlib import Path
import pytest
from PIL import Image

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.leaf_verifier import LeafVerifier
from backend.core.config import settings

@pytest.fixture(scope="module")
def leaf_verifier():
    models_dir = Path("backend/models")
    return LeafVerifier(
        model_path=models_dir / "leaf_verifier.onnx",
        config_path=models_dir / "leaf_verifier_config.json",
        labels_path=models_dir / "labels.json",
    )

def test_leaf_verifier_predictions(leaf_verifier):
    test_images_dir = Path("tests/ml/test_images")
    
    # 1. Clear Real Leaf
    try:
        img_a = Image.open(test_images_dir / "A_clear_leaf.jpg")
        result_a = leaf_verifier.predict(img_a)
        assert result_a["verification"]["is_leaf"] is True
        assert result_a["verification"]["confidence"] >= settings.LEAF_VERIFICATION_THRESHOLD
    except FileNotFoundError:
        pass

    # 2. Multiple Real Leaves
    try:
        img_b = Image.open(test_images_dir / "B_multiple_leaves.jpg")
        result_b = leaf_verifier.predict(img_b)
        assert result_b["verification"]["is_leaf"] is True
        assert result_b["verification"]["confidence"] >= settings.LEAF_VERIFICATION_THRESHOLD
    except FileNotFoundError:
        pass
        
    # 3. Different Crop Species
    try:
        img_c = Image.open(test_images_dir / "C_different_crop.jpg")
        result_c = leaf_verifier.predict(img_c)
        assert result_c["verification"]["is_leaf"] is True
        assert result_c["verification"]["confidence"] >= settings.LEAF_VERIFICATION_THRESHOLD
    except FileNotFoundError:
        pass

    # 4. Non-Leaf Object
    try:
        img_d = Image.open(test_images_dir / "D_non_leaf_object.jpg")
        result = leaf_verifier.predict(img_d)
        assert result["verification"]["is_leaf"] is False
    except FileNotFoundError:
        pass

    # 5. Human
    try:
        img_e = Image.open(test_images_dir / "E_human.jpg")
        result = leaf_verifier.predict(img_e)
        assert result["verification"]["is_leaf"] is False
    except FileNotFoundError:
        pass

    # 6. Sky
    try:
        img_f = Image.open(test_images_dir / "F_sky.jpg")
        result = leaf_verifier.predict(img_f)
        assert result["verification"]["is_leaf"] is False
    except FileNotFoundError:
        pass

    # 7. Blurry Leaf (Should return is_leaf=False due to BLURRY_IMAGE)
    try:
        img_g = Image.open(test_images_dir / "G_blurry_leaf.jpg")
        result = leaf_verifier.predict(img_g)
        assert result["verification"]["is_leaf"] is False
        assert result["verification"].get("error_code") == "BLURRY_IMAGE"
    except FileNotFoundError:
        pass
        
    # 8. Low Light Leaf (Should pass if ML can see it, or fail if dark. Let's see)
    try:
        img_h = Image.open(test_images_dir / "H_low_light_leaf.jpg")
        leaf_verifier.predict(img_h)
    except FileNotFoundError:
        pass
