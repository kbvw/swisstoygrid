from itertools import chain

import pp_toy_model
from network_topology_optimization.grid.data import Grid, GridParams

def create_toy_model(config_file='config/example_config.yaml'):
    
    net = pp_toy_model.create_toy_model(config_file=config_file)
    
    cn_list = {'line_' + c.name: frozenset({net.bus.loc[c.from_bus]['name'],
                                            net.bus.loc[c.to_bus]['name']})
               for c in net.line.itertuples()}
    
    ln_list = {'load_' + l.name: net.bus.loc[l.bus]['name']
               for l in net.load.itertuples()}
    
    gn_list = {'gen_' + g.name: net.bus.loc[g.bus]['name']
               for g in net.gen.itertuples()}
    
    y_list = {c: complex(real=1/c.r_ohm_per_km, imag=1/c.x_ohm_per_km)
              for c in net.line.itertuples()}
    
    s_list = {g: 1/len(net.gen.index)
              for g in gn_list}
    
    v_list = {e: net.bus['vn_kv'][0] 
              for e in chain(cn_list, ln_list, gn_list)}
    
    p_base = 100000
    
    return (Grid(cn_list, ln_list, gn_list),
            GridParams(y_list, s_list, v_list, p_base))

if __name__ == '__main__':
    
    net = create_toy_model()