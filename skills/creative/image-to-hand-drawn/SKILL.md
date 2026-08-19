---
name: image-to-hand-drawn
description: Transform photographs into cohesive, high-quality hand-drawn illustrations while preserving the complete visual story of the original image, including people, landscapes, water, lakes, rivers, mountains, trees, grass, flowers, animals, buildings, architecture, vehicles, objects, and other meaningful environmental elements. Simplify visual noise without removing meaningful scene elements.
---

# Image to Hand-Drawn Illustration

## Purpose

Transform the entire input image into a **high-quality hand-drawn illustration** while preserving the complete visual story, subject relationships, environmental context, spatial depth, and meaningful visual elements of the original image.

The transformation must preserve **both the foreground subject and the surrounding environment**.

This is not a "subject extraction" task.

It is a **complete scene reconstruction** task.

The output should look like the original photograph was carefully redrawn by a professional illustrator, with a coherent hand-drawn visual language applied consistently across the entire image.

---

# Core Philosophy

The most important rule is:

> **Preserve meaningful visual information; simplify visual noise.**

Do NOT interpret "simplify the image" as "remove the background."

Do NOT interpret "keep the main subject" as "keep only the person."

A person's surroundings can be an essential part of the image.

For example, in a portrait taken beside a lake:

**Person + lake + water reflections + trees + grass + mountains + sky + animals + architecture + environmental lighting**

may collectively form the actual visual subject of the photograph.

All meaningful environmental elements should therefore be preserved.

---

# Scene Understanding

Before rendering, analyze the image as a complete visual scene.

Identify:

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

The scene should be treated as a **hierarchical composition**, not as a single isolated object.

---

# Element Preservation Rules

## Tier 1 — Primary Subjects

These must be preserved with the highest fidelity.

Examples:

* People
* Animals
* Main buildings
* Main vehicles
* Main objects
* Important architectural structures

Preserve:

* Identity
* Shape
* Silhouette
* Pose
* Gesture
* Proportions
* Position
* Orientation
* Important details
* Major colors

---

## Tier 2 — Meaningful Environmental Elements

These are extremely important and MUST NOT be automatically removed.

Examples include:

### Water

* Lakes
* Rivers
* Oceans
* Ponds
* Streams
* Waterfalls
* Reflections
* Ripples
* Shorelines
* Wet surfaces

### Vegetation

* Trees
* Forests
* Grass
* Bushes
* Flowers
* Leaves
* Plants
* Vines
* Fields
* Crops

### Landscape

* Mountains
* Hills
* Valleys
* Cliffs
* Rocks
* Beaches
* Sand
* Snow
* Fields
* Meadows
* Islands

### Sky and Atmosphere

* Sky
* Clouds
* Sunlight
* Sunset
* Sunrise
* Fog
* Mist
* Atmospheric haze
* Rain
* Snow
* Moon
* Stars

### Animals

* Birds
* Dogs
* Cats
* Horses
* Cows
* Wildlife
* Fish
* Other visible animals

### Built Environment

* Houses
* Buildings
* Bridges
* Roads
* Paths
* Fences
* Piers
* Boats
* Architecture
* Statues
* Signs when visually meaningful

These elements contribute to the **identity and narrative of the scene** and should be retained.

---

# Tier 3 — Supporting Details

Supporting elements should generally be preserved but simplified.

Examples:

* Small plants
* Distant trees
* Small rocks
* Minor buildings
* Distant people
* Small boats
* Background vehicles
* Repetitive architectural details
* Small landscape textures

Do not delete them automatically.

Instead, reduce their detail according to their distance and visual importance.

---

# Tier 4 — Visual Noise

Only genuinely unnecessary information should be removed.

Examples:

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

# Landscape Preservation

Landscape scenes require special treatment.

When the input contains a person in a natural environment, preserve the surrounding landscape as part of the composition.

For example:

### Person + Lake

Preserve:

* Person
* Lake
* Water surface
* Shoreline
* Reflections
* Trees
* Grass
* Mountains
* Sky
* Clouds
* Boats
* Animals
* Relevant background structures

Do NOT convert the image into:

> Person + blank background

---

### Person + Forest

Preserve:

* Person
* Trees
* Tree trunks
* Leaves
* Forest depth
* Grass
* Paths
* Rocks
* Sunlight
* Atmospheric perspective

Simplify the forest rather than deleting it.

---

### Person + Mountain

Preserve:

* Person
* Mountains
* Mountain silhouettes
* Valleys
* Rocks
* Grass
* Trees
* Clouds
* Sky
* Atmospheric haze

Distant mountains may be simplified but should remain clearly recognizable.

---

# Environmental Hierarchy

Use **progressive detail reduction** based on spatial depth.

## Foreground

High detail.

Preserve:

* Important textures
* Grass
* Leaves
* Rocks
* Water details
* Objects
* People
* Animals

## Midground

Moderate detail.

