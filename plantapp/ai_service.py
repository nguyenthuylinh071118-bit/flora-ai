
from functools import lru_cache
from pathlib import Path

import torch
from torch import nn
from PIL import Image, ImageOps
from torchvision import models, transforms

from django.conf import settings
from .models import Plant


CLASS_TO_PLANT_NAME = {
    "bong_trang": "Hoa bông trang",
    "cay_buoi": "Cây bưởi",
    "cay_chuoi": "Cây chuối",
    "cay_phuong": "Cây phượng",
    "hoa_hong": "Hoa hồng",
    "hoa_layon": "Hoa layon",
    "hoa_sen": "Hoa sen",
    "lan_mokara": "Lan Mokara",
    "muong_trau": "Cây muồng trâu",
    "vong_mong_ga": "Vông mồng gà",
}


IMAGE_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


@lru_cache(maxsize=1)
def load_model():
    model_path = Path(settings.BASE_DIR) / "plant_model.pth"

    if not model_path.is_file():
        raise FileNotFoundError(
            f"Khong tim thay mo hinh: {model_path}"
        )

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    checkpoint = torch.load(
        model_path,
        map_location=device,
        weights_only=True,
    )

    class_names = checkpoint["class_names"]

    if class_names != list(CLASS_TO_PLANT_NAME.keys()):
        raise ValueError(
            "Danh sach lop cua mo hinh khong khop."
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
    model.to(device)
    model.eval()

    print("[LOCAL AI] Da tai EfficientNet-B0:", model_path)

    return model, device, class_names


def recognize_plant(image_file):
    model, device, class_names = load_model()

    try:
        image_file.seek(0)

        with Image.open(image_file) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            tensor = IMAGE_TRANSFORM(image).unsqueeze(0)

    except Exception as exc:
        raise ValueError(
            "Khong doc duoc anh. Hay thu anh JPG hoac PNG."
        ) from exc

    tensor = tensor.to(device)

    with torch.inference_mode():
        outputs = model(tensor)
        probabilities = torch.softmax(outputs, dim=1)[0]
        index = int(torch.argmax(probabilities).item())

    plant_name = CLASS_TO_PLANT_NAME[class_names[index]]
    score = float(probabilities[index].item()) * 100

    print(
        f"[LOCAL AI] Ket qua: {plant_name} "
        f"(diem mo hinh: {score:.2f}%)"
    )

    if not Plant.objects.filter(name=plant_name).exists():
        raise ValueError(
            f"{plant_name} chua co trong co so du lieu."
        )

    return plant_name
