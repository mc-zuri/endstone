# Collision Extractor

Endstone plugin to extract block collision shapes at runtime.

## Commands

### `/collision [x y z]`
Get collision shapes for a block at the specified position, or the block below the player if no position given.

### `/collisionall`
Extract collision shapes for all 16 neighbor combinations of a fence/pane block. Place the target block below you and run this command. It will:

1. Test all 16 combinations of N/S/E/W neighbors (stone blocks)
2. Query the collision shape for each combination
3. Save results to `collision_shapes.json` in the plugin data folder

## Usage

1. Build and install endstone with the `get_collision_shapes()` API
2. Install this plugin
3. Place a fence or glass pane
4. Stand on it and run `/collisionall`
5. Results saved to `plugins/collision_extractor/collision_shapes.json`

## Output Format

```json
{
  "minecraft:oak_fence": {
    "0": [[0.375, 0, 0.375, 0.625, 1.5, 0.625]],
    "1": [[0.375, 0, 0, 0.625, 1.5, 0.625]],
    ...
  }
}
```

Neighbor bitmask:
- 1 = North (-Z)
- 2 = South (+Z)
- 4 = East (+X)
- 8 = West (-X)
