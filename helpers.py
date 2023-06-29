# standard library modules
import os, json, pickle
from time import time,sleep
from itertools import count
from urllib.request import urlretrieve
from urllib.parse import urlparse
import shutil

# outside standard library modules
import requests

# project modules
data_dir = '_data'
sonemic_dir = os.path.join(data_dir, 'sonemic')

ceildiv = lambda a,b: -(-a // b)

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

def clean_params(params):
    from urllib.parse import quote
    params = {quote(k):quote(v) for k,v in params.items()}
    return params

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
        except requests.exceptions.ConnectionError:
            pass
        s = int(n**.5+1)
        print(f'download failed - sleeping for {s} seconds - {url}')
        sleep(s)

def download_file(url, fp, method=requests.get, params=None, encoding=None, with_urlretrieve=False, **kw):
    # must requests.post or other to method to override method=requests.get
    if os.path.exists(fp): return
    directory = os.path.dirname(fp)
    os.makedirs(directory, exist_ok=True)

    printed_url = url_with_params(url, params)
    print(f'downloading {printed_url}')
    if with_urlretrieve:
        urlretrieve(url, fp)
    # the following is alternative to urlretrieve(url, fp)
    else:
        with method(url, params=params, stream=True, **kw) as r:
            with open(fp, 'w', encoding=encoding) as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk.decode())
                #shutil.copyfileobj(r.text, f)
    print(f'saving to {fp}')
    return fp

def memoize_if_current(f):
    memo = dict()
    def g(*args):
        if (args not in memo) or (g.current) != True:
            memo[args] = f(*args)
            g.current = True
        return memo[args]
    return g

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

