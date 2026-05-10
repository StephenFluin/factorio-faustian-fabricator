-- Control stage: The logic of the machine
-- Every tick, we update our machine instances

local TICKS_PER_SECOND = 60

-- Safe inventory define
local INV_RESULT = defines.inventory.crafter_output or defines.inventory.furnace_result or 2

local function get_level_up_ticks()
    local seconds = settings.global["faustian-fabricator-levelup-seconds"].value
    return math.max(1, math.floor(seconds * TICKS_PER_SECOND))
end

local function get_base_generation_tick_rate()
    local seconds = settings.global["faustian-fabricator-generation-seconds"].value
    return math.max(1, math.floor(seconds * TICKS_PER_SECOND))
end

local function calculate_generation_tick_rate(machine)
    local upgrades = machine.speed_upgrade_count or 0
    local base_rate = get_base_generation_tick_rate()
    return math.max(1, math.floor(base_rate * (0.8 ^ upgrades)))
end

local function item_exists(item_name)
    if not item_name then return false end

    -- Factorio 2.0+ API
    if prototypes and prototypes.item then
        return prototypes.item[item_name] ~= nil
    end

    -- Factorio 1.1 API (guarded for compatibility when key is absent)
    if game then
        local ok, item_prototypes = pcall(function() return game.item_prototypes end)
        if ok and item_prototypes then
            return item_prototypes[item_name] ~= nil
        end
    end

    return false
end

local function should_show_message_log(player)
    local player_settings = settings.get_player_settings(player)
    return player_settings["faustian-fabricator-show-message-log"].value
end

-- Define 6 buckets of items for progression with Science Packs
local item_tiers = {
    { "iron-ore", "copper-ore", "coal", "stone", "wood", "automation-science-pack" }, -- Bucket 1: Raw / Red Science
    { "iron-plate", "copper-plate", "stone-brick", "steel-plate", "logistic-science-pack" }, -- Bucket 2: Smelted / Green Science
    { "iron-gear-wheel", "copper-cable", "pipe", "electronic-circuit", "military-science-pack" }, -- Bucket 3: Components / Gray Science
    { "advanced-circuit", "engine-unit", "plastic-bar", "sulfur", "concrete", "chemical-science-pack" }, -- Bucket 4: Advanced / Blue Science
    { "processing-unit", "electric-engine-unit", "battery", "flying-robot-frame", "production-science-pack" }, -- Bucket 5: Elite / Purple Science
    { "low-density-structure", "rocket-fuel", "rocket-part", "utility-science-pack", "space-science-pack" } -- Bucket 6: Space / Yellow & White Science
}

-- Helper for logging to the machine's internal log
local function machine_log(machine, message)
    machine.log = machine.log or {}
    table.insert(machine.log, 1, string.format("[%d] %s", game.tick, message))
    if #machine.log > 5 then table.remove(machine.log) end
end

-- Helper to check if pool has an item
local function pool_has_item(pool, item_name)
    for _, name in pairs(pool) do
        if name == item_name then return true end
    end
    return false
end

-- Helper to get unacquired items grouped by bucket
local function get_active_buckets(machine)
    local active_buckets = {}
    for tier_index, tier_items in ipairs(item_tiers) do
        local unacquired = {}
        for _, item_name in pairs(tier_items) do
            if item_exists(item_name) and not pool_has_item(machine.item_pool, item_name) then
                table.insert(unacquired, item_name)
            end
        end
        if #unacquired > 0 then
            table.insert(active_buckets, {index = tier_index, items = unacquired})
        end
    end
    return active_buckets
end

-- DATA REPAIR
local function repair_machine(machine)
    local repaired = false
    if not machine.item_pool or #machine.item_pool == 0 then
        machine.item_pool = {"iron-ore", "copper-ore"}
        repaired = true
    end
    if not machine.log then machine.log = {"Machine data repaired."} repaired = true end

    local cleaned_pool = {}
    for _, item_name in pairs(machine.item_pool) do
        if item_exists(item_name) then
            table.insert(cleaned_pool, item_name)
        else
            repaired = true
        end
    end
    if #cleaned_pool == 0 then
        cleaned_pool = {"iron-ore", "copper-ore"}
        repaired = true
    end
    machine.item_pool = cleaned_pool

    if not machine.level then machine.level = 1 repaired = true end
    if not machine.pending_upgrades then machine.pending_upgrades = 0 repaired = true end
    if not machine.speed_upgrade_count then
        local current_rate = machine.generation_tick_rate or get_base_generation_tick_rate()
        local base_rate = get_base_generation_tick_rate()
        local estimated = 0
        if current_rate < base_rate then
            estimated = math.floor((math.log(current_rate / base_rate) / math.log(0.8)) + 0.5)
        end
        machine.speed_upgrade_count = math.max(0, estimated)
        repaired = true
    end
    machine.generation_tick_rate = calculate_generation_tick_rate(machine)
    repaired = true
    if machine.level_progress_ticks == nil then
        machine.level_progress_ticks = machine.total_operating_ticks % get_level_up_ticks()
        repaired = true
    end
    if not machine.next_generation_tick then machine.next_generation_tick = game.tick + machine.generation_tick_rate repaired = true end
    return machine
