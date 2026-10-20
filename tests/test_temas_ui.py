"""Contraste de los tokens aplicados: texto AA y bordes de campos."""
import re
import unittest
from pathlib import Path

CSS = (Path(__file__).resolve().parents[1] / 'frontend/static/css/estilos.css').read_text(encoding='utf-8')


def tokens(selector):
    bloque = CSS.split(selector, 1)[1].split('}', 1)[0]
    return dict(re.findall(r'--([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;', bloque))


def contraste(a, b):
    def luminancia(h):
        rgb = [int(h[i:i+2], 16)/255 for i in (1,3,5)]
        rgb = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        return sum(v*p for v,p in zip(rgb, (.2126,.7152,.0722)))
    menor, mayor = sorted((luminancia(a), luminancia(b)))
    return (mayor+.05)/(menor+.05)


class TemasUITest(unittest.TestCase):
    def test_textos_superficies_acciones_estados_y_bordes(self):
        for nombre, t in [('claro',tokens(':root {')), ('oscuro',tokens(':root[data-theme="dark"] {'))]:
            pares = [(a,b) for a in ('text-primary','text-secondary','text-muted') for b in ('bg-app','bg-surface')]
            pares += [('text-primary','bg-subtle'), ('text-secondary','bg-subtle'), ('on-primary','primary'), ('on-primary','primary-hover'), ('on-danger','danger-fill'), ('accent-text','accent-tint'), ('sidebar-text','sidebar-bg'), ('sidebar-secondary','sidebar-bg')]
            pares += [(a,a+'-soft') for a in ('success','warning','danger','info')]
            for a,b in pares:
                with self.subTest(tema=nombre,texto=a,fondo=b):
                    self.assertGreaterEqual(contraste(t[a],t[b]),4.5)
            for fondo in ('bg-surface','bg-subtle','bg-app'):
                with self.subTest(tema=nombre,borde=fondo):
                    self.assertGreaterEqual(contraste(t['input-border'],t[fondo]),3)

    def test_automatico_y_manual_comparten_tokens_oscuros(self):
        self.assertEqual(tokens(':root:not([data-theme="light"]):not([data-theme="dark"]) {'),tokens(':root[data-theme="dark"] {'))


if __name__ == '__main__':
    unittest.main()
