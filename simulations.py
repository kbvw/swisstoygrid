import os
import pandas as pd
import yaml
from tqdm import tqdm

from pp_toy_model import (eq_yaml_parser, apply_eq_from_yaml,
                          set_eq_by_bus_name)

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
                    
                # File has header
                else:
                    first_line = lines[0]
                    last_line= lines[0]
                    self.columns = pd.Index((first_line[1:]
                                             .rstrip().split(',')))
                    self.header = True
                    
                    # File is empty with header
                    if last_line.split(',')[0] == 0:
                        self.last_run = None
                    
                    # Previous result computations exists
                    else:
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
        self.columns = columns
        for column in columns:
            self.res.write(','+column)
        self.res.write('\n')
        
    def write_res(self, idx, res_series):
        res_list = res_series[self.columns].values
        self.res.write(str(idx))
        for res in res_list:
            self.res.write(','+str(res))
        self.res.write('\n')
        
def run_simulations(path, net, metrics, simulation_step_func,
                    until=None, overwrite=False):
               
    # Load simulation inputs   
    with open(path+'input_config.yaml', 'r') as config_file:
        eq_list = yaml.safe_load(config_file)
        
    eq_frame_dict = {}
    for (element, quantity) in eq_list:
        eq_frame = pd.read_csv(path+f'{element}_{quantity}.csv',
                               index_col=0)
        eq_frame_dict[(element, quantity)] = eq_frame
    
    # Set final simulation step
    if until==None:
        stop = len(eq_frame.index)
    else:
        stop = until
        
    # Logic for applying n-th inputs and running simulation step
    def set_eq_and_run(n): 
        for (e_name, q_name), q_value in eq_frame_dict.items():
            q_series = pd.Series(q_value.loc[n, :], name=q_name)
            set_eq_by_bus_name(net, e_name, q_series)
        return simulation_step_func(net, metrics)
        
    # Check progress with logger
    with ResLogger(path) as l:
        
        # If no header, run zeroth simulation step to infer column names
        if not l.header:
            progress = iter(tqdm(range(stop)))
            results = set_eq_and_run(next(progress))
            l.write_header(results.index)
            l.write_res(0, results)
        
        # If header but no last run, start from beginning
        elif not l.last_run:
            progress = tqdm(range(stop))
            
        # Otherwise start after last run
        else:
            progress = tqdm(range(l.last_run + 1, stop))
            
        # Main loop
        for n in progress:
            results = set_eq_and_run(n)
            l.write_res(n, results)
        
def init_simulations(path, eq_frame_dict):
    if not os.path.isdir(path): 
        os.mkdir(path)
        
    eq_list = []
    for (element, quantity), eq_frame in eq_frame_dict.items():
        eq_frame.to_csv(path+f'{element}_{quantity}.csv')
        eq_list.append([element, quantity])
    
    with open(path+'input_config.yaml', 'w') as config_file:
        yaml.dump(eq_list, config_file)

def create_time_series(base_yaml, net, apply_noise_func, length,
                       elements='all', quantities='all'):
    eq_series_dict = eq_yaml_parser(base_yaml)
    
    # Note: complicated and unoptimized due to time constraints
    # To do: either use network object or base profile, not both
    
    # Check for each element-quantity pair and initialize dataframe
    eq_frame_dict = {}
    for (element, quantity), value in eq_series_dict.items():
        if ((elements == 'all' or element in elements) 
            and (quantities == 'all' or quantity in quantities)):
            columns = eq_series_dict[(element, quantity)].index
            eq_frame = pd.DataFrame(index=range(length), columns=columns)
            eq_frame_dict[(element, quantity)] = eq_frame
            
    # Generate time series using the network object and apply-noise function
    for n in range(length):
        apply_eq_from_yaml(net, base_yaml)
        apply_noise_func(net)
        for (element, quantity), eq_frame in eq_frame_dict.items():
            value_series = net[element][quantity]
            value_series.index = net[element]['name']
            eq_frame.loc[n, :] = value_series
            
    return eq_frame_dict