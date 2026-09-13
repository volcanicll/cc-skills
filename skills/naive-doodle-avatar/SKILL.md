---
name: naive-doodle-avatar
description: Generate "Naive Doodle Avatar" images by transforming real-person portrait photos into cute, childlike, hand-drawn chibi doodle avatars. Preserve recognizable visual traits such as hairstyle, glasses, face shape, expression, accessories, clothing details and masks while simplifying them into rough textured brushwork, bold graphic facial features, restrained colors and charming asymmetry. Use whenever the user asks to turn a photo into a doodle avatar, naive-art portrait, hand-drawn avatar, chibi sketch, cartoon profile picture, or similar illustration.
metadata:
  category: creative
---

# Naive Doodle Avatar

Transform real-person portrait photos into cute, hand-drawn doodle avatars. Not a polished digital illustration — the result should feel like a talented person casually drew the portrait with colored pencils, crayons, wax pastels, or rough digital brushes.

## Core Transformation

Follow this pipeline:

real photo → simplified facial structure → exaggerated cute proportions → rough hand-drawn lines → flat restrained colors → expressive doodle avatar

Do not simply apply a cartoon filter. Reconstruct the person as an intentionally hand-drawn character.

## Identity & Feature Preservation

Carefully extract and preserve the most visually important characteristics from the reference photo:

- overall face shape
- hairstyle and hair length
- hair parting
- hair volume and silhouette
- bangs and loose strands
- eyebrow shape
- eye spacing and general eye shape
- nose and mouth placement
- glasses shape, frame color and proportions
- earrings and jewelry
- mask shape and color
- visible clothing details
- facial expression
- head angle and general pose

Simplify these elements rather than reproducing photographic detail.

The avatar should remain clearly recognizable as the same person through visual characteristics, not through photorealistic facial detail.

## Character Proportion

Use a cute simplified chibi portrait:

- oversized head
- relatively small facial features
- compact neck or no visible neck
- shoulders only when useful
- simplified upper-body framing
- slightly exaggerated hair volume
- clean silhouette
- friendly, approachable expression

Avoid extreme anime proportions. The character should look like a cute personal doodle avatar, not an anime character or commercial mascot.

## Face Rendering

Use simplified graphic facial features.

**Eyes:** Large but natural cartoon eyes with dark pupils, simple highlights, minimal eyelid detail, slightly asymmetrical shapes, expressive but not overly anime-like. For smiling portraits, slightly curve the eyes to reproduce the expression.

**Nose:** A tiny simplified mark or minimal curved stroke. Do not draw a realistic nose.

**Mouth:** A simple curved line or tiny expressive shape. Preserve the emotional character of the original photo.

**Cheeks:** When appropriate, add soft pink blush marks. The blush should look hand-drawn rather than airbrushed.

## Hair Rendering

Hair is one of the strongest identity features.

Convert photographic hair into large simplified masses while preserving:

- exact approximate haircut
- parting direction
- hair length
- side volume
- silhouette
- characteristic outward curls or inward bends

Use many rough overlapping strokes around the outer hair silhouette. Hair should have visible brush texture. Do not make the hair perfectly smooth or vector-like.

Recommended visual language: rough dark strokes + layered scribbles + imperfect edges + simplified large hair masses.

## Glasses

If glasses are present, preserve them prominently. Match:

- frame shape
- approximate size
- bridge position
- frame thickness
- lens proportions
- frame color

Glasses should remain an important visual identifier. For thin gold or metallic frames, use a simple warm brown/gold hand-drawn outline. Do not allow the glasses to become overly geometric or perfectly symmetrical.

## Masks

If the reference contains a mask:

- preserve the mask
- preserve its approximate color
- simplify its construction
- retain visible straps when useful
- integrate the mask naturally into the face

For the orange/yellow mask shown in the reference, use a warm saturated yellow-orange tone. The mask can contain a small simplified emblem or decorative detail when visible in the reference.

Do not remove the mask merely to make the face more attractive.

## Accessories

Preserve distinctive accessories such as:

- earrings
- necklaces
- glasses
- hair accessories

Simplify them into a few recognizable strokes. For pearl earrings, use small circular white shapes with subtle outlines. For necklaces, use thin imperfect hand-drawn lines and simplified pendants.

Accessories should support recognition without overpowering the face.

## Color Palette

Use a restrained warm palette.

Primary colors:

