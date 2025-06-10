import threading
import logging
#tables
FID_TABLE = {'/': '1-1'}
CALLBACK_TABLE = {} #FID:TRUE(IF FINE)/FALSE(IF NOT FINE)
LOCK = threading.Lock()
VOLUME_TABLE = {1:('127.0.0.1', 22353)}
logger = logging.getLogger(__name__)

def get_fid(current_path):
    LOCK.acquire()
    print(f'getting fid {current_path}')
    logger.info(f'getting fid {current_path} {FID_TABLE.get(current_path, None)}')
    fid = FID_TABLE.get(current_path, None)
    LOCK.release()
    return fid

def set_fid(key, value):
    LOCK.acquire()
    print(f'setting fid {key}:{value}')
    logger.info(f'setting fid {key}:{value}')
    FID_TABLE[key] = value
    LOCK.release()

def clear_fid():
    FID_TABLE.clear()
    FID_TABLE['/'] = 1 

def clear_callback():
    CALLBACK_TABLE.clear()

def get_callback():
    return CALLBACK_TABLE

def callback_broke(path):
    fid = get_fid(path)
    LOCK.acquire() # ? later
    a = CALLBACK_TABLE.get(fid, False)
    LOCK.release() # ? later
    return not a

def set_callback(key, value:bool = True):
    f'setting callback {key}:{value}'
    LOCK.acquire()
    CALLBACK_TABLE[key] = value
    LOCK.release()

def volume_in_cache(volume):
    print(volume)
    print(f'volume in cache: {volume}, {VOLUME_TABLE.keys()}  {volume in (VOLUME_TABLE.keys())}')
    return volume in VOLUME_TABLE.keys()

def get_address_from_cache(volume):
    return VOLUME_TABLE.get(volume, None)