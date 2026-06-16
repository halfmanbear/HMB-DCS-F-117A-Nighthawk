self_ID = "F-117-NightHawk"
declare_plugin(
    self_ID,
    {
        displayName = _("F-117A Nighthawk"),
        developerName = "HalfManBear",
        image = "F-117A.png",
        installed = true,
        dirName = current_mod_path,
        fileMenuName = _("F-117A Nighthawk"),
        shortName = _("F-117A Nighthawk"),
        version = "2.0.0",
        creditsFile  = "credits.txt",
        state = "installed",
        info = _(
            "F-117A, also called Nighthawk, single-seat, twin-engine jet fighter-bomber built by the Lockheed Corporation as a part of the skunk works team(now part of the Lockheed Martin Corporation) for the U.S. Air Force. It was the first stealth aircraft—i.e., an aircraft designed entirely around the concept of evading detection by radar and other sensors."
        ),
        binaries = {"F_117_NightHawk.dll"},
        InputProfiles = {
            ["F-117-NightHawk"] = current_mod_path .. "/Input/F-117-NightHawk"
        },
        Skins = {
            {
                name = _("F-117A Nighthawk"),
                dir = "Theme"
            }
        },
        Missions = {
            {
                name = _("F-117A Nighthawk"),
                dir = "Missions"
            }
        },
        LogBook = {
            {
                name = _("F-117A Nighthawk"),
                type = "F-117-NightHawk"
            }
        },
        Options = {
            {
                name = _("F-117A Nighthawk"),
                nameId = "F-117-NightHawk",
                dir = "Options"
            }
        }
    }
)

mount_vfs_texture_path(current_mod_path .. "/Theme/ME")
mount_vfs_model_path(current_mod_path .. "/Shapes")
mount_vfs_model_path(current_mod_path .. "/Cockpit/Shape")
mount_vfs_texture_path(current_mod_path .. "/Textures/F-117-NightHawk-TEXTURES")
mount_vfs_texture_path(current_mod_path .. "/Cockpit/Textures/F-117-NightHawk-CPT-TEXTURES") --
mount_vfs_liveries_path(current_mod_path .. "/Liveries")

----------------------------------------------------------------------------------------

local cfg_path = current_mod_path .. "/FM/config.lua"
dofile(cfg_path)
FM[1] = self_ID
FM[2] = "F_117_NightHawk"
FM.config_path = cfg_path
-- FM.old not needed for make_flyable (was FC3 profile inheritance for MAC_flyable)


-------------------------------------------------------------------------------------

dofile(current_mod_path .. "/Views.lua")
make_view_settings("F-117-NightHawk", ViewSettings, SnapViews)

-------------------------------------------------------------------------------

local support_cockpit = current_mod_path .. "/Cockpit/Scripts/"
make_flyable("F-117-NightHawk", support_cockpit, FM, current_mod_path .. "/comm.lua")

-- IRADS sensor registration not possible from entry.lua: the environment has no pcall,
-- no _G["db"], and declare_sensor() is unavailable. Registration is skipped.
-- The DLIR camera uses a body-mounted camera indicator instead (DLIR_Camera_init.lua).

-------------------------------------------------------------------------------

-- NOTE: entry.lua runs in a restricted DCS Lua state that has no pcall, no _G["db"],
-- and declare_sensor() is unavailable here. Sensor declaration must be handled
-- by referencing an already-declared DCS-core sensor in the aircraft Sensors table.

dofile(current_mod_path .. "/Weapons/gbu-31.lua")
dofile(current_mod_path .. "/Weapons/gbu-31v3b.lua")
dofile(current_mod_path .. "/Weapons/gbu-32.lua")
dofile(current_mod_path .. "/Weapons/agm-65d.lua")
dofile(current_mod_path .. "/Weapons/agm-65l.lua")
dofile(current_mod_path .. "/Weapons/agm-154.lua")
dofile(current_mod_path .. "/F-117-NightHawk.lua")

----------------------------------------------------------------------------------------
plugin_done()
