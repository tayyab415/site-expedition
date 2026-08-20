# OpenAI image-to-diagram playbook

How we made the architecture diagrams on Redrob (India Runs), ECHO, LaunchRoom, and GrowEasy, so an agent can make the same kind of pictures for this repo. Do not regenerate those old diagrams. Copy the loop, the style lock, and the prompt shape. Change only the subject.

This file is for Site Expedition and for the insurance nonrenewal skin in `OBJECTIVE.md`.

## What we were actually doing

Three tools, three jobs. Mixing them up is how the pictures go wrong.

ChatGPT, or a leftover generated image, made the first style picture. The one that stuck is `Generated Image June 09, 2026 - 5_16AM.png` in Downloads. LaunchRoom AI: white slide, rounded boxes, teal / blue / orange, thin gray arrows, Google Sans Flex. ECHO on 8 Apr 2026 used the same family: light grid, colored headers, labeled arrows. Those files are the look. They are not the content.

Codex `imagegen` did the image-to-diagram step. Attach the style picture. Tell the model, in writing, that it may copy style and aesthetics only. Then feed it a labeled computation diagram. Quote titles. Quote boxes. Name what each color means. Name what must never appear. Codex used the built-in `image_gen` tool, use-case `infographic-diagram`, 16:9, light background. Outputs landed in the project's `assets/architecture-diagrams/`.

Claude Code plus Stitch / getdesign locked UI chrome, not the architecture slides. On GrowEasy the command was:

```bash
npx getdesign@latest add claude
```

That installed `DESIGN.md`. Cream canvas `#faf9f5`, coral `#cc785c`, Copernicus / Tiempos serif, StyreneB / Inter body, dark navy product surfaces. Use that path when you want the board to look like a product. Do not put hex codes or font names into a Stitch generation prompt. Stitch already applies the design system at project level. Imagegen diagrams are the opposite. Spell the palette and the type in the prompt, because gpt-image has no design-system object.

The user sentence that started the Redrob set, almost verbatim:

> Give me three to four system architecture diagrams using imagegen. Light background. Architecture means how things are computed. Simple and understandable. Use the attached image as a reference. Copy the style and aesthetics, not the other data inside it. Font is Google Sans Flex.

That is the whole procedure in one paragraph.

## The loop

Do this in order. Skip a step and the model invents systems.

1. Pick the computation, not the marketing. Read the markdown that is the source of truth. For this repo that is `README.md`, `ONE_PAGER.md`, `PRODUCT.md`, and for the insurance skin `OBJECTIVE.md`. Write down the real stages, file names, and vetoes. If a box is not in those docs, it does not get a box.

2. Choose a style reference. Prefer the LaunchRoom June 9 image, or one of the Redrob outputs in `[PUB] India_runs_data_and_ai_challenge/github_folder/assets/architecture-diagrams/`. One reference. Label it style only. If you are generating on the hub, copy that PNG into `expedition/assets/architecture-diagrams/style-reference.png` first. Do not commit it unless asked.

3. Split into 3 to 4 slides, plus one beginner slide if a judge has to get it in ten seconds. Redrob was full pipeline, Stage A, Stage B, validation, then a six-box "how it chooses" card. Do not cram the whole system onto one canvas unless you explicitly ask for a detailed two-zone diagram.

4. Write one prompt per slide with the schema below. Quote every label. Spell unusual words. Name the layout: left-to-right, stacked gates, or two zones with a dashed boundary.

5. Generate with Codex imagegen, built-in `image_gen` unless someone asked for the CLI. Inspect the pixels. Wrong labels, dropped boxes, tiny text, copied LaunchRoom agent names. One targeted edit per retry. Repeat invariants every time.

6. Save into this repo. Never leave the only copy under `~/.codex/generated_images/`. Suggested path: `expedition/assets/architecture-diagrams/`. Version with a new filename, like `site-expedition-pipeline-v2.png`. Do not overwrite.

7. If the picture is a UI mockup, not a computation diagram, leave imagegen. Use Stitch / getdesign and `DESIGN.md`. Those are screens. These are slides.

## Style lock

Copy this into every architecture prompt until someone changes it on purpose.

