---
name: native-design-proposal
description: Propose designs for native apps for approval before building them, as real native code rendered by the platform itself. Builds several genuinely different variants of a screen or flow with the platform's own toolkit (SwiftUI, UIKit, AppKit, Jetpack Compose, WinUI, Expo / React Native, Flutter, GPUI), captures them from the simulator, emulator or a real window, shows the captures side by side in a tabbed decision page with tradeoffs, lets the user try each variant live, iterates on feedback, and reports the approved direction as an implementation-ready spec. Use this whenever a task involves new or reworked UI for an iOS, iPadOS, macOS, Android or Windows app and the visual direction is not settled, such as "design the settings screen of my iPhone app", "how should this Mac window look", "give me options for the onboarding of the Expo app", "mockup", "redesign", "make it feel native", even if the user doesn't say "proposal". Do not use it for websites and web apps (that is `design-proposal`), for fixing a layout bug, or when an approved design already exists and just needs implementing.
compatibility: Apple platforms need Xcode with an iOS Simulator runtime (bundled build-and-capture script, no Xcode project required). Android needs the Android SDK with an emulator or device; Windows needs a Windows machine. Gets better with the optional skills impeccable, emil-design-eng, apple-design, ios-design, the better-* family, and the project toolkit's own skill (expo-native-ui, gpui-kit-design-guides, write-swift).
---

# Native Design Proposal

Goal: get the user to approve a visual direction for a native app **before** production code is written. The output of this skill is a decision plus a spec, backed by throwaway code. It is not the feature.

## Why real code, not a picture of it

A native look is not a style you can paint. The operating system draws the bars, the materials, the lists and the controls, and it redraws them differently on every OS release, appearance, text size and device. An HTML imitation is a guess that goes stale, and it shows the one thing a native design must not have: controls that are almost right.

So every variant is a small real program, built with the platform's toolkit from the platform's stock components, and what the user judges is a capture of what the system actually rendered. Three things follow, and they shape every step below:

- **The capture is the truth.** Don't describe from memory what an OS version looks like. Build it, look at the capture, and correct your idea of the platform from it.
- **Stock first is also the cheapest route.** A `List` in a `NavigationStack` is five lines and already correct in dark mode, at large text and under next year's OS. Hand-drawn chrome is more code and wrong in all three.
- **The user can touch it.** A variant that runs can be tried in the simulator or as a window. For anything about feel (a sheet against a push, a gesture, a transition), that beats any screenshot.

## Companion skills

Check the available skills once at the start. Use whichever are present, skip the others silently, and name the ones you used in the first report so the user knows which quality bar applied.

| Skill | What it is for here | Read |
| --- | --- | --- |
| `impeccable` | Project context, and its native platform references and audit | `SKILL.md`, then `reference/ios.md` or `reference/android.md` for the target, `reference/adapt.native.md` when a design moves between platforms or device classes, `reference/audit.native.md` for the check in step 5. Leave out the parts that overlap with this skill or don't apply: its `detect` script scans a DOM and says nothing about a native capture; its init interview, `concept-seed` and `new-work` flow build a decision page of their own, and this skill already is the decision round. |
| `apple-design` | How motion and materials should behave on Apple platforms: springs, interruptibility, velocity, translucency, type | before adding any custom motion or material on iOS or macOS |
| `ios-design` | iPhone navigation and state, hierarchy, safe areas, keyboard, Dynamic Type | for iPhone and iPad proposals. Skip its image-generation step: the capture replaces the generated target. |
| `emil-design-eng` | Whether something should animate at all: frequency, purpose, press feedback | before adding any motion. Its values are CSS; step 2 says how they carry over. |
| `better-ui`, `better-typography`, `better-layout`, `better-colors`, `better-accessibility`, `better-writing` | Polish that is not platform-specific: concentric radii, optical alignment, hierarchy, contrast, labels | when a variant has custom-drawn content (a card, a chart, a hero). Their principles carry over; their CSS recipes do not. |
| the toolkit's skill: `write-swift`, `expo-native-ui` (with `expo-router`, `expo-ui`, `expo-animation`), `gpui-kit-design-guides` (normative for GPUI Kit apps) | Writing the variants correctly in the project's toolkit | before writing code in that toolkit |

## 1. Gather context (before building anything)

