"""Read, change and write DCS mission (.miz) files.

A .miz is a zip. `mission`, `options`, `warehouses` and `l10n/<LANG>/dictionary` are Lua
files that each assign one table. Text such as the briefing is stored as a `DictKey_...`
name in `mission`, and the words themselves are in the dictionary.

    miz = Miz.load('in.miz')
    for group, unit in miz.player_units():
        unit['payload']['fuel'] = 5000
    miz.set_text('descriptionText', 'New briefing')
    miz.save('out.miz')

Every other file in the archive (options, warehouses, images, sounds) is written back
unchanged, so the mission keeps the version DCS saved it with.
"""
import zipfile
from pathlib import Path

from lupa import LuaRuntime

DICTIONARY = 'l10n/DEFAULT/dictionary'
CATEGORIES = ('plane', 'helicopter', 'vehicle', 'ship', 'static')


def is_table(value):
    return type(value).__name__ == '_LuaTable'


def _quote(text):
    return '"' + str(text).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\\n') + '"'


def serialize(value, indent=0):
    """Write a Lua value out in the style DCS uses for mission files."""
    if is_table(value):
        pad = '\t' * (indent + 1)
        items = []
        for key in value:
            label = f'[{key!r}]' if isinstance(key, (int, float)) and not isinstance(key, bool) else f'[{_quote(key)}]'
            items.append(f'{pad}{label} = {serialize(value[key], indent + 1)},')
        if not items:
            return '{}'
        return '\n' + '\t' * indent + '{\n' + '\n'.join(items) + '\n' + '\t' * indent + '}'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return repr(value)
    return _quote(value)


def lua_file(name, table):
    """The text of a mission archive file that assigns `table` to `name`."""
    return f'{name} = {serialize(table)} -- end of {name}\n'


class Miz:
    def __init__(self, files):
        self.files = files
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.mission = self._run('mission', 'mission')
        self.dictionary = self._run(DICTIONARY, 'dictionary') if DICTIONARY in files else self.lua.table()

    @classmethod
    def load(cls, path):
        with zipfile.ZipFile(path) as archive:
            return cls({name: archive.read(name) for name in archive.namelist()})

    def _run(self, name, variable):
        self.lua.execute(self.files[name].decode('utf-8-sig'))
        return self.lua.globals()[variable]

    def table(self, value=None):
        """A Lua table from a Python dict or list (nested), for assigning into the mission."""
        if value is None:
            return self.lua.table()
        if isinstance(value, dict):
            result = self.lua.table()
            for key, item in value.items():
                result[key] = self.table(item) if isinstance(item, (dict, list)) else item
            return result
        if isinstance(value, list):
            return self.table({index + 1: item for index, item in enumerate(value)})
        return value

    def save(self, path):
        self.files['mission'] = lua_file('mission', self.mission).encode('utf-8')
        if len(self.dictionary) or DICTIONARY in self.files:
            self.files[DICTIONARY] = lua_file('dictionary', self.dictionary).encode('utf-8')
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as out:
            for name, data in self.files.items():
                out.writestr(name, data)

    # Text -----------------------------------------------------------------
    def text(self, field):
        """The words for a mission text field such as descriptionText or sortie."""
        key = self.mission[field]
        return self.dictionary[key] if key and str(key).startswith('DictKey_') else key

    def set_text(self, field, words):
        key = self.mission[field]
        if not key or not str(key).startswith('DictKey_'):
            key = f'DictKey_{field}_{self._next_dict_id()}'
            self.mission[field] = key
        self.dictionary[key] = words

    def _next_dict_id(self):
        self.mission['maxDictId'] = (self.mission['maxDictId'] or 0) + 1
        return self.mission['maxDictId']

    # Units ----------------------------------------------------------------
    def groups(self):
        """Yield (side, country, category, index, group) for every group in the mission."""
        for side in ('blue', 'red', 'neutrals'):
            countries = self.mission['coalition'][side]['country'] if self.mission['coalition'][side] else None
            for c in (list(countries) if countries else []):
                country = countries[c]
                for category in CATEGORIES:
                    holder = country[category]
                    if not holder or not holder['group']:
                        continue
                    for g in list(holder['group']):
                        yield side, country, category, g, holder['group'][g]

    def player_units(self):
        """Yield (group, unit) for each unit a human flies."""
        for _, _, _, _, group in self.groups():
            for u in list(group['units']):
                if group['units'][u]['skill'] in ('Player', 'Client'):
                    yield group, group['units'][u]

    def remove_groups(self, keep):
        """Delete every group for which keep(group) is false."""
        holders = {}
        for _, country, category, _, group in list(self.groups()):
            kept = holders.setdefault((id(country[category]), category), (country, []))[1]
            if keep(group):
                kept.append(group)
        for (_, category), (country, kept) in holders.items():
            country[category]['group'] = self.table(kept)
