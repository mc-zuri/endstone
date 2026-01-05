"""Collision shape extractor plugin for Endstone."""

from endstone.plugin import Plugin
from endstone.command import Command, CommandSender
from endstone import Player
import json
import os


class CollisionExtractor(Plugin):
    api_version = "0.5"

    commands = {
        "collision": {
            "description": "Get collision shapes for a block at position or player location",
            "usages": [
                "/collision",
                "/collision <pos: block_pos>",
            ],
            "permissions": ["collision_extractor.command.collision"],
        },
        "collisionall": {
            "description": "Extract collision shapes for all neighbor combinations of a fence/pane block",
            "usages": ["/collisionall"],
            "permissions": ["collision_extractor.command.collision"],
        },
    }

    permissions = {
        "collision_extractor.command.collision": {
            "description": "Allow users to use collision commands",
            "default": "op",
        }
    }

    def on_enable(self):
        self.logger.info("CollisionExtractor enabled!")
        self._results = {}

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_message("This command must be run by a player")
            return True

        player = sender

        if command.name == "collision":
            return self._handle_collision(player, args)
        elif command.name == "collisionall":
            return self._handle_collision_all(player, args)

        return True

    def _handle_collision(self, player: Player, args: list[str]) -> bool:
        """Get collision shape at a position."""
        dim = player.dimension

        if len(args) >= 3:
            # Use provided coordinates
            try:
                x, y, z = int(args[0]), int(args[1]), int(args[2])
            except ValueError:
                player.send_message("Invalid coordinates")
                return True
        else:
            # Use block below player
            loc = player.location
            x, y, z = int(loc.x), int(loc.y) - 1, int(loc.z)

        block = dim.get_block_at(x, y, z)
        if not block:
            player.send_message(f"No block at {x}, {y}, {z}")
            return True

        # Get collision shapes using the new API
        shapes = block.get_collision_shapes()

        player.send_message(f"§6Block:§r {block.type}")
        player.send_message(f"§6Position:§r {x}, {y}, {z}")
        player.send_message(f"§6Shapes ({len(shapes)}):§r")

        for i, shape in enumerate(shapes):
            # Round for display
            rounded = [round(v, 4) for v in shape]
            player.send_message(f"  §7[{i}]§r {rounded}")

        if not shapes:
            player.send_message("  §7(empty - no collision)§r")

        return True

    def _handle_collision_all(self, player: Player, args: list[str]) -> bool:
        """Extract all 16 neighbor combinations for fence/pane at player position."""
        dim = player.dimension
        loc = player.location

        # Center position (block below player)
        cx, cy, cz = int(loc.x), int(loc.y) - 1, int(loc.z)

        center_block = dim.get_block_at(cx, cy, cz)
        if not center_block:
            player.send_message("No block below you")
            return True

        block_type = center_block.type
        player.send_message(f"§6Extracting shapes for:§r {block_type}")
        player.send_message(f"§6Center:§r {cx}, {cy}, {cz}")

        # Neighbor offsets: N(-Z)=1, S(+Z)=2, E(+X)=4, W(-X)=8
        offsets = [
            (0, 0, -1, 1, "North"),   # N
            (0, 0, 1, 2, "South"),    # S
            (1, 0, 0, 4, "East"),     # E
            (-1, 0, 0, 8, "West"),    # W
        ]

        results = {}

        # Test all 16 combinations
        for combo in range(16):
            # Clear neighbors first
            for dx, dy, dz, bit, name in offsets:
                neighbor = dim.get_block_at(cx + dx, cy + dy, cz + dz)
                if neighbor:
                    neighbor.set_type("minecraft:air")

            # Place stone for active bits
            active = []
            for dx, dy, dz, bit, name in offsets:
                if combo & bit:
                    neighbor = dim.get_block_at(cx + dx, cy + dy, cz + dz)
                    if neighbor:
                        neighbor.set_type("minecraft:stone")
                    active.append(name)

            # Re-place center block to trigger shape update
            center_block = dim.get_block_at(cx, cy, cz)
            center_block.set_type(block_type, True)

            # Get shapes
            center_block = dim.get_block_at(cx, cy, cz)
            shapes = center_block.get_collision_shapes()

            results[combo] = shapes

            neighbors_str = "+".join(active) if active else "none"
            player.send_message(f"§7[{combo}] {neighbors_str}:§r {len(shapes)} shape(s)")

        # Save results to file
        output = {
            block_type: {str(k): v for k, v in results.items()}
        }

        output_path = os.path.join(self.data_folder, "collision_shapes.json")
        os.makedirs(self.data_folder, exist_ok=True)

        # Merge with existing if present
        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                existing = json.load(f)
            existing.update(output)
            output = existing

        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        player.send_message(f"§aSaved to:§r {output_path}")

        # Clean up - clear neighbors
        for dx, dy, dz, bit, name in offsets:
            neighbor = dim.get_block_at(cx + dx, cy + dy, cz + dz)
            if neighbor:
                neighbor.set_type("minecraft:air")

        return True
