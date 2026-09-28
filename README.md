# skills

Agent skills by [@B0redDev](https://github.com/B0redDev), for Claude Code and other agents that read `SKILL.md`.

| Skill | What it does |
| --- | --- |
| [design-proposal](skills/design-proposal/SKILL.md) | Proposes several UI design variants as one self-contained HTML file with tabs, opens it in the browser, iterates on your feedback, and reports the approved direction as a spec. |

## Install

With the [`skills`](https://github.com/vercel-labs/skills) CLI:

```bash
npx skills add B0redDev/skills
```

Manually, for Claude Code:

```bash
git clone https://github.com/B0redDev/skills.git ~/Developer/skills
ln -s ~/Developer/skills/skills/design-proposal ~/.claude/skills/design-proposal
```

### Optional companions for `design-proposal`

`design-proposal` works on its own. When these skills are installed it also uses them: impeccable for design quality (project context, variant derivation, craft floor, anti-pattern detector) and emil-design-eng for interaction and motion.

```bash
npx skills add pbakaus/impeccable
npx skills add emilkowalski/skill
```

## Layout

```
skills/<name>/
├── SKILL.md      # frontmatter (name, description) + instructions
├── assets/       # files the skill uses in its output
└── evals/        # test prompts used while developing the skill
```