- Use case: `infographic-diagram`
- Canvas: 16:9 landscape, presentation-slide, light white background
- Type: Google Sans Flex, dark gray labels, large enough to read on a README
- Boxes: simple rounded rectangles, generous spacing, almost no shadow
- Arrows: thin gray, labeled when the data on the wire matters
- Palette: inputs white with gray outline, compute blue, analysis / gates teal, outputs orange, safety / reject muted red outline
- Title: one line, quoted verbatim
- Footer: one sentence that states the rule the picture is proving
- Forbidden: dark theme, 3D, logos, watermarks, decorative blobs, tiny text, extra systems, invented metrics

The LaunchRoom picture had eleven fan-out agents and Gemini / Lyria boxes. Those labels die at the reference step. If "Campaign Director" or "Lyria 3" shows up on a Mireye slide, the prompt failed the "style only" line.

## Prompt schema

Fill this once per diagram. Keep the user's facts. Do not add objects the docs do not name.

```text
Use case: infographic-diagram
Asset type: methodology architecture diagram for a technical markdown/report
Input images: Use the attached architecture diagram only as a style and aesthetics reference: light white background, large clean title, simple rounded rectangles, teal/blue/orange accent blocks, thin gray arrows, generous spacing, minimal shadows, clean Google Sans Flex typography. Do not copy its data or labels.
Primary request: <one sentence: which computation this slide explains>
Canvas: 16:9 landscape, light background, clean presentation-slide style.
Typography: Google Sans Flex style, large readable labels, dark gray text.
Title text, verbatim: "<exact title>"
Layout: <left-to-right / two zones / central box with stacked gates>
Diagram labels, verbatim and keep short:
1. "<box>"
2. "<box>"
...
Footer text, verbatim: "<the rule this slide is proving>"
Style: Stage / compute boxes in blue, analysis or gate boxes in teal, final output in orange, inputs in white outlined boxes, reject / safety in muted red outline. Thin gray arrows.
Constraints: no extra systems, no invented metrics, no logos, no watermark, no dark background, no tiny text. Avoid clutter and decorative blobs.
```

Redrob also ran a detailed variant. Two horizontal zones, a dashed "frozen artifact boundary", a validation row along the bottom. Use that when one picture must show both the live-credit path and the deterministic verdict path. Still quote every label.

Beginner variant: six large numbered cards, helper text under each, no file names, no formulas. Title has to be readable in ten seconds. That slide is for judges. The detailed slide is for us.

## How to run it

Codex is what we used for Redrob. In the project workspace, attach the style image, mention `$imagegen` or the imagegen skill, and paste one schema per requested picture. Built-in `image_gen` does not need `OPENAI_API_KEY`. Codex drops files under `$CODEX_HOME/generated_images/` first. Move the keepers into `expedition/assets/architecture-diagrams/`.

CLI fallback, only if someone asks for the API path, or Claude on GrowEasy when they said "use my OpenAI API key".

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export IMAGE_GEN="${CODEX_HOME}/skills/.system/imagegen/scripts/image_gen.py"
# also present at ~/.codex2/skills/.system/imagegen/scripts/image_gen.py on the Mac

python "$IMAGE_GEN" generate \
  --prompt-file expedition/assets/architecture-diagrams/prompts/site-expedition-pipeline.txt \
  --quality high \
  --size 1536x1024 \
  --out expedition/assets/architecture-diagrams/site-expedition-pipeline.png
