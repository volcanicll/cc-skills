---
name: image-to-hand-drawn
description: Transform photographs into cohesive, high-quality hand-drawn illustrations while preserving the complete visual story of the original image, including people, landscapes, water, lakes, rivers, mountains, trees, grass, flowers, animals, buildings, architecture, vehicles, objects, and other meaningful environmental elements. Simplify visual noise without removing meaningful scene elements. Use when the user asks to convert a photo into a hand-drawn illustration, redraw a photograph in an illustrated style, or apply an illustration treatment that keeps the full scene intact.
metadata:
  category: creative
  triggers:
    - 手绘插图
    - 照片转手绘
    - 手绘风格
    - image to illustration
    - hand drawn photo
---

# Image to Hand-Drawn Illustration

## Purpose

Transform the entire input image into a **high-quality hand-drawn illustration** while preserving the complete visual story, subject relationships, environmental context, spatial depth, and meaningful visual elements of the original image.

The transformation must preserve **both the foreground subject and the surrounding environment**.

This is not a "subject extraction" task. It is a **complete scene reconstruction** task.

The output should look like the original photograph was carefully redrawn by a professional illustrator, with a coherent hand-drawn visual language applied consistently across the entire image.

---

## Core Philosophy

The most important rule is:

> **Preserve meaningful visual information; simplify visual noise.**

Do NOT interpret "simplify the image" as "remove the background."

Do NOT interpret "keep the main subject" as "keep only the person."

A person's surroundings can be an essential part of the image. For example, in a portrait taken beside a lake, **person + lake + water reflections + trees + grass + mountains + sky + animals + architecture + environmental lighting** may collectively form the actual visual subject of the photograph. All meaningful environmental elements should therefore be preserved.

---

## Scene Understanding

Before rendering, analyze the image as a complete visual scene. Identify:

1. Primary subjects
2. Secondary subjects
3. Environmental elements
4. Foreground elements
5. Midground elements
6. Background elements
7. Atmospheric elements
8. Lighting and shadows
9. Spatial relationships
10. Important textures and patterns

Treat the scene as a **hierarchical composition**, not as a single isolated object.

---

## Element Preservation Rules

### Tier 1 — Primary Subjects

Preserve with the highest fidelity:

* People
* Animals
* Main buildings
* Main vehicles
* Main objects
* Important architectural structures

Preserve their identity, shape, silhouette, pose, gesture, proportions, position, orientation, important details, and major colors.

### Tier 2 — Meaningful Environmental Elements

These are extremely important and MUST NOT be automatically removed. Examples include:

**Water** — lakes, rivers, oceans, ponds, streams, waterfalls, reflections, ripples, shorelines, wet surfaces

**Vegetation** — trees, forests, grass, bushes, flowers, leaves, plants, vines, fields, crops

**Landscape** — mountains, hills, valleys, cliffs, rocks, beaches, sand, snow, fields, meadows, islands

**Sky and Atmosphere** — sky, clouds, sunlight, sunset, sunrise, fog, mist, atmospheric haze, rain, snow, moon, stars

**Animals** — birds, dogs, cats, horses, cows, wildlife, fish, other visible animals

**Built Environment** — houses, buildings, bridges, roads, paths, fences, piers, boats, architecture, statues, signs when visually meaningful

These elements contribute to the **identity and narrative of the scene** and should be retained.

### Tier 3 — Supporting Details

Supporting elements should generally be preserved but simplified. Examples:

* Small plants
* Distant trees
* Small rocks
* Minor buildings
* Distant people
* Small boats
* Background vehicles
* Repetitive architectural details
* Small landscape textures

Do not delete them automatically. Reduce their detail according to their distance and visual importance.

### Tier 4 — Visual Noise

Only genuinely unnecessary information should be removed. Examples:

* Random clutter
* Disposable objects
* Unimportant background debris
* Excessive photographic noise
* Compression artifacts
* Sensor noise
* Accidental obstructions
* Repetitive tiny details with no visual meaning
* Distracting text
* Watermarks
* UI elements

