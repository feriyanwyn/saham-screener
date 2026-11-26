"""PyTorch Neural Network Models: LSTM Regressor & BiLSTM Classifier.
Memenuhi persyaratan Section C: Model LSTM dan BiLSTM tanpa data leakage masa depan.
"""
import torch
import torch.nn as nn


class LSTMReturnRegressor(nn.Module):
    """LSTM model to predict expected next-period price return and volatility."""

    def __init__(self, input_dim: int = 9, hidden_dim: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        last_step = out[:, -1, :]
        pred_return = self.fc(last_step)
        return pred_return.squeeze(-1)


class BiLSTMDirectionClassifier(nn.Module):
    """Bidirectional LSTM model to capture patterns from the input sequence window."""

    def __init__(self, input_dim: int = 9, hidden_dim: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.bilstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        # Bidirectional produces 2 * hidden_dim
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.bilstm(x)
        last_step = out[:, -1, :]
        logits = self.fc(last_step)
        return logits.squeeze(-1)

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        logits = self.forward(x)
        return torch.sigmoid(logits)
