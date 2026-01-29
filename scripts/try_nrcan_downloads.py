#!/usr/bin/env python3
"""Try common NRCan download URLs for the Canada magnetic grid."""
from pathlib import Path
import urllib.request
import urllib.error

def try_download(url, outdir='magnetic_data/nrcan'):
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
        'https://ftp.maps.canada.ca/pub/nrcan_rncan/Magnetic-Magnetique/Canada_MAG_400m.zip',
        'https://ftp.maps.canada.ca/pub/nrcan_rncan/Magnetic-Magnetique/Canada_MAG.zip',
        'https://ftp.maps.canada.ca/pub/nrcan_rncan/Magnetic-Magnetique/Canada_MAG_200m.zip',
        'https://gdr.agg.nrcan.gc.ca/pub/gdr/GRD/Canada_MAG_400m.zip'
    ]
    for c in candidates:
        ok = try_download(c)
        if ok:
            break
    else:
        print('No NRCan candidates succeeded. You can try NRCan GeoScan or manual download.')
