# Photoreal version – prompt pack

Use these prompts with an AI image generator (e.g., Adobe Firefly, Midjourney, ChatGPT/DALL·E, Leonardo). **Generate one full image per fan, then cut the layers yourself** (steps below). Generating the layers separately almost never lines up.

## Base prompt (reuse for every fan)
> Photorealistic studio photo of a college football fan, waist-up, centered, facing the camera with the head turned slightly to the [LEFT/RIGHT] and eyes looking off to the side at a game (not at the camera). Both arms raised straight up above the head, palms open and facing forward, fingers together. Even, soft stadium-style lighting. Plain solid bright green background (#00FF00) for keying. Sharp focus, 4k, natural skin texture. No logos except the plain text described.

Then generate a **second image with the same seed/reference image** where the only change is:
> …same person, same pose, now cheering excitedly with mouth wide open, eyebrows raised.

(In Midjourney use `--cref` / `--seed`. In Firefly and ChatGPT, upload the first image and ask it to "edit only the facial expression.")

## Fan descriptions (swap into [DESCRIPTION])
1. Tall white man, early 20s, short straight brunette hair, royal-blue t-shirt with "KANSAS JAYHAWKS" in white and red block letters. Head turned left.
2. Light-skinned Black/biracial woman, early 20s, long black hair in tight curls, white cropped t-shirt with "KANSAS" in blue text and a gold wheat stalk graphic, high-waisted jeans. Head turned right.
3. Short white man, mid 20s, dark hair in tight curls, full dark beard and mustache, royal-blue football jersey with "KANSAS" and a large white number 22 outlined in red, white and red sleeve stripes. Head turned right.
4. Black man, early 20s, average build, short black twists, royal-blue t-shirt with "KANSAS FOOTBALL" in white letters. Head turned left.
5. White woman, early 20s, long straight blonde hair, black tank top with "KANSAS" in blue and "FOOTBALL" in red. Head turned right.
6. White man, early 20s, short blonde hair, white t-shirt with "KANSAS" in royal blue and "FOOTBALL" in red. Head turned left.

## Cutting the layers (Photoshop / Photopea, which is free)
1. Remove the green background (Select → Color Range, or "Remove Background").
2. Keep the canvas the same size for all layers so they stack in the same place.
3. **Arms layer:** lasso each arm from the shoulder seam up, and cut it to a new layer (Ctrl+Shift+J).
4. **Head layer:** lasso the head, hair and neck down to the collar, and cut it to a new layer. Do the same on the cheering image. Align it to the calm head before you export.
5. **Body layer:** what's left. Paint over the holes left at the shoulders and neck (Content-Aware Fill works well), so no gaps show when the arms rotate.
6. Export each layer as a PNG with transparency. Use the naming from the illustrated set, so you can swap the files into your TouchDesigner network directly.