The goal is **noise reduction**, not environmental removal.

---

## Landscape & Scene Preservation

Landscape scenes require special treatment. When the input contains a person in a natural environment, preserve the surrounding landscape as part of the composition.

### Person + Lake

Preserve the person, lake, water surface, shoreline, reflections, trees, grass, mountains, sky, clouds, boats, animals, and relevant background structures. Do NOT convert the image into "person + blank background".

### Person + Forest

Preserve the person, trees, tree trunks, leaves, forest depth, grass, paths, rocks, sunlight, and atmospheric perspective. Simplify the forest rather than deleting it.

### Person + Mountain

Preserve the person, mountains, mountain silhouettes, valleys, rocks, grass, trees, clouds, sky, and atmospheric haze. Distant mountains may be simplified but should remain clearly recognizable.

### Person-Environment Relationship

A person in a landscape is **not automatically the only subject**. Treat the scene as a complete composition and preserve the meaningful relationship between person and environment (person ↔ lake, mountain, forest, beach, river, garden, city, architecture, or animals). The environment provides context, scale, mood, and narrative, so it must remain visible and recognizable.

### Nature Photography

For nature and outdoor scenes, preserve the complete ecological and geographical structure: water, trees, grass, flowers, mountains, hills, rocks, soil, sand, clouds, sky, animals, birds, snow, ice, forests, fields, shorelines, and reflections. Simplify their rendering but retain their presence.

### Complex Scenes

For crowded scenes, do not attempt to preserve every microscopic detail. Instead:

1. Preserve all major objects.
2. Preserve meaningful secondary elements.
3. Preserve environmental context.
4. Preserve spatial depth.
5. Simplify repetitive details.
6. Remove only genuine visual noise.

The output should remain visually rich but readable.

---

## Environmental Hierarchy

Use **progressive detail reduction** based on spatial depth.

### Foreground

High detail. Preserve important textures, grass, leaves, rocks, water details, objects, people, and animals.

### Midground

Moderate detail. Preserve trees, buildings, water, landscape, animals, paths, and structures. Simplify fine textures.

### Background

Low-to-moderate detail. Preserve mountain silhouettes, forest masses, skyline, clouds, buildings, major landscape forms, and atmospheric color. Reduce micro-details but maintain the scene's identity.

### Distant Background

Use atmospheric simplification. Preserve major shapes, color masses, horizon, silhouettes, light direction, and atmospheric depth. Do not erase meaningful environmental structures.

---

## Spatial Depth

Preserve the original sense of depth. The final illustration should clearly distinguish foreground, midground, and background. Use atmospheric perspective, reduced detail with distance, softer edges, slightly lower contrast, natural color transitions, and layered shapes. Do not flatten the entire scene into one plane.

---

## Element Rendering

### Water

Water must remain recognizable as water. Preserve its surface shape, horizon, shoreline, reflections, ripples, highlights, color variation, reflected trees, reflected sky, and light direction. Render water with expressive hand-painted strokes rather than photographic texture. Do not replace a lake, river, or ocean with a generic flat blue background.

### Trees and Vegetation

Trees, grass, plants, and vegetation are meaningful scene elements, but do not individually reproduce every leaf. Preserve tree silhouettes, major branches, foliage masses, color variation, forest density, light and shadow, and spatial distribution. Use simplified clusters of hand-drawn strokes. The goal is **recognizable vegetation + natural illustration texture**, not **photographic leaf-by-leaf reproduction**.

### Animals

Animals visible in the source image should remain present when they contribute meaningfully to the scene. Preserve species identity, general body shape, pose, position, direction, and important markings. Small distant animals may be rendered with simplified silhouettes while remaining recognizable. Do not accidentally remove animals simply because they are not the primary subject.

### Architecture and Objects

