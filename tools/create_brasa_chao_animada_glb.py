"""Mescla a brasa no chão original com as chamas animadas da Chama Viva.

Roda da raiz: python tools/create_brasa_chao_animada_glb.py
"""
import os

from create_fogueira_animada_glb import merge


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
merge(
    os.path.join(ROOT, "assets", "objetos", "brasa_chao.glb"),
    os.path.join(ROOT, "assets", "objetos", "brasa_chao_animada.glb"),
)
