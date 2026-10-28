# Faustian Fabricator

A Factorio mod for Factorio 2.0 and 2.1. The Faustian Fabricator is a cursed 3x3 machine that levels up over time, trading power for ever-greater output.

## Releasing

Every release ships as two zips, one for Factorio 2.0 and one for 2.1, that share a `Major.Minor` version. The patch number marks the Factorio version the zip targets:

| Release | Factorio 2.0 | Factorio 2.1 |
| ------- | ------------ | ------------ |
| 0.2     | 0.2.0        | 0.2.1        |
| 0.3     | 0.3.0        | 0.3.1        |

Factorio allows only three numbers in a version (no `-2.1` style suffixes), and the mod portal won't take the same version twice, so the patch number does the suffix's job.

1. Bump the minor version in `info.json` (for example `0.2.1` → `0.3.1`). `build_mod.py` replaces the patch number, so only `Major.Minor` matters. Leave `factorio_version` on `2.1` for local testing.
2. Add two entries to the top of `changelog.txt`: `0.3.1` (Factorio 2.1, "Same changes as 0.3.0.") above `0.3.0` (Factorio 2.0, the full list of changes).
3. If the graphics changed, run `python3 generate_graphics.py`.
4. Run `python3 build_mod.py`. It writes `dist/2.0/faustian-fabricator_0.3.0.zip` and `dist/2.1/faustian-fabricator_0.3.1.zip`, setting `version` and `factorio_version` in each zip's `info.json`.
5. Test each zip in its Factorio version.
6. Commit, then upload both zips to the mod portal as separate releases: the 2.0 zip first, then the 2.1 zip. The portal reads the target Factorio version from each zip.

Always release both versions together, even for a fix that only affects one of them. A fix gets a new minor version (`0.3.x` → `0.4.x`), never a patch bump, so the two releases keep matching versions.