- dark brown / almost black for hair and outlines
- warm peach / light skin tone for face
- muted pink for cheeks
- warm brown/gold for glasses
- soft red for lips
- warm yellow-orange for masks or other strong reference colors

Keep the number of colors limited. Avoid: neon colors, glossy gradients, complex lighting, photorealistic skin shading, excessive color variation, cinematic color grading.

Prefer: flat color fills + subtle uneven texture + occasional rough color overlap.

## Line & Brush Style

This is essential. Use a visibly hand-drawn brush:

- rough pencil texture
- crayon-like edges
- slightly uneven line weight
- imperfect contours
- overlapping strokes
- small gaps and irregularities
- mild asymmetry
- visible brush grain

The outline should NOT look like clean SVG/vector artwork. Avoid: smooth vector outlines, perfect geometric circles, polished 3D rendering, glossy digital painting, airbrushed gradients, hyper-clean anime line art.

The illustration should look intentionally imperfect.

## Composition

For a single reference photo:

- centered head-and-shoulders portrait
- white or very light background
- generous empty space
- no unnecessary scenery
- avatar occupies approximately 65–80% of the canvas height

## Multi-Reference Transformation

When the input is a collage such as `photo 1 → avatar 1`, `photo 2 → avatar 2`, treat each photo independently. Do not merge multiple reference photos into one face.

For each source image:

1. identify the person's hairstyle
2. identify face shape
3. identify glasses/accessories
4. identify expression
5. identify mask or clothing details
6. simplify the facial structure
7. redraw using the same naive doodle style

The resulting avatars should look like they belong to the same illustration series.

Example:

- Photo A with mask → Avatar A must retain the mask.
- Photo B without mask → Avatar B must retain the uncovered face and smile.
- Photo A wearing glasses → Avatar A keeps glasses.
- Photo B wearing glasses → Avatar B keeps the corresponding glasses.

## Background

Use a plain white background. No:

- scenery
- room interior
- aircraft cabin
- car interior
- photographic background
- shadows from the original environment
- decorative background elements

The purpose is to isolate the person as a clean avatar.

## Negative Prompt

Avoid:

- photorealism
- realistic skin texture
- 3D character rendering
- Pixar style
- Disney style
- anime
- manga
- realistic vector illustration
- polished corporate mascot
- overly smooth digital painting
- glossy rendering
- dramatic lighting
- complex background
- excessive details
- perfectly symmetrical face
- perfectly symmetrical hair
- generic character replacement
- changing hairstyle
- removing glasses
- removing important accessories
- removing a mask
- changing the person's recognizable features

## Master Prompt

Transform the provided portrait photo into a cute naive hand-drawn doodle avatar.

Preserve the person's recognizable visual characteristics, especially the hairstyle, hair length, hair parting, face shape, glasses, eyes, expression, mask, earrings, necklace and other distinctive accessories.

Simplify the face into a charming chibi portrait with a slightly oversized head, compact proportions and expressive simplified facial features.

Use rough dark brown hand-drawn brush strokes for the hair and outlines. Build the hair from layered scribbled strokes with irregular edges, visible brush grain and subtle asymmetry.

Use a warm peach skin tone with simple flat coloring. Add small hand-drawn pink blush marks when appropriate.

Draw the eyes as large expressive cartoon eyes with dark pupils and simple highlights, but keep them natural and avoid anime styling.

Simplify the nose and mouth into minimal expressive marks while preserving the original facial expression.

Preserve the exact style and shape of the person's glasses. Keep distinctive accessories such as earrings and necklaces.

If the person is wearing a mask, preserve it exactly as an important character feature, simplifying it into a flat warm-colored hand-drawn shape.

Use a restrained warm color palette with flat fills and subtle crayon/pencil texture.

The final artwork should look like a personal handmade doodle portrait, as if someone drew the person's photo from memory using rough colored pencils, crayons or a textured digital brush.

White background, centered portrait, clean composition, no scenery.

Important: do not make the result look like a generic anime avatar. The goal is to preserve the specific person from the reference while translating their appearance into a naive, cute, imperfect hand-drawn illustration.

## Style Keywords

"naive doodle avatar, hand-drawn portrait, childlike drawing, rough brush texture, colored pencil texture, crayon texture, cute chibi portrait, simplified face, expressive cartoon eyes, warm pastel palette, imperfect linework, asymmetric drawing, white background, personal avatar, handmade illustration"

## Quality Target

The final result should feel:

recognizable > cute > handmade > simple > expressive

rather than:

realistic > polished > detailed > perfectly symmetrical
