# data_acsess.py
import os
from storage.AfsFiles import AfsNode, AfsDir
from CacheManager.tables import *
import logging

logger = logging.getLogger(__name__)

def cache_files(data:AfsNode, path):
    logger.info(f'caching {data} in {path}')
    if not type(data) is AfsDir:
        print('wrote ' + f'path: {path} data: {data.data}' + "\n")
        with open('./client.txt', 'a') as file:#with open(f'{path}', 'w') as file:
            file.write(f'path: {path} data: {data.data}' + "\n")#file.write(f.data + "\n")
        set_fid(f'{path}', data.fid) # i dont know if needed  later
        return
    
    print('wrote ' + f'dir {data.name} {data.fid}: {path}' + "\n")
    with open('./client.txt', 'a') as file:#instad of os.makedirs(f'{path}', exist_ok=True)
        file.write(f'dir {data.name} {data.fid}: {path}' + "\n")#os.makedirs(f'{path}', exist_ok=True)

    set_fid(f'{path}', data.fid) # i dont know if needed  later

    for f in data.children:
        if path == '/':
            print('changing path')
            path = ''
        if type(f) is AfsDir:
            print('wrote ' + f'{path}/{f.name}' + "\n")
            with open('./client.txt', 'a') as file:#instad of os.makedirs(f'{path}/{f.name}', exist_ok=True)
                file.write(f'{path}/{f.name}' + "\n")#os.makedirs(f'{path}/{f.name}', exist_ok=True)
        else:
            print(f'path: {path}/{f.name} data: {f.data}' + "\n")
            with open('./client.txt', 'a') as file:#with open(f'{path}/{f.name}', 'w') as file:
                file.write(f'path: {path}/{f.name} data: {f.data}' + "\n")#file.write(f.data + "\n")
        set_fid(f'{path}/{f.name}', f.fid)


def need_fetch(file_path:str):  # need fixing for example gives back /dir2/ maybe rewrite
    #returns the path that you need to start fetching from
    paths = file_path.split('/')
    logger.info(f'in need_fetch for {file_path}')
    current_path = '/'
    while '' in paths:
        paths.remove('')
    if len(paths) == 0:
        paths.append('')
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
        current_path+= '/'
    print('none')
    return None


def file_exists(filepath:str): 
    #check if file exists
    f = open('./client.txt', 'r')
    b =  filepath in f.read(4000)
    print('file exists bool:' , b)
    f.close()
    return b
    
