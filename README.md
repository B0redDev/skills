# skills

Agent skills by [@B0redDev](https://github.com/B0redDev), for Claude Code and other agents that read `SKILL.md`.

| Skill | What it does |
| --- | --- |
| [design-proposal](skills/design-proposal/SKILL.md) | Proposes several web UI design variants as one self-contained HTML file: all of them side by side, then each one in a real-size desktop, tablet or phone frame, with working interactions and motion. Opens it in the browser, iterates on your feedback, and reports the approved direction as a spec. |
| [native-design-proposal](skills/native-design-proposal/SKILL.md) | The same loop for native apps (iOS, iPadOS, macOS, Android, Windows): builds the variants as real native code from stock components, captures them from the simulator or as real windows, shows the captures in a tabbed decision page, lets you try each variant live, and reports the approved direction as a spec. Ships a build-and-capture script for SwiftUI that needs no Xcode project. |
| [theme-generator](skills/theme-generator/SKILL.md) | Generates Tailwind v4 palettes or shadcn/ui tokens (colours, radius, fonts) from a brand colour, a description, an image, a URL or your current theme; previews 2–3 candidates in light and dark with contrast checks and writes the chosen one into your CSS. |

## Install

With the [`skills`](https://github.com/vercel-labs/skills) CLI:

```bash
npx skills add B0redDev/skills
```

Manually, for Claude Code:

```bash
git clone https://github.com/B0redDev/skills.git ~/Developer/skills
ln -s ~/Developer/skills/skills/design-proposal ~/.claude/skills/design-proposal
ln -s ~/Developer/skills/skills/native-design-proposal ~/.claude/skills/native-design-proposal
ln -s ~/Developer/skills/skills/theme-generator ~/.claude/skills/theme-generator
```

### Optional companions for `design-proposal`

`design-proposal` works on its own. When these skills are installed it also uses them: impeccable for design quality (project context, variant derivation, craft floor, anti-pattern detector) and emil-design-eng for interaction and motion. When the agent has an image generation tool, it also generates the pictures a design needs, in the style of the product's own.

```bash
npx skills add pbakaus/impeccable
npx skills add emilkowalski/skill
```

### Optional companions for `native-design-proposal`

`native-design-proposal` works on its own with Xcode installed (Android needs the Android SDK, Windows a Windows machine). When these skills are installed it also uses them: impeccable for project context, variant derivation and its native platform references; emil-design-eng and apple-design for motion; ios-design for iPhone structure; the better-* family for polish of custom content; and the project toolkit's own skill.

```bash
npx skills add pbakaus/impeccable
npx skills add emilkowalski/skills     # emil-design-eng, apple-design
npx skills add jakubkrehel/skills      # better-ui, better-typography, better-layout, better-colors, better-accessibility, better-writing
npx skills add expo/skills             # expo-native-ui, for Expo apps
npx skills add longbridge/gpui-kit     # gpui-kit-design-guides, for GPUI Kit apps
```

## Layout

```
skills/<name>/
├── SKILL.md      # frontmatter (name, description) + instructions
├── assets/       # files the skill uses in its output
├── references/   # docs the skill reads only when the task needs them
├── scripts/      # code the skill runs instead of having the agent write it
└── evals/        # test prompts used while developing the skill
```
