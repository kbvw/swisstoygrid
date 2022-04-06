import os
import pandas as pd
import yaml
from tqdm import tqdm

from pp_toy_model import (load_gen_parser, apply_load_gen, 
                          _set_by_element_name)

class ResLogger:
    def __init__(self, path, metrics):
        self.columns = [metric.__name__ for metric in metrics]

        # Temporary solution
        columns_m = [col+'_m' for col in self.columns]
        self.columns.extend(columns_m)
        
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
        
    def write_res(self, idx, res_series):
        res_list = res_series[self.columns].values
        self.res.write(str(idx))
        for res in res_list:
            self.res.write(','+str(res))
        self.res.write('\n')
        
def run_simulations(path, net, metrics, simulation_step_func,
                    until='end', overwrite=False):
    columns = [metric.__name__ for metric in metrics]
    
    # Temporary solution
    columns_m = [col+'_m' for col in columns]
    columns.extend(columns_m)
    
    # Note: complicated and unoptimized due to time constraints
    
    # Load simulation inputs
    with open(path+'config.yaml', 'r') as config_file:
        eq_list = yaml.full_load(config_file)
    eq_frame_dict = {}
    for (element_name, quantity_name) in eq_list:
        eq_frame = pd.read_csv(path+f'{element_name}_{quantity_name}.csv',
                               index_col=0)
        eq_frame_dict[(element_name, quantity_name)] = eq_frame
    
    # Set final simulation step
    if until=='end':
        stop = eq_frame.index[-1]
    else:
        stop = until
    
    # Check progress with logger
    with ResLogger(path, metrics) as l:
        if not l.header:
            l.write_header(columns)
            start = 0
        elif not l.last_run:
            start = 0
        else:
            start = l.last_run
            
        # Main loop
        for n in tqdm(range(start, stop)):
            
            # Set quantity values on the network object
            for (e_name, q_name), q_value in eq_frame_dict.items():
                q_series = pd.Series(q_value.loc[n, :], name=q_name)
                _set_by_element_name(net, e_name, q_series)
            
            # Run user-specified simulation step
            
            # Temporary solution
            results, results_m = simulation_step_func(net, metrics)
            results_m = results_m.copy()
            results_m.index += '_m'
            results = pd.concat([results, results_m])
            
            # Write results
            l.write_res(n, results)
        
def init_simulations(path, eq_frame_dict):  
    if not os.path.isdir(path): 
        os.mkdir(path)
        
    # Note: complicated and unoptimized due to time constraints
    
    eq_list = []
    for (element_name, quantity_name), eq_frame in eq_frame_dict.items():
        eq_frame.to_csv(path+f'{element_name}_{quantity_name}.csv')
        eq_list.append((element_name, quantity_name))
        
    with open(path+'config.yaml', 'w') as config_file:
        yaml.dump(eq_list, config_file)

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
        apply_load_gen(net, base_file)
        apply_noise_func(net)
        for (element_name, quantity_name), eq_frame in eq_frame_dict.items():
            quantity_series = net[element_name][quantity_name]
            quantity_series.index = net[element_name]['name']
            eq_frame.loc[n, :] = quantity_series
            
    return eq_frame_dict