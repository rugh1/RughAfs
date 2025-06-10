import threading
import logging
#tables
FID_TABLE = {'/': '1-1'}
CALLBACK_TABLE = {} #FID:TRUE(IF FINE)/FALSE(IF NOT FINE)
LOCK = threading.Lock()
VOLUME_TABLE = {1:('127.0.0.1', 22353)}
logger = logging.getLogger(__name__)


def get_fid(current_path):
    """
    get_fid()

    Parameters:
        current_path: str
            The relative path of the file or directory (used as the key in FID_TABLE).

    Returns:
        str or None
            The fid found in FID_TABLE for the given current_path, or None if not present.

    Description:
        Retrieves the fid associated with the specified current_path from the FID_TABLE.
    """
    print(f'getting fid {current_path}')
    LOCK.acquire()
    logger.info(f'getting fid {current_path} {FID_TABLE.get(current_path, None)}')
    fid = FID_TABLE.get(current_path, None)
    LOCK.release()
    return fid

def set_fid(key, value):
    """
    set_fid()

    Parameters:
        key: str
            The relative path of the file or directory to map to an fid.
        value: any
            The fid to assign for the given key.

    Returns:
        None

    Description:
        Inserts or updates the entry in FID_TABLE, mapping the given key to the specified value.
    """
    LOCK.acquire()
    print(f'setting fid {key}:{value}')
    logger.info(f'setting fid {key}:{value}')
    FID_TABLE[key] = value
    LOCK.release()


def get_callback():
    """
    get_callback()
    Parameters:
        None

    Returns:
        dict
            The entire CALLBACK_TABLE structure, containing callback status for each fid.

    Description:
        Returns the current CALLBACK_TABLE, which tracks whether callbacks are “broken” for each fid.
    """
    return CALLBACK_TABLE

def callback_broke(path):
    """
    callback_broke()

    Parameters:
        path: str
            The relative path of the file or directory whose callback status is being checked.

    Returns:
        bool
            True if the callback is broken for the specified path; False otherwise.

    Description:
        Checks whether the callback has “broken” for the given file or directory, based on CALLBACK_TABLE.
    """
    fid = get_fid(path)
    LOCK.acquire() # ? later
    a = CALLBACK_TABLE.get(fid, False)
    LOCK.release() # ? later
    return not a

def set_callback(key, value:bool = True):
    """
    set_callback()

    Parameters:
        key: str
            The fid for which to update the callback status in CALLBACK_TABLE.
        value: bool
            The new callback status (True = broken, False = intact).

    Returns:
        None

    Description:
        Updates CALLBACK_TABLE by setting the callback status for the given key to the specified value.
    """
    f'setting callback {key}:{value}'
    LOCK.acquire()
    CALLBACK_TABLE[key] = value
    LOCK.release()

def volume_in_cache(volume):
    """
    volume_in_cache()

    Parameters:
        volume: int
            The volume number to check for existence in VOLUME_TABLE.

    Returns:
        bool
            True if the specified volume exists in VOLUME_TABLE; False otherwise.

    Description:
        Checks whether the given volume number is present in VOLUME_TABLE.
    """
    print(volume)
    print(f'volume in cache: {volume}, {VOLUME_TABLE.keys()}  {volume in (VOLUME_TABLE.keys())}')
    return volume in VOLUME_TABLE.keys()

def get_address_from_cache(volume):
    return VOLUME_TABLE.get(volume, None)