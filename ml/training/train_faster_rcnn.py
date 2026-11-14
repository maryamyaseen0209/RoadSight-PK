from pathlib import Path
from typing import Any, Dict, Optional, Union

from backend.app.core.logging_config import logger


def run_faster_rcnn_training(
    images_dir: Union[str, Path],
    annotations_dir: Union[str, Path],
    epochs: int = 30,
    batch_size: int = 4,
    lr: float = 0.0005,
    save_dir: str = "artifacts/checkpoints/faster_rcnn",
    device: str = "auto",
) -> Dict[str, Any]:
    """
    Executes training loop for Faster R-CNN with ResNet-50 FPN V2.
    """
    try:
        import torch
        from torch.utils.data import DataLoader
        from ml.models.faster_rcnn_detector import build_faster_rcnn_model, RoadDefectDataset
    except ImportError as e:
        raise RuntimeError(f"PyTorch environment required for Faster R-CNN training: {e}")

    dev = torch.device("cuda" if torch.cuda.is_available() and device != "cpu" else "cpu")
    logger.info(f"Training Faster R-CNN on device: {dev}")

    dataset = RoadDefectDataset(images_dir, annotations_dir)

    def collate_fn(batch):
        return tuple(zip(*batch))

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0,
    )

    model = build_faster_rcnn_model(num_classes=5, pretrained=True)
    model.to(dev)

    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(params, lr=lr, momentum=0.9, weight_decay=0.0005)
    lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)

    model.train()
    history = []

    out_path = Path(save_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, epochs + 1):
        epoch_loss = 0.0
        batches = 0

        for images, targets in loader:
            images = list(img.to(dev) for img in images)
            targets = [{k: v.to(dev) for k, v in t.items()} for t in targets]

            loss_dict = model(images, targets)
            losses = sum(loss for loss in loss_dict.values())

            optimizer.zero_grad()
            losses.backward()
            optimizer.step()

            epoch_loss += losses.item()
            batches += 1

        lr_scheduler.step()
        avg_loss = epoch_loss / max(1, batches)
        history.append({"epoch": epoch, "loss": round(avg_loss, 4)})
        logger.info(f"Epoch [{epoch}/{epochs}] - Loss: {avg_loss:.4f}")

    checkpoint_file = out_path / "faster_rcnn_best.pth"
    torch.save(model.state_dict(), checkpoint_file)
    logger.info(f"Checkpoint saved to {checkpoint_file}")

    return {
        "checkpoint_path": str(checkpoint_file),
        "history": history,
        "epochs": epochs,
    }
