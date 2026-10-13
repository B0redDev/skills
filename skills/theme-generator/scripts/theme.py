#!/usr/bin/env python3
"""Tailwind v4 / shadcn theme generator. Python 3.8+, standard library only.

  theme.py build SPEC.json --out DIR            candidates -> DIR/preview.html, DIR/<slug>.css
  theme.py apply SPEC.json --pick A --css FILE  write the chosen candidate into the project's CSS [--dry-run]
  theme.py extract IMAGE|URL                    dominant colours as OKLCH
  theme.py palette COLOR                        one 50-950 scale

Colour math is OKLCH, gamut-mapped to sRGB; contrast is WCAG 2.
"""
import argparse
import colorsys
import difflib
import json
import math
import re
import signal
import struct
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
REF = json.loads((ASSETS / "tailwind-palettes.json").read_text())
STEPS = REF["steps"]
PALETTES = {k: [tuple(c) for c in v] for k, v in REF["palettes"].items()}
GRAYS = ("slate", "gray", "zinc", "neutral", "stone", "mauve", "olive", "mist", "taupe")
WHITE = (1.0, 0.0, 0.0)
RED_LIGHT, RED_DARK = (0.577, 0.245, 27.325), (0.704, 0.191, 22.216)  # shadcn's destructive
STACKS = {
    "sans": "ui-sans-serif, system-ui, sans-serif",
    "serif": "ui-serif, Georgia, serif",
    "mono": "ui-monospace, SFMono-Regular, Menlo, monospace",
    "heading": "var(--font-sans)",
}
TW_RADIUS = {"xs": 0.125, "sm": 0.25, "md": 0.375, "lg": 0.5, "xl": 0.75, "2xl": 1, "3xl": 1.5, "4xl": 2}
TEXT_PAIRS = [
    ("foreground", "background"), ("card-foreground", "card"), ("popover-foreground", "popover"),
    ("primary-foreground", "primary"), ("secondary-foreground", "secondary"), ("muted-foreground", "background"),
    ("muted-foreground", "muted"), ("accent-foreground", "accent"), ("destructive", "background"),
    ("sidebar-foreground", "sidebar"), ("sidebar-primary-foreground", "sidebar-primary"),
    ("sidebar-accent-foreground", "sidebar-accent"),
]

# ── colour math ──────────────────────────────────────────────────────────────


def _cbrt(x):
    return math.copysign(abs(x) ** (1 / 3), x)


def to_linear(c):
    """OKLCH -> linear sRGB (may be out of [0, 1])."""
    L, C, H = c
    a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def from_srgb(r, g, b):
    """sRGB (0-1, gamma-encoded) -> OKLCH."""
    r, g, b = (v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in (r, g, b))
    l = _cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = _cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = _cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    C = math.hypot(a, bb)
    return (L, C, math.degrees(math.atan2(bb, a)) % 360 if C > 1e-4 else 0.0)


def in_gamut(c, eps=1e-4):
    return all(-eps <= v <= 1 + eps for v in to_linear(c))


def gamut(c):
    """Clamp L, then lower chroma at constant L and H until the colour fits sRGB."""
    L, C, H = min(max(c[0], 0.0), 1.0), max(c[1], 0.0), c[2] % 360
    if in_gamut((L, C, H)):
        return (L, C, H)
    lo, hi = 0.0, C
    for _ in range(24):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if in_gamut((L, mid, H)) else (lo, mid)
    return (L, lo, H)


