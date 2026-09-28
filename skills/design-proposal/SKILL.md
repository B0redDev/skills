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
- **Platform**: web desktop, responsive web, or mobile app. This decides the default frame (see template).
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

Start from `assets/template.html` (read it; it contains the tab shell, keyboard navigation, notes panel, and a desktop/tablet/mobile frame toggle). With impeccable, read `<impeccable-dir>/reference/craft-floor.md` right before writing the variants. Its checks and bans apply to mockups as much as to shipped UI, and the user will judge what they see. Rules:

- **One file, no build step, no external requests** — raw HTML + CSS, inline SVG for icons, system font stack unless the project's font is essential (then a single Google Fonts `<link>` is acceptable). It must render offline and stay shareable.
- Scope every variant's CSS under its section id (`#v-a .card {…}`) so variants don't bleed into each other or into the `.dp-` chrome.
- Frames are container-query containers: write responsive rules with `@container frame (max-width: 600px)` instead of `@media`, so the frame toggle actually previews breakpoints. Set `data-default-frame="mobile"` on `<body>` for mobile-app proposals.
- Minimal JS only for interactions that are part of the decision (e.g. opening a drawer). Static is fine otherwise.
- Keep the file readable; the user or a later agent may reuse chunks when implementing.

## 4. Save and open

Save to the system temp dir, versioned per round so earlier rounds stay comparable:

```bash
dir="${TMPDIR:-/tmp}/design-proposal/<kebab-slug>"; mkdir -p "$dir"
# write $dir/v1.html, then v2.html for the next round, …
open "$dir/v1.html"        # macOS
# xdg-open on Linux, `start ""` on Windows
```

If a browser automation tool is available, take a screenshot of each tab to sanity-check rendering (overflow, broken layout, unreadable contrast) before showing it to the user, at the frame sizes the proposal targets. With impeccable, also run `<impeccable-dir>/scripts/impeccable detect --json "$dir/vN.html"` once and fix the mechanical findings (contrast, banned patterns). Fix obvious breakage first — the user's attention is the scarce resource. One inspection round plus one confirmation round is enough; polishing mockups nobody has chosen yet wastes the user's time.

## 5. Collect feedback

Tell the user the file path, then **end your message with a question**. The loop depends on the answer, and a recommendation on its own tends to get read as a finished deliverable. Ask which variant is closest, what to keep from the others, and what feels wrong. You may give your own recommendation first, but it goes before the question, not in its place. Use a structured question tool if available: options are the variant names plus "mix of variants", and the free-text answer carries the details.

## 6. Iterate

Each round writes a new `vN.html`:

- If the user picked one: refine it, and optionally add 1–2 sub-variants exploring the open questions they raised.
- If they want a mix: build the combined version as the first tab, keep the sources as reference tabs.
- If nothing works: ask what's missing, then go wider, not narrower.

Mention what changed since the previous round (a short "Changes" line in the notes) so the user doesn't have to diff visually. Stop iterating when the user approves.

## 7. Finalise and report

Write `final.html` containing only the approved design (one tab, including the relevant states), open it, and report back in the user's language:

- chosen variant and the key decisions (and what was rejected, briefly);
- spec: layout structure, components, tokens used (colors, type scale, spacing, radii), interactions and states;
- motion & interaction, when the design has any: a table `Interaction | Trigger & frequency | Animation | Easing | Duration`. With emil-design-eng, the values follow its framework, and "none" is a valid, often correct answer for high-frequency and keyboard actions;
- implementation notes: mapping to existing components in the codebase, new components needed, open questions;
- path of `final.html` (and earlier rounds).

Don't start implementing production code as part of this skill — the approval is the deliverable. Offer to implement next.