end

-- Initialize storage
local function init_storage()
    storage.idle_machines = storage.idle_machines or {}
end

script.on_init(init_storage)
script.on_configuration_changed(function()
    init_storage()
    for _, m in pairs(storage.idle_machines) do repair_machine(m) end
end)

-- Register new machines
local function on_entity_built(event)
    local entity = event.entity or event.created_entity
    if entity and entity.name == "faustian-fabricator" then
        init_storage()
        local machine = {
            entity = entity,
            total_operating_ticks = 0,
            level_progress_ticks = 0,
            level = 1,
            pending_upgrades = 0,
            speed_upgrade_count = 0,
            generation_tick_rate = get_base_generation_tick_rate(),
            next_generation_tick = game.tick + get_base_generation_tick_rate(),
            item_pool = {"iron-ore", "copper-ore"},
            log = {"Machine initialized (Electric)."}
        }
        table.insert(storage.idle_machines, machine)
    end
end

script.on_event(defines.events.on_built_entity, on_entity_built, {{filter = "name", name = "faustian-fabricator"}})
script.on_event(defines.events.on_robot_built_entity, on_entity_built, {{filter = "name", name = "faustian-fabricator"}})
script.on_event(defines.events.script_raised_built, on_entity_built, {{filter = "name", name = "faustian-fabricator"}})

-- Helper to find machine data
local function get_machine(unit_number)
    if not storage.idle_machines then return nil end
    for _, m in pairs(storage.idle_machines) do
        if m.entity.valid and m.entity.unit_number == unit_number then
            return repair_machine(m)
        end
    end
    return nil
end

-- Update the GUI for a player
local function update_gui(player, machine)
    local relative = player.gui.relative
    local frame = relative.idle_upgrade_frame
    if not frame then return end
    
    local gen_remaining = math.max(0, machine.next_generation_tick - game.tick)
    local gen_progress = 1 - (gen_remaining / machine.generation_tick_rate)
    frame.status_flow.gen_flow.gen_bar.value = math.min(1, math.max(0, gen_progress))
    
    local items_per_second = 60 / machine.generation_tick_rate
    if items_per_second > 1 then
        frame.status_flow.gen_flow.gen_timer.caption = string.format("%.1f items/s", items_per_second)
    else
        frame.status_flow.gen_flow.gen_timer.caption = string.format("%.1fs", gen_remaining / 60)
    end
    
    local level_up_ticks = get_level_up_ticks()
    local ticks_this_level = machine.level_progress_ticks or 0
    local level_remaining = level_up_ticks - ticks_this_level
    local level_progress = ticks_this_level / level_up_ticks
    frame.status_flow.level_flow.level_bar.value = math.min(1, math.max(0, level_progress))
    frame.status_flow.level_flow.level_timer.caption = string.format("%ds", math.floor(level_remaining / 60))
    
    -- Status text
    local status = machine.entity.status
    local is_powered = status ~= defines.entity_status.no_power and status ~= defines.entity_status.not_plugged_in_electric_network
    frame.status_flow.status_label.caption = "Status: " .. (is_powered and "POWERED" or "NO POWER")
    frame.status_flow.status_label.style.font_color = is_powered and {0, 1, 0} or {1, 0, 0}

    -- Update Item Pool UI
    local pool_flow = frame.pool_section.pool_flow
    if #pool_flow.children ~= #machine.item_pool then
        pool_flow.clear()
        for _, item_name in pairs(machine.item_pool) do
            local sprite_name = item_exists(item_name) and ("item/" .. item_name) or "utility/questionmark"
            pool_flow.add{
                type = "sprite-button",
                sprite = sprite_name,
                tooltip = item_name,
                style = "slot_button"
            }
        end
    end

    -- Update Log
    local show_log = should_show_message_log(player)
    frame.log_separator.visible = show_log
    frame.log_flow.visible = show_log
    if show_log then
        frame.log_flow.log_box.caption = table.concat(machine.log or {}, "\n")
    end

    frame.title_flow.title_label.caption = "Faustian Fabricator Lvl " .. machine.level
    frame.upgrade_section.upgrade_label.caption = "Upgrades Available: " .. machine.pending_upgrades
    frame.upgrade_section.btn_flow.idle_upgrade_faster.enabled = machine.pending_upgrades > 0
    
    -- Disable "MORE" if no more items exist in buckets
    local active_buckets = get_active_buckets(machine)
    frame.upgrade_section.btn_flow.idle_upgrade_more.enabled = machine.pending_upgrades > 0 and #active_buckets > 0