def luminance(c):
    r, g, b = (min(max(v, 0.0), 1.0) for v in to_linear(c))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(c1, c2):
    hi, lo = sorted((luminance(c1), luminance(c2)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def to_hex(c):
    out = ""
    for v in to_linear(c):
        v = min(max(v, 0.0), 1.0)
        v = 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
        out += f"{round(v * 255):02x}"
    return "#" + out


def fmt(c):
    if isinstance(c, str):
        return c
    L, C, H = c
    if C < 0.0005:
        return f"oklch({round(L, 3):g} 0 0)"
    return f"oklch({round(L, 3):g} {round(C, 3):g} {round(H, 3):g})"


def parse(s):
    """hex, rgb(), hsl(), oklch(), white/black, or a Tailwind colour like amber-500."""
    s = s.strip().lower()
    if s in ("white", "black"):
        return WHITE if s == "white" else (0.0, 0.0, 0.0)
    m = re.fullmatch(r"([a-z]+)-(\d+)", s)
    if m and m[1] in PALETTES and m[2] in STEPS:
        return PALETTES[m[1]][STEPS.index(m[2])]
    if m := re.fullmatch(r"#([0-9a-f]{3,8})", s):
        h = m[1] if len(m[1]) >= 6 else "".join(ch * 2 for ch in m[1][:3])
        return from_srgb(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))
    if m := re.fullmatch(r"oklch\(\s*([\d.]+)(%?)\s+([\d.]+)\s+([\d.]+|none)\s*(?:/[^)]*)?\)", s):
        return (float(m[1]) / (100 if m[2] else 1), float(m[3]), 0.0 if m[4] == "none" else float(m[4]))
    if m := re.fullmatch(r"rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)[^)]*\)", s):
        return from_srgb(*(float(m[i]) / 255 for i in (1, 2, 3)))
    if m := re.fullmatch(r"hsla?\(\s*([\d.]+)(?:deg)?[\s,]+([\d.]+)%[\s,]+([\d.]+)%[^)]*\)", s):
        return from_srgb(*colorsys.hls_to_rgb(float(m[1]) / 360, float(m[3]) / 100, float(m[2]) / 100))
    raise ValueError(f"unrecognised colour: {s}")


# ── scales ───────────────────────────────────────────────────────────────────


def _hue_diff(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def scale(seed):
    """A 50-950 scale that follows the Tailwind palette closest to the seed and holds the seed at its step.

    Returns (scale, anchor index). Lightness keeps the reference curve, rescaled on each side of the anchor so
    the ends stay Tailwind's; chroma and hue drift follow the reference, offset to the seed. Extra chroma in the
    seed fades out over four steps, so a vivid light seed doesn't oversaturate the whole scale.
    """
    L0, C0, H0 = seed

    def anchor(p):
        return min(range(11), key=lambda i: abs(p[i][0] - L0))

    if C0 < 0.005:
        name = "neutral"
    else:  # nearest hue in units of ~30°, nearest chroma in units of ~0.05
        name = min(PALETTES, key=lambda n: _hue_diff(PALETTES[n][anchor(PALETTES[n])][2], H0) / 30
                   + abs(PALETTES[n][anchor(PALETTES[n])][1] - C0) / 0.05)
    ref = PALETTES[name]
    a = anchor(ref)
    La, Ca, Ha = ref[a]
    top, bottom = max(ref[0][0], L0), min(ref[-1][0], L0)
    out = []
    for i, (L, C, H) in enumerate(ref):
        if i < a:
            L = L0 + (L - La) / (ref[0][0] - La) * (top - L0) if ref[0][0] != La else top
        elif i > a:
            L = L0 - (La - L) / (La - ref[-1][0]) * (L0 - bottom) if ref[-1][0] != La else bottom
        else:
            L = L0
        f = C0 / Ca if Ca > 1e-3 else 0
        if f > 1:
            f = 1 + (f - 1) * max(0.0, 1 - abs(i - a) / 4)
        C = C * f if Ca > 1e-3 else C0
        out.append(gamut((L, C, H + H0 - Ha if Ca > 1e-3 else H0)))
    out[a] = gamut(seed)
    return out, a


def neutral_scale(kind, seed, tint=1.0):
    """A Tailwind gray family by name, or 'tinted': neutral lightness, taupe-strength chroma, the brand's hue."""
    if kind in GRAYS:
        return list(PALETTES[kind])
    if kind != "tinted":
        raise ValueError(f"neutral must be one of {', '.join(GRAYS)} or 'tinted', got {kind!r}")
    return [gamut((n[0], t[1] * tint, seed[2])) for n, t in zip(PALETTES["neutral"], PALETTES["taupe"])]


# ── candidates ───────────────────────────────────────────────────────────────


def font_value(role, family):
    """A quoted family plus the role's fallbacks; var(...) (e.g. a next/font variable) passes through unquoted."""
    name = family if family.startswith("var(") else f'"{family}"'
    return f"{name}, {STACKS[role]}"


def semantic(cand, brand, anchor, neutral, accent):
    """shadcn tokens for light and dark, mapped like shadcn's own themes, with the brand colour as primary."""
    n = dict(zip(STEPS, neutral))
    b = dict(zip(STEPS, brand))
    seed = brand[anchor]

    def fg(bg):
        """shadcn's near-white/near-black pair first; pure white or the darkest step when those miss 4.5:1."""
        best = max((n["50"], n["900"]), key=lambda c: contrast(c, bg))
        if contrast(best, bg) >= 4.5:
            return best
        return max((WHITE, n["950"], best), key=lambda c: contrast(c, bg))

    # Dark mode keeps the brand colour unless it drowns in the background, then steps lighter.
    dark_primary = next(c for c in [seed] + brand[:anchor][::-1] + [n["50"]] if contrast(c, n["950"]) >= 3)

    def legible(c, *bgs, step=-0.005):
        """Move c's lightness (darker by default) until it reaches 4.5:1 on every background."""
        while min(contrast(c, bg) for bg in bgs) < 4.5 and 0 < c[0] < 1:
            c = gamut((c[0] + step, c[1], c[2]))
        return c

    # shadcn's stock muted text is 4.3:1 on muted; nudge it just far enough to pass AA.
    muted_fg = legible(n["500"], WHITE, n["100"])
    dark_muted_fg = legible(n["400"], n["950"], n["800"], step=0.005)
    if accent:
        a = dict(zip(STEPS, accent))
        charts = ([b["500"], a["500"], b["700"], a["300"], b["300"]], [b["400"], a["400"], b["600"], a["200"], b["200"]])
    else:
        charts = ([b[s] for s in ("300", "500", "600", "700", "800")], [b[s] for s in ("200", "300", "400", "500", "600")])
    light = {
        "background": WHITE, "foreground": n["950"], "card": WHITE, "card-foreground": n["950"],
        "popover": WHITE, "popover-foreground": n["950"], "primary": seed, "primary-foreground": fg(seed),
        "secondary": n["100"], "secondary-foreground": n["900"], "muted": n["100"], "muted-foreground": muted_fg,
        "accent": n["100"], "accent-foreground": n["900"], "destructive": RED_LIGHT, "border": n["200"],
        "input": n["200"], "ring": seed, "sidebar": n["50"], "sidebar-foreground": n["950"],
        "sidebar-primary": seed, "sidebar-primary-foreground": fg(seed), "sidebar-accent": n["100"],
        "sidebar-accent-foreground": n["900"], "sidebar-border": n["200"], "sidebar-ring": seed,
    }
    dark = {
        "background": n["950"], "foreground": n["50"], "card": n["900"], "card-foreground": n["50"],
        "popover": n["900"], "popover-foreground": n["50"], "primary": dark_primary,
        "primary-foreground": fg(dark_primary), "secondary": n["800"], "secondary-foreground": n["50"],
        "muted": n["800"], "muted-foreground": dark_muted_fg, "accent": n["800"], "accent-foreground": n["50"],
        "destructive": RED_DARK, "border": "oklch(1 0 0 / 10%)", "input": "oklch(1 0 0 / 15%)",
        "ring": dark_primary, "sidebar": n["900"], "sidebar-foreground": n["50"], "sidebar-primary": dark_primary,
        "sidebar-primary-foreground": fg(dark_primary), "sidebar-accent": n["800"], "sidebar-accent-foreground": n["50"],
        "sidebar-border": "oklch(1 0 0 / 10%)", "sidebar-ring": dark_primary,
    }
    for tokens, chart in ((light, charts[0]), (dark, charts[1])):
        tokens.update({f"chart-{i + 1}": c for i, c in enumerate(chart)})
    for mode, tokens in (("light", light), ("dark", dark)):
        for k, v in (cand.get("overrides") or {}).get(mode, {}).items():
            tokens[k] = v if "/" in v or "var(" in v else parse(v)
    return light, dark


def report(light, dark):
    rows = []
    for mode, t in (("light", light), ("dark", dark)):
        for fg_, bg in TEXT_PAIRS:
            if isinstance(t.get(fg_), tuple) and isinstance(t.get(bg), tuple):
                rows.append({"mode": mode, "pair": f"{fg_} / {bg}", "ratio": round(contrast(t[fg_], t[bg]), 2), "min": 4.5})
        if isinstance(t["primary"], tuple):
            rows.append({"mode": mode, "pair": "primary / background (non-text)",
                         "ratio": round(contrast(t["primary"], t["background"]), 2), "min": 3})
    return rows


def resolve(cand):
    seed = parse(cand["brand"])
    brand, anchor = scale(seed)
    accent = scale(parse(cand["accent"]))[0] if cand.get("accent") else None
    neutral = neutral_scale(cand.get("neutral", "neutral"), seed, cand.get("tint", 1.0))
    light, dark = semantic(cand, brand, anchor, neutral, accent)
    fonts = {role: font_value(role, fam) for role, fam in (cand.get("fonts") or {}).items()}
    palettes = {"brand": brand, **({"accent": accent} if accent else {}), "neutral": neutral}
    return {"light": light, "dark": dark, "fonts": fonts, "palettes": palettes, "report": report(light, dark)}


def tailwind_decls(cand, r):
    """@theme declarations: every palette (the chosen gray as --color-neutral-*), fonts, the radius scale."""
    decls = {f"color-{name}-{s}": fmt(c) for name, p in r["palettes"].items() for s, c in zip(STEPS, p)}
    decls.update({f"font-{role}": v for role, v in r["fonts"].items()})
    if cand.get("radius") is not None:
        decls.update({f"radius-{k}": f"{round(v * cand['radius'] / 0.5, 4):g}rem" for k, v in TW_RADIUS.items()})
    return decls


def css_for(cand, r, mode):
    """The candidate as a standalone CSS file."""
    radius = cand.get("radius")
    head = f"/* {cand['name']}: generated by theme-generator ({mode}) */\n"
    if mode == "tailwind":
        return head + "@theme {\n" + "".join(f"  --{k}: {v};\n" for k, v in tailwind_decls(cand, r).items()) + "}\n"
    root = ([f"  --radius: {radius}rem;"] if radius is not None else []) + [f"  --{k}: {fmt(v)};" for k, v in r["light"].items()]
    dark = [f"  --{k}: {fmt(v)};" for k, v in r["dark"].items()]
    inline = [f"  --font-{role}: {v};" for role, v in r["fonts"].items()]
    inline += [f"  --color-{k}: var(--{k});" for k in r["light"]]
    inline += ["  --radius-sm: calc(var(--radius) * 0.6);", "  --radius-md: calc(var(--radius) * 0.8);",
               "  --radius-lg: var(--radius);", "  --radius-xl: calc(var(--radius) * 1.4);"]
    return (head + "@custom-variant dark (&:is(.dark *));\n\n:root {\n" + "\n".join(root) + "\n}\n\n.dark {\n"
            + "\n".join(dark) + "\n}\n\n@theme inline {\n" + "\n".join(inline) + "\n}\n")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "theme"


def load_spec(path):
    spec = json.loads(Path(path).read_text())
    if spec.get("mode") not in ("tailwind", "shadcn"):
        sys.exit("spec.mode must be 'tailwind' or 'shadcn'")
    if not spec.get("candidates"):
        sys.exit("spec.candidates is empty")
    return spec


# ── build ────────────────────────────────────────────────────────────────────


def build(args):
    spec = load_spec(args.spec)
    mode, out = spec["mode"], Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    data, families, log = [], [], []
    for cand in spec["candidates"]:
        r = resolve(cand)
        css = css_for(cand, r, mode)
        (out / f"{slug(cand['name'])}.css").write_text(css)
        for fam in (cand.get("fonts") or {}).values():  # Google Fonts serves the family without fontsource's " Variable"
            fam = re.sub(r"\s+Variable$", "", fam)
            if not fam.startswith("var(") and fam not in families:
                families.append(fam)
        data.append({
            "name": cand["name"], "note": cand.get("note", ""), "mode": mode, "css": css,
            "radius": f"{cand.get('radius', 0.625)}rem", "report": r["report"],
            # the preview loads Google Fonts, which name families without fontsource's " Variable"
            "fonts": {k: re.sub(r'\s+Variable"', '"', v) for k, v in r["fonts"].items()},
            "light": {k: fmt(v) for k, v in r["light"].items()}, "dark": {k: fmt(v) for k, v in r["dark"].items()},
            "palettes": [{"name": name, "steps": [{"step": s, "css": fmt(c), "hex": to_hex(c),
                                                   "white": round(contrast(c, WHITE), 1),
                                                   "black": round(contrast(c, (0.0, 0.0, 0.0)), 1)}
                                                  for s, c in zip(STEPS, p)]} for name, p in r["palettes"].items()],
        })
        fails = [f"{x['mode']} {x['pair']} {x['ratio']}:1 (min {x['min']})" for x in r["report"] if x["ratio"] < x["min"]]
        log.append(f"{cand['name']}: {out / (slug(cand['name']) + '.css')}")
        log += [f"  below WCAG AA: {f}" for f in fails]
        for name, p in r["palettes"].items():  # what Tailwind users need when they pair text-white / text-black with a step
            white = next((s for s, c in zip(STEPS, p) if contrast(c, WHITE) >= 4.5), None)
            black = next((s for s, c in reversed(list(zip(STEPS, p))) if contrast(c, (0.0, 0.0, 0.0)) >= 4.5), None)
            log.append(f"  {name}: white text passes AA from {white or 'no step'}, black text up to {black or 'no step'}")
    links = "\n".join(
        f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={urllib.parse.quote_plus(f)}:wght@400..700&display=swap"'
        ' onerror="this.onerror=null; this.href=this.href.replace(/:wght@[^&]*/, \'\')">'  # static families: plain request
        for f in families)
    page = (ASSETS / "preview.html").read_text()
    page = page.replace("<!--FONTS-->", links).replace("/*THEMES*/[]", json.dumps(data).replace("</", "<\\/"))
    (out / "preview.html").write_text(page)
    print("\n".join(log + [f"preview: {out / 'preview.html'}"]))


# ── apply ────────────────────────────────────────────────────────────────────


def _blocks(css, selector):
    """(start, end) of each block body whose selector matches; braces excluded, nesting respected."""
    for m in re.finditer(selector, css):
        i = m.end() - 1
        depth = 0
        for j in range(i, len(css)):
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            if depth == 0:
                yield i + 1, j
                break


def _set(css, selector, decls, prefer=None, create=None):
    """Set each --name: value inside the first block matching selector (one containing `prefer` if any)."""
    if not decls:
        return css
    found = list(_blocks(css, selector))
    found = [b for b in found if prefer and prefer in css[b[0]:b[1]]] or found
    if not found:
        body = "".join(f"  --{k}: {v};\n" for k, v in decls.items())
        return create(css, body) if create else css + f"\n{selector_text(selector)} {{\n{body}}}\n"
    s, e = found[0]
    body = css[s:e]
    indent = (re.search(r"\n([ \t]+)--", body) or [None, "  "])[1]
    for k, v in decls.items():
        pat = re.compile(rf"(--{re.escape(k)}\s*:\s*)[^;]*;")
        if pat.search(body):
            body = pat.sub(lambda m: f"{m[1]}{v};", body)
        else:
            body = body.rstrip(" \t")
            body += ("" if body.endswith("\n") else "\n") + f"{indent}--{k}: {v};\n"
    return css[:s] + body + css[e:]


def selector_text(selector):
    return {r"(?m)^[ \t]*:root\s*\{": ":root", r"(?m)^[ \t]*\.dark\s*\{": ".dark",
            r"@theme\s+inline\s*\{": "@theme inline", r"@theme\s*\{": "@theme"}[selector]


def _after_imports(block):
    def create(css, body):
        imports = list(re.finditer(r"(?m)^@import[^;]*;\s*$", css))
        at = imports[-1].end() if imports else 0
        return css[:at] + f"\n\n{block} {{\n{body}}}\n" + css[at:]
    return create


def apply(args):
    spec = load_spec(args.spec)
    mode = spec["mode"]
    cands = spec["candidates"]
    pick = next((c for c in cands if c["name"].lower().startswith(args.pick.lower())), None)
    if pick is None and args.pick.isdigit() and 0 < int(args.pick) <= len(cands):
        pick = cands[int(args.pick) - 1]
    if pick is None:
        sys.exit(f"no candidate matches {args.pick!r}: {', '.join(c['name'] for c in cands)}")
    r = resolve(pick)
    path = Path(args.css)
    before = path.read_text()
    css = before
    if mode == "shadcn":
        root = {k: fmt(v) for k, v in r["light"].items()}
        if pick.get("radius") is not None:
            root = {"radius": f"{pick['radius']}rem", **root}
        css = _set(css, r"(?m)^[ \t]*:root\s*\{", root, prefer="--background")
        css = _set(css, r"(?m)^[ \t]*\.dark\s*\{", {k: fmt(v) for k, v in r["dark"].items()}, prefer="--background")
        target = r"@theme\s+inline\s*\{" if re.search(r"@theme\s+inline\s*\{", css) else r"@theme\s*\{"
        fonts = {f"font-{k}": v for k, v in r["fonts"].items()}
        css = _set(css, target, fonts, create=_after_imports(selector_text(target)))
    else:
        css = _set(css, r"@theme\s*\{", tailwind_decls(pick, r), create=_after_imports("@theme"))
    if args.dry_run:
        sys.stdout.writelines(difflib.unified_diff(before.splitlines(True), css.splitlines(True), str(path), str(path)))
        return
    path.write_text(css)
    changed = sum(1 for a, b in zip(before.splitlines(), css.splitlines()) if a != b) + abs(len(css.splitlines()) - len(before.splitlines()))
    print(f"{pick['name']} -> {path} ({changed} lines changed)")


# ── extract ──────────────────────────────────────────────────────────────────


def _pixels(path):
    """RGBA pixels of the image shrunk to <= 96px: ffmpeg if present, else macOS sips via BMP."""
    try:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "scale=96:96:force_original_aspect_ratio=decrease",
                              "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True, check=True).stdout
        return [tuple(raw[i:i + 4]) for i in range(0, len(raw) - 3, 4)]
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    with tempfile.TemporaryDirectory() as d:
        bmp = Path(d) / "x.bmp"
        try:
            subprocess.run(["sips", "-s", "format", "bmp", "-Z", "96", path, "--out", str(bmp)], capture_output=True, check=True)
            b = bmp.read_bytes()
        except (FileNotFoundError, subprocess.CalledProcessError, OSError):
            sys.exit(f"cannot decode {path}: needs ffmpeg (or macOS sips) and a raster image (PNG, JPEG, WebP)")
    off, (w, h), bpp = struct.unpack_from("<I", b, 10)[0], struct.unpack_from("<ii", b, 18), struct.unpack_from("<H", b, 28)[0]
    n, px = bpp // 8, []
    row = (w * n + 3) & ~3
    for y in range(abs(h)):
        for x in range(w):
            p = b[off + y * row + x * n: off + y * row + x * n + n]
            px.append((p[2], p[1], p[0], p[3] if n == 4 else 255))
    return px


def _group(colors):
    """Greedy grouping of (oklch, weight) by OKLab distance; returns [(mean oklch, weight)] heaviest first."""
    groups = []
    for c, w in sorted(colors, key=lambda x: -x[1]):
        lab = (c[0], c[1] * math.cos(math.radians(c[2])), c[1] * math.sin(math.radians(c[2])))
        for g in groups:
            if math.dist(lab, [v / g[1] for v in g[0]]) < 0.06:
                g[0] = [s + v * w for s, v in zip(g[0], lab)]
                g[1] += w
                break
        else:
            groups.append([[v * w for v in lab], w])
    out = []
    for sums, w in groups:
        L, a, b = (v / w for v in sums)
        C = math.hypot(a, b)
        out.append(((L, C, math.degrees(math.atan2(b, a)) % 360 if C > 1e-4 else 0.0), w))
    return sorted(out, key=lambda g: -g[1])


def _describe(groups, total, key):
    return [{"oklch": fmt(c), "hex": to_hex(c), key: round(w / total, 3) if key == "share" else w} for c, w in groups]


def extract(args):
    src = args.source
    if re.match(r"https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 theme-generator"})
        with urllib.request.urlopen(req, timeout=15) as r:
            page = r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")
        texts = [page]
        for tag in re.findall(r"<link[^>]+>", page)[:40]:
            if "stylesheet" in tag and (m := re.search(r'href=["\']([^"\']+)', tag)) and len(texts) < 13:
                try:
                    req = urllib.request.Request(urllib.parse.urljoin(src, m[1]), headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=15) as r:
                        texts.append(r.read().decode("utf-8", "replace"))
                except OSError:
                    pass
        text = "\n".join(texts)
        counts = {}
        for lit in re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|(?:rgba?|hsla?|oklch)\([^)]*\)", text):
            try:
                c = parse(lit)
            except ValueError:
                continue
            counts[fmt(c)] = (c, counts.get(fmt(c), (c, 0))[1] + 1)
        groups = _group(list(counts.values()))
        result = {
            "source": src, "stylesheets": len(texts) - 1,
            "theme_color": (re.search(r'<meta[^>]+name=["\']theme-color["\'][^>]+content=["\']([^"\']+)', page) or [None, None])[1],
            "chromatic": _describe([g for g in groups if g[0][1] >= 0.03][:10], 1, "count"),
            "neutral": _describe([g for g in groups if g[0][1] < 0.03][:6], 1, "count"),
            "variables": dict(list(dict(re.findall(
                r"(--[\w-]*(?:primary|brand|accent|background|foreground)[\w-]*)\s*:\s*([^;}{]+)", text)).items())[:24]),
        }
    else:
        px = [p for p in _pixels(src) if p[3] >= 128]
        counts = {}
        for r_, g, b, _ in px:
            key = (r_ >> 3, g >> 3, b >> 3)
            counts[key] = counts.get(key, 0) + 1
        groups = _group([(from_srgb(*((v * 8 + 4) / 255 for v in k)), n) for k, n in counts.items()])
        result = {"source": src, "pixels": len(px),
                  "chromatic": _describe([g for g in groups if g[0][1] >= 0.03][:8], len(px), "share"),
                  "neutral": _describe([g for g in groups if g[0][1] < 0.03][:5], len(px), "share")}
    print(json.dumps(result, indent=1))


def palette(args):
    s, a = scale(parse(args.color))
    for step, c in zip(STEPS, s):
        mark = "  <- seed" if step == STEPS[a] else ""
        print(f"{step:>4}  {fmt(c):<28} {to_hex(c)}  on white {contrast(c, WHITE):5.2f}  on black {contrast(c, (0, 0, 0)):5.2f}{mark}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("spec")
    b.add_argument("--out", required=True)
    a = sub.add_parser("apply")
    a.add_argument("spec")
    a.add_argument("--pick", required=True, help="candidate name prefix (e.g. A) or 1-based index")
    a.add_argument("--css", required=True, help="the project's main CSS file")
    a.add_argument("--dry-run", action="store_true")
    e = sub.add_parser("extract")
    e.add_argument("source", help="image path or http(s) URL")
    pl = sub.add_parser("palette")
    pl.add_argument("color")
    args = p.parse_args()
    if hasattr(signal, "SIGPIPE"):  # `theme.py … | head` should stop quietly, not with a traceback
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    {"build": build, "apply": apply, "extract": extract, "palette": palette}[args.cmd](args)


if __name__ == "__main__":
    main()
