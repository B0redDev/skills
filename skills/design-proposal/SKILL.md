---
name: design-proposal
description: Propose UI designs for a web app or website for approval before building them. Produces one self-contained HTML file with several genuinely different design variants, shown side by side and one at a time in real-size desktop, tablet and phone frames, with working interactions and motion; opens it in the browser, collects the user's feedback, iterates, and reports the approved direction as an implementation-ready spec. Use this whenever a task involves new or reworked UI and the visual direction is not already settled — "design a settings page", "how should this dashboard look", "give me some options for the onboarding", "where should these bulk actions go", "mockup", "redesign", "propose a layout", or before implementing a sizeable UI feature from a vague brief — even if the user doesn't say "proposal". Do not use for pure CSS bug fixes or when an approved design/mockup already exists and just needs implementing.
compatibility: Works standalone. Gets better with the optional `impeccable` (pbakaus/impeccable) and `emil-design-eng` (emilkowalski/skill) skills installed, with a browser automation tool for screenshots, and with an image generation tool for the pictures a design needs.
---

# Design Proposal

Goal: get the user to approve a visual direction **before** production code is written. A browser mockup is cheap to change; a half-built feature isn't. Output of this skill is a decision plus a spec, not production code.

## Companion skills

Two skills sharpen the proposals when they're installed. Check the available skills list once at the start; use whichever is present, skip silently otherwise, and name the ones you used in the first report so the user knows which quality bar applied.

- **`impeccable`** is the design-quality layer: project context, variant derivation, the craft floor, and a mechanical anti-pattern detector. Read its `SKILL.md` first; `<impeccable-dir>` below is the folder that contains it. Use only the parts named in the steps below. Its init interview, `concept-seed`, decision page and finish reviewer overlap with this skill, which already is the decision round, and would make the user wait for a design-system setup when they asked for mockups.
- **`emil-design-eng`** is the interaction and motion layer: whether something should animate, easing, duration, press feedback. Read its `SKILL.md` before you add interaction or motion to the variants.

## 1. Gather context (before drawing anything)

Variants that ignore the real product are useless for approval, so look first:

