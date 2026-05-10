-- Data stage: Defining the machine's existence
local idle_machine_energy_usage_kw = settings.startup["faustian-fabricator-electricity-kw"].value

local idle_machine_item = {
    type = "item",
    name = "faustian-fabricator",
    icon = "__faustian-fabricator__/graphics/icons/faustian-fabricator.png",
    icon_size = 64,
    subgroup = "production-machine",
    order = "a[faustian-fabricator]",
    place_result = "faustian-fabricator",
    stack_size = 10
}

local idle_machine_recipe = {
    type = "recipe",
    name = "faustian-fabricator",
    enabled = true,
    ingredients = {
        {type = "item", name = "iron-plate", amount = 2}
    },
    results = {{type = "item", name = "faustian-fabricator", amount = 1}}
}

-- Dummy recipe to keep the furnace "active"
local idle_dummy_recipe = {
    type = "recipe",
    name = "idle-dummy-recipe",
    icon = "__faustian-fabricator__/graphics/icons/faustian-fabricator.png",
    icon_size = 64,
    enabled = true,
    hidden = true,
    energy_required = 1,
    ingredients = {},
    results = {},
    category = "faustian-fabricator-crafting"
}

local idle_machine_entity = {
    type = "furnace",
    name = "faustian-fabricator",
    icon = "__faustian-fabricator__/graphics/icons/faustian-fabricator.png",
    flags = {"placeable-neutral", "placeable-player", "player-creation"},
    minable = {mining_time = 0.2, result = "faustian-fabricator"},
    max_health = 150,
    corpse = "big-remnants",
    dying_explosion = "big-explosion",
    collision_box = {{-1.2, -1.2}, {1.2, 1.2}},
    selection_box = {{-1.5, -1.5}, {1.5, 1.5}},
    module_specification = { module_slots = 3 },
    allowed_effects = {"consumption", "speed", "productivity", "pollution"},
    crafting_categories = {"faustian-fabricator-crafting"},
    crafting_speed = 1,
    source_inventory_size = 0,
    result_inventory_size = 20,
    energy_usage = tostring(idle_machine_energy_usage_kw) .. "kW",
    energy_source = {
        type = "electric",
        usage_priority = "secondary-input",
        emissions_per_minute = { pollution = 1 }
    },
    graphics_set = {
        animation = {
            layers = {
                {
                    filename = "__faustian-fabricator__/graphics/entity/faustian-fabricator.png",
                    priority = "high",
                    width = 214,
                    height = 190,
                    frame_count = 32,
                    line_length = 8,
                    shift = {0.34375, 0.03125},
                    scale = 0.5
                }
            }
        }
    }
}

data:extend({
    {
        type = "recipe-category",
        name = "faustian-fabricator-crafting"
    },
    idle_machine_item,
    idle_machine_recipe,
    idle_dummy_recipe,
    idle_machine_entity
})
