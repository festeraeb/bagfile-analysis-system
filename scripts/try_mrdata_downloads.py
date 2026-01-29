#!/usr/bin/env python3
"""Try downloading common MRData magnetic grids (USmag, NAmag) from MRData server."""
from pathlib import Path
import urllib.request
import urllib.error

def try_download(url, outdir='magnetic_data/mrdata'):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    fname = url.split('/')[-1]
    out = outdir / fname
    print('Trying', url)
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as r:
            with open(out, 'wb') as f:
                f.write(r.read())
        print('Downloaded', out)
        return True
    except urllib.error.HTTPError as e:
        print('HTTP Error', e.code, url)
        return False
    except Exception as e:
        print('Error', e, url)
        return False

if __name__ == '__main__':
    candidates = [
        'https://mrdata.usgs.gov/magnetic/NAmag_origmrg.zip',
        'https://mrdata.usgs.gov/magnetic/NAmag_hp500.zip',
        'https://mrdata.usgs.gov/magnetic/NAmag_CM.zip',
        'https://mrdata.usgs.gov/magnetic/USmag_origmrg.zip',
        'https://mrdata.usgs.gov/magnetic/USmag_hp500.zip',
        'https://mrdata.usgs.gov/magnetic/USmag_CM.zip',
        'https://mrdata.usgs.gov/magnetic/magnetic.xyz.gz'
    ]
    for c in candidates:
        ok = try_download(c)
        if ok:
            break