Preserve meaningful man-made elements: houses, buildings, bridges, boats, roads, piers, fences, benches, vehicles, and statues. Simplify repetitive details while preserving overall shape, scale, position, architectural identity, and major colors.

### Sky and Atmospheric Elements

The sky is part of the scene and should generally be preserved. Retain sky color, clouds, sun position, sunset/sunrise colors, atmospheric haze, fog, mist, and light rays when meaningful. Do not replace a detailed sky with a generic blank background.

---

## Composition Preservation

Maintain the original aspect ratio, framing, camera perspective, horizon position, subject placement, landscape arrangement, major shapes, relative scale, and visual hierarchy. The final illustration should still be immediately recognizable as the same scene. Avoid excessive cropping or reframing.

---

## Hand-Drawn Reconstruction

The image should be **redrawn**, not filtered. Use organic linework, natural brush strokes, painterly shapes, subtle paper texture, hand-painted color transitions, soft edges, controlled imperfections, natural shading, and layered color.

The same visual language must apply to people, animals, trees, grass, water, mountains, buildings, sky, objects, and background elements. Do not make the person hand-drawn while leaving the landscape photographic. The **entire image must share the same illustration treatment**.

---

## Photographic Texture Removal

Remove photographic characteristics while preserving visual information. Reduce camera noise, excessive micro-detail, lens artifacts, digital sharpening, compression artifacts, photographic skin texture, and overly realistic surface detail. Do NOT remove the underlying objects or environmental structures.

Example:

* Incorrect: Remove trees because they are background details.
* Correct: Keep the trees, but simplify their leaves and render them using hand-drawn foliage shapes.

---

## Detail Simplification

Use the following rule:

> **Simplify detail, not meaning.**

For example:

* **Original**: A forest containing 10,000 individual leaves.
* **Correct output**: A clearly recognizable forest composed of tree trunks, foliage masses, layered branches, light and shadow, and hand-drawn leaf clusters.
* **Incorrect output**: A blank green background.

---

## Color Strategy

Preserve the original color relationships and translate photographic colors into a cohesive illustration palette. Use natural colors, slightly softened saturation, harmonious color relationships, painterly gradients, controlled highlights, and natural shadows.

Preserve important environmental color identities: blue water, green vegetation, gray rocks, brown tree trunks, blue sky, white clouds, warm sunset, and snow-covered mountains. Do not arbitrarily recolor the environment.

---

## Lighting

Preserve the original lighting direction and atmospheric mood. Pay attention to sunlight, shadows, reflections, backlighting, rim light, cloud shadows, water reflections, tree shadows, and atmospheric haze. Translate them into hand-painted lighting rather than photographic rendering.

---

## Scene Narrative

Preserve the **story of the image**. Ask: *What is happening in this scene?* Then preserve the visual elements necessary to communicate that story.

For example, if the original shows a person standing beside a lake while birds fly above the trees and mountains appear in the distance, the illustration should still communicate person + lake + trees + birds + mountains + sky. It should NOT become a person on a simplified empty background.

---

## Negative Constraints

Avoid:

```text
subject isolation
background removal
blank background
generic background
missing landscape
missing trees
missing grass
missing water
missing lake
missing river
missing mountains
missing animals
missing architecture
missing environmental elements
removed scenery
flattened composition
simplified scene into a single subject
photorealistic
photographic texture
3D render
CGI
plastic texture
hyperrealism
generic image filter
generic style transfer
changed identity
changed pose
changed proportions
distorted anatomy
extra characters
extra objects
duplicate objects
random decorations
unnecessary elements
watermark
logo
UI elements
background text
oversaturated colors
neon colors
excessive contrast
excessive sharpening
heavy outlines
mechanical vector lines
flat empty background
```

---

## Transformation Priority

When making decisions, follow this priority:

1. **Preserve the complete scene**
2. **Preserve primary subjects**
3. **Preserve meaningful environmental elements**
4. **Preserve spatial relationships**
5. **Preserve composition**
6. **Preserve lighting and atmosphere**
7. **Simplify photographic micro-details**
8. **Remove visual noise**
9. **Apply coherent hand-drawn rendering**
10. **Refine artistic details**

