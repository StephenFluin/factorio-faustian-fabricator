data:extend({
    {
        type = "int-setting",
        name = "faustian-fabricator-electricity-kw",
        setting_type = "startup",
        default_value = 1000,
        minimum_value = 30,
        maximum_value = 100000,
        order = "a"
    },
    {
        type = "double-setting",
        name = "faustian-fabricator-generation-seconds",
        setting_type = "runtime-global",
        default_value = 10,
        minimum_value = 3,
        maximum_value = 180,
        order = "b"
    },
    {
        type = "int-setting",
        name = "faustian-fabricator-levelup-seconds",
        setting_type = "runtime-global",
        default_value = 600,
        minimum_value = 30,
        maximum_value = 7200,
        order = "c"
    },
    {
        type = "bool-setting",
        name = "faustian-fabricator-show-message-log",
        setting_type = "runtime-per-user",
        default_value = true,
        order = "d"
    }
})