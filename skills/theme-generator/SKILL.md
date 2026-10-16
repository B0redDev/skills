---
name: theme-generator
description: Generate a colour, radius and font theme for Tailwind CSS v4 (`@theme` palettes on Tailwind's 50–950 scale) or shadcn/ui (semantic light and dark tokens), starting from a brand colour, a description, an image or logo, a website URL, or the project's current theme. Builds 2–3 candidates with a bundled OKLCH engine, previews them on real components in light and dark with WCAG contrast checks, and writes the approved one into the project's CSS. Use whenever the user asks for a theme, a palette, a colour scheme, brand colours, dark-mode colours, "make the app feel like X", a shadcn or tweakcn-style theme, or Tailwind colour tokens, even if they don't say "theme". Not for designing screens or components.
compatibility: Needs Python 3.8+ (standard library only). Image input uses ffmpeg, or sips on macOS. URL input needs network access.
---

# Theme Generator

Goal: a theme the user has seen and approved, written into their project. Colour math is where hand-written themes go wrong (uneven scales, foregrounds that fail contrast, dark modes that are just inverted), so it lives in `<skill-dir>/scripts/theme.py`, where `<skill-dir>` is the folder that contains this file. Your job is the taste: what to start from, and which 2–3 directions are worth comparing.

## 1. Ask what to build

Ask only what the user's message doesn't already answer, in one batched question (use a structured question tool if there is one):

- **Output: Tailwind or shadcn.**
  - *Tailwind*: an `@theme` block with `--color-brand-50` … `-950` palettes on Tailwind's own lightness curve, the chosen gray as `--color-neutral-*` (it replaces Tailwind's stock `neutral`), plus fonts and radius. Used as `bg-brand-600`, `text-neutral-500`.
  - *shadcn*: the semantic tokens (`--background`, `--primary`, `--muted-foreground`, `--chart-*`, `--sidebar-*`, …) for `:root` and `.dark`, plus `--radius` and the fonts in `@theme inline`.
  - Recommend shadcn when the project has a `components.json`, Tailwind otherwise.
- **Starting point**, if none was given: a brand colour, a description of the feel, an image or logo, a website URL, or the project's current theme.

## 2. Gather

- **Project**: find the main CSS file. `npx shadcn@latest info`, run where `components.json` is (the app's folder in a monorepo), reports it as `tailwindCss`; without shadcn it's the file with `@import "tailwindcss"`. Read it: current tokens, how fonts are loaded (`@fontsource` imports in CSS, or `next/font` variables), and tokens beyond shadcn's set. The generator also writes `--success`, `--warning` and `--info`; check how the project uses them (below). Other extras (`--success-soft`, ReUI's `--*-foreground` pairs, …) are left untouched.
- **Brand colour**: any CSS colour or a Tailwind name (`amber-500`). `python3 <skill-dir>/scripts/theme.py palette <colour>` prints its scale with contrast against white and black.
- **Image or URL**: `python3 <skill-dir>/scripts/theme.py extract <path-or-url>` returns the dominant chromatic and neutral colours as OKLCH (for a URL: from its CSS, plus `theme-color` and colour-named custom properties). Pick the brand colour from those; don't eyeball a screenshot when exact values are available.
- **Description**: translate it into a seed colour, a neutral family, a radius and fonts, and say how in the notes.
- **Current theme**: take its primary as the seed and its neutral family as the starting neutral, then change only what the user asked about.

## 3. Write 2–3 candidates

Candidates must differ in ways the user can judge: neutral temperature, radius, the type pairing, or the reading of the brand (faithful, refined, bolder). Three hues of the same idea isn't a choice. Write `$dir/spec.json`:

```json
{
  "mode": "shadcn",
  "candidates": [
    {
      "name": "A · Warm amber",
      "note": "The current yellow as primary, warm stone neutrals, Inter throughout.",
      "brand": "#f5b400",
      "accent": "sky-500",
      "neutral": "stone",
      "tint": 1,
      "radius": 0.625,
      "fonts": { "sans": "Inter Variable", "heading": "Fraunces", "mono": "JetBrains Mono" },
      "overrides": { "light": { "accent": "oklch(0.97 0.02 85)" }, "dark": {} }
    }
  ]
}
```

