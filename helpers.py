# standard library modules
import os, json, pickle
from time import time,sleep
from itertools import count
from urllib.parse import urlparse

# outside standard library modules
import requests

data_dir = '_data'

def origin(url):
    parsed = urlparse(url)
    parts = [parsed.scheme, parsed.netloc]
    if not all(parts): return None
    return '://'.join(parts)

def url_with_params(url, params):
    req = requests.models.PreparedRequest()
    req.prepare_url(url, params)
    url = req.url.replace('+','%20')
    return url

def safe_get(url, accepted_codes=[], max_tries=None, params=None, must_be_ok=False, **kw):
    url = url_with_params(url, params)
    for n in count(1):
        if max_tries and max_tries<n: return None
        try:
            print(f'downloading {url}')
            response = requests.get(url, **kw)
            print(f"Response code: {response.status_code}")
            if response.status_code in [200]+accepted_codes:
                return response
            elif must_be_ok:
                raise Exception(f"""\
Response gave not okay status code {response.status_code}.
Check if you are banned.
                """)
        except requests.exceptions.ConnectionError as e:
            raise e("Session timeout. Probably an indication of IP banned. Refresh in your private browsing tab to check if you are banned.")
        s = int(n**.5+1)
        print(f'download failed - sleeping for {s} seconds - {url}')
        sleep(s)

def disk_memoize(**kw):
    if kw.get('mode', None) == 'json':
        ext, load, dump, binary = '.json', json.load, json.dump, ''
    elif kw.get('mode', None) == 'pickle':
        ext, load, dump, binary = '.pkl', pickle.load, pickle.dump, 'b'
    else:
        ext, load, dump, binary = '', lambda f: f.read(), (lambda data, f: f.write(data)), ''
    ext = kw.get('ext', ext)
    
    def decorator(func):
        def too_old(fp):
            #if 'maxage' not in kw: return False
            #return time() - os.path.getmtime(fp) > kw['maxage']
            if 'maxage' not in dir(new_func): return False
            return time() - os.path.getmtime(fp) > kw['maxage']
        def new_func(*args, **kwargs):
            dn = kw.get('dn', '')
            dn = kwargs.get('dn') or dn # user can overwrite the dirname if necessary
            dn = os.path.join(dn, kwargs.get('sd', ''))
            fn = f"{kwargs.get('name') or kwargs.get('fn') or kw.get('name') or kw.get('fn')}{ext}"
            fn = kwargs.get('fn') or fn # user can overwrite the filename if necessary
            fp = os.path.join(dn, fn)
            fp = kw.get('fp') or fp
            fp = kwargs.get('fp') or fp # user can overwrite the filepath if necessary
            dn = os.path.dirname(fp)
            if dn != '': os.makedirs(dn, exist_ok=True)
            if os.path.exists(fp) and not too_old(fp):
                if kwargs.get("just_check", False) == True: return True
                with open(fp, f'r{binary}', encoding=kw.get('encoding')) as f:
                    return_value = load(f)
            else:
                if kwargs.get("just_check", False) == True: return False
                return_value = func(*args, **kwargs)
                if (type(return_value) == str) and (return_value == "DELETE_ME"):
                    if os.path.exists(fp): os.remove(fp)
                    return None
                if (kw.get('mode', None) == 'json') and (type(return_value) in [str, bytes, bytearray]):
                    return_value = json.loads(return_value)
                with open(fp, f'w{binary}', encoding=kw.get('encoding')) as f:
                    if 'indent' in kw: dump(return_value, f, indent=kw['indent'])
                    else: dump(return_value, f)
            return return_value
        if 'maxage' in kw: new_func.maxage = kw['maxage']
        return new_func
    return decorator