def sqlite_memoize(sqlite_db_fp, table_name="cache", expire=None):
    import sqlite3
    table_name = ''.join( x for x in str(table_name) if x.isalnum() )
    # even if I am the only one who uses this code, I will still sanitize
    # the table name to stop me from stupidly SQL-injecting myself
    def decorator(func):
        def new_func(*args, **kwargs):
            if new_func.first_time == True:
                initialize()
                new_func.first_time = False
            now = int(time())
            if 'key' in kwargs: key = kwargs['key']
            else: key = json.dumps((args, tuple(sorted(kwargs.items()))))

            # connection = sqlite3.connect(sqlite_db_fp)
            curse = new_func.connection.cursor()
            curse.execute(f"""
                SELECT val,timestamp from {table_name}
                WHERE key=?;
                """, (key,))
            row = curse.fetchone()
            if (row is None) or (now - row[1] > expire):
                val = func(*args, **kwargs)
                curse.execute(f"""
                    REPLACE INTO {table_name}(key,val,timestamp)
                    VALUES(?,?,?);
                    """, (key,val,now))
                new_func.connection.commit()
            else:
                val = row[0]
            # connection.close()
            return val
        
        new_func.first_time = True
        def initialize():
            os.makedirs(os.path.dirname(sqlite_db_fp), exist_ok=True)
            new_func.connection = sqlite3.connect(sqlite_db_fp)
            curse = new_func.connection.cursor()

            curse.executescript(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    key TEXT NOT NULL,
                    val TEXT NOT NULL,
                    timestamp INTEGER NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS id_UNIQUE ON {table_name}(key);
                """)
            
            if expire:
                cutoff = int(time()) - expire
                curse.execute(f"""
                    DELETE FROM {table_name} where timestamp < ?;
                """, (cutoff,))

            new_func.connection.commit()
            # connection.close()
        
        return new_func
    return decorator

def shelve_it(fp, expire=None):
    import shelve
    import yaml
    
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    def decorator(func):
        db = shelve.open(fp)
        
        def new_func(*args, **kwargs):
            dn = os.path.dirname(fp)
            if dn != '': os.makedirs(dn, exist_ok=True)

            now = time()
            key = yaml.dump((args, tuple(sorted(kwargs.items()))))
            if key not in db or (expire and now-db[key]['TS'] > expire):
                db[key] = {'TS': now, 'data': func(*args, **kwargs)}
                db.sync()
            return db[key]['data']

        return new_func
    return decorator

def slow_shelve(fp, expire=None):
    '''
    I wrote this function so multiple threads or processes can use the shelf without it locking
    to a single thread or process.
    '''
    import shelve
    import yaml
    
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    def decorator(func):       
        def new_func(*args):
            db = shelve.open(fp)
            dn = os.path.dirname(fp)
            if dn != '': os.makedirs(dn, exist_ok=True)

            now, key = time(), yaml.dump(args)
            if key not in db or (expire and now-db[key]['TS'] > expire):
                db.close()
                return_value = {'TS': now, 'data': func(*args)}
                db = shelve.open(fp)
                db[key] = return_value
                db.sync()
            else:
                return_value = db[key]['data']
            db.close()
            return return_value

        return new_func
    return decorator

def yaml_memoize(func):
    import yaml
    d = dict()
    def new_func(*args):
        key = yaml.dump(args) # serialized arguments
        return d[key] if key in d else d.setdefault(key, func(*args))
    return new_func

from collections.abc import Hashable
def id_memoize(func):
    """
    TOTALLY UNSAFE - DO NOT USE!
    """
    d = dict()
    def new_func(*args):
        key = tuple(a if isinstance(a, Hashable) else id(a) for a in args)
        return d[key] if key in d else d.setdefault(key, func(*args))
    return new_func

def key_memoize(func):
    d = dict()
    def new_func(*args):
        key = func.key_func(*args)
        return d[key] if key in d else d.setdefault(key, func(*args))
    return new_func

def line_items(fp):
    with open(fp) as f:
        return f.read().strip().splitlines()

meters_to_miles = lambda d: 0.000621371*d
miles_to_meters = lambda d: 1609.34*d
from math import radians, degrees, sin, cos, asin, sqrt
hav = lambda a: sin(a/2)**2 # haversine
def angular_distance(c1, c2):
    """
    c1 must be Point(lon lat)
    c2 must be Point(lon lat)
    Uses the law of haversines method instead of the rounding-error prone law of cosines method
    refer to https://en.wikipedia.org/wiki/Haversine_formula
    (Using simple cartesian distance doesn't work at any lattitude except lat~=90 degrees)
    """
    try:
        l1, p1 = map(radians, [c1.longitude,c1.latitude])
        l2, p2 = map(radians, [c2.longitude,c2.latitude])
    except AttributeError:
        l1, p1 = map(radians, [c1.lon,c1.lat])
        l2, p2 = map(radians, [c2.lon,c2.lat])
    # ds = acos( sin(p1)*sin(p2) + cos(p1)*cos(p2)*cos(l1-l2) ) # Deprecated law of cosines method
    ds = 2*asin(sqrt( hav(p1-p2) + cos(p1)*cos(p2)*hav(l1-l2) ))
    return degrees(ds)
def aerial_distance(c1, c2):
    return 40000*angular_distance(c1,c2)/360

def weighted_avg_and_std(values, weights, give_unbiased=False):
    import numpy as np
    average = np.average(values, weights=weights)
    variance = np.average((values-average)**2, weights=weights)
    if give_unbiased:
        bias_factor = 1 - sum(w**2 for w in weights) / sum(weights)**2
        # see https://en.wikipedia.org/wiki/Weighted_arithmetic_mean#Reliability_weights
        variance /= bias_factor
    std = variance**.5
    return (average, std)

def frequency_avg_and_std(values, weights, give_unbiased=False):
    import numpy as np
    average = np.average(values, weights=weights)
    if give_unbiased:
        variance = sum(w*(x-average)**2 for x,w in zip(values, weights)) / (sum(weights) - 1)
        # see https://en.wikipedia.org/wiki/Weighted_arithmetic_mean#Frequency_weights
    else:
        variance = np.average((values-average)**2, weights=weights)
    std = variance**.5
    return (average, std)