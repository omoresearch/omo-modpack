# Omo Modpack — release preparation

A separate, versioned client pack for Omo Space, for import into Prism Launcher.
This candidate is not yet a public release. No binary ZIP is approved for distribution.

## What is being prepared

- A new Prism instance, rather than changes to an existing installation.
- A pinned Minecraft/Fabric mod set with SHA-256 checksums.
- Upstream download references and the required third-party notices.
- No account files, private worlds, logs, local Java paths, native caches or private server settings.

## Build tool

Python 3.10 or newer is required. No third-party Python packages are used.

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/build_release.py --lock modpack.lock.json --jars ./reviewed-jars --output ./dist/omo-modpack.zip
```

The release lock is intentionally not provided yet. Each entry must have an exact
SHA-256, source and permission evidence, licence notices, and completed permission
and privacy reviews. An unreviewed entry blocks the build. Files not named in the
lock are never copied. The tool does not download or run mods.

The generated ZIP is deterministic and verified by reopening every entry. A sibling
`.sha256` file records its SHA-256. These are packaging checks, not a proof of
launcher, dependency, operating-system, game-join or microphone compatibility.

## Release acceptance still required

1. Finish provenance, redistribution, nested-dependency and binary privacy review.
2. Resolve each blocked mod without silently substituting a different mod set.
3. Create the reviewed lock and build the actual release ZIP.
4. Verify a clean Prism import and launch on Linux and macOS.
5. Test an actual server join and voice audio separately.
6. Review the exact final source revision and assets before public publication.

A working game server does not imply that an HTTP website exists at the same address.
An answering game-status endpoint does not prove that an authenticated client can join.

## Updating and rollback

Import a published version into a separate instance. Keep the previous instance until
the new version launches and joins correctly. Do not overwrite saves or account data.

## Licensing

Third-party mods retain their own licences. The pack's repository licence does not
grant rights to those mods. A licence for the packaging code is not selected yet.
