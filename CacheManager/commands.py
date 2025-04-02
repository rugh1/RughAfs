#commands.py
from CacheManager.data_access import need_fetch
from CacheManager.network import fetch_file, get_volume_server

def open_file(path:str, mode:str):
    file_path_start = need_fetch(path)
    print(file_path_start)
    if file_path_start is not None:
        print('need fetch')
        server = get_volume_server(path)
        fetch_file(server, file_path_start, path)
    else:
        print(f'{path} already in cache')
    return