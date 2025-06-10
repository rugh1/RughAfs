# data_acsess.py
import os
import shutil
from storage.AfsFiles import AfsNode, AfsDir, AfsFile
from CacheManager.tables import *
import logging

logger = logging.getLogger(__name__)
ROOT_DIR = r'C:\AfsCache'
VIRTUAL_ACCSESS_DIR = r'C:\Users\vboxuser\Desktop\AFS'


def set_virtual_file(file:AfsNode, path):
    """
    set_virtual_file()

    Parameters:
        file: AfsNode
            An AfsNode object representing a file or directory in the AFS structure.
        path: str
            The relative path within the virtual structure (e.g., '/dir1/file.txt', 
            not 'C:/foo/dir1/file.txt').

    Returns:
        None

    Description:
        Creates an empty virtual representation (file or directory) at the appropriate 
        location for display purposes.
    """
    if file.name == 'main dir':
        return
    if path == '':
        return
    actual_path = VIRTUAL_ACCSESS_DIR + path
    logger.info(f'setting virtual path : {actual_path} and path : {path}')
    if type(file) is AfsDir:
        print('is dir')
        if not os.path.exists(actual_path):
            print('creating folder :', actual_path)
            os.makedirs(actual_path)
        return
    
    # actual_path += '/' + file.name
    else :
        logger.info(f'virtual file: { actual_path } , {str(file)}')
        with open(actual_path, 'w'):
            pass

def clear_cache():
    """
    clear_cache()

    Parameters:
        None

    Returns:
        bool
            True if the cache directory (ROOT_DIR) was successfully cleared; False otherwise.

    Description:
        Deletes all files and folders in the cache directory (ROOT_DIR).
    """
    for filename in os.listdir(ROOT_DIR):
        file_path = os.path.join(ROOT_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
            return False
    return True


def clear_virtual_cache():
    """
    clear_virtual_cache()

    Parameters:
        None

    Returns:
        bool
            True if the virtualization directory (VIRTUAL_ACCESS_DIR) was successfully cleared; False otherwise.

    Description:
        Deletes all files and folders in the virtualization directory (VIRTUAL_ACCESS_DIR).
    """
    for filename in os.listdir(VIRTUAL_ACCSESS_DIR):
        file_path = os.path.join(VIRTUAL_ACCSESS_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
            return False
    return True


def get_actual_file(path):
    """
    get_actual_file()

    Parameters:
        path: str
            The relative path within ROOT_DIR.

    Returns:
        bytes
            The full binary content of the file from the local cache.

    Description:
        Reads and returns the binary content of a file from the local cache.
    """
    print('in get real file')
    actual_path = ROOT_DIR + path
    f = open(actual_path, 'rb')
    data = f.read()
    f.close()
    return data

  
def cache_files(data:AfsNode, path):
    """
    cache_files()

    Parameters:
        data: AfsNode
            An AfsNode object representing a file or directory.
        path: str
            The relative path in the local cache.

    Returns:
        None

    Description:
        Saves a file or directory to the local cache and creates a virtual representation for it.
    """
    actual_path = ROOT_DIR + path
    print('real path: ' + actual_path)
    logger.info(f'caching {data} in {path}')
    if not type(data) is AfsDir:
        print('wrote ' + f'path: {path} data: {data.data}' + "\n")
        with open(actual_path, 'wb') as file:  # with open(f'{path}', 'w') as file:
            file.write(data.data)
        set_fid(f'{path}', data.fid)  # i dont know if needed  later
        set_virtual_file(data, path)
        return

    print(f'create dir {path}' + "\n")
    if not os.path.exists(actual_path):
        os.makedirs(actual_path)
    set_fid(f'{path}', data.fid)  # i dont know if needed  later
    set_virtual_file(data, path)
    for f in data.children:
        if path == '/':
            print('changing path')
            path = ''
        set_fid(f'{path}/{f.name}', f.fid)
        set_virtual_file(f, f'{path}/{f.name}')

def need_fetch(file_path:str):
    #returns the path that you need to start fetching from
    """
    need_fetch()

    Parameters:
        file_path: str
            The requested relative path (e.g., '/dir2/sub/file.txt').

    Returns:
        str | None
            None if the file is up to date, or the path from which a fetch should start.

    Description:
        Determines whether part of the tree needs to be downloaded and returns 
        the path from which to begin fetching, or None if no fetch is required.
    """
    paths = file_path.split('/')
    logger.info(f'in need_fetch for {file_path}')
    current_path = ''
    while '' in paths:
        paths.remove('')
    paths.insert(0, '/')
    print(f'in need fetch {paths}')
    logger.info(paths)
    for path in paths:
        current_path += f'{path}'
        logger.info(f'checking {current_path} ')
        print(f'in need fetch curr: {current_path}')
        if not file_exists(current_path):  # not os.path.exists(current_path)
            current_path = current_path[:-1 * len(f'{path}')]
            if current_path.endswith('/'):
                current_path = current_path[:-1]
            if current_path == '':
                current_path = '/'
            print(f'current_path2: {current_path}')
            logger.info(f'file not exists fetching from {current_path}')
            return current_path
        if callback_broke(current_path):
            print(f'callback broke for {current_path}')
            logger.info(f'callback broke for {current_path}')
            return current_path
        if current_path != '/':
            current_path += '/'
    print('none')
    return None


def file_exists(filepath:str):
    """
    file_exists()

    Parameters:
        filepath: str
            The relative path within the cache (ROOT_DIR + filepath).

    Returns:
        bool
            True if the path exists in the local cache; False otherwise.

    Description:
        Checks whether a given file exists in the local cache.
    """
    #check if file exists
    actual_path = ROOT_DIR + filepath 
    return os.path.exists(actual_path) 
    