# Omo Modpack — Public Core

A version-pinned client pack for Prism Launcher, using public Omo Space and official upstream downloads.

**Status: unpublished release candidate.** `0.1.0-rc.1` imports and launches on Linux but **cannot join Omo World at `play.omo.sh`**. The server rejects two unknown registry entries in the missing `fruitfly` namespace. Do not advertise this candidate as a working server-join pack.

## Contents

- Minecraft 26.2; Fabric Loader 0.19.5; Java 25.
- Public Omo Space v1.2.0 and 23 upstream mods, all pinned by file hashes.
- Simple Voice Chat, graphics/performance mods and the Omo client dependencies.
- No account files, private worlds, logs, host Java paths, native caches or server lists.

The public `.mrpack` contains a download manifest, not third-party JARs. Prism fetches the pinned files from their official hosts. A binary-filled Prism ZIP is not provided because the upstream mods do not all permit re-hosting.

## Import

1. In a current Prism Launcher, select **Add Instance → Import** and choose the `.mrpack`.
2. Create a **new instance**. Do not overwrite an existing pack.
3. The Omo mod comes from its official GitHub release. Prism may warn about files outside Modrinth; inspect the source before trusting it.
4. Use Java 25 and your own Minecraft account.

Tested launcher: Prism 11.1.1 on Linux. macOS is not tested. The source manifest is `modrinth.index.json`; release checksums are generated in `dist/SHA256SUMS`.

## Rebuild

Python 3.10 or newer; no additional Python packages.

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/build_manifest.py --scope release-scope.json --cache ./reviewed-jars --output ./dist
```

The builder fetches and verifies all 24 approved files and generates a deterministic `.mrpack`. Downloaded JARs remain in the local cache, outside the public archive. `build_release.py` is a separate, gated raw-ZIP tool; it is not used for this release format and requires its own reviewed redistribution lock.

## Real verification

- All 24 official downloads fetched and checked.
- Real Prism import completed. Every installed filename, size, SHA-1 and SHA-512 matches the manifest.
- Real Linux client launched off-screen and loaded the mods.
- Authenticated Omo World connection **failed** with a missing `fruitfly` registry.
- Voice native codecs initialized, but peer microphone/audio was **not tested**. The test used dummy audio output.
- macOS import/launch and in-world Omo terminal behaviour are **not verified**.

## Deliberate omissions

Agent Toast, Book Paste, Fruit Fly, GLaDOS, Omo Guide, Omo Voice (AI speech), Omo Teleporter and Twitch Chat are omitted from this approved preparation scope. Adding a compatibility mod requires a scope revision. The live server and original private pack are unchanged.

## Update and rollback

Import a new version into a separate instance and keep the old one until the new version passes testing. Do not copy accounts, private worlds, native caches or local service settings into shared archives.

## Rights

Every upstream mod retains its own licence. An official download reference is not permission to re-host the file. Omo code comes from `omoresearch/omo-space` v1.2.0. A separate licence for the packaging scripts has not been selected. This project is not affiliated with Mojang or Microsoft.
