"""Add one reviewed Fruit Fly override to the unchanged public-core mrpack."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

BASE_SHA256='adc632a6918312bbc2fd5b777d7d1fbf71708dfc10efa33cc469af694dd6cded'
PROPOSAL_SHA256='f3198dfd700937ec2b4fd00ffb015450f17ff720d9ea572aa183348aba31b707'


def build(base, proposal_path, jar_path, notices_dir, destination):
    raw=Path(base).read_bytes()
    proposal_raw=Path(proposal_path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=BASE_SHA256:
        raise ValueError('Base candidate changed')
    if hashlib.sha256(proposal_raw).hexdigest()!=PROPOSAL_SHA256:
        raise ValueError('Compatibility scope changed')
    proposal=json.loads(proposal_raw)
    mod=proposal['addition']
    jar=Path(jar_path).read_bytes()
    if hashlib.sha256(jar).hexdigest()!=mod['sha256']:
        raise ValueError('Compatibility JAR hash mismatch')
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.namelist()!=['modrinth.index.json']:
            raise ValueError('Unexpected base archive files')
        index=json.loads(archive.read('modrinth.index.json'))
    if len(index['files'])!=24:
        raise ValueError('Base must contain 24 official downloads')
    if any(entry['path']=='mods/'+mod['file'] for entry in index['files']):
        raise ValueError('Duplicate compatibility mod')
    index['versionId']='0.1.0-rc.2'
    index['name']='Omo Modpack — Public Core + Fruit Fly'
    index['summary']='25-mod client candidate. Server-join and platform testing are recorded separately.'
    notice_root=Path(notices_dir)
    license_text=(notice_root/'LICENSE').read_bytes()
    provenance=(notice_root/'PROVENANCE.md').read_bytes()
    if hashlib.sha256(license_text).hexdigest()!='8d4a6ecd83baaed6d625e7dfb70b75de9a82e45f291ed4ae7ce6240201ea7d1b':
        raise ValueError('Fruit Fly licence changed')
    if hashlib.sha256(provenance).hexdigest()!='05261067ce595dde99af2ab958721aa33e6abf3cea8f5daa5ad130d82f9f6156':
        raise ValueError('Fruit Fly provenance changed')
    encoded=(json.dumps(index,indent=2)+'\n').encode()
    files={'modrinth.index.json':encoded,'overrides/mods/'+mod['file']:jar,
           'overrides/Omo-notices/fruitfly/LICENSE':license_text,
           'overrides/Omo-notices/fruitfly/PROVENANCE.md':provenance,
           'overrides/Omo-notices/fruitfly/PORT.md':(
               '# Fruit Fly compatibility port\n\n'
               'Original source: https://github.com/blendi-remade/fly-brain-minecraft\n'
               'Code copyright: Blendi Remade / fal.ai; MIT licence included.\n'
               'This JAR is a local Minecraft 26.2 Fabric port, not an upstream release binary.\n'
               'Port changes adapt the Java mod to Minecraft 26.2; no dataset changes are claimed.\n'
               'The embedded connectome matches the dataset SHA-256 in PROVENANCE.md.\n'
               'Data: male-cns:v1.0, CC BY 4.0, with producers and transformations credited in PROVENANCE.md.\n'
               'Data licence: https://creativecommons.org/licenses/by/4.0/\n').encode()}
    out=Path(destination)
    out.mkdir(parents=True,exist_ok=True)
    path=out/'omo-modpack-public-core-0.1.0-rc.2.mrpack'
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2020,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            archive.writestr(info,data)
    with zipfile.ZipFile(path) as archive:
        if set(archive.namelist())!=set(files):
            raise ValueError('Archive file set mismatch')
        for name,data in files.items():
            if archive.read(name)!=data:
                raise ValueError('Archive content mismatch')
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    (out/'SHA256SUMS').write_text(digest+'  '+path.name+'\n')
    report={'version':'0.1.0-rc.2','total_mods':25,'official_downloads':24,'embedded_compatibility_mods':1,
            'embedded_mod_sha256':mod['sha256'],'archive_sha256':digest,'archive_bytes':path.stat().st_size,
            'notices_included':True,'base_sha256':BASE_SHA256,'scope_sha256':PROPOSAL_SHA256,
            'runtime_status':'not tested by this builder'}
    (out/'BUILD-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',required=True)
    parser.add_argument('--proposal',required=True)
    parser.add_argument('--jar',required=True)
    parser.add_argument('--notices',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.base,args.proposal,args.jar,args.notices,args.output),indent=2))
