# Omo Modpack — Public Core + Fruit Fly

A version-pinned Minecraft client pack for Prism Launcher. **Prerelease `0.1.0-rc.2`: real Linux import, launch and Omo World join verified.** macOS and end-to-end microphone audio remain unverified.

## Install

1. Use a current Prism Launcher. The tested version is **11.1.1**.
2. Select **Add Instance → Import** and choose `omo-modpack-public-core-0.1.0-rc.2.mrpack`.
3. Create a **new instance**. Keep your existing pack unchanged.
4. Prism may warn about two mods outside Modrinth: the public Omo GitHub download and the bundled Fruit Fly compatibility port. Inspect their sources and hashes before trusting the pack.
5. Use **Java 25** and sign in with your own Minecraft account.
6. Select Multiplayer → Direct Connection and enter **`play.omo.sh`**.

`play.omo.sh` is a Minecraft game-server address. A browser page is not required to join it. Access remains subject to the server's rules and availability.

## Contents and distribution

- **25 mods**: public Omo Space v1.2.0, 23 official upstream mod downloads, and one reviewed Fruit Fly compatibility JAR.
- Minecraft **26.2**, Fabric Loader **0.19.5**.
- Includes Simple Voice Chat and graphics/performance mods.
- **24 files are downloaded from pinned official URLs**, not re-hosted inside the pack.
- The Fruit Fly Minecraft 26.2 port is included as an override, with its MIT licence and CC BY 4.0 data provenance/attribution. It is not an upstream release binary.
- No accounts, private worlds, logs, host Java paths, native caches, private service settings or server lists are packaged.

The following extras are deliberately omitted: Agent Toast, Book Paste, GLaDOS, Omo Guide, Omo Voice (AI speech), Omo Teleporter and Twitch Chat. The original private pack and live server configuration are not changed by this client pack.

## What was actually tested

On Linux x86_64 with Prism 11.1.1 and Java 25:

- The real `.mrpack` import installed all 25 expected mods and the Fruit Fly notices.
- Installed filenames, sizes and hashes were verified against the candidate.
- The real client launched and loaded the mods.
- An authenticated connection to Omo World succeeded and loaded the overworld.
- Simple Voice Chat received server authentication and connection-check acknowledgements.
- The test client disconnected afterwards. No blocks were changed and no server configuration was edited.

Two initial authentication-service errors preceded a successful retry. Their cause was not determined; authentication settings were not changed.

**Not verified:** macOS or Windows import/launch; microphone-to-peer audio; local AI voice sidecars; in-world Omo terminal behaviour. The Linux test used dummy audio and software rendering. A voice protocol handshake is not proof that another person can hear you.

The earlier 24-mod candidate (`rc.1`) failed the server registry check because Fruit Fly was missing. Do not use that candidate to join Omo World.

## Rebuild the packaging

Python 3.10 or newer; no extra Python packages. Source snapshots and the reviewed input hashes are version-pinned.

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/build_manifest.py --scope release-scope.json --cache ./reviewed-jars --output ./dist/base
python3 scripts/build_compatibility.py --base ./dist/base/omo-modpack-public-core-0.1.0-rc.1.mrpack --proposal compatibility-scope.json --jar ./reviewed-jars/fruitfly-connectome-1.0.0+mc26.2.jar --notices ./notices/fruitfly --output ./dist
```

The reviewed Fruit Fly JAR must match the exact SHA-256 in `compatibility-scope.json`. It can be recovered from `overrides/mods/` in this release's `.mrpack`. These steps reproduce **packaging from pinned binary inputs**; they do not claim a reproducible source build of the Fruit Fly port.

`manifests/rc1.index.json` records the unchanged 24 official download entries; the final release manifest is `modrinth.index.json`. Release hashes are in `SHA256SUMS`. Unit tests cover packaging guards, not the game, microphone or macOS.

`build_release.py` is a separate, gated raw-ZIP utility and is not used for this release. It requires its own redistribution review.

## Updates and rollback

Import each version into a separate instance. Keep the old one until the new version passes your checks. Do not copy accounts, private worlds, native caches or local service settings into shared archives.

## Rights and credits

Every upstream mod retains its own licence. Official download references do not grant permission to re-host those files. Omo code comes from `omoresearch/omo-space` v1.2.0. Fruit Fly code is credited to Blendi Remade / fal.ai; its bundled dataset producers, licence and transformations are listed in `notices/fruitfly/PROVENANCE.md`.

A separate licence for these packaging scripts has not been selected. This project is not affiliated with Mojang or Microsoft.
