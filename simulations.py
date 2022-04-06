import os
import pandas as pd

from pp_toy_model import load_gen_parser

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
        
def iterate_load_gen(path, overwrite=False):
    pass

def create_time_series(base_file, net, apply_noise_func, length,
                       elements='all', quantities='all'):
    series_dict = load_gen_parser(base_file)
    
    # Note: complicated and unoptimized due to time constraints
    # To do: either use network object or base profile, not both
    
    # Check for each element-quantity pair and initialize dataframe
    eq_frame_dict = {}
    for (element_name, quantity_name), quantity_value in series_dict.items():
        if ((elements == 'all' or element_name in elements) 
            and (quantities == 'all' or quantity_name in quantities)):
            columns = series_dict[(element_name, quantity_name)].index
            eq_frame = pd.DataFrame(index=range(length), columns=columns)
            eq_frame_dict[(element_name, quantity_name)] = eq_frame
            
    # Generate time series using the network object and apply-noise function
    for n in range(length):
        apply_noise_func(net)
        for (element_name, quantity_name), eq_frame in eq_frame_dict.items():
            quantity_series = net[element_name][quantity_name]
            quantity_series.index = net[element_name]['name']
            eq_frame.loc[n, :] = quantity_series
            
    return eq_frame_dict
            

