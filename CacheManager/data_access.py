# data_acsess.py
import os
import shutil
from storage.AfsFiles import AfsNode, AfsDir
from CacheManager.tables import *
import logging

logger = logging.getLogger(__name__)
ROOT_DIR = './cache_files'


def set_virtual_file(file:AfsNode, path):
    pass
    

def clear_cache():
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

def get_actual_file(path):
    print('in get real file')
    actual_path = ROOT_DIR + path
    f = open(actual_path, 'rb')
    data = f.read()
    f.close()
    return data

def cache_files(data:AfsNode, path):
    actual_path = ROOT_DIR + path
    print('real path: ' + actual_path)
    logger.info(f'caching {data} in {path}')
    if not type(data) is AfsDir:
        print('wrote ' + f'path: {path} data: {data.data}' + "\n")
        with open(actual_path, 'wb') as file:#with open(f'{path}', 'w') as file:
            file.write(data.data)
        set_fid(f'{path}', data.fid) # i dont know if needed  later
        set_virtual_file(data, path)
        return
    
    print(f'create dir {path}' + "\n")
    if not os.path.exists(actual_path):
        os.makedirs(actual_path)
    set_fid(f'{path}', data.fid) # i dont know if needed  later
    set_virtual_file(data, path)
    for f in data.children:
        if path == '/':
            print('changing path')
            path = ''
        # if type(f) is AfsDir:
        #     print('wrote ' + f'{path}/{f.name}' + "\n")
        #     with open('./client.txt', 'a') as file:#instad of os.makedirs(f'{path}/{f.name}', exist_ok=True)
        #         file.write(f'{path}/{f.name}' + "\n")#os.makedirs(f'{path}/{f.name}', exist_ok=True)
        # else:
        #     print(f'path: {path}/{f.name} data: {f.data}' + "\n")
        #     with open('./client.txt', 'a') as file:#with open(f'{path}/{f.name}', 'w') as file:
        #         file.write(f'path: {path}/{f.name} data: {f.data}' + "\n")#file.write(f.data + "\n")
        set_fid(f'{path}/{f.name}', f.fid)
        set_virtual_file(f, path)

def need_fetch(file_path:str):  # need fixing for example gives back /dir2/ maybe rewrite
    #returns the path that you need to start fetching from
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
        if not file_exists(current_path): # not os.path.exists(current_path)
            current_path = current_path[:-1*len(f'{path}')]
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
            current_path+= '/'
    print('none')
    return None


def file_exists(filepath:str): 
    #check if file exists
    actual_path = ROOT_DIR + filepath 
    return os.path.exists(actual_path) 
    
