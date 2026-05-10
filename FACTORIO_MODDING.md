# Factorio 2.0 Modding Standards

## Core Principles
- **Data vs Control:** Prototypes are defined in `data.lua` (and its stages). Logic is defined in `control.lua`.
- **Persistence:** All persistent mod state MUST be stored in the `storage` table (formerly `global`).
- **Performance:** Use events efficiently. Avoid expensive logic in `on_tick` unless filtered or throttled.

## 2.0 Specific Changes
- **`global` is now `storage`**: Rename all references in `control.lua`.
- **Fluids 2.0**: No more throughput bottlenecks within segments. Pipes are now just containers in a segment.
- **Collision Layers**: Defined in prototypes. `collision_mask` uses `layers`.
- **Quality**: New system for item tiers. Space platform ghosts only use normal quality.

## Project Structure
- `info.json`: Mod metadata.
- `data.lua`: Prototype definitions.
- `control.lua`: Runtime scripting.
- `locale/en/config.cfg`: Localization strings.
- `graphics/`: Textures and icons.

## Common Snippets

### Standard entity lookup
```lua
local function get_machine(unit_number)
    for _, m in pairs(storage.idle_machines) do
        if m.entity.unit_number == unit_number then
            return m
        end
    end
    return nil
end
```

### Event Filtering
Always use filters for `on_built_entity` and similar to reduce script overhead.
```lua
script.on_event(defines.events.on_built_entity, on_entity_built, {
    {filter = "name", name = "faustian-fabricator"}
})
```