end

-- The main loop
script.on_event(defines.events.on_tick, function(event)
    if not storage.idle_machines then return end
    
    for i = #storage.idle_machines, 1, -1 do
        local machine = repair_machine(storage.idle_machines[i])
        
        if not machine.entity.valid then
            table.remove(storage.idle_machines, i)
            goto continue
        end

        local status = machine.entity.status
        local is_powered = status ~= defines.entity_status.no_power and status ~= defines.entity_status.not_plugged_in_electric_network
        
        if is_powered then
            machine.total_operating_ticks = machine.total_operating_ticks + 1
            machine.level_progress_ticks = (machine.level_progress_ticks or 0) + 1
            
            -- Handle Level Up
            local level_up_ticks = get_level_up_ticks()
            while machine.level_progress_ticks >= level_up_ticks do
                machine.level_progress_ticks = machine.level_progress_ticks - level_up_ticks
                machine.level = machine.level + 1
                machine.pending_upgrades = machine.pending_upgrades + 1
                machine_log(machine, "LEVEL UP! Gained 1 upgrade point.")
            end

            -- Handle Item Generation
            if event.tick >= machine.next_generation_tick then
                local item_to_gen = machine.item_pool[math.random(#machine.item_pool)]
                local result_inv = machine.entity.get_inventory(INV_RESULT)
                
                if result_inv then
                    local inserted = result_inv.insert({name = item_to_gen, amount = 1})
                    if inserted > 0 then
                        machine.next_generation_tick = event.tick + machine.generation_tick_rate
                        machine_log(machine, "Produced: " .. item_to_gen)
                    else
                        machine.next_generation_tick = event.tick + 60
                        machine_log(machine, "Inventory full! Paused 1s.")
                    end
                end
            end
        else
            machine.next_generation_tick = machine.next_generation_tick + 1
        end

        -- Update GUIs
        if event.tick % 10 == 0 then
            for _, player in pairs(game.players) do
                if player.opened == machine.entity then
                    update_gui(player, machine)
                end
            end
        end

        ::continue::
    end
end)

-- Handle GUI Opened
script.on_event(defines.events.on_gui_opened, function(event)
    if not event.entity or event.entity.name ~= "faustian-fabricator" then return end
    
    local player = game.get_player(event.player_index)
    local machine = get_machine(event.entity.unit_number)
    if not machine then return end

    local relative = player.gui.relative
    if relative.idle_upgrade_frame then relative.idle_upgrade_frame.destroy() end

    local anchor = {gui = defines.relative_gui_type.furnace_gui, position = defines.relative_gui_position.right}
    local frame = relative.add{
        type = "frame",
        name = "idle_upgrade_frame",
        direction = "vertical",
        anchor = anchor,
        tags = {machine_unit_number = event.entity.unit_number}
    }

    local title_flow = frame.add{type = "flow", name = "title_flow"}
    title_flow.add{type = "label", name = "title_label", caption = "Faustian Fabricator Lvl " .. machine.level, style = "frame_title"}

    -- Status Section
    local status_flow = frame.add{type = "flow", name = "status_flow", direction = "vertical"}
    status_flow.style.vertical_spacing = 4
    status_flow.style.padding = 8
    status_flow.add{type = "label", name = "status_label", caption = "Status: CHECKING..."}

    -- Gen Timer
    status_flow.add{type = "label", caption = "Next Item Generation:"}
    local gen_flow = status_flow.add{type = "flow", name = "gen_flow", direction = "horizontal"}
    gen_flow.add{type = "progressbar", name = "gen_bar", size = 150, value = 0}
    gen_flow.add{type = "label", name = "gen_timer", caption = "0s"}
    
    -- Level Timer
    status_flow.add{type = "label", caption = "Progress to Next Level:"}
    local level_flow = status_flow.add{type = "flow", name = "level_flow", direction = "horizontal"}
    level_flow.add{type = "progressbar", name = "level_bar", size = 150, value = 0, style = "production_progressbar"}
    level_flow.add{type = "label", name = "level_timer", caption = "0s"}

    -- Item Pool Section
    frame.add{type = "line"}
    local pool_section = frame.add{type = "flow", name = "pool_section", direction = "vertical"}
    pool_section.style.padding = 8
    pool_section.add{type = "label", caption = "Current Item Pool:", style = "heading_2_label"}
    local pool_flow = pool_section.add{type = "table", name = "pool_flow", column_count = 5}
    pool_flow.style.minimal_height = 40

    -- Event Log Section
    frame.add{type = "line", name = "log_separator"}
    local log_flow = frame.add{type = "flow", name = "log_flow", direction = "vertical"}
    log_flow.style.padding = 8
    log_flow.add{type = "label", caption = "Machine Event Log:", style = "heading_2_label"}
    local log_box = log_flow.add{
        type = "label",
        name = "log_box",
        caption = "Wait...",
        single_line = false
    }
    log_box.style.font = "default-small"
    log_box.style.maximal_width = 250
    log_box.style.maximal_height = 80

    -- Upgrade Section
    frame.add{type = "line"}
    local upgrade_section = frame.add{type = "flow", name = "upgrade_section", direction = "vertical"}
    upgrade_section.style.padding = 8
    local upgrade_label = upgrade_section.add{type = "label", name = "upgrade_label", caption = "Upgrades Available: " .. machine.pending_upgrades}
    upgrade_label.style.font = "default-bold"
    
    local btn_flow = upgrade_section.add{type = "flow", name = "btn_flow", direction = "horizontal"}
    btn_flow.add{
        type = "button",
        name = "idle_upgrade_faster",
        caption = "FASTER (Speed)",
        enabled = machine.pending_upgrades > 0
    }
    btn_flow.add{
        type = "button",
        name = "idle_upgrade_more",
        caption = "MORE (Variety)",
        enabled = machine.pending_upgrades > 0
    }
    
    update_gui(player, machine)
end)

-- Handle GUI clicks
script.on_event(defines.events.on_gui_click, function(event)
    if event.element.name ~= "idle_upgrade_faster" and event.element.name ~= "idle_upgrade_more" then return end
    
    local frame = event.element.parent.parent.parent
    local machine = get_machine(frame.tags.machine_unit_number)
    if not machine or machine.pending_upgrades <= 0 then return end

    if event.element.name == "idle_upgrade_faster" then
        machine.speed_upgrade_count = (machine.speed_upgrade_count or 0) + 1
        machine.generation_tick_rate = calculate_generation_tick_rate(machine)
        machine_log(machine, "UPGRADE: Production speed increased.")
    else
        -- VARIETY UPGRADE LOGIC (Bucket System)
        local active_buckets = get_active_buckets(machine)

        if #active_buckets == 0 then
            machine_log(machine, "MAXED: Every possible item discovered!")
        else
            local target_bucket = nil
            -- If only one bucket has items, force it (no 10% chance for a non-existent higher bucket)
            if #active_buckets == 1 then
                target_bucket = active_buckets[1]
                local new_item = target_bucket.items[math.random(#target_bucket.items)]
                table.insert(machine.item_pool, new_item)
                machine_log(machine, string.format("UPGRADE: Found %s (Tier %d)", new_item, target_bucket.index))
            else
                -- 90% lowest bucket, 10% next bucket up
                if math.random(1, 100) <= 90 then
                    target_bucket = active_buckets[1]
                    local new_item = target_bucket.items[math.random(#target_bucket.items)]
                    table.insert(machine.item_pool, new_item)
                    machine_log(machine, string.format("UPGRADE: Found %s (Tier %d)", new_item, target_bucket.index))
                else
                    target_bucket = active_buckets[2]
                    local new_item = target_bucket.items[math.random(#target_bucket.items)]
                    table.insert(machine.item_pool, new_item)
                    machine_log(machine, string.format("CRITICAL SUCCESS! Found %s (Tier %d)", new_item, target_bucket.index))
                end
            end
        end
    end

    machine.pending_upgrades = machine.pending_upgrades - 1
    update_gui(game.get_player(event.player_index), machine)
end)

script.on_event(defines.events.on_gui_closed, function(event)
    if event.entity and event.entity.name == "faustian-fabricator" then
        local player = game.get_player(event.player_index)
        if player.gui.relative.idle_upgrade_frame then
            player.gui.relative.idle_upgrade_frame.destroy()
        end
    end
end)

script.on_event(defines.events.on_runtime_mod_setting_changed, function(event)
    if event.setting ~= "faustian-fabricator-generation-seconds" and event.setting ~= "faustian-fabricator-levelup-seconds" then
        return
    end

    if event.setting == "faustian-fabricator-generation-seconds" and storage.idle_machines then
        for _, machine in pairs(storage.idle_machines) do
            if machine.entity and machine.entity.valid then
                local old_rate = machine.generation_tick_rate or get_base_generation_tick_rate()
                local remaining = math.max(0, (machine.next_generation_tick or game.tick) - game.tick)
                local progress = 0
                if old_rate > 0 then
                    progress = 1 - (remaining / old_rate)
                end
                machine.generation_tick_rate = calculate_generation_tick_rate(machine)
                local new_remaining = math.max(1, math.floor((1 - progress) * machine.generation_tick_rate))
                machine.next_generation_tick = game.tick + new_remaining
            end
        end
    end
end)
