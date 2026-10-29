# Automated runtime packages

The `Package mod` GitHub Actions workflow builds a standalone, installable mod ZIP.
It never copies the mod repository's DLLs or reads a local proxy configuration.
No local usernames or absolute workstation paths are configured in the workflow.

| Trigger | Mod source | EFM source branch | Result |
| --- | --- | --- | --- |
| Push to `dev` | Pushed commit | `dev` | ZIP artifact and a new GitHub prerelease |
| Push to `main` | Pushed commit | `main` | ZIP artifact; no published release |
| Push `vX.Y.Z` tag | Tagged commit, required to be on `main` | `main` | Stable GitHub release |
| Actions > Package mod > Run workflow | Selected `dev` or `main` branch | Same branch | ZIP artifact only |

## Version and EFM selection

`entry.lua` is the source of the numeric `major.minor.patch` version. For example,
`version = "2.1.0"` produces:

- Main: `F-117-Nighthawk-2.1.0.zip`, with `2.1.0` in the packaged `entry.lua`.
- Dev: `F-117-Nighthawk-2.1.0-dev-abcdef0.zip`, with the same suffixed version in
  the packaged `entry.lua`. The suffix is the mod commit's short SHA.

Stable tags must match the version exactly (`v2.1.0` in this example). Dev
prerelease tags additionally include the Actions run ID and attempt so repeated
packaging runs cannot overwrite an earlier package. Dev prereleases do not become
the latest stable release. Increment `entry.lua` before creating a new stable tag.

The EFM repository is `halfmanbear/HMB-DCS-F-117A-EFM`. It currently has no Actions
build workflow. Instead of relying on a possibly stale committed DLL, this workflow
checks out the latest commit on the **matching branch** when the job starts and
builds its project as Release x64 with VS 2022. It does not fall back to another
branch, an old DLL, or the proxy if checkout or compilation fails.

The EFM build uses isolated output/intermediate folders and disables debug
information for this packaging build. Neither repository's source project nor
your development configuration is modified. New EFM commits alone do not trigger
this mod's workflow; push the mod or run the workflow manually to package them.
Both repositories must have their intended changes committed and pushed first.

## Package contents

`tools/package_release.py` reads a committed Git snapshot and includes the runtime
folders listed in `RUNTIME_DIRS` and the top-level files listed in `ROOT_FILES`.
Only approved runtime file extensions are included. Update those lists when adding
a new runtime folder or asset format.

The ZIP contains a single `F-117-NightHawk/` directory, ready to extract into
`Saved Games/DCS/Mods/aircraft/`. It includes:

- Runtime scripts, models, textures, missions, sounds, and other approved assets.
- Exactly one DLL: the fresh EFM build at `bin/F_117_NightHawk.dll`.
- Contributor credits and a short installation/attribution README.
- `build-manifest.json`: base/package versions, channel, both commit IDs, EFM
  repository/branch, and the DLL SHA256.

The workflow also publishes a SHA256 checksum file alongside the ZIP. GitHub's
automatic source archives remain source snapshots; use the named mod ZIP to install.

Backups, old test scripts, Blender projects, model inspection files, development
reports, proxy settings, original DLLs, build products, workflow files, and tooling
are excluded. Lua/configuration text and the inserted DLL are checked for personal
absolute paths. The DLL must pass x64/EFM sanity checks and must not contain the
proxy configuration marker. These checks do not replace a DCS runtime test or
promise to remove arbitrary metadata embedded in third-party assets.

## Enable and use

Commit and push the workflow, packager, targets, and tests along with all intended
runtime changes. In particular, commit both `IRADS_Terrain.lua` and
`IRADS_Diagnostics.lua` if `Displays.lua` loads them; the packager rejects missing
modules rather than shipping an incomplete cockpit.

The EFM repository is public, so no cross-repository secret is needed. The build
job has read-only permissions; only the separate publication job receives
`contents: write` through the standard `GITHUB_TOKEN`. Repository/organization
settings must permit GitHub Actions and release creation. No credentials belong in
the packaging script.

For a stable release, merge the intended changes into `main`, set the desired
version in `entry.lua`, then push the matching version tag. For development
prereleases, push to `dev`. Publication takes place only after build, tests, and
package validation succeed. Pushing these files enables automation; no release is
published by merely creating them locally.

Run packager regression checks locally with:

```powershell
python -m unittest discover -s tests/packaging -v
```

For a local packaging check with an already built real DLL (paths supplied by the
caller, not committed in scripts):

```powershell
python tools/package_release.py package --channel dev --efm-root ../efm-checkout --dll ../build/F_117_NightHawk.dll --output dist
```

This exports committed mod files; uncommitted changes are intentionally excluded.
The EFM checkout must be on the corresponding named branch. The automated build
is the recommended path because it guarantees the input DLL comes from the recorded
checkout rather than a caller-supplied local binary.
