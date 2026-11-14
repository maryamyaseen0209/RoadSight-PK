from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

try:
    import torch
    import torch.nn as nn
    from torchvision.models.detection import fasterrcnn_resnet50_fpn_v2, FasterRCNN_ResNet50_FPN_V2_Weights
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    from torch.utils.data import Dataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def build_faster_rcnn_model(
    num_classes: int = 5,  # 4 defect classes + 1 background
    pretrained: bool = True,
    trainable_backbone_layers: int = 3,
):
    """
    Constructs a Faster R-CNN model with ResNet-50 FPN V2 backbone and custom 5-class head.
    Class 0: Background
    Class 1: Longitudinal Crack [D00]
    Class 2: Transverse Crack [D10]
    Class 3: Alligator Crack [D20]
    Class 4: Pothole [D40]
    """
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch and torchvision are required for Faster R-CNN.")

    weights = FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT if pretrained else None
    model = fasterrcnn_resnet50_fpn_v2(
        weights=weights,
        trainable_backbone_layers=trainable_backbone_layers,
    )

    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    return model


if TORCH_AVAILABLE:
    class RoadDefectDataset(Dataset):
        """Custom PyTorch dataset loading VOC XML annotations for Faster R-CNN."""

        def __init__(
            self,
            images_dir: Union[str, Path],
            annotations_dir: Union[str, Path],
            transforms=None,
        ):
            from ml.data.parse_voc import parse_voc_xml

            self.images_dir = Path(images_dir)
            self.annotations_dir = Path(annotations_dir)
            self.transforms = transforms
            self.parse_voc = parse_voc_xml

            self.image_files = sorted(
                list(self.images_dir.glob("*.jpg")) +
                list(self.images_dir.glob("*.png")) +
                list(self.images_dir.glob("*.jpeg"))
            )

        def __len__(self) -> int:
            return len(self.image_files)

        def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
            img_path = self.image_files[idx]
            xml_path = self.annotations_dir / f"{img_path.stem}.xml"

            img = Image.open(img_path).convert("RGB")
            w, h = img.size

            boxes = []
            labels = []

            if xml_path.exists():
                parsed = self.parse_voc(xml_path, img_width=w, img_height=h)
                for b in parsed["boxes"]:
                    boxes.append([b["xmin"], b["ymin"], b["xmax"], b["ymax"]])
                    # Faster R-CNN background is 0, so defect classes shift by +1
                    labels.append(b["class_id"] + 1)

            if len(boxes) == 0:
                boxes_tensor = torch.zeros((0, 4), dtype=torch.float32)
                labels_tensor = torch.zeros((0,), dtype=torch.int64)
            else:
                boxes_tensor = torch.as_tensor(boxes, dtype=torch.float32)
                labels_tensor = torch.as_tensor(labels, dtype=torch.int64)

            target = {
                "boxes": boxes_tensor,
                "labels": labels_tensor,
                "image_id": torch.tensor([idx]),
            }

            import torchvision.transforms.functional as F
            tensor_img = F.to_tensor(img)

            return tensor_img, target
else:
    class RoadDefectDataset:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch and torchvision are required.")
