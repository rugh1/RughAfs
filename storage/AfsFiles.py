import pickle 
class AfsNode:
    def __init__(self, name, fid):
        self.name = name
        self.fid = fid
        self.raccess = []
        self.waccess = []

    def add_read_access(self, user):
        self.raccess.append(user)

    def add_write_access(self, user):
        self.waccess.append(user)
        if user not in self.raccess:
            self.raccess.append(user)

    def __str__(self):
        return f'name:{self.name},fid:{self.fid},read_access:{self.raccess},write_access:{self.waccess} '

    def pickle_me(self):
        return pickle.dumps(self)
    
class AfsFile(AfsNode):
    def __init__(self, name, fid, data = None):
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
    
    def pickle_me(self, user):
        new_child = []
        for i in self.children:
            if user not in i.raccess:
                continue
            if type(i) is AfsDir:
                new_child.append(AfsDir(i.name, i.fid)) #so i wont send the entire tree
            else:   
                new_child.append(AfsFile(i.name, i.fid))
        return pickle.dumps(AfsDir(self.name, self.fid, new_child))

    def add(self, AfsNode):
        self.children.append(AfsNode)
    