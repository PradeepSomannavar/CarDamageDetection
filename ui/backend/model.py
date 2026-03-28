import torch
import torch.nn as nn
import torchvision.models as models


CLASS_NAMES = ['F_Breakage', 'F_Crushed', 'F_Normal', 'R_Breakage', 'R_Crushed', 'R_Normal']

CLASS_LABELS = {
    'F_Breakage': 'Front Breakage',
    'F_Crushed':  'Front Crushed',
    'F_Normal':   'Front Normal',
    'R_Breakage': 'Rear Breakage',
    'R_Crushed':  'Rear Crushed',
    'R_Normal':   'Rear Normal',
}


class CarClassifierResNet(nn.Module):
    """ResNet50 fine-tuned for 6-class car damage classification."""

    def __init__(self, num_classes: int = 6, dropout_rate: float = 0.4):
        super().__init__()
        self.model = models.resnet50(weights=None)

        # Freeze all layers (mirrors the training setup)
        for param in self.model.parameters():
            param.requires_grad = False

        # Replace final FC layer
        self.model.fc = nn.Sequential(
            nn.Dropout(dropout_rate),
            nn.Linear(self.model.fc.in_features, num_classes),
        )

    def forward(self, x):
        return self.model(x)


def load_model(weights_path: str, device: torch.device) -> CarClassifierResNet:
    """Instantiate the model and load state dict from *weights_path*."""
    model = CarClassifierResNet(num_classes=len(CLASS_NAMES))
    state_dict = torch.load(weights_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model