Preserve:

* Trees
* Buildings
* Water
* Landscape
* Animals
* Paths
* Structures

Simplify fine textures.

## Background

Low-to-moderate detail.

Preserve:

* Mountain silhouettes
* Forest masses
* Skyline
* Clouds
* Buildings
* Major landscape forms
* Atmospheric color

Reduce micro-details but maintain the scene's identity.

## Distant Background

Use atmospheric simplification.

Preserve:

* Major shapes
* Color masses
* Horizon
* Silhouettes
* Light direction
* Atmospheric depth

Do not erase meaningful environmental structures.

---

# Spatial Depth

Preserve the original sense of depth.

The final illustration should clearly distinguish:

* Foreground
* Midground
* Background

Use:

* Atmospheric perspective
* Reduced detail with distance
* Softer edges
* Slightly lower contrast
* Natural color transitions
* Layered shapes

Do not flatten the entire scene into one plane.

---

# Water Rendering

When water is present, it must remain recognizable as water.

Preserve:

* Surface shape
* Horizon
* Shoreline
* Reflections
* Ripples
* Highlights
* Color variation
* Reflected trees
* Reflected sky
* Light direction

Render water using expressive hand-painted strokes rather than photographic texture.

Do not replace a lake, river, or ocean with a generic flat blue background.

---

# Trees and Vegetation

Trees, grass, plants, and vegetation are meaningful scene elements.

Do not individually reproduce every leaf.

Instead:

* Preserve tree silhouettes
* Preserve major branches
* Preserve foliage masses
* Preserve color variation
* Preserve forest density
* Preserve light and shadow
* Preserve spatial distribution

Use simplified clusters of hand-drawn strokes.

The goal is:

**recognizable vegetation + natural illustration texture**

rather than:

**photographic leaf-by-leaf reproduction.**

---

# Animals

Animals visible in the source image should remain present when they contribute meaningfully to the scene.

Preserve:

* Species identity
* General body shape
* Pose
* Position
* Direction
* Important markings

Small distant animals may be rendered with simplified silhouettes while remaining recognizable.

Do not accidentally remove animals simply because they are not the primary subject.

---

# Architecture and Objects

Meaningful man-made elements should also be preserved.

Examples:

* Houses
* Buildings
* Bridges
* Boats
* Roads
* Piers
* Fences
* Benches
* Vehicles
* Statues

Simplify repetitive details while preserving:

* Overall shape
* Scale
* Position
* Architectural identity
* Major colors

---

# Sky and Atmospheric Elements

The sky is part of the scene and should generally be preserved.

Retain:

* Sky color
* Clouds
* Sun position
* Sunset/sunrise colors
* Atmospheric haze
* Fog
* Mist
* Light rays when meaningful

Do not replace a detailed sky with a generic blank background.

---

# Composition Preservation

Maintain the original:

* Aspect ratio
* Framing
* Camera perspective
* Horizon position
* Subject placement
* Landscape arrangement
* Major shapes
* Relative scale
* Visual hierarchy

The final illustration should still be immediately recognizable as the same scene.

Avoid excessive cropping or reframing.

---

# Hand-Drawn Reconstruction

The image should be **redrawn**, not filtered.

Use:

* Organic linework
* Natural brush strokes
* Painterly shapes
* Subtle paper texture
* Hand-painted color transitions
* Soft edges
* Controlled imperfections
* Natural shading
* Layered color

The same visual language must apply to:

* People
* Animals
* Trees
* Grass
* Water
* Mountains
* Buildings
* Sky
* Objects
* Background elements

Do not make the person hand-drawn while leaving the landscape photographic.

The **entire image must share the same illustration treatment**.

---

# Photographic Texture Removal

Remove photographic characteristics while preserving visual information.

Reduce:

* Camera noise
* Excessive micro-detail
* Lens artifacts
* Digital sharpening
* Compression artifacts
* Photographic skin texture
* Overly realistic surface detail

But do NOT remove the underlying objects or environmental structures.

Example:

Incorrect:

> Remove trees because they are background details.

Correct:

> Keep the trees, but simplify their leaves and render them using hand-drawn foliage shapes.

---

# Detail Simplification

Use the following rule:

> **Simplify detail, not meaning.**

For example:

### Original

A forest containing 10,000 individual leaves.

### Correct output

A clearly recognizable forest composed of:

* Tree trunks
* Foliage masses
* Layered branches
* Light and shadow
* Hand-drawn leaf clusters

### Incorrect output

A blank green background.

---

# Color Strategy

Preserve the original color relationships.

Translate photographic colors into a cohesive illustration palette.

Use:

* Natural colors
* Slightly softened saturation
* Harmonious color relationships
* Painterly gradients
* Controlled highlights
* Natural shadows

Preserve important environmental color identities:

* Blue water
* Green vegetation
* Gray rocks
* Brown tree trunks
* Blue sky
* White clouds
* Warm sunset
* Snow-covered mountains