- **Brief**: what is being designed, for whom, the primary task on the screen, hard constraints.
- **Platforms and device classes**: iPhone only, iPhone and iPad, a Mac window, an Android phone and tablet, Windows. Each platform a product ships on gets its own variants, built from that platform's idioms. A design is translated between platforms, never transplanted.
- **Toolkit and OS target** (if there's a codebase): SwiftUI or UIKit, Compose or Views, Expo, Flutter, GPUI; the deployment target or `minSdk`; the app's accent colour, fonts, icon set, asset catalog, and the shared components it already has. With impeccable, run `<impeccable-dir>/scripts/impeccable context` once from the project root; `PRODUCT.md` and `DESIGN.md` outrank your own grep. A missing `PRODUCT.md` doesn't block a proposal: when the script answers `PRODUCT_INIT_REQUIRED`, carry on without it.
- **Real content**: plausible domain data (real-looking names, numbers, dates, labels) in a shared sample-data file. Never lorem ipsum: fake text hides truncation, which is half of what a native layout has to survive. When the app is about media (photos, stickers, covers), take sample images from the project's fixtures or assets, or render a set once with a short script, and don't spend the round on them.
- **Render route**. Read the reference for each target platform now; it holds the look, the build recipe and the capture commands:

  | Target | Reference | Bundled harness |
  | --- | --- | --- |
  | iPhone, iPad | `references/ios.md` | `scripts/apple-render.sh ios` |
  | Mac | `references/macos.md` | `scripts/apple-render.sh mac` |
  | Android | `references/android.md` | none: the project's Gradle build, then `adb` |
  | Windows | `references/windows.md` | none: needs a Windows machine |
  | A variant that must use the app's own components, or a toolkit other than SwiftUI | `references/in-project.md` | the project's own build, then `apple-render.sh mac` with `APP=` for a Mac executable, `simctl` or `adb` otherwise |

  Prefer a **standalone** proposal (stock components plus the product's tokens copied in): it builds in seconds and touches nothing in the repository. Go **in-project** only when the decision depends on the app's own components or on a toolkit the standalone harness doesn't cover.

Check the toolchain before promising anything (`xcrun simctl list devices available`, `adb devices`). If the platform can't be built or run on this machine, say so before designing, and offer the two honest options: set the toolchain up, or fall back to the `design-proposal` skill with the proposal clearly labelled as an HTML approximation. Never pass an imitation off as a native render.

If a missing answer would change the variants fundamentally (which platform, phone or tablet), ask one batched question. Otherwise assume, state the assumption in the notes, and proceed.

## 2. Design the variants

Make **3 variants** by default (2 if the space is narrow, 4 at most). Each must differ in a way that matters for the decision, and each must stay native. On a native platform the meaningful differences are:

- **navigation container**: tabs, a stack, a sidebar or split view, a single window with an inspector;
- **presentation of the secondary task**: push, sheet, popover, inline expansion, separate window;
- **content shape**: grouped list, plain list, table, grid, one custom hero above a stock list;
- **density and emphasis**: glanceable summary against full detail;
- **where the primary action lives**: toolbar, bottom bar, floating button, inline;
- **how much brand shows**: stock with the product's tint, stock scaffolding around custom content cells, one signature element.

A colour or font swap is not a variant. If the brief is precise, vary the last axis as a risk level: A is what Apple, Google or Microsoft would ship, B adds the product's own content design inside stock scaffolding, C makes one bold move and keeps everything else stock. Don't build your first three ideas: list five to seven materially different structures from the content, the task and how the user behaves, order them by how well they fit, and build the top three. The long list is what keeps variant C from being variant A with another sidebar.

**The native floor**, which every variant has to clear, bold ones included:

- **Stock containers and controls.** Navigation, bars, lists, forms, sheets, menus, pickers, switches come from the toolkit, unstyled. Custom drawing is for the content that is the product (a score card, a chart, a player), never for chrome.
- **Semantic everything.** System text styles, semantic colours, the system icon set, the system font for body and controls. They are what makes dark mode, larger text and high contrast work without extra code. Brand goes through the channels the platform leaves open: tint or accent, a display typeface for a few moments, imagery, the content cells.
- **The platform's input model.** Touch: full-size targets, nothing that depends on hover, system gestures left alone. Pointer and keyboard: menus, shortcuts, right-click, resizable windows, tighter density.
- **No web tells.** Cards with shadows inside cards, a hero header on a utility screen, a hand-built back button or tab bar, a hamburger menu, toasts for everything, a centred max-width column in a desktop window, pill buttons spanning the screen on a Mac, hand-rolled glass. The platform reference lists the ones that give each platform away.

Give each variant a short evocative name ("A · Grouped settings", "B · Team first") and write for the notes panel: the idea in one sentence, who it's best for, and honest tradeoffs. Tradeoffs are what make the choice informed.

Show the states that affect the decision: the primary state always; empty, loading, error, selected, a sheet open, when they're part of the question. Don't pad with states nobody asked about.

**Interaction and motion.** The system's own transitions (push, sheet, popover, menu) are the default and usually the right final answer: users have the muscle memory, and they come free with the stock containers. Add custom motion only where it is part of the decision. With emil-design-eng, its framework still decides *whether*: how often the user will see it (never on keyboard-initiated or high-frequency actions), and what it is for. Its CSS durations and curves do not port. On a native platform the *how* is the toolkit's springs and motion tokens, interruptible and continuing from the gesture's velocity, with the platform's haptic on the commit, and a cross-fade under Reduce Motion (with apple-design, its spring defaults: critically damped unless a gesture carried momentum). The platform reference names the APIs. Note every motion choice in the variant's notes.

## 3. Build the variants

Work in a scratch directory, one per proposal, outside the repository. It is the deliverable, so it has to outlive the session (the system's temp directory is cleaned behind your back):

```bash
dir="$HOME/.cache/native-design-proposal/<kebab-slug>"; mkdir -p "$dir"
```

Follow the platform reference for the code contract. Whatever the toolkit, the shape is the same:

- **One entry point that switches on `variant` and `state`**, given at launch (arguments, a deep link, intent extras). A state is just an initial value: the sheet starts open, the data starts empty, a row starts selected. That is what lets every capture be taken without tapping through the app, and reproduced exactly in the next round. Where the toolkit doesn't take them from the system, the entry point also takes the appearance (light or dark) and, on a desktop, the window size.
- **One file per variant**, plus one shared file of sample data, so a round touches only the variants that change.
- **The least code that renders the idea.** No networking, persistence, view models or tests: sample data in, pixels out. Controls should respond (a toggle toggles, a tab switches), because the user will try them, but nothing needs to be saved.

**Write as you design.** Settle the concepts first, a line or two each in the terms of the notes, then write each variant directly. A layout problem is cheaper to fix after the first capture than to prevent by deliberating, and here the first capture arrives within seconds.

## 4. Capture and assemble

Capture every variant with the platform reference's commands. Each round's captures go in their own subdirectory (`v1`, `v2`, …), so earlier rounds stay comparable. The default set per variant is the primary state in light and in dark, plus each state that is part of the decision; add a second device class when the product ships on it. `apple-render.sh` prints one ready `<figure>` tag per capture:

```bash
NAME="Matchday" "<skill-dir>/scripts/apple-render.sh" ios "$dir" shot -o v1 a a@dark a:empty b b@dark c c@dark
```

The decision page is assembled from small files in `$dir`. `head.html` holds the title:

```html
<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Settings · Matchday</title>
<body data-subtitle="Round 1 · three directions · iPhone, iOS 27">
```

Each variant is one fragment, `a.html`, `b.html`, …: the figures the script printed, then the notes. File order is tab order.

```html
<section class="np-variant" id="v-a" data-name="A · Grouped settings">
  <figure class="np-shot np-iphone"><img src="v1/a-iphone.png" width="402" alt=""><figcaption>iPhone 18 Pro · light</figcaption></figure>
  <figure class="np-shot np-iphone"><img src="v1/a-iphone-dark.png" width="402" alt=""><figcaption>iPhone 18 Pro · dark</figcaption></figure>
  <div class="np-variant-notes">
    <h2>A · Grouped settings</h2>
    <p>The idea in one sentence.</p>
    <h3>Best for</h3><p>…</p>
    <h3>Tradeoffs</h3><ul><li>+ …</li><li>− …</li></ul>
    <h3>Built from</h3><p>The stock components used, and anything custom.</p>
    <h3>Try it</h3><pre>"&lt;skill-dir&gt;/scripts/apple-render.sh" ios "&lt;dir&gt;" run a</pre>
    <!-- From round 2 on: <h3>Changes</h3><ul><li>…</li></ul> -->
  </div>
</section>
```

Edit the captions so they say what differs between the captures of a variant ("Empty", "Sheet open"). Keep the `width` the script printed: it is the capture's size in points, so the page shows it at real size. For a capture you take by hand, the class is `np-iphone`, `np-ipad`, `np-mac`, `np-android` or `np-windows`, and `width` is the pixel width divided by the screen's scale. Write the "Try it" command with real absolute paths, so the user can paste it into a terminal as it is.

`<skill-dir>/assets/shell.html` is the tab bar, the notes panel, keyboard navigation and the "Fit" toggle. Append it with `cat`; don't read or retype it:

```bash
(cd "$dir" && cat head.html a.html b.html c.html "<skill-dir>/assets/shell.html" > v1.html)
open "$dir/v1.html"        # macOS; xdg-open on Linux, `start ""` on Windows
```

The page references the captures by relative path, so `$dir` as a whole is the deliverable.

## 5. Check the captures before the user sees them

Open every capture and look at it. You wrote the code from an idea of the platform; the capture is what the platform made of it, and the two differ more often than expected on a new OS release.

- Is anything clipped, truncated, overlapping, or under the status bar, home indicator or title bar?
- Does each variant clear the native floor from step 2? Would a fluent user of the platform take it for a first-party app, or pause at something? Go through the "Tells" list of the platform reference. With impeccable, on iOS and Android, score the recommended variant against "Platform Conformance" and "Appearance & Theming" in `reference/audit.native.md`; for a GPUI Kit app, run the guide's design review checklist instead.
- Dark: is any text or icon lost, any raw colour left unadapted?
- Do the variants still differ in a way that matters, now that they are real?

Fix in the variant's source and capture again. One inspection round plus one confirmation round is enough: polishing variants nobody has chosen wastes the user's time. Large text, a small device and landscape are checked on the approved variant in step 8, not on all of them. Once the page is assembled, load it once and confirm every capture shows.

## 6. Collect feedback

Leave the variant you recommend running (`apple-render.sh … run <variant>`, or the reference's equivalent), tell the user the page's path and that each variant's notes carry the command to try it live, then **end your message with a question**. The loop depends on the answer, and a recommendation on its own tends to get read as a finished deliverable. Ask which variant is closest, what to keep from the others, and what feels wrong. You may give your own recommendation first, but it goes before the question, not in its place. Use a structured question tool if available: options are the variant names plus "mix of variants", and the free-text answer carries the details.

## 7. Iterate

Each round captures into a new subdirectory and assembles a new `vN.html`. The sources and the fragments are the working copy, changed in place; every `vN.html` with its captures is a snapshot. Capture only the variants that changed: an unchanged fragment keeps pointing at its earlier captures.

- If the user picked one: refine it, and optionally add one or two sub-variants exploring the open questions they raised (copy its source and fragment, give them a new variant id).
- If they want a mix: build the combined version as a new variant, first in the `cat`, and keep the sources as reference tabs.
- If nothing works: ask what's missing, then go wider, not narrower.

Mention what changed since the previous round (a short "Changes" list in the notes) so the user doesn't have to diff captures by eye. Stop iterating when the user approves.

## 8. Finalise and report

Give the approved variant the checks that were skipped while it was one of three, and fix what they find: a large text size, the smallest device or window the product supports, the second device class and landscape if it ships there, and Reduce Motion if it has custom motion. Capture them into `final/`, assemble `final.html` from `head.html` and the approved fragment only, and open it. Then stop what the proposal left running (`apple-render.sh … stop` quits the app and shuts down the simulators the proposal booted).

Report back in the user's language:

- chosen variant and the key decisions (and what was rejected, briefly);
- spec, in the platform's own vocabulary: the navigation structure and containers, the stock components by name, the semantic tokens (text styles, colour roles, tint, symbol names), spacing only where it departs from the system's, the states;
- motion and interaction, when the design has any: a table `Interaction | Trigger & frequency | Animation | Spring or token | Haptic`. "System transition" is a valid and often correct row;
- what was checked and on what: which simulator, emulator or window, which OS version, which checks from the list above. Say plainly what a simulator cannot show (gesture feel, performance, a real display) and what was not checked;
- implementation notes: mapping to existing components in the codebase, new components needed, open questions. The approved variant's source is a head start, with its sample data and state switches to be replaced by the real thing;
- paths: `final.html`, the earlier rounds, the variant sources.

Don't start implementing production code as part of this skill. The approval is the deliverable. Offer to implement next.