```

`gpt-image-2` is the CLI default. High quality for dense labels. Do not pass `--input-fidelity` on gpt-image-2. To edit an existing diagram, fix one label and keep everything else with `python "$IMAGE_GEN" edit --image <file> --prompt "..."`. Repeat the invariants.

ChatGPT desktop is fine for the first style reference or a one-off. It is a worse factory than Codex once you have four labeled slides and a repo path.

## What to draw in this repo

Do not invent a sixth layer. The product already has five, and the insurance skin is a different courtroom on the same eyes.

### Site Expedition (current board)

Source: `README.md`, `ONE_PAGER.md`, `PRODUCT.md`.

**Slide 1. Pipeline.** Title `Site Expedition: Need to Verdict`. Boxes, left to right: Mission Plan with no credit yet, OSM / user pin labeled `USER SITE` / `POTENTIAL` / `LISTED` only with a real listing, Mireye screen, Earth Engine plus public follow-ups when the record asks for them, code verdict `Reject` / `Conditional` / `Strong Fit`, cited brief. Footer: `A model may narrate. It never changes the verdict. The globe is the view, not the evidence.`

**Slide 2. Eyes vs witnesses.** Title `Cited record, then independent witnesses`. Left: Mireye, FEMA, terrain, grid, parcel. Right: Earth Engine, JRC water history, NASADEM vs 3DEP, Dynamic World. Side: OSM, EPA ECHO, Routes. Orange: Google aerial / 3D labeled `presentation only`. Footer: `Mireye says what the official record is today. Earth Engine says whether the ground has been arguing with that record.`

**Slide 3. Credit and cancel.** Title `Quote before fetch`. Show the San Leon demo: plan confirmed, five pins, San Leon Reject on FEMA present-state, rest of spend cancelled. Flood-rewind is history, not the veto. Footer: `Reject cancels the rest of the spend. The packet is what a human takes to the next authority.`

**Slide 4. Layers.** Title `Five layers, verdict stays in code`. Eyes, Intelligence, Verdict, Packet, Interface, matching `PRODUCT.md`. Intelligence is the unfinished layer. Interface is paused. Footer: `Verdicts are code. Google pixels never enter the cited packet.`

### Insurance nonrenewal skin (`OBJECTIVE.md`)

This is the other courtroom: aerial-imagery due process on homeowners nonrenewal, not a hail claim file and not new-business underwriting.

**Slide 1. Agent loop.** Title `Nonrenewal challenge packet`. Boxes: drop in the carrier notice, read the state aerial rulebook, check image date against the legal clock, attach USDA NAIP timeline with capture dates, cite Mireye site facts, emit packet with cure deadline. Footer: `Not "we dated your shingles from space."`

**Slide 2. Statute boxes, not vibes.** Georgia O.C.G.A. § 33-9-45: disclose, 12-month images, 60-day cure, must renew if cured. Indiana IC 27-7-12-6.5: aerial as sole reason, 24-month images, 60-day cure, must renew. Louisiana R.S. 22:1339: no sole reliance unless images are within 24 months. Michigan bulletin is guidance, not a statute. Footer: `GA and IN require disclose + max age + cure + must-renew.`

**Slide 3. Why roof CSI is dead.** Austin permit probe: like-for-like redeck invisible, embeddings match the neighbor, Texas NAIP in EE ends mid-2022. Footer: `Build the statute-vs-record agent. Do not build roof CSI.`

Keep insurance diagrams off the warehouse globe. Same eyes, different fight, different buyer: public adjuster or producer.

## Stitch, if you also want UI frames

1. Keep or write `DESIGN.md`. GrowEasy's is the Claude cream / coral system. For this board you may want a colder industrial palette. Either way, tokens live in `DESIGN.md`, not in the Stitch generate prompt.
2. `npx getdesign@latest add <name>` applies that file to a frontend. GrowEasy: `add claude`.
3. Stitch generate/edit: layout, content, structure only. No hex, no font names, no roundness in a *new screen* prompt.
4. After a screen exists, screenshot it and you may feed that screenshot to imagegen as a UI-mockup reference. That is a different use case, `ui-mockup`, not `infographic-diagram`.

## Inspect before you keep it

Open the PNG. Fail the slide if any of these is true:

- A LaunchRoom, ECHO, or Redrob label leaked. Campaign Director, Lyria, URSI, Raspberry Pi.
- A box the docs do not name appeared
- The globe is scoring
- A model is deciding Reject / Conditional / Strong Fit
- Image dates are missing on an insurance NAIP slide
- Text is too small to read at README width
- Dark background or 3D chrome showed up

Fix with one edit prompt: `change only X; keep Y unchanged`. Re-quote the title, the labels, and the footer.

## Where the old pictures live (do not redo them)

| Set | Path |
|---|---|
| Style reference | `/Users/tayyabkhan/Downloads/Generated Image June 09, 2026 - 5_16AM.png` |
| Redrob architecture set | `Downloads/[PUB] India_runs_data_and_ai_challenge/github_folder/assets/architecture-diagrams/` |
| ECHO hardware / conversation | `Downloads/Generated Image April 08, 2026 - *.jpg` |
| GrowEasy UI design system | `Downloads/groweasy/DESIGN.md` |
| EduScroll gpt-image-2 mockups | hub `~/Shared/canvas-mockups-gpt-image-2/` |

Codex skill on the Mac: `~/.codex2/skills/.system/imagegen/SKILL.md`. Some installs put it under `~/.codex/skills/.system/imagegen/`. Prompt recipes: `references/prompting.md`, `references/sample-prompts.md`. CLI: `scripts/image_gen.py`.
