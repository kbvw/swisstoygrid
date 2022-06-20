from itertools import chain
import pandas as pd

import pp_toy_model
from network_topology_optimization.grid.data import Grid, GridParams
from network_topology_optimization.grid.powerflow import GridData

def create_toy_model(config_file='config/example_config.yaml'):
    
    net = pp_toy_model.create_toy_model(config_file=config_file)
    
    cn_list = {'line_' + c.name: frozenset({net.bus.loc[c.from_bus]['name'],
                                            net.bus.loc[c.to_bus]['name']})
               for c in net.line.itertuples()}
    
    ln_list = {'load_' + l.name: net.bus.loc[l.bus]['name']
               for l in net.load.itertuples()}
    
    gn_list = {'gen_' + g.name: net.bus.loc[g.bus]['name']
               for g in net.gen.itertuples()}
    
    y_list = {'line_' + c.name: 1/complex(real=c.r_ohm_per_km,
                                          imag=c.x_ohm_per_km)
              for c in net.line.itertuples()}
    
    s_list = {g: 1/len(net.gen.index)
              for g in gn_list}
    
    v_list = {e: net.bus['vn_kv'][0]*10**3
              for e in chain(cn_list, ln_list, gn_list)}
    
    p_base = 10**9
    
    return (Grid(cn_list, ln_list, gn_list),
            GridParams(y_list, s_list, v_list, p_base))

def grid_data(path):
    
    load = pd.read_csv(path + 'load_p_mw.csv', index_col=0)
    gen = pd.read_csv(path + 'gen_p_mw.csv', index_col=0)
    
    load.columns = 'load_' + load.columns
    gen.columns = 'gen_' + gen.columns
    
    p = pd.concat([-load*(10**6), gen*(10**6)], axis=1)
    
    for i in range(min(len(load.index), len(gen.index))):
        yield GridData(p_list=dict(p.loc[i, :]), q_list={}, mag_list={})

if __name__ == '__main__':
    
    grid, params = create_toy_model()