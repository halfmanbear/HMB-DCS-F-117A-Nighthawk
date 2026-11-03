"""Load missions in DCS, let each run for a while, quit, and keep the relevant dcs.log lines.

    python tools/missions/dcs_run.py Missions/Training/*.miz        # check each mission loads
    python tools/missions/dcs_run.py --seconds 5 tools/missions/results/terrain_probe.miz

For each mission a temporary hook unpauses the simulation, records whether the player
aircraft exists, and asks DCS to exit after the given model time. The lines mentioning the
F-117, the lesson script or a scripting error are printed and saved next to the mission
as <mission>.log in tools/missions/results. Close DCS first. About a minute per mission.
"""
import argparse
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[1]
SAVED_GAMES = MOD.parents[2]
DCS_EXE = Path(r'E:\Eagle Dynamics\DCS World\bin-mt\DCS.exe')
RESULTS = HERE / 'results'
KEEP = ('F117PROBE', 'F117RUN', 'F117TEST', 'Lesson', 'SCRIPTING', 'Scripting', 'F117_WEAPONS', 'ERROR   Mission')
DROP = ('BHD', 'Black Hawk', 'plugin:', 'PLUGINS', 'OBSOLETE', 'Command line')

HOOK = r"""-- Temporary hook written by tools/missions/dcs_run.py. Safe to delete.
local seconds, reported = {SECONDS}, false
local hook = {{}}
function hook.onSimulationFrame()
    if DCS.getPause() then DCS.setPause(false) end
    local now = DCS.getModelTime()
    if not reported and now > 2 then
        local me = Export.LoGetSelfData()
        log.write('F117RUN', log.INFO, 'player ' .. (me and (me.Name .. ' alt ' .. math.floor(me.LatLongAlt.Alt)) or 'missing'))
        reported = true
    end
    if now > seconds then
        log.write('F117RUN', log.INFO, 'done')
        DCS.exitProcess()
    end
end
DCS.setUserCallbacks(hook)
"""


def run(mission, seconds):
    if 'DCS.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq DCS.exe'], capture_output=True, text=True).stdout:
        raise SystemExit('Close DCS first.')
    hook_path = SAVED_GAMES / 'Scripts/Hooks/zz_f117_mission_run.lua'
    hook_path.write_text(HOOK.format(SECONDS=seconds), encoding='utf-8')
    started = time.time()
    try:
        process = subprocess.Popen([str(DCS_EXE), '--mission', str(Path(mission).resolve())])
        try:
            process.wait(240 + seconds)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(60)
    finally:
        hook_path.unlink(missing_ok=True)
    log = SAVED_GAMES / 'Logs/dcs.log'
    if not log.exists() or log.stat().st_mtime < started:
        return ['dcs.log was not written']
    lines = [line for line in log.read_text(encoding='utf-8', errors='replace').splitlines()
             if any(word in line for word in KEEP) and not any(word in line for word in DROP)]
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / (Path(mission).stem + '.log')).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('missions', nargs='+')
    parser.add_argument('--seconds', type=float, default=20, help='model time to run each mission')
    args = parser.parse_args()
    for mission in args.missions:
        print('==', mission, flush=True)
        for line in run(mission, args.seconds):
            print('  ', line[24:] if len(line) > 24 else line, flush=True)


if __name__ == '__main__':
    main()
