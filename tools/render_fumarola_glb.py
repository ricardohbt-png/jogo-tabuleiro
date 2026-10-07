"""Exporta somente o GLB e as miniaturas da fumarola."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_decoracoes_caverna_glb import build_fumarola, export_one

if __name__ == "__main__":
    export_one("fumarola", build_fumarola, 81211, preview_frame=87)
