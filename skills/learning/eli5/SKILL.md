---
name: eli5
description: "Explain any topic, concept, codebase, or system in extremely simple terms - as if talking to someone who knows nothing about the field - and produce a beautiful HTML visualization page with big pictures, few words, and clear flow diagrams. Use when the user says ELI5, explain like I'm five, 通俗易懂地解释, 用大白话讲讲, or asks for a simple/visual explanation of something complex."
---

# ELI5 - Explain Like I'm Five

Explain anything in radically simple terms and render the explanation as a beautiful, visual-first HTML artifact.

> Origin: popularized by Thariq Shihipar (Anthropic, Claude Code team) as a beloved internal skill.
> Core prompt: "Explain like I'm someone who knows nothing about this topic, using an HTML artifact with big pictures and few words."

## Trigger

Activate when the user:

- Says "ELI5", "explain like I'm five", or "explain like I know nothing about this"
- Asks for a simple, plain-language, or visual explanation of a complex topic
- Asks "这是什么/怎么工作的" and wants an intuitive understanding, not a technical deep-dive

Typical invocations:

- `/eli5 how does this module work`
- `/eli5 what is a transformer architecture`
- `/eli5 为什么需要数据库索引`
- `/eli5 explain the auth flow in this codebase`

## Core Principle

The audience knows **nothing** about this field. Assume zero prior knowledge:

- No jargon without an immediate, everyday-life analogy
- No walls of text - if a paragraph is needed, it should be a picture instead
- Every concept maps to something the person already knows from daily life

## Workflow

1. **Understand the subject**: Read the code, docs, or topic thoroughly. Identify the 3-5 essential ideas that carry the whole explanation.
2. **Find analogies**: For each essential idea, find one concrete everyday analogy (post offices, kitchens, traffic, plumbing, libraries...).
3. **Design the story**: Arrange ideas into a simple narrative arc - a problem, then the solution, then how the pieces connect.
4. **Build the HTML artifact** following the design rules below.
5. **Verify simplicity**: Re-read the output. If any sentence requires domain knowledge to understand, simplify or visualize it.

## HTML Artifact Design Rules

The output is a single self-contained HTML file with inline CSS (and inline JS only when needed for simple interactions like step-through animations).

### Visual-first, text-light

- **Big pictures dominate**: large diagrams, illustrations, and icons carry the explanation
- **Few words**: short labels and one-liners only; no paragraphs longer than 2 sentences
- **One idea per screen/section**: generous whitespace, clear visual hierarchy

### Clear flow diagrams

- Use SVG or styled HTML/CSS boxes with arrows to show how things connect
- Show **sequences** (step 1 → 2 → 3) and **structures** (component A contains B) visually
- Color-code related concepts consistently throughout the page
- Prefer simple shapes and emoji/icons over trying to draw realistically

### Style guidance

- Clean, modern, friendly aesthetic: soft background, rounded cards, large readable type
- A big friendly title, then sections that flow top-to-bottom like a story
- Use size and color contrast to signal importance (the key insight should be the biggest thing on screen)
- Optional: simple step-by-step reveal animations to walk through a process
- Dark or light theme both fine - prioritize clarity and contrast

### Structure template

```
┌─────────────────────────────────┐
│  🎯 Big Title (the one-liner)   │
├─────────────────────────────────┤
│  The Problem (why it exists)    │
│  [visual: everyday analogy]     │
├─────────────────────────────────┤
│  The Solution (core idea)       │
│  [big diagram with few labels]  │
├─────────────────────────────────┤
│  How It Works (step by step)    │
│  [flow: 1 → 2 → 3 → 4]          │
├─────────────────────────────────┤
│  The Big Picture (recap)        │
│  [one memorable visual]         │
└─────────────────────────────────┘
```

## Tone

- Warm, patient, and encouraging - never condescending
- Celebrate the "aha" moment: the goal is that the person walks away truly getting it
- It is fine to say "the real details are more complex, but this is the heart of it"

## Example

For `/eli5 how does the internet work`:

- Analogy: the postal system (IP addresses = home addresses, routers = post offices, packets = envelopes)
- Visual: a big colorful map of envelopes traveling between houses through post offices
- Flow: "You write a letter → post office reads the address → passes it along → arrives at the right house"
- Almost no text; the picture does the talking