- **Brief**: what is being designed, for whom, the primary task on the screen, hard constraints (platform, existing flows, data shown).
- **Scope**: the whole screen, or one part of it (a toolbar, a row, a panel, an empty state). When it is a part, the rest of the screen is the same in every variant, and you write it once as the shared context (step 3).
- **Existing design language** (if there's a codebase): grep for theme/tokens files, Tailwind config, CSS variables, component library, fonts, icon set. Reuse real colors, radii, type scale, spacing, and copy tone so the proposal looks like *their* product. With impeccable: run `<impeccable-dir>/scripts/impeccable context` once from the project root. It loads `PRODUCT.md`, `DESIGN.md` and any surface brief, and those outrank your own grep. A missing `PRODUCT.md` doesn't block a proposal, so skip the init it suggests.
- **Platform**: web desktop, responsive web, or mobile web. This decides the default frame. For a native app, hand over to the `native-design-proposal` skill when it is installed and the platform's toolchain is available: it renders the variants with the real toolkit instead of imitating it in HTML.
- **Real content**: use plausible domain data (real-looking names, numbers, dates, labels). Never lorem ipsum — fake text hides layout problems and makes variants hard to judge.

If a missing answer would change the variants fundamentally (e.g. mobile vs desktop), ask one batched question. Otherwise make a reasonable assumption, state it in the notes, and proceed.

## 2. Design the variants

Make **3 variants** by default (2 if the space is narrow, max 4). Each must differ in a way that matters for the decision:

- information hierarchy / layout structure (list vs cards vs split view vs table),
- interaction model (inline edit vs modal vs dedicated page, tabs vs stepper),
- density and emphasis (compact power-user vs spacious guided).

Color or font swaps alone are not variants — the user can't make a meaningful choice between them. If the brief is precise, vary the risk level instead: one safe/conventional, one refined, one bolder.

With impeccable: pick its mode for the surface (Operate for app UI, Persuade for marketing, Read for docs, Experience for showcases; read `reference/operate.md` for app UI). Then follow its derivation instead of your first idea: list five to seven materially different structures from the content, task and user behaviour, order them by resonance, and build the top three. The long list is what keeps variant C from being variant A with a darker theme.

Give each variant a short evocative name ("A · Split inbox", "B · Card feed") and write, in the notes panel: the idea in one sentence, who it's best for, and honest tradeoffs. Tradeoffs are what make the choice informed. The first sentence is also the caption under the variant in the overview, so it has to stand on its own.

Show the states that affect the decision: primary state always; empty/loading/error/hover/selected when they're part of the question. Don't pad with states nobody asked about.

**Interaction and motion.** Mockups move. Give each variant the interactions and motion its implementation would have: press and hover feedback, the transition of every state change it shows (drawer, modal, expand, tab switch, selection), and an entrance where content arrives. How a design responds is part of what the user approves, and a still picture hides it. Keep the amount of motion even across variants unless motion is what they differ in, so no variant wins for being the only one that moves.

Without emil-design-eng, hold this baseline: animate only `transform` and `opacity`, ease out on a custom curve, stay under 300ms, give pressables `active:scale-[0.97]`, add a `motion-reduce:` fallback, and don't animate keyboard-initiated or high-frequency actions. With emil-design-eng, its decision framework replaces the baseline, and "no animation" is a valid, often correct outcome.

Note the motion choices in the variant's notes.

## 3. Write the fragments

Every character you write costs time, so write only what is specific to the proposal, styled with Tailwind utility classes: they map one-to-one onto a Tailwind codebase, so markup can move straight into the implementation.

A proposal lives in its own folder in the system temp dir:

```bash
dir="${TMPDIR:-/tmp}/design-proposal/<kebab-slug>"; mkdir -p "$dir"
```

You write these files into it, and step 4 assembles them:

| File | Holds |
| --- | --- |
| `head.html` | The document head, the body options and the product's theme. The same in every round. |
| `context.html` | Optional: the markup every variant shares, when the proposal is about one part of a screen. |
| `images.html` | Optional: the pictures the variants use, embedded as CSS variables. |
| `a.html`, `b.html`, … | One variant each. File order is tab order. |

Step 4 also appends two files from `<skill-dir>/assets/` (`<skill-dir>` is the folder that contains this file). `tailwind.html` is the Tailwind v4 runtime: it compiles the classes in the browser, with no build step or network. `shell.html` is the preview around the variants: overview, tabs, frames, notes panel. Don't read or retype them; together they're 300 KB.

With impeccable, read `<impeccable-dir>/reference/craft-floor.md` right before writing the variants. Its checks and bans apply to mockups as much as to shipped UI, and the user will judge what they see.

**`head.html`** holds what no variant should restate. Keyframes and easing curves go in `@theme`, so every variant animates with the same ones. The same goes for what the variants repeat in their markup: icons as an SVG sprite right after `<body>` (`<symbol id="i-close">`, used with `<svg><use href="#i-close"/></svg>`), and controls such as a field or a primary button as classes in `@layer components`, the way a project's own CSS would define them.

```html
<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Settings · Matchday</title>
<style type="text/tailwindcss">
  @theme {
    --color-brand: #0b7a4b; --font-sans: Inter, system-ui, sans-serif;
    --ease-out-strong: cubic-bezier(0.23, 1, 0.32, 1);
    --animate-rise: rise 300ms var(--ease-out-strong) both;
    @keyframes rise { from { opacity: 0; transform: translateY(8px); } }
  }
  @layer base {
    .dp-variant { @apply bg-white text-zinc-900 antialiased; }  /* in base, so a variant's own bg-* wins */
  }
</style>
<body data-subtitle="Where notifications live" data-url="matchday.app">
```

**A variant** is one section holding its notes. The shell gives the section its own frame and moves the notes into the side panel.

```html
<section class="dp-variant grid md:grid-cols-[260px_1fr]" id="v-a" data-name="A · Grouped list">
  <!-- design markup -->
  <div class="dp-variant-notes">
    <h2>A · Grouped list</h2>
    <p>The idea in one sentence.</p>
    <h3>Best for</h3><p>…</p>
    <h3>Tradeoffs</h3><ul><li>+ …</li><li>− …</li></ul>
    <!-- From round 2 on: <h3>Changes</h3><ul><li>…</li></ul> -->
  </div>
</section>
```

**The shared context** is for a proposal about one part of a screen. Write the rest of the screen once, with a `<slot>` wherever a variant may put something:

```html
<template class="dp-context">
  <div class="grid h-screen grid-cols-[240px_1fr]">
    <aside><!-- sidebar --></aside>
    <main class="flex min-h-0 flex-col">
      <header class="flex h-14 items-center px-6"><h1>Invoices</h1><slot name="toolbar"></slot></header>
      <slot name="banner"></slot>
      <div class="min-h-0 flex-1 overflow-auto"><slot><!-- what the screen shows today --></slot></div>
    </main>
  </div>
</template>
```

The shell wraps a copy around every variant. A direct child of the section with `slot="toolbar"` replaces that slot, children without a `slot` attribute replace the unnamed one, and a slot nothing fills keeps its own content. So each variant holds only its part and its notes, placed where that variant wants it:

```html
<section class="dp-variant" id="v-b" data-name="B · Banner">
  <div slot="banner" class="…"><!-- only what B adds --></div>
  <div class="dp-variant-notes">…</div>
</section>
```

Without it every fragment repeats the same sidebar and table: more to write, and variants that drift apart in places that aren't part of the decision. A variant that restructures the whole screen opts out with `data-context="none"`. The context is copied once per variant, so keep ids and scripts out of it.

**Images.** When a variant leans on a picture (a hero, a cover, a product shot, the visual half of a split screen) and an image generation tool is available, generate the picture: a grey box hides how much the design depends on it, and an SVG drawing imitating a photo looks amateur. Start from the pictures the product already has: look in its assets for illustrations, covers and photos, and when they share a style pass two of them to the generator as style references, so the new picture belongs to the same family. A handsome picture from another world reads as stock. Describe the subject from what the product is about, with the palette of its tokens, no text or logos inside the picture, and quiet areas where copy will sit, or a flat background the layout can continue. Look at the result before using it, and generate a second candidate as a sub-variant when the subject is the open question. Shrink it to at most twice its displayed size (`cwebp`, `sips` or `ffmpeg`, whichever is installed) and embed it once, in its own fragment, so the variants stay readable and the file self-contained:

```bash
{ printf '<style>:root{--img-hero:url("data:image/webp;base64,'; base64 < hero.webp | tr -d '\n'; printf '")}</style>\n'; } > images.html
```

A variant uses it as `bg-[image:var(--img-hero)] bg-cover`, with `bg-[position:…]` per breakpoint when the crop changes. Say in the notes that the picture is generated. Without such a tool, use flat blocks in the product's colours and say that the picture is missing; never hotlink one.

### The shell contract

| Where | Attribute or element | What it does |
| --- | --- | --- |
| `<head>` | `<title>` | Title in the preview's header. |
| `<body>` | `data-subtitle` | What is being decided, next to the title. Not the round: the shell reads it from the file name (`v2.html` is "Round 2", `final.html` is "Final"). |
| `<body>` | `data-default-frame` | `desktop` (default), `tablet` or `mobile`: the frame the file opens in. |
| `<body>` | `data-desktop` | Desktop viewport, `1440x900` by default. `1280x800` for a product used on small laptops. |
| `<body>` | `data-default-orientation` | `landscape` when that is how the device is held. |
| `<body>` | `data-theme` | `light` or `dark`: the product has both themes and this one shows first. Adds the theme toggle, which sets the class of the project's `dark` variant on the frame (`.dark` when it defines none); `dark:` utilities follow it. |
| `<body>` | `data-url` | The domain in Safari's address bar. |
| `<body>` | `data-chrome="app"` | Device frames without Safari: an installed PWA, or the HTML approximation of a native app. |
| `context.html` | `<template class="dp-context">`, `<slot>`, `<slot name>` | The shared context. |
| section | `class="dp-variant"`, `id`, `data-name` | A variant. `data-name` is its tab label. |
| section | `data-context="none"` | Don't wrap this variant in the shared context. |
| section | `data-theme-color` | Colour of the device's bars, when the section's background isn't it. |
| section child | `slot="name"` | Which slot of the context the element fills. |
| section child | `class="dp-variant-notes"` | The notes. |

The file opens on the overview: every variant side by side, scaled down, with its name and first sentence. Keys: `0` overview, `1`–`9` a variant (pressing it again replays its entrance animations), `R` rotate, `D` theme, `Z` actual size, `N` notes. The URL hash holds the view, `#<id or all>@<frame>@<orientation>@<theme>`, so `v1.html#v-b@mobile` opens variant B in the phone.

### Rules

- **One file, no external requests** — HTML with Tailwind classes, inline SVG for icons, system font stack unless the project's font is essential (then a single Google Fonts `<link>` in `head.html` is acceptable). It must render offline and stay shareable.
- If the project uses Tailwind, copy its theme into `head.html` as it is (the `@theme` blocks, the variables they read, its `@custom-variant`s), so the variants use the project's own classes, `bg-background` and all. The shell reads the project's breakpoints and the class of its `dark` variant from there, so `lg:` and the theme toggle mean what they mean in the project. Leave out `@import` and `@plugin` lines: the runtime can't fetch them, and a single one fails the whole build. Otherwise put the product's tokens in `@theme`.
- **Frames are real viewports.** Desktop is 1440×900, tablet and mobile are an iPad Air 11" and an iPhone 15/16 in Safari, each scaled down to fit the window. The page scrolls inside the frame, so the fold is real. Breakpoints (`sm:` to `2xl:`, `max-sm:` to `max-2xl:`), container variants (`@md:`) and the screen utilities (`h-screen`, `min-h-screen`, `h-dvh`, `w-screen`) measure the frame, not the browser window, so project markup behaves as it will in production: with Tailwind's default breakpoints, at 1440 `xl:` applies and `2xl:` doesn't. Only arbitrary values like `min-[900px]:` and `h-[100vh]` still follow the window.
- `fixed` is positioned against the frame, so overlays, drawers and modals stay inside it. APIs that draw in the browser's top layer (`popover`, `<dialog>.showModal()`) do not: build those from positioned elements. On a device the status bar and Safari's toolbar lie over the edges of the screen, so anchor app bars and bottom CTAs with `sticky` inside the variant.
- **State lives in an attribute.** Toggle it inline, `onclick="document.getElementById('a-drawer').toggleAttribute('data-open')"`, and style both states with `data-open:` (or `group-data-open:`) and a `transition-*`: `translate-x-full transition-transform duration-200 ease-out-strong data-open:translate-x-0`. Entrances use the `animate-*` utilities from `head.html`, staggered with `[animation-delay:50ms]`. Anything longer than a line of JS goes in a `<script>` inside the section.
- What utilities can't express goes in a `<style>` inside the section, scoped under its id (`#v-a …`). The `.dp-` prefix belongs to the shell; don't use it for your own classes.
- Keep the files readable; the user or a later agent may reuse chunks when implementing. Generating repeated rows or chart paths with a throwaway script is fine, as long as the fragment it writes is plain HTML.

**Write as you design.** Settle the concepts first, a line or two each in the terms of the notes, then write each fragment directly instead of drafting all of them in your head. One long planning pass before the first line is where about half of a round's time goes, and a layout problem is cheaper to fix after the screenshot than to prevent by deliberating.

## 4. Assemble and check

Each round is assembled into its own file, so earlier rounds stay comparable:

```bash
(cd "$dir" && cat head.html images.html context.html a.html b.html c.html "<skill-dir>/assets/tailwind.html" "<skill-dir>/assets/shell.html" > v1.html)
open "$dir/v1.html"        # macOS; xdg-open on Linux, `start ""` on Windows
```

Leave `images.html` and `context.html` out of the `cat` when the proposal has none.

If a browser automation tool is available, take a screenshot before showing the file to the user. `v1.html#all` puts every variant in one screenshot, which is enough to catch a broken layout, overflow or unreadable contrast; open a single tab (`v1.html#v-b@mobile`) at the frame the proposal targets to look closer. For a responsive product look at the other frames as well (`#all@tablet`, `#all@mobile`): a layout drawn for desktop most often goes wrong at the width in between, stretched from edge to edge or missing what was hidden below a breakpoint. Fix in the fragments and rerun the `cat`: a patch to `vN.html` is lost at the next assembly. Fix obvious breakage first — the user's attention is the scarce resource. One inspection round plus one confirmation round is enough; polishing mockups nobody has chosen yet wastes the user's time.

With impeccable, also run `<impeccable-dir>/scripts/impeccable detect --json "file://$dir/vN.html"` once and fix the mechanical findings (contrast, banned patterns). Pass the `file://` URL, not the path: only a rendered page has the Tailwind styles, and one run covers every tab. If it finds no Chrome, point `IMPECCABLE_BROWSER` at any Chromium executable.

## 5. Collect feedback

Tell the user the file path, then **end your message with a question**. The loop depends on the answer, and a recommendation on its own tends to get read as a finished deliverable. Ask which variant is closest, what to keep from the others, and what feels wrong. You may give your own recommendation first, but it goes before the question, not in its place. Use a structured question tool if available: options are the variant names plus "mix of variants", and the free-text answer carries the details.

## 6. Iterate

Each round assembles a new `vN.html`. The fragments are the working copy, changed in place, and every `vN.html` a snapshot, so rewrite or edit only the fragments that change; unchanged variants cost nothing, and `head.html` stays as it is.

- If the user picked one: refine it, and optionally add 1–2 sub-variants exploring the open questions they raised (copy its fragment and rename its id).
- If they want a mix: write the combined version as a new fragment, first in the `cat`, and keep the sources as reference tabs.
- If nothing works: ask what's missing, then go wider, not narrower.

Mention what changed since the previous round (a short "Changes" section in the notes) so the user doesn't have to diff visually. Stop iterating when the user approves.

## 7. Finalise and report

`final.html` is the file that gets shared: with whoever signs the design off, and with whoever builds it. Before assembling it, rewrite the notes of the approved fragment for that reader: what it is, how to look at it (frames, theme, what is clickable), what changes from today, and what is still to decide. Drop the round-by-round changes. Then assemble it from `head.html`, `images.html` and `context.html` if there are any, and the approved fragment only (one tab, including the relevant states), open it, and report back in the user's language:

- chosen variant and the key decisions (and what was rejected, briefly);
- spec: layout structure, components, tokens used (colors, type scale, spacing, radii), interactions and states;
- motion & interaction: a table `Interaction | Trigger & frequency | Animation | Easing | Duration`, one row per interaction the mockup shows. "None" is a valid row for high-frequency and keyboard actions;
- implementation notes: mapping to existing components in the codebase, new components needed, open questions;
- assets: every generated picture, as something to approve, redo or replace before it ships;
- path of `final.html` (and earlier rounds).

**Other browsers, optional.** The rounds are checked in one browser, which is enough to choose a direction. Once a variant is approved its markup is what the implementation starts from, so ask whether to check `final.html` in Safari and Firefox as well. When the user says yes, open it in each (`open -a Safari "$dir/final.html"`, `open -a Firefox "$dir/final.html"` on macOS), compare it with the approved rendering at the frames the product ships at, fix the fragment, and list what differed in the report.

Don't start implementing production code as part of this skill — the approval is the deliverable. Offer to implement next.
