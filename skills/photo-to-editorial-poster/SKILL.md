---
name: photo-to-editorial-poster
description: Turn each uploaded photo into a separate high-end editorial poster with a 3:4 canvas, original photo on top with subtle magazine-grade grading, and a naive retro hand-drawn editorial illustration on the bottom. Also supports horizontal split (photo left, illustration right) and illustration-only mode, plus asymmetric, framed, and card-style structure variants. Use when the user asks to convert photos into posters, split editorial posters, photo-plus-illustration posters, vintage travel/fashion poster designs, or similar image-to-poster transformations.
metadata:
  category: creative
---

# Photo to Editorial Poster

Turn each uploaded photograph into a **separate, high-end design poster**. Do NOT combine multiple photos into a collage; output **one poster per photo**.

---

## Mode Selection

Choose the output mode before composing. If the user does not specify, use `vertical-split` as the default.

| Mode | Name | Output |
|------|------|--------|
| 上下 | `vertical-split` | 3:4 vertical canvas, photo on top, illustration on bottom — each exactly 50% (default) |
| 左右 | `horizontal-split` | 4:3 horizontal canvas, photo on the left, illustration on the right — each exactly 50% |
| 只出效果图 | `illustration-only` | A standalone illustrated artwork only — no photo section, no split; the full canvas is the hand-drawn editorial illustration |

The specification below is written for `vertical-split`. For the other modes, keep every sentence of the specification and apply only the geometry adjustments in `Mode Adjustments`.

---

## Structure Variants

Within any mode, an optional structure variant may be applied. If the user does not specify, use `half-half`. Variants only adjust framing or section proportions; they never change the style, palette, texture, or mood requirements of the specification.

| Variant | Name | Composition |
|---------|------|-------------|
| 对半 | `half-half` | Photo and illustration each occupy exactly 50% of the canvas (default) |
| 不对称 | `asymmetric` | One section takes roughly 3/7 of the canvas, the other 4/7; keep the photo section on the larger side for split modes, and keep the whole layout balanced |
| 复古边框 | `framed` | Add a thin, slightly imperfect hand-drawn vintage border or frame around the poster; keep generous inner negative space |
| 卡片式 | `card` | The poster sits as a centered card on an off-white/pale background with generous margins, like a museum card or art print |

---

## Generation Instruction

Use the **Verbatim Specification** below as your generation prompt, **word-for-word**. Do NOT compress, paraphrase, summarize, or "improve" any part of it — the original wording and its level of detail are what produce the intended poster quality. Apply the mode and variant adjustments only when the user requested a non-default mode or variant.

### Verbatim Specification (default: `vertical-split`)

Please turn each photo I upload into a separate, high-end design poster. Do not combine multiple photos into a collage; output one poster per photo.

Use an overall 3:4 vertical composition, strictly divided into two equal sections, with the top and bottom each occupying exactly 50% of the canvas height.

For the top half, preserve the original photograph, maintaining the subject's structure, realistic texture, natural lighting, and original color atmosphere. Apply only subtle, refined photographic color grading to give it the quality of editorial magazine photography and fine-art exhibition imagery. To adapt the image to the required aspect ratio, naturally extend the sky, ground, or surrounding environment when necessary, but do not stretch, distort, or alter the main subject.

For the bottom half, extract the most recognizable subject, silhouette, pose, and narrative relationships from the photograph, then reinterpret them as a light, naïve, retro hand-drawn editorial illustration. Do not mechanically trace or reproduce every detail. Instead, reinterpret the subject through simplified forms, slightly exaggerated proportions, symbolic features, and humorous visual metaphors, while ensuring that the original subject remains instantly recognizable. Blend the aesthetics of modernist editorial illustration, Bauhaus composition, children's picture books, and fashion sketching. Keep the forms concise and the lines thin, delicate, and slightly imperfect by hand. The overall feeling should be relaxed, intelligent, playful, and restrained.

Derive the color palette from the photograph above, using a limited palette with high lightness and low-to-medium saturation. Leave generous areas of off-white or pale negative space, with small touches of complementary color used as visual accents. Use a mixed-media texture inspired by watercolor, gouache, colored pencil, oil pastel, and dry-brush techniques. Preserve visible paper grain, rough edges, areas of exposed paper, slight misregistration, and imperfect brushwork. Avoid smooth vector graphics, photorealistic lighting, 3D rendering, and plastic-looking surfaces.

Keep the overall composition balanced, airy, and spacious, with a strong sense of breathing room. A small number of hand-drawn lines, geometric symbols, or abstract elements may be added. Typography should be used sparingly, such as retro handwritten titles, numbers, or years, naturally integrated into the illustration.

The overall visual direction should reference vintage fashion picture books, travel illustration, art publications, and sophisticated editorial design, creating a mood that feels gentle, nostalgic, relaxed, stylish, humorous, slightly awkward, and confidently eccentric.

Avoid anything that feels overly cartoonish, cheap, commercial/e-commerce-oriented, or template-driven.

### Mode Adjustments (only when a non-default mode is requested)

- **`horizontal-split`**: Replace the geometry sentence with "Use an overall 4:3 horizontal composition, strictly divided into two equal sections, with the left and right each occupying exactly 50% of the canvas width." Apply the top-half photograph requirements to the left half and the bottom-half illustration requirements to the right half. Keep every other sentence verbatim.
- **`illustration-only`**: Output a single standalone hand-drawn editorial illustration on the full canvas, with no photograph and no split. Apply the illustration sentences of the specification verbatim — the naïve retro hand-drawn reinterpretation paragraph, the full color-palette paragraph, the full texture paragraph, the full composition/typography paragraph, the full visual-direction paragraph, and the full avoidance paragraph. Use a 3:4 vertical canvas by default, or follow the user's requested aspect ratio. Do not include the photograph, the photo grading, or the 50/50 split language.

### Structure Variant Adjustment (only when requested)

- Append: "Apply the requested structure variant: half-half (default 50/50), asymmetric (3/7 vs 4/7), framed (thin imperfect hand-drawn vintage border with generous inner negative space), or card (centered card on an off-white background with generous margins). The variant only adjusts framing or section proportions; keep every style requirement above unchanged."

---

## Multiple Photos

When the user uploads multiple photos:

- Generate **one poster per photo**
- Do not merge photos into a collage
- Apply the same mode, structure variant, and visual language across the series so the posters feel like a coherent set while each remains independent

---

## Quality Check

Before finishing, verify:

- One poster per input photo, never a collage
- Default mode: 3:4 vertical, top photo / bottom illustration, each exactly 50%, and every sentence of the Verbatim Specification was followed
- Non-default mode applied cleanly: horizontal-split (4:3, left photo / right illustration, each 50%) or illustration-only (standalone illustration, no photo)
- Requested structure variant applied cleanly (half-half, asymmetric, framed, or card) without altering any style requirement
- Photo section still reads as the original photograph, only subtly graded, with no distortion of the subject
- Illustration section is clearly hand-drawn, naive and retro, yet the subject remains instantly recognizable
- Palette is limited and high-lightness; texture is mixed media on paper, not smooth vector or 3D
- Typography is sparse; the overall mood is gentle, nostalgic, relaxed, stylish, humorous, and slightly eccentric — never cheap or template-like
