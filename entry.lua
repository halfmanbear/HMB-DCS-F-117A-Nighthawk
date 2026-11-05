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

local function mod_file(path)
    return current_mod_path .. "/" .. path
end

for _, folder in ipairs({"Theme/ME", "Textures/F-117-NightHawk-TEXTURES",
                         "Cockpit/Textures/F-117-NightHawk-CPT-TEXTURES"}) do
    mount_vfs_texture_path(mod_file(folder))
end
for _, folder in ipairs({"Shapes", "Cockpit/Shape"}) do
    mount_vfs_model_path(mod_file(folder))
end
mount_vfs_liveries_path(mod_file("Liveries"))

-- External flight model: FM/config.lua fills the FM table, then the EFM DLL is
-- named by plugin and binary.
local fm_config = mod_file("FM/config.lua")
dofile(fm_config)
FM.config_path = fm_config
FM[1], FM[2] = self_ID, "F_117_NightHawk"

dofile(mod_file("Views.lua"))
make_view_settings(self_ID, ViewSettings, SnapViews)

make_flyable(self_ID, mod_file("Cockpit/Scripts/"), FM, mod_file("comm.lua"))

-- The AI uses the IRADS sensor DCS already declares; the player's IRADS is created by the EFM.

-------------------------------------------------------------------------------

dofile(current_mod_path .. "/Weapons/agm-65d.lua")
dofile(current_mod_path .. "/Weapons/agm-65l.lua")
dofile(current_mod_path .. "/Weapons/agm-154.lua")
dofile(current_mod_path .. "/F-117-NightHawk.lua")

----------------------------------------------------------------------------------------
plugin_done()