Do not arbitrarily recolor the environment.

---

# Lighting

Preserve the original lighting direction and atmospheric mood.

Pay attention to:

* Sunlight
* Shadows
* Reflections
* Backlighting
* Rim light
* Cloud shadows
* Water reflections
* Tree shadows
* Atmospheric haze

Translate them into hand-painted lighting rather than photographic rendering.

---

# Scene Narrative

Preserve the **story of the image**.

Ask:

> What is happening in this scene?

Then preserve the visual elements necessary to communicate that story.

For example:

If the original shows:

> A person standing beside a lake while birds fly above the trees and mountains appear in the distance.

The illustration should still communicate:

> A person + lake + trees + birds + mountains + sky.

It should NOT become:

> A person on a simplified empty background.

---

# Negative Constraints

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

# Special Rule for People in Landscapes

When a person is present in a landscape photograph:

**The person is not automatically the only subject.**

Treat the scene as a complete composition.

Preserve the meaningful relationship between:

**Person ↔ Environment**

Examples:

* Person ↔ Lake
* Person ↔ Mountain
* Person ↔ Forest
* Person ↔ Beach
* Person ↔ River
* Person ↔ Garden
* Person ↔ City
* Person ↔ Architecture
* Person ↔ Animals

The environment provides context, scale, mood, and narrative.

Therefore, environmental elements must remain visible and recognizable.

---

# Special Rule for Nature Photography

For nature and outdoor scenes, preserve the complete ecological and geographical structure.

Potentially meaningful elements include:

* Water
* Trees
* Grass
* Flowers
* Mountains
* Hills
* Rocks
* Soil
* Sand
* Clouds
* Sky
* Animals
* Birds
* Snow
* Ice
* Forests
* Fields
* Shorelines
* Reflections

Simplify their rendering but retain their presence.

---

# Special Rule for Complex Scenes

For crowded scenes, do not attempt to preserve every microscopic detail.

Instead:

1. Preserve all major objects.
2. Preserve meaningful secondary elements.
3. Preserve environmental context.
4. Preserve spatial depth.
5. Simplify repetitive details.
6. Remove only genuine visual noise.

The output should remain visually rich but readable.

---

# Transformation Priority

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

# Default Visual Style

Unless the user specifies otherwise, use:

**Refined contemporary hand-drawn illustration**

Characteristics:

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

Do not automatically introduce:

* Anime
* Manga
* Cartoon
* Comic-book style
* Children's book style
* Watercolor
* Oil painting

unless explicitly requested.

---

# Style Overrides

If the user specifies a different hand-drawn medium, adapt the rendering while preserving the complete scene.

### Pencil

Use:

* Graphite strokes
* Cross-hatching
* Paper grain
* Tonal pencil shading

### Watercolor

Use:

* Transparent pigment
* Soft edges
* Natural color bleeding
* Layered washes

### Ink

Use:

* Expressive ink lines
* Controlled hatching
* Brush variation
* Strong silhouette definition

### Colored Pencil

Use:

* Layered pencil strokes
* Visible pigment texture
* Fine directional strokes

### Gouache

Use:

* Opaque paint
* Soft brush texture
* Layered color blocks

### Traditional Chinese Painting

Use:

* Ink-inspired brushwork
* Controlled washes
* Appropriate atmospheric simplification
* Traditional compositional sensitivity

Style changes must not remove meaningful scene elements.

---

# Final Generation Prompt

Use this as the primary generation instruction:

> Transform the entire input image into a cohesive, high-quality hand-drawn illustration while preserving the complete visual story and structure of the original scene. Preserve all meaningful visual elements, including the main subject, people, animals, water, lakes, rivers, trees, grass, flowers, forests, mountains, hills, rocks, buildings, architecture, roads, boats, vehicles, sky, clouds, reflections, shadows, and other environmental elements that contribute to the scene. Do not isolate the main subject or remove the landscape. Treat the entire image as one complete illustrated scene. Preserve the original composition, framing, perspective, proportions, spatial relationships, depth, lighting direction, atmosphere, and major color relationships. Redraw every meaningful element using one consistent hand-drawn visual language with organic linework, natural brush strokes, subtle painterly texture, soft color transitions, gentle shading, and refined illustration quality. Simplify photographic micro-details, repetitive textures, distant elements, and visual noise, but do not remove meaningful objects or environmental structures. Use progressive detail reduction with distance while maintaining recognizable foreground, midground, and background forms. Preserve water as water, trees as trees, grass as grass, mountains as mountains, animals as animals, and architecture as architecture. The result should look as if a professional illustrator carefully redrew the entire original photograph by hand, preserving its complete scene and visual narrative rather than applying a generic artistic filter. Clean, coherent, atmospheric, detailed where important, simplified where appropriate, natural, elegant, and professionally illustrated.

---

# Final Quality Check

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
