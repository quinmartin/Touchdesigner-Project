# Wave the Wheat – Kansas Fan Layers

6 fans × layers, each a transparent PNG (plus the source SVG) on the same 1000×1400 canvas, so every layer lines up when stacked at the same position.

## Files per fan
| File | Use |
|---|---|
| `*_1_body.png` | Torso, neck and shirt. Stays still. |
| `*_2_arms.png` | Both arms raised, in one image. Rotate it around `both_arms_pivot_px`. |
| `*_2_arms_left.png` / `*_2_arms_right.png` | Each arm on its own. Rotate each around its shoulder pivot for a more natural sway. |
| `*_3_head_calm.png` | Calm face, watching the game (eyes off to the side). |
| `*_4_head_cheer.png` | Cheering face. Switch to it when the user is waving. |

## Stack order (bottom → top)
1. arms
2. body
3. head (calm **or** cheer, switched with a Switch TOP)

The arms go behind the body so the shoulder joint stays hidden while they rotate.

## Pivots
`pivots.json` lists the shoulder and neck pivots for each fan in pixels, measured from the **top-left** corner of the image.
TouchDesigner's Transform TOP measures from the centre, with Y pointing up, so convert like this:

```
pivot_x_TD = (px_x / 1000) - 0.5      # fraction of width, 0 = centre
pivot_y_TD = 0.5 - (px_y / 1400)      # fraction of height, 0 = centre
```
Set the Transform TOP's units to fraction, then use those values for Pivot X/Y and drive Rotate from the user's arm angle (for example, ±15–25°).

## Scale
The fans are drawn at different heights: fan 1 is tallest (1.0) and fan 3 is shortest (0.86). Every layer of a fan uses the same scale, so layers still line up. Scale a whole fan up or down in TD to push them into the crowd.

## Logos
The shirts use "KANSAS / JAYHAWKS / FOOTBALL" text and generic jersey styling. They do **not** include the official Jayhawk mascot logo. Fan 2's crop top has a wheat stalk graphic in place of the logo.
