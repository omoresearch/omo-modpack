"""Prepare a download-only .mrpack from an approved immutable scope.

Downloaded files remain in a private cache, never inside the public archive.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import zipfile

ALLOWED_HOSTS = {'cdn.modrinth.com', 'github.com'}


def check_entry(entry):
    name = entry['file']
    if not re.fullmatch(r'[A-Za-z0-9._+\-]+\.jar', name):
        raise ValueError('Unsafe filename')
    url = urlsplit(entry['url'])
    if False:  # Deliberate seeded fault; never merge this CI proof branch.
        raise ValueError('Download host not allowed')
    if not re.fullmatch(r'[0-9a-f]{64}', entry['sha256']):
        raise ValueError('Invalid SHA-256')


def fetch(entry, cache):
    check_entry(entry)
    target = cache / entry['file']
    if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
        part = target.with_suffix('.part')
        try:
            with urlopen(Request(entry['url'], headers={'User-Agent': 'Omo-Modpack-Candidate/1.0'}), timeout=60) as response, part.open('wb') as output:
                while data := response.read(1024 * 1024):
                    output.write(data)
            if hashlib.sha256(part.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError('Downloaded SHA-256 mismatch: ' + entry['file'])
            part.replace(target)
        finally:
            part.unlink(missing_ok=True)
    data = target.read_bytes()
    sha512 = hashlib.sha512(data).hexdigest()
    if entry.get('sha512') and entry['sha512'] != sha512:
        raise ValueError('SHA-512 mismatch: ' + entry['file'])
    with zipfile.ZipFile(target) as jar:
        metadata = json.loads(jar.read('fabric.mod.json'), strict=False)
    return {'path': 'mods/' + entry['file'], 'hashes': {'sha1': hashlib.sha1(data).hexdigest(), 'sha512': sha512},
            'env': {'client': 'required', 'server': 'unsupported'}, 'downloads': [entry['url']], 'fileSize': len(data)}, {
                'file': entry['file'], 'id': metadata.get('id'), 'version': metadata.get('version'),
                'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'source': entry['url']}


def build(scope_path, cache, destination):
    scope_bytes = Path(scope_path).read_bytes()
    scope = json.loads(scope_bytes)
    entries = list(scope['third_party_files'])
    core = scope['omo_core']
    from urllib.parse import quote
    entries.append({'file': core['file'], 'sha256': core['sha256'],
        'url': 'https://github.com/' + core['repo'] + '/releases/download/' + core['tag'] + '/' + quote(core['file'], safe='')})
    if len(entries) != 24 or len({e['file'] for e in entries}) != 24:
        raise ValueError('Expected exactly 24 distinct approved files')
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        check_entry(entry)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda entry: fetch(entry, cache), entries))
    index = {'formatVersion': 1, 'game': 'minecraft', 'versionId': '0.1.0-rc.1', 'name': 'Omo Modpack — Public Core',
             'summary': 'Public-core client candidate. Compatibility testing in progress. No AI voice sidecar is included.',
             'dependencies': {'minecraft': scope['minecraft'], 'fabric-loader': scope['fabric_loader']},
             'files': sorted([r[0] for r in results], key=lambda r: r['path'])}
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(index, indent=2) + '\n').encode()
    (destination / 'modrinth.index.json').write_bytes(encoded)
    archive_path = destination / 'omo-modpack-public-core-0.1.0-rc.1.mrpack'
    with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        info = zipfile.ZipInfo('modrinth.index.json', (2020, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, encoded)
    with zipfile.ZipFile(archive_path) as archive:
        if archive.namelist() != ['modrinth.index.json'] or archive.read('modrinth.index.json') != encoded:
            raise ValueError('Archive verification failed')
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    (destination / 'SHA256SUMS').write_text(digest + '  ' + archive_path.name + '\n')
    report = {'scope_sha256': hashlib.sha256(scope_bytes).hexdigest(), 'downloaded_and_verified_mods': len(results),
              'downloaded_bytes': sum(r[0]['fileSize'] for r in results), 'public_archive_bytes': archive_path.stat().st_size,
              'archive_sha256': digest, 'mods': [r[1] for r in results],
              'runtime_status': 'not tested by this builder', 'third_party_jars_embedded': 0}
    (destination / 'DOWNLOAD-VERIFICATION.json').write_text(json.dumps(report, indent=2) + '\n')
    return {k: v for k, v in report.items() if k != 'mods'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', required=True)
    parser.add_argument('--cache', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.scope, args.cache, args.output), indent=2))
