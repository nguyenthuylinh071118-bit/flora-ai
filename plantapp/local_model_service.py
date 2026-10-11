import os
import io
import logging
from functools import lru_cache
from pathlib import Path

import torch
from PIL import Image, ImageOps
from django.conf import settings
from torchvision import models, transforms
from torch import nn

logger = logging.getLogger(__name__)

EXPECTED_CLASSES = [
    "bong_trang",
    "cay_buoi",
    "cay_chuoi",
    "cay_phuong",
    "hoa_hong",
    "hoa_layon",
    "hoa_sen",
    "lan_mokara",
    "muong_trau",
    "vong_mong_ga",
]

IMAGE_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])



@lru_cache(maxsize=1)
def load_plant_model():
    model_path = Path(settings.BASE_DIR) / "plant_model_backup.pth"

    # Nếu Render chưa có mô hình, tự tải từ Google Drive
    if not model_path.is_file():
        model_url = os.environ.get("PLANT_MODEL_URL", "").strip()

        if not model_url:
            raise FileNotFoundError(
                "Chưa cấu hình biến môi trường PLANT_MODEL_URL trên Render."
            )

        import gdown

        logger.info("Đang tải mô hình nhận diện từ Google Drive...")

        downloaded_path = gdown.download(
            url=model_url,
            output=str(model_path),
            quiet=False,
            fuzzy=True,
        )

        if (
            not downloaded_path
            or not model_path.is_file()
            or model_path.stat().st_size < 1_000_000
        ):
            model_path.unlink(missing_ok=True)
            raise RuntimeError(
                "Không tải được file mô hình hợp lệ từ Google Drive. "
                "Hãy kiểm tra liên kết chia sẻ."
            )

        logger.info("Đã tải mô hình thành công.")

    checkpoint = torch.load(
        model_path,
        map_location="cpu",
        weights_only=True,
    )

    class_names = checkpoint.get("class_names")

    if class_names != EXPECTED_CLASSES:
        raise RuntimeError(
            "Danh sách lớp trong checkpoint không khớp cấu hình."
        )

    model = models.efficientnet_b0(weights=None)
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.35),
        nn.Linear(
            model.classifier[1].in_features,
            len(class_names),
        ),
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    return model, class_names



def recognize_with_local_model(image_bytes):
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            tensor = IMAGE_TRANSFORM(image).unsqueeze(0)

        model, class_names = load_plant_model()

        with torch.inference_mode():
            logits = model(tensor)
            probabilities = torch.softmax(logits, dim=1)[0]

        index = int(torch.argmax(probabilities).item())
        confidence = float(probabilities[index].item())

        return class_names[index], confidence

    except Exception:
        logger.exception("Lỗi nhận diện bằng mô hình cục bộ")
        raise
