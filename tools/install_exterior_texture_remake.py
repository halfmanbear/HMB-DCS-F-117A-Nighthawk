"""Install validated exterior candidates, or restore the exact local backups."""
from pathlib import Path
import hashlib, json, os, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'dist/exterior-texture-remake'
TEX=ROOT/'Textures/F-117-NightHawk-TEXTURES'
BACKUP=WORK/'originals'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def install():
    manifest=json.loads((WORK/'texture-manifest.json').read_text())
    validation=json.loads((WORK/'validation.json').read_text())
    assert not validation['errors'], validation['errors']
    assert len(manifest['textures'])==len(validation['textures'])==27
    checks={r['name']:r for r in validation['textures']}
    for row in manifest['textures']:
        name=row['original']
        assert Path(name).name==name
        assert sha(TEX/name)==row['original_sha256'], 'Original changed: '+name
        assert sha(WORK/'replacements'/name)==checks[name]['sha256'], 'Candidate changed: '+name
    BACKUP.mkdir(exist_ok=True)
    for row in manifest['textures']:
        name=row['original']
        if (BACKUP/name).exists():
            assert sha(BACKUP/name)==row['original_sha256'], 'Backup differs: '+name
        else:shutil.copy2(TEX/name,BACKUP/name)
    changed=[]
    try:
        for row in manifest['textures']:
            name=row['original'];temp=TEX/(name+'.restore-tmp')
            shutil.copy2(WORK/'replacements'/name,temp)
            os.replace(temp,TEX/name)
            changed.append(name)
        for name in changed:assert sha(TEX/name)==checks[name]['sha256']
    except Exception:
        for name in changed:shutil.copy2(BACKUP/name,TEX/name)
        raise
    result={'installed':len(changed),'index_unchanged':sha(ROOT/'.git/index')==manifest['index_sha256_before'],'files':[{ 'name':name,'sha256':sha(TEX/name)} for name in changed]}
    (WORK/'installation-validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({'installed':len(changed),'index_unchanged':result['index_unchanged']}))
def restore():
    manifest=json.loads((WORK/'texture-manifest.json').read_text())
    checks={r['name']:r for r in json.loads((WORK/'validation.json').read_text())['textures']}
    for row in manifest['textures']:
        name=row['original']
        assert sha(BACKUP/name)==row['original_sha256']
        assert sha(TEX/name) in [row['original_sha256'],checks[name]['sha256']], 'Working texture changed since installation: '+name
    for row in manifest['textures']:shutil.copy2(BACKUP/row['original'],TEX/row['original'])
    print('Restored all 27 original textures.')
if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ['install','restore']:raise SystemExit('Usage: python tools/install_exterior_texture_remake.py install|restore')
    globals()[sys.argv[1]]()
