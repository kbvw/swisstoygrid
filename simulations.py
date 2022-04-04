import os

class ResLogger:
    def __init__(self, path):
        self.path = path
        if not os.path.isdir(path): 
            os.mkdir(path)
            
        # Infer the last result computation that has been run
        if os.path.isfile(path+'res.csv'):
            with open(path+'res.csv', 'r') as res:
                lines = res.readlines()
                
                # File is empty with no header
                if len(lines) == 0:
                    self.header = False
                    self.last_run = None  
                
                # File is empty with header
                elif len(lines[-1].split(',')[0]) == 0:
                    self.header = True
                    self.last_run = None
                    
                # Previous result computations exists
                else:
                    self.header = True
                    self.last_run = int(lines[-1].split(',')[0])
        
        # If result file does not exist
        else:
            self.header = False
            self.last_run = None
    
    def __enter__(self):
        self.res = open(self.path+'res.csv', 'a').__enter__()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.res.__exit__(exc_type, exc_value, traceback)
        
    def write_header(self, columns):
        for column in columns:
            self.res.write(','+column)
        self.res.write('\n')
        
    def write_res(self, idx, res_list):
        self.res.write(str(idx))
        for res in res_list:
            self.res.write(','+str(res))
        self.res.write('\n')