- `brand` (required) becomes primary and the `brand` palette. The seed keeps its exact value at its step, and the steps around it follow the closest Tailwind palette. A light seed (a pastel, a logo tint) lands on 200–300 and becomes primary as it is; if the brand's core colour is darker, seed with that one.
- `accent` (optional) adds an `accent` palette (Tailwind mode) and alternates with the brand in `--chart-*` (shadcn mode).
- `neutral`: a Tailwind gray (`slate`, `gray`, `zinc`, `neutral`, `stone`, `mauve`, `olive`, `mist`, `taupe`) or `tinted`, which gives grays the brand's hue; `tint` scales that (default 1, around 0.5–2). In Tailwind mode it is emitted as `--color-neutral-*`.
- `radius`: rem. shadcn's `--radius`; in Tailwind mode it is `--radius-lg`, and the rest of the scale follows proportionally.
- `fonts`: family names as the project will load them (fontsource variable packages register "Inter Variable"), or a `var(--font-…)` for `next/font`. Roles: `sans`, `serif`, `mono`, `heading`.
- `overrides` (shadcn mode): any token per mode, for deliberate departures from the mapping.

The mapping follows shadcn's own themes: white background, neutral steps for surfaces and borders, the brand as `primary` and `ring`, a dark mode that keeps the brand unless it falls below 3:1 on the dark background, and foregrounds chosen to reach 4.5:1. shadcn's stock `muted-foreground` is 4.3:1 on `muted`; the generator darkens it just enough to pass.

Status colours work like shadcn's `destructive`: a text colour, also used as its own tint (`text-warning bg-warning/10`). Each must reach 4.5:1 on background and card, with and without that 10% tint. In light mode Tailwind's text steps don't match each other (green-800 and yellow-800 look muddy, blue-700 is twice as saturated), so the generator keeps one hue and chroma per status (green 150, burnt orange 45, blue 250; chroma 0.12–0.15) at the lightest lightness that passes. Warning is orange because any yellow dark enough for text on white turns brown. In dark mode the Tailwind 400s (green, yellow, blue) already match. They are chosen after the overrides, so they follow an overridden background. If the project already tuned them, or uses them as fills with a `-foreground` pair, put its values in `overrides` so the preview shows them and `apply` keeps them. A brand close to a status hue (a green primary, an orange one) makes states ambiguous: say so in the note.

## 4. Build and show

```bash
dir="${TMPDIR:-/tmp}/theme-generator/<kebab-slug>"; mkdir -p "$dir"
# write $dir/spec.json, then:
python3 <skill-dir>/scripts/theme.py build "$dir/spec.json" --out "$dir"
open "$dir/preview.html"        # macOS; xdg-open on Linux, start "" on Windows
```

`build` writes one standalone CSS file per candidate and `preview.html`. The preview has a tab per candidate (keys 1–9), with a sample app in light and dark (buttons, inputs, status badges and success/warning/info alerts), the palettes, the contrast report and the CSS. Fonts load from Google Fonts for the preview only.

The script prints every pair below WCAG AA. Text pairs pass unless an override broke them; fix those before showing anything. A non-text warning on `primary / background` means the brand is light (yellow, lime): fine for filled buttons, but text or icons in the primary colour will be hard to read. Tell the user rather than silently darkening their brand.

The contrast report checks the shadcn mapping, which picks each foreground for its background, and the status colours on their grounds. Tailwind users pick text colours themselves, so `build` also prints, per palette, the first step that takes white text and the last that takes black text at AA. Pass that on: "`text-white` from `brand-700`" prevents `text-white bg-brand-600` at 3.5:1. In Tailwind mode the light status colours land in `@theme` as `--color-success`/`-warning`/`-info`; `build` prints the dark-mode steps to pair with them (`text-warning dark:text-yellow-400`).

Tell the user the preview path, give your recommendation, and **end with a question**: which candidate, and what to change. To iterate, edit `spec.json` and rebuild; it takes a second.

## 5. Apply

Only after the user picks:

```bash
python3 <skill-dir>/scripts/theme.py apply "$dir/spec.json" --pick A --css <project css> --dry-run   # review
python3 <skill-dir>/scripts/theme.py apply "$dir/spec.json" --pick A --css <project css>
```

`apply` rewrites the values of the tokens it generates where they already are, adds the missing ones to the same block, and leaves every other rule and token alone.

- *shadcn*: `:root` and `.dark` get the tokens and `--radius`; fonts and the `--color-success`/`-warning`/`-info` mappings go in `@theme inline`. A token already declared in a later block of the same selector is rewritten there, so nothing shadows it.
- *Tailwind*: everything goes in the `@theme` block, which is created after the `@import`s if there isn't one.

Then load the fonts the way the project already does:

- **fontsource**: add the package with the project's package manager (`@fontsource-variable/<name>` when it exists, `@fontsource/<name>` otherwise) and its `@import` next to the existing ones.
- **next/font**: add the font in the root layout with a `variable`, and use `var(--that-variable)` as the family in the spec.

Remove font imports nothing uses any more. If the dev server is running, look at one real page in light and dark.

## 6. Report

In the user's language:

- the candidate applied and the file changed;
- the fonts added and the packages installed;
- contrast: all text pairs pass, plus any non-text caveat;
- the paths of the preview and `spec.json`, so the other candidates stay reachable.
