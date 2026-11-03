"""The F-117 as a pydcs aircraft type, so pydcs can place it in new missions.

pydcs only knows the aircraft in its own database. Importing this module adds the mod's
F-117 to that database. `STORES` lists every store the pylons offer, keyed by a short
name, and `F117.arm(group, 'GBU-27', 'GBU-10')` puts one store on each station.
"""
from dcs import task
from dcs.planes import PlaneType, plane_map

# Short name -> (CLSID, ME name, weight kg). Same list and order as F-117-NightHawk.lua.
STORES = {
    'GBU-27': ('{EF0A9419-01D6-473B-99A3-BEBDB923B14D}', 'GBU-27 - 2000lb Laser Guided Penetrator Bomb', 1200),
    'GBU-10': ('{51F9AAE5-964F-4D21-83FB-502E3BFE5F8A}', 'GBU-10 - 2000lb Laser Guided Bomb', 959),
    'GBU-12': ('{DB769D48-67D7-42ED-A2BE-108D566C8B1E}', 'GBU-12 - 500lb Laser Guided Bomb', 277),
    'GBU-31V1': ('{GBU-31}', 'GBU-31(V)1/B - JDAM, 2000lb GPS Guided Bomb', 934),
    'GBU-31V3': ('{GBU-31V3B}', 'GBU-31(V)3/B - JDAM, 2000lb GPS Guided Penetrator Bomb', 981),
    'GBU-32': ('{GBU_32_V_2B}', 'GBU-32(V)2/B - JDAM, 1000lb GPS Guided Bomb', 467),
    'AGM-65D': ('{444BA8AE-82A7-4345-842E-76154EFCCA47}', 'AGM-65D - Maverick D (IIR ASM)', 218),
    'AGM-65E': ('{F16A4DE0-116C-4A71-97F0-2CF85B0313EF}', 'AGM-65E - Maverick E (Laser ASM - Lg Whd)', 293),
    'AGM-154A': ('{AGM-154A}', 'AGM-154A - JSOW CEB (CBU-type)', 485),
    'AGM-154B': ('{AGM-154B}', 'AGM-154B - JSOW Anti-Armour', 485),
    'AGM-154C': ('{9BCC2A2B-5708-4860-B1F1-053A18442067}', 'AGM-154C - JSOW Unitary BROACH', 484),
    'CBU-105': ('{CBU_105}', 'CBU-105 - 10 x SFW, CBU with WCMD', 417),
    'MK-82': ('{BCE4E030-38E9-423E-98ED-24BE3DA87C32}', 'Mk-82 - 500lb GP Bomb LD', 228),
    'MK-84': ('{AB8B8299-F1CC-4359-89B5-2172E0CF4A5A}', 'Mk-84 - 2000lb GP Bomb LD', 894),
}

# Stores that home on the IRADS laser. Its code is fixed at 1688, which is also the DCS default.
LASER_STORES = {'GBU-27', 'GBU-10', 'GBU-12', 'AGM-65E'}


def _weapon(name):
    clsid, label, weight = STORES[name]
    return {'clsid': clsid, 'name': label, 'weight': weight}


class F117(PlaneType):
    id = 'F-117-NightHawk'
    flyable = True
    height = 3.78
    width = 13.2
    length = 20.08
    fuel_max = 8255
    max_speed = 1040
    category = 'Air'
    tacan = False
    eplrs = False
    radio_frequency = 251
    pylons = {1, 2}
    tasks = [task.PinpointStrike, task.GroundAttack, task.RunwayAttack]
    task_default = task.PinpointStrike
    property_defaults = {}
    livery_name = 'F-117-NIGHTHAWK'

    @staticmethod
    def arm(group, station1, station2=None):
        """Put a store on station 1 and on station 2 (same store if only one is given)."""
        for pylon, name in ((1, station1), (2, station2 or station1)):
            group.load_pylon((pylon, _weapon(name)), pylon)


plane_map[F117.id] = F117
