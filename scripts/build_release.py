"""Build a reproducible Prism ZIP from a reviewed lock and local JARs.

No implicit file discovery. No host settings. No network or live game changes.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile


def validate(lock):
    if lock.get('format') != 1:
        raise ValueError('Unsupported lock format')
    for field in ('minecraft', 'fabric_loader', 'release'):
        if not re.fullmatch(r'[A-Za-z0-9.+_-]+', lock.get(field, '')):
            raise ValueError('Invalid ' + field)
    entries = lock.get('mods')
    if not isinstance(entries, list) or not entries:
        raise ValueError('Empty mod list')
    seen = set()
    for mod in entries:
        name = mod.get('file', '')
        if PurePosixPath(name).name != name or not re.fullmatch(r'[A-Za-z0-9._+\-]+\.jar', name):
            raise ValueError('Unsafe filename')
        if name in seen:
            raise ValueError('Duplicate filename')
        seen.add(name)
        if not re.fullmatch('[0-9a-f]{64}', mod.get('sha256', '')):
            raise ValueError('Invalid SHA-256')
        if mod.get('redistribution') != 'approved' or mod.get('privacy') != 'approved':
            raise ValueError('Unreviewed mod: ' + name)
        for field in ('permission_evidence', 'source'):
            if not isinstance(mod.get(field), str) or not mod[field].startswith('https://'):
                raise ValueError('Missing evidence: ' + name)
        if not mod.get('notices'):
            raise ValueError('Missing notices: ' + name)
    return entries


def build(lock_path, jars_dir, output):
    lock = json.loads(Path(lock_path).read_text())
    entries = validate(lock)
    files = {}
    root = Path(jars_dir).resolve()
    for mod in entries:
        source = root / mod['file']
        if source.is_symlink() or source.resolve().parent != root:
            raise ValueError('Unsafe source path')
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != mod['sha256']:
            raise ValueError('Hash mismatch: ' + mod['file'])
        # A valid ZIP alone is not a runtime/dependency or permission test.
        files['.minecraft/mods/' + mod['file']] = data
        for notice_name, text in mod['notices'].items():
            if not re.fullmatch(r'[A-Za-z0-9._-]+', notice_name) or not isinstance(text, str) or not text.strip():
                raise ValueError('Invalid notice')
            files['notices/' + mod['file'] + '/' + notice_name] = text.encode()
    files['mmc-pack.json'] = (json.dumps({'formatVersion': 1, 'components': [
        {'uid': 'net.minecraft', 'version': lock['minecraft'], 'important': True},
        {'uid': 'net.fabricmc.fabric-loader', 'version': lock['fabric_loader']}
    ]}, indent=2) + '\n').encode()
    files['instance.cfg'] = b'[General]\nConfigVersion=1.2\nname=Omo Modpack\nInstanceType=OneSix\n'
    files['modpack.lock.json'] = (json.dumps(lock, indent=2, sort_keys=True) + '\n').encode()
    files['README.txt'] = ("Omo Modpack " + lock['release'] + "\n\n"
        "Import this ZIP as a NEW instance in Prism Launcher.\n"
        "Let the launcher select the correct Java version. Sign in with your own account.\n"
        "No account, world, server list, native cache or host settings are included.\n"
        "A successful import does not prove multiplayer or voice compatibility.\n").encode()
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + '.partial')
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(files.items()):
                info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        with zipfile.ZipFile(temporary) as archive:
            assert set(archive.namelist()) == set(files)
            for name, data in files.items():
                assert archive.read(name) == data
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix(target.suffix + '.sha256').write_text(digest + '  ' + target.name + '\n')
    return {'artifact': target.name, 'sha256': digest, 'mods': len(entries), 'status': 'archive-verified; runtime untested'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lock', required=True)
    parser.add_argument('--jars', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.lock, args.jars, args.output), indent=2))
