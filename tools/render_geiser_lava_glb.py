"""Exporta somente o GLB e as miniaturas do gêiser de lava."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_decoracoes_caverna_glb import build_geiser_lava, export_one

if __name__ == "__main__":
    export_one("geiser_lava", build_geiser_lava, 81054, preview_frame=77)
