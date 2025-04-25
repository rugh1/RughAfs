import pickle 
class AfsNode:
    def __init__(self, name, fid):
        self.name = name
        self.fid = fid

    def __str__(self):
        return f'name:{self.name},fid:{self.fid}'

    def pickle_me(self):
        return pickle.dumps(self)
    
class AfsFile(AfsNode):
    def __init__(self, name, fid, data):
        super().__init__(name, fid)
        self.data = data

    def __str__(self):
        return super().__str__() + f', data:{self.data}'

class AfsDir(AfsNode):
    def __init__(self, name, fid, children = None):
        super().__init__(name, fid)
        if children is None:
            children = []
        self.children = children
    
    def __str__(self):
        files_list = ''
        for i in self.children:
            files_list += f'    {i}\n'
            # print(files_list)
        return 'dir ' + super().__str__() + f' files: \n{files_list}' 
    
    def pickle_me(self):
        new_child = []
        for i in self.children:
            if type(i) is AfsDir:
                new_child.append(AfsDir(i.name, i.fid)) #so i wont send the entire tree
            else:
                new_child.append(i)
        return pickle.dumps(AfsDir(self.name, self.fid, new_child))

    def add(self, AfsNode):
        self.children.append(AfsNode)
    