Never remove a meaningful environmental element simply because it is technically part of the background.

---

## Default Visual Style

Unless the user specifies otherwise, use **refined contemporary hand-drawn illustration**:

* Organic linework
* Soft painterly rendering
* Subtle paper texture
* Natural brush strokes
* Gentle color transitions
* Simplified but recognizable environmental forms
* Atmospheric depth
* Natural lighting
* Strong scene fidelity
* Professional editorial illustration quality

Do not automatically introduce anime, manga, cartoon, comic-book style, children's book style, watercolor, or oil painting unless explicitly requested.

---

## Style Overrides

If the user specifies a different hand-drawn medium, adapt the rendering while preserving the complete scene.

### Pencil

Graphite strokes, cross-hatching, paper grain, tonal pencil shading.

### Watercolor

Transparent pigment, soft edges, natural color bleeding, layered washes.

### Ink

Expressive ink lines, controlled hatching, brush variation, strong silhouette definition.

### Colored Pencil

Layered pencil strokes, visible pigment texture, fine directional strokes.

### Gouache

Opaque paint, soft brush texture, layered color blocks.

### Traditional Chinese Painting

Ink-inspired brushwork, controlled washes, appropriate atmospheric simplification, traditional compositional sensitivity.

Style changes must not remove meaningful scene elements.

---

## Final Generation Prompt

Use this as the primary generation instruction:

> Transform the entire input image into a cohesive, high-quality hand-drawn illustration while preserving the complete visual story and structure of the original scene. Preserve all meaningful visual elements, including the main subject, people, animals, water, lakes, rivers, trees, grass, flowers, forests, mountains, hills, rocks, buildings, architecture, roads, boats, vehicles, sky, clouds, reflections, shadows, and other environmental elements that contribute to the scene. Do not isolate the main subject or remove the landscape. Treat the entire image as one complete illustrated scene. Preserve the original composition, framing, perspective, proportions, spatial relationships, depth, lighting direction, atmosphere, and major color relationships. Redraw every meaningful element using one consistent hand-drawn visual language with organic linework, natural brush strokes, subtle painterly texture, soft color transitions, gentle shading, and refined illustration quality. Simplify photographic micro-details, repetitive textures, distant elements, and visual noise, but do not remove meaningful objects or environmental structures. Use progressive detail reduction with distance while maintaining recognizable foreground, midground, and background forms. Preserve water as water, trees as trees, grass as grass, mountains as mountains, animals as animals, and architecture as architecture. The result should look as if a professional illustrator carefully redrew the entire original photograph by hand, preserving its complete scene and visual narrative rather than applying a generic artistic filter. Clean, coherent, atmospheric, detailed where important, simplified where appropriate, natural, elegant, and professionally illustrated.

---

## Final Quality Check

Before considering the transformation complete, verify:

### Subject

* Is the main subject still recognizable?
* Is the pose preserved?
* Are important features preserved?

### Environment

* Are meaningful trees still present?
* Is water still present?
* Are mountains still present?
* Is grass/vegetation still present?
* Are animals still present?
* Are buildings and structures still present?
* Is the sky still represented?

### Composition

* Does the image still depict the same scene?
* Is the horizon preserved?
* Is spatial depth preserved?
* Are foreground, midground, and background distinguishable?

### Style

* Does the entire image look hand-drawn?
* Are people and environments rendered in the same visual language?
* Are photographic textures replaced with illustration textures?

### Simplification

* Was detail simplified rather than meaning removed?
* Were only genuinely unnecessary elements removed?
* Is the scene cleaner without becoming empty?

### Final Test

The viewer should be able to look at the illustration and immediately recognize:

> **"This is the same complete scene as the original photograph, but professionally redrawn as a hand-drawn illustration."**
