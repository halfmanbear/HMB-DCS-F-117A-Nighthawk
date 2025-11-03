-- Mods\aircraft\F-117\UnitPayloads\F-117-NightHawk.lua
local unitPayloads = {
  ["name"] = "F-117-NightHawk",
  ["payloads"] = {
    [1] = {
      ["name"] = "DEFAULT – 2× GBU-27 (BLU-109)",
      ["pylons"] = {
        [1] = { ["CLSID"] = "{EF0A9419-01D6-473B-99A3-BEBDB923B14D}", ["num"] = 1 },
        [2] = { ["CLSID"] = "{EF0A9419-01D6-473B-99A3-BEBDB923B14D}", ["num"] = 2 },
      },
      ["tasks"] = {
        [1] = 30,
        [2] = 31,
        [3] = 33,
      },
    },
    [2] = {
      ["name"] = "JDAM – 2× GBU-31(V)3/B",
      ["pylons"] = {
        [1] = { ["CLSID"] = "GBU31_V3B_JDAM", ["num"] = 1 },
        [2] = { ["CLSID"] = "GBU31_V3B_JDAM", ["num"] = 2 },
      },
      ["tasks"] = {
        [1] = 30,
        [2] = 31,
        [3] = 33,
      },
    },
    [3] = {
      ["name"] = "LGB – 2× GBU-12",
      ["pylons"] = {
        [1] = { ["CLSID"] = "{DB769D48-67D7-42ED-A2BE-108D566C8B1E}", ["num"] = 1 },
        [2] = { ["CLSID"] = "{DB769D48-67D7-42ED-A2BE-108D566C8B1E}", ["num"] = 2 },
      },
      ["tasks"] = {
        [1] = 30,
        [2] = 31,
        [3] = 33,
      },
    },
  },
  ["unitType"] = "F-117-NightHawk",
}

return unitPayloads
