import threading
#tables
FID_TABLE = {'/': 1}
CALLBACK_TABLE = {} #FID:TRUE(IF FINE)/FALSE(IF NOT FINE)
LOCK = threading.Lock()
import logging
 
logger = logging.getLogger(__name__)
def get_fid(current_path):
    print(f'getting fid {current_path}')
    logger.info(f'getting fid {current_path} {FID_TABLE.get(current_path, None)}')
    return FID_TABLE.get(current_path, None)

def set_fid(key, value):
    print(f'setting fid {key}:{value}')
 
    logger.info(f'setting fid {key}:{value}')
    FID_TABLE[key] = value


def clear_fid():
    FID_TABLE.clear()
    FID_TABLE['/'] = 1 

def clear_callback():
    CALLBACK_TABLE.clear()

def get_callback():
    return CALLBACK_TABLE

def callback_broke(path):
    fid = get_fid(path)
    #LOCK.acquire() # ? later
    a = CALLBACK_TABLE.get(fid, False)
    #LOCK.release() # ? later
    return not a

def set_callback(key, value:bool = True):
    f'setting callback {key}:{value}'
    CALLBACK_TABLE[key] = value
