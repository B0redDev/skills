"""Checks for theme.py. Run: python3 scripts/test_theme.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import theme as t  # noqa: E402

SCRIPT = Path(__file__).with_name("theme.py")


def apply(spec, css):
    with tempfile.TemporaryDirectory() as d:
        spec_path, css_path = Path(d, "spec.json"), Path(d, "app.css")
        spec_path.write_text(json.dumps(spec))
        css_path.write_text(css)
        subprocess.run([sys.executable, SCRIPT, "apply", spec_path, "--pick", "A", "--css", css_path], check=True, capture_output=True)
        return css_path.read_text()


# A Tailwind colour as seed rebuilds its own palette (chroma trimmed to sRGB where Tailwind uses P3).
for name in ("blue", "emerald", "rose", "amber", "stone"):
    ref = t.PALETTES[name]
    got, anchor = t.scale(ref[5])
    assert anchor == 5, name
    for r, g in zip(ref, got):
        assert abs(r[0] - g[0]) < 1e-9 and g[1] <= r[1] + 1e-9 and t.in_gamut(g), (name, r, g)

# The seed sits unchanged at its step, and lightness falls from 50 to 950.
for seed in ("#f5b400", "#0f766e", "oklch(0.3 0.1 300)", "#fafafa", "#111827"):
    s, a = t.scale(t.parse(seed))
    assert t.to_hex(s[a]) == t.to_hex(t.gamut(t.parse(seed))), seed
    assert all(x[0] > y[0] for x, y in zip(s, s[1:])), seed

assert t.to_hex(t.parse("#3366cc")) == t.to_hex(t.parse("rgb(51 102 204)")) == t.to_hex(t.parse("hsl(220 60% 50%)")) == "#3366cc"
assert round(t.contrast(t.WHITE, (0, 0, 0)), 2) == 21

# A seed more vivid than Tailwind at its step doesn't push the far end of the scale past Tailwind's own chroma.
light_seed, a = t.scale(t.parse("#8fa4ff"))
ref = t.PALETTES["indigo"]
assert all(c[1] <= r[1] + 1e-9 for i, (c, r) in enumerate(zip(light_seed, ref)) if abs(i - a) >= 4), light_seed

# A neutral brand on the neutral family gives shadcn's light neutral theme.
light = t.resolve({"name": "x", "brand": "neutral-900", "neutral": "neutral"})["light"]
shadcn = {"background": "oklch(1 0 0)", "foreground": "oklch(0.145 0 0)", "primary": "oklch(0.205 0 0)",
          "primary-foreground": "oklch(0.985 0 0)", "secondary": "oklch(0.97 0 0)", "border": "oklch(0.922 0 0)",
          "sidebar": "oklch(0.985 0 0)"}
assert {k: t.fmt(light[k]) for k in shadcn} == shadcn, light

# Every text pair reaches WCAG AA, whatever the brand.
for brand in ("#f5b400", "#0f766e", "blue-600", "#e11d48", "#111827", "#a3e635"):
    for neutral in ("tinted", "zinc", "stone"):
        r = t.resolve({"name": "x", "brand": brand, "neutral": neutral})
        bad = [x for x in r["report"] if x["min"] == 4.5 and x["ratio"] < 4.5]
        assert not bad, (brand, neutral, bad)

# Status colours are picked after the overrides, so they still read on an overridden background.
r = t.resolve({"name": "x", "brand": "#111827", "overrides": {"light": {"background": "oklch(0.9 0.02 80)"}, "dark": {"card": "oklch(0.35 0 0)"}}})
assert not [x for x in r["report"] if x["pair"].split(" /")[0] in t.STATUS and x["ratio"] < 4.5], r["report"]
assert t.fmt(t.resolve({"name": "x", "brand": "#111827", "overrides": {"light": {"warning": "oklch(0.45 0.09 75)"}}})["light"]["warning"]) == "oklch(0.45 0.09 75)"

# shadcn apply: values change in place (duplicates and later blocks too, so nothing shadows them),
# other tokens and rules stay, missing ones are added to the main block.
out = apply({"mode": "shadcn", "candidates": [{"name": "A", "brand": "#0f766e", "radius": 0.5, "fonts": {"sans": "Inter Variable"}}]},
            '@import "tailwindcss";\n\n:root {\n  --background: oklch(1 0 0);\n  --primary: oklch(0.2 0 0);\n'
            '  --primary: oklch(0.3 0 0);\n}\n\n.dark {\n  --background: oklch(0.1 0 0);\n}\n\n'
            ':root {\n  --success: var(--color-emerald-500);\n  --success-soft: oklch(0.96 0.025 155);\n}\n\n'
            '@theme inline {\n  --font-sans: "Old", sans-serif;\n  --color-background: var(--background);\n}\n')
assert out.split(".dark")[0].count("--primary: oklch(0.511 0.086 186.391);") == 2, out
main, extra = (b.split("}")[0] for b in out.split(":root {")[1:])
assert "--success:" not in main and "--warning:" in main and "--success: oklch(" in extra, out
assert "--success-soft: oklch(0.96 0.025 155);" in out and "--color-background: var(--background);" in out
assert "--color-warning: var(--warning);" in out and out.count("--success:") == 2  # :root and .dark
assert '--font-sans: "Inter Variable", ui-sans-serif' in out and "--radius: 0.5rem;" in out and "--sidebar-ring:" in out
assert out.count(":root {") == 2 and out.count(".dark {") == 1

# Tailwind apply: a new @theme block lands after the imports.
out = apply({"mode": "tailwind", "candidates": [{"name": "A", "brand": "#0f766e", "radius": 0.75}]},
            '@import "tailwindcss";\n\nbody { color: red; }\n')
assert out.index("@import") < out.index("@theme {") < out.index("body {"), out
assert "--color-brand-700: oklch(0.511 0.086 186.391);" in out and "--radius-lg: 0.75rem;" in out
assert "--color-neutral-500: oklch(0.556 0 0);" in out  # the chosen gray is always emitted, as neutral-*
assert "--color-warning: oklch(0.545 0.15 45);" in out  # status colours too, so text-warning exists

print("ok")
