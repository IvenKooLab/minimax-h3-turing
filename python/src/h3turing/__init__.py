"""h3-turing: field-tested toolkit for MiniMax H3 on Turing (sm_75) GPUs.

Codifies the optimization experience documented in the handbook:
https://github.com/IvenKooLab/minimax-h3-turing

Zero runtime dependencies - stdlib only, like the ComfyUI ecosystem itself.
"""

__version__ = "0.1.0"

from .tiers import TIERS, Tier, get
from .workflows import load, render, set_prompt, set_seed

__all__ = ["TIERS", "Tier", "get", "load", "render", "set_prompt", "set_seed", "__version__"]
