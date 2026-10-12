---
name: design-proposal
description: Propose UI designs for approval before building them. Produces one self-contained HTML file with several genuinely different design variants in tabs, opens it in the browser, collects the user's feedback, iterates, and reports the approved direction as an implementation-ready spec. Use this whenever a task involves new or reworked UI and the visual direction is not already settled — "design a settings page", "how should this dashboard look", "give me some options for the onboarding", "mockup", "redesign", "propose a layout", or before implementing a sizeable UI feature from a vague brief — even if the user doesn't say "proposal". Do not use for pure CSS bug fixes or when an approved design/mockup already exists and just needs implementing.
compatibility: Works standalone. Gets better with the optional `impeccable` (pbakaus/impeccable) and `emil-design-eng` (emilkowalski/skill) skills installed, and with a browser automation tool for screenshots.
---

# Design Proposal

Goal: get the user to approve a visual direction **before** production code is written. A browser mockup is cheap to change; a half-built feature isn't. Output of this skill is a decision plus a spec, not production code.

## Companion skills

Two skills sharpen the proposals when they're installed. Check the available skills list once at the start; use whichever is present, skip silently otherwise, and name the ones you used in the first report so the user knows which quality bar applied.

- **`impeccable`** is the design-quality layer: project context, variant derivation, the craft floor, and a mechanical anti-pattern detector. Read its `SKILL.md` first; `<impeccable-dir>` below is the folder that contains it. Use only the parts named in the steps below. Its init interview, `concept-seed`, decision page and finish reviewer overlap with this skill, which already is the decision round, and would make the user wait for a design-system setup when they asked for mockups.
- **`emil-design-eng`** is the interaction and motion layer: whether something should animate, easing, duration, press feedback. Read its `SKILL.md` before you add any interaction or motion to a variant.

## 1. Gather context (before drawing anything)

Variants that ignore the real product are useless for approval, so look first:

- **Brief**: what is being designed, for whom, the primary task on the screen, hard constraints (platform, existing flows, data shown).
- **Existing design language** (if there's a codebase): grep for theme/tokens files, Tailwind config, CSS variables, component library, fonts, icon set. Reuse real colors, radii, type scale, spacing, and copy tone so the proposal looks like *their* product. With impeccable: run `<impeccable-dir>/scripts/impeccable context` once from the project root. It loads `PRODUCT.md`, `DESIGN.md` and any surface brief, and those outrank your own grep. A missing `PRODUCT.md` doesn't block a proposal, so skip the init it suggests.
- **Platform**: web desktop, responsive web, mobile web, or native mobile app. This decides the default frame and, on mobile, whether Safari's chrome is shown (see step 3).
- **Real content**: use plausible domain data (real-looking names, numbers, dates, labels). Never lorem ipsum — fake text hides layout problems and makes variants hard to judge.

If a missing answer would change the variants fundamentally (e.g. mobile vs desktop), ask one batched question. Otherwise make a reasonable assumption, state it in the notes, and proceed.

## 2. Design the variants

Make **3 variants** by default (2 if the space is narrow, max 4). Each must differ in a way that matters for the decision:

- information hierarchy / layout structure (list vs cards vs split view vs table),
- interaction model (inline edit vs modal vs dedicated page, tabs vs stepper),
- density and emphasis (compact power-user vs spacious guided).

Color or font swaps alone are not variants — the user can't make a meaningful choice between them. If the brief is precise, vary the risk level instead: one safe/conventional, one refined, one bolder.

With impeccable: pick its mode for the surface (Operate for app UI, Persuade for marketing, Read for docs, Experience for showcases; read `reference/operate.md` for app UI). Then follow its derivation instead of your first idea: list five to seven materially different structures from the content, task and user behaviour, order them by resonance, and build the top three. The long list is what keeps variant C from being variant A with a darker theme.

Give each variant a short evocative name ("A · Split inbox", "B · Card feed") and write, in the notes panel: the idea in one sentence, who it's best for, and honest tradeoffs. Tradeoffs are what make the choice informed.

Show the states that affect the decision: primary state always; empty/loading/error/hover/selected when they're part of the question. Don't pad with states nobody asked about.

**Interaction and motion.** Add motion only where it is part of the decision (drawer vs modal, inline expand vs new page). A variant that animates everything makes the comparison unfair to the static ones. With emil-design-eng, every animation passes its decision framework:

- how often the user will see it, and never on keyboard-initiated actions;
- what it is for;
- a custom ease-out curve;
- under 300ms;
- `transform`/`opacity` only;
- `scale(0.97)` on `:active` for pressables;
- hover effects gated behind `@media (hover: hover) and (pointer: fine)`;
- a `prefers-reduced-motion` fallback.

Note the motion choices in the variant's notes.

## 3. Build the HTML file

Every character you write costs time, so write only what is specific to the proposal, styled with Tailwind utility classes: they map one-to-one onto a Tailwind codebase, so markup can move straight into the implementation.

Step 4 appends two files from `<skill-dir>/assets/` (`<skill-dir>` is the folder that contains this file) with `cat`. `tailwind.html` is the Tailwind v4 runtime: it compiles the classes in the browser, with no build step or network. `shell.html` is the tab bar, notes panel, keyboard navigation, and the desktop/tablet/mobile frame toggle, where tablet and mobile are a real-size iPad and iPhone in Safari. Don't read or retype them; together they're 300 KB.

With impeccable, read `<impeccable-dir>/reference/craft-floor.md` right before writing the variants. Its checks and bans apply to mockups as much as to shipped UI, and the user will judge what they see.

All files go in `$dir` (step 4). `head.html` holds what every variant shares, so no variant restates it: the document head, the body options, and the product's theme.

```html
<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Settings · Matchday</title>
<style type="text/tailwindcss">
  @theme { --color-brand: #0b7a4b; --font-sans: Inter, system-ui, sans-serif; }
  @layer base {
    .dp-variant { @apply bg-white text-zinc-900 antialiased; }  /* in base, so a variant's own bg-* wins */
  }
</style>
<body data-subtitle="Round 1 · three directions" data-default-frame="desktop" data-url="matchday.app">
```

Each variant is one fragment, `a.html`, `b.html`, …: a single section holding its notes. The shell moves the section into the frame and the notes into the side panel; file order is tab order.

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

Rules:

- **One file, no external requests** — HTML with Tailwind classes, inline SVG for icons, system font stack unless the project's font is essential (then a single Google Fonts `<link>` in `head.html` is acceptable). It must render offline and stay shareable.
- If the project uses Tailwind, copy its theme into `head.html` (the `@theme` block, the variables it reads, its `@custom-variant`s), so the variants use the project's own classes, `bg-background` and all. Leave out `@import` and `@plugin` lines: the runtime can't fetch them, and a single one fails the whole build. Otherwise put the product's tokens in `@theme`.
- Breakpoints (`sm:` to `2xl:`, `max-sm:` to `max-2xl:`) and container variants (`@md:`) measure the frame, not the browser window, so the frame toggle previews them; only arbitrary ones like `min-[900px]:` still follow the window. The desktop frame is the window minus the notes panel, about 1080px in a 1440px window, so `lg:` applies there and `xl:` usually doesn't. Set `data-default-frame="mobile"` on `<body>` for mobile proposals.
- What utilities can't express goes in a `<style>` inside the section, scoped under its id (`#v-a …`). The `.dp-` prefix belongs to the shell; don't use it for your own classes.
- Mobile and tablet are a real-size iPhone 15/16 and iPad Air 11" in Safari; the page scrolls inside the screen, so the fold is real. Rotate (key `R`) switches to landscape; set `data-default-orientation="landscape"` on `<body>` when that's the primary use. Put the page's domain in `data-url` on `<body>`; for a native app set `data-chrome="app"` to drop Safari. The bars take the variant's background tint; `data-theme-color` on the section overrides it. Give full-height app layouts `h-full` on the section, not `h-screen` or `dvh`, which measure the browser window. Anchor app bars and sticky CTAs with `sticky` inside the variant, never `fixed`, which escapes the device.
- Minimal JS only for interactions that are part of the decision (e.g. opening a drawer). Static is fine otherwise.
- Keep the files readable; the user or a later agent may reuse chunks when implementing. Generating repeated rows or chart paths with a throwaway script is fine, as long as the fragment it writes is plain HTML.

**Write as you design.** Settle the concepts first, a line or two each in the terms of the notes, then write each fragment directly instead of drafting all of them in your head. One long planning pass before the first line is where about half of a round's time goes, and a layout problem is cheaper to fix after the screenshot than to prevent by deliberating.

## 4. Save and open

Each round is assembled into its own file in the system temp dir, so earlier rounds stay comparable:

```bash
dir="${TMPDIR:-/tmp}/design-proposal/<kebab-slug>"; mkdir -p "$dir"
# write head.html, a.html, b.html, c.html into $dir, then:
(cd "$dir" && cat head.html a.html b.html c.html "<skill-dir>/assets/tailwind.html" "<skill-dir>/assets/shell.html" > v1.html)
open "$dir/v1.html"        # macOS
# xdg-open on Linux, `start ""` on Windows
```

If a browser automation tool is available, take a screenshot of each tab to sanity-check rendering (overflow, broken layout, unreadable contrast) before showing it to the user, at the frame sizes the proposal targets; `v1.html#v-b@mobile` opens tab B in the mobile frame. Fix in the fragments and rerun the `cat`: a patch to `vN.html` is lost at the next assembly. Fix obvious breakage first — the user's attention is the scarce resource. One inspection round plus one confirmation round is enough; polishing mockups nobody has chosen yet wastes the user's time.

With impeccable, also run `<impeccable-dir>/scripts/impeccable detect --json "file://$dir/vN.html"` once and fix the mechanical findings (contrast, banned patterns). Pass the `file://` URL, not the path: only a rendered page has the Tailwind styles, and one run covers every tab. If it finds no Chrome, point `IMPECCABLE_BROWSER` at any Chromium executable.

## 5. Collect feedback

Tell the user the file path, then **end your message with a question**. The loop depends on the answer, and a recommendation on its own tends to get read as a finished deliverable. Ask which variant is closest, what to keep from the others, and what feels wrong. You may give your own recommendation first, but it goes before the question, not in its place. Use a structured question tool if available: options are the variant names plus "mix of variants", and the free-text answer carries the details.

## 6. Iterate

Each round assembles a new `vN.html`. The fragments are the working copy, changed in place, and every `vN.html` a snapshot, so rewrite or edit only the fragments that change; unchanged variants cost nothing.

- If the user picked one: refine it, and optionally add 1–2 sub-variants exploring the open questions they raised (copy its fragment and rename its id).
- If they want a mix: write the combined version as a new fragment, first in the `cat`, and keep the sources as reference tabs.
- If nothing works: ask what's missing, then go wider, not narrower.

Mention what changed since the previous round (a short "Changes" line in the notes) so the user doesn't have to diff visually. Stop iterating when the user approves.

## 7. Finalise and report

Assemble `final.html` from `head.html` and the approved fragment only (one tab, including the relevant states), open it, and report back in the user's language:

- chosen variant and the key decisions (and what was rejected, briefly);
- spec: layout structure, components, tokens used (colors, type scale, spacing, radii), interactions and states;
- motion & interaction, when the design has any: a table `Interaction | Trigger & frequency | Animation | Easing | Duration`. With emil-design-eng, the values follow its framework, and "none" is a valid, often correct answer for high-frequency and keyboard actions;
- implementation notes: mapping to existing components in the codebase, new components needed, open questions;
- path of `final.html` (and earlier rounds).

Don't start implementing production code as part of this skill — the approval is the deliverable. Offer to implement next.
