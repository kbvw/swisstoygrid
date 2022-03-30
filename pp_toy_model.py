import pandas as pd
import pandapower as pp
import yaml

__all__ = ['create_toy_model', 
           'apply_load_from_series', 
           'apply_gen_from_series', 
           'apply_load_gen']

# Hard-coded node coordinates
COORDS_PATH = {1: 'config/one_sub_coords.yaml', 
               2: 'config/two_sub_coords.yaml',
               4: 'config/four_sub_coords.yaml'}

# Hard-coded mapping from zone to line type
LINE_PARAMS_MAP = {('center', 'center'): 'internal',
                   ('center', 'inner'): 'internal',
                   ('inner', 'inner'): 'internal',
                   ('inner', 'outer'): 'internal_external',
                   ('outer', 'outer'): 'external'}

# Conversion of total line parameter values to per kilometer in Pandapower
def _line_params_to_pp(params):
    pp_params = {}
    for (line_type, line_type_params) in params.items():
        pp_params[line_type] = {}
        pp_params[line_type]['length_km'] = 1.
        pp_params[line_type]['r_ohm_per_km'] = line_type_params['r_ohm']
        pp_params[line_type]['x_ohm_per_km'] = line_type_params['x_ohm']
        pp_params[line_type]['c_nf_per_km'] = line_type_params['c_nf']
        pp_params[line_type]['max_i_ka'] = line_type_params['max_i_ka']
        
    return pp_params

def create_toy_model(config_file='config/example_config.yaml'):
    """Generates the toy model as a Pandapower network object.
    
    The model is implemented for 1, 2 or 4 central substations.
    Number of substations, voltage and line parameters can be 
    specified in the config file: see config/example_config.yaml.
    
    Parameters
    ----------
    config_file : str
        Path to YAML file containing model parameters. 
        The default is 'config/example_config.yaml'.

    Raises
    ------
    NotImplementedError
        In case the number of substations specified in the
        config file is anything other than 1, 2 or 4.

    Returns
    -------
    net : pandapowerNet
        A Pandapower network object of the toy model, with 
        zero active and reactive power injections everywhere.
    """
    
    # Load configuration files
    with open(config_file, 'r') as config:
        config = yaml.safe_load(config)
    if config['substations'] not in COORDS_PATH.keys():
        raise NotImplementedError('This model is defined for'
                                  ' 1, 2 or 4 substations.')
        
    n_subs = config['substations']
    voltage = config['voltage_kv']
    line_params = config['parameters']
    
    coords_config = yaml.safe_load(open(COORDS_PATH[n_subs]))
    center_order = coords_config['order']['center']
    ring_order = coords_config['order']['ring']
    bus_coords = coords_config['coordinates']
    
    # Unpack line parameters to pandapower, setting length to 1 km
    line_params = _line_params_to_pp(line_params)
    
    # Create Pandapower Network object
    net = pp.create_empty_network()
    
    # Inner logic for adding buses of one zone
    def add_buses(zone, bus_coords):
        bus_idx_map = {}
        
        # Specific order for adding center buses
        if zone == 'center':
            buses = center_order
        
        # General order for adding all ring buses
        else:
            buses = ring_order
        
        # Store bus indices after creating buses
        for bus in buses:
            name = f'{zone}_{bus}'
            bus_idx = pp.create_bus(net, vn_kv=voltage, name=name, 
                                    zone=zone, geodata=bus_coords[bus])
            bus_idx_map[bus] = bus_idx
            
            # Add a zero-P-and-Q load to every bus
            pp.create_load(net, bus_idx, p_mw=0, name=name)
            
            # Add a zero-P generator to every bus, slack if in center
            if zone == 'center':
                slack = True
            else:
                slack = False 
                
            pp.create_gen(net, bus_idx, p_mw=0, name=name, slack=slack)

        return bus_idx_map

    # Inner logic for adding lines between buses in center zone
    def add_center_lines(zones):

        # Map zones to correct line parameters
        params = line_params[LINE_PARAMS_MAP[zones]]
        
        # No line if only one center bus
        if n_subs == 1:
            return
        
        # Line endpoints hard-coded as each of two center buses
        if n_subs == 2:
            from_buses_idx = [bus_idx_map[zones[0]][center_order[0]]]
            to_buses_idx = [bus_idx_map[zones[0]][center_order[1]]]
            names = [f'{zones[0]}_{center_order[0]}_{zones[1]}_{center_order[1]}']

        # Lines connect from one bus to the next bus in the provided order
        if n_subs > 2:
            to_buses = center_order[:]
            to_buses.append(to_buses.pop(0))
            
            from_buses_idx = [bus_idx_map[zones[0]][bus] for bus in center_order]
            to_buses_idx = [bus_idx_map[zones[1]][bus] for bus in to_buses]
            names = [f'{zones[0]}_{from_bus}_{zones[1]}_{to_bus}'
                     for (from_bus, to_bus) in zip(center_order, to_buses)]
          
        for (from_bus, to_bus, name) in zip(from_buses_idx, to_buses_idx, names): 
            pp.create_line_from_parameters(net, 
                                           from_bus=from_bus, to_bus=to_bus,
                                           name=name,
                                           **params)
            
    # Inner logic for adding radial lines between zones
    def add_radial_lines(zones):
        
        # Map zones to correct line parameters
        params = line_params[LINE_PARAMS_MAP[zones]]
        
        # Lines connecting to center are distributed over center buses
        if zones[0] == 'center':
            lines_per_bus = range(len(ring_order)//len(center_order))
            from_buses = [bus for bus in center_order for l in lines_per_bus]
            from_buses_idx = [bus_idx_map[zones[0]][bus] for bus in from_buses]
        
        # Lines between rings connect buses with the same name
        else:
            from_buses = ring_order
            
        # Look up bus indices and create line names
        from_buses_idx = [bus_idx_map[zones[0]][bus] for bus in from_buses]   
        to_buses_idx = [bus_idx_map[zones[1]][bus] for bus in ring_order]
        names = [f'{zones[0]}_{from_bus}_{zones[1]}_{to_bus}'
                 for (from_bus, to_bus) in zip(from_buses, ring_order)]
        
        for (from_bus, to_bus, name) in zip(from_buses_idx, to_buses_idx, names): 
            pp.create_line_from_parameters(net, 
                                           from_bus=from_bus, to_bus=to_bus,
                                           name=name,
                                           **params)
            
    # Inner logic for adding tangential lines within a zone
    def add_tangential_lines(zones):
        
        # Map zones to correct line parameters
        params = line_params[LINE_PARAMS_MAP[zones]]
        
        # Lines connect from one bus to the next bus in the provided order
        to_buses = ring_order[:]
        to_buses.append(to_buses.pop(0))
        
        from_buses_idx = [bus_idx_map[zones[0]][bus] for bus in ring_order]
        to_buses_idx = [bus_idx_map[zones[1]][bus] for bus in to_buses]
        names = [f'{zones[0]}_{from_bus}_{zones[1]}_{to_bus}'
                 for (from_bus, to_bus) in zip(ring_order, to_buses)]
        
        for (from_bus, to_bus, name) in zip(from_buses_idx, to_buses_idx, names): 
            pp.create_line_from_parameters(net, 
                                           from_bus=from_bus, to_bus=to_bus,
                                           name=name,
                                           **params)
    
    # Create buses from center outwards and store indices
    bus_idx_map = {}
    for zone in ['center', 'inner', 'outer']:
        bus_idx_map[zone] = add_buses(zone, bus_coords[zone])
    
    # Add lines from center outwards and store indices
    add_center_lines(('center', 'center'))
    add_radial_lines(('center', 'inner'))
    add_tangential_lines(('inner', 'inner'))
    add_radial_lines(('inner', 'outer'))
    add_tangential_lines(('outer', 'outer'))
    
    # Create maps for indexing tables by element name
    def create_name_map(element):
        name_map = getattr(net, element)['name']
        name_map = pd.Series(name_map.index, index=name_map)
        return name_map
        
    net.bus_name_map = create_name_map('bus')
    net.line_name_map = create_name_map('line')
    net.load_name_map = create_name_map('load')  
    net.gen_name_map = create_name_map('gen')    
    
    return net

def _set_by_element_name(net, element_name, quantity):
    pp_idx = getattr(net, element_name + '_name_map')[quantity.index]
    getattr(net, element_name).loc[pp_idx, quantity.name] = quantity.values
    
def apply_load_from_series(net, p_mw=None, q_mvar=None):      
    if p_mw is not None:
        _set_by_element_name(net, 'load', p_mw)
    if q_mvar is not None:
        _set_by_element_name(net, 'load', q_mvar)

def apply_gen_from_series(net, p_mw=None, vm_pu=None):
    if p_mw is not None:
        _set_by_element_name(net, 'gen', p_mw)
    if vm_pu is not None:
        _set_by_element_name(net, 'gen', vm_pu)
        
def apply_load_gen(net, load_gen_file='config/one_sub_load_gen_example.yaml'):
    with open(load_gen_file, 'r') as load_gen:
        load_gen_dict = yaml.safe_load(load_gen)
        
    # Parser for load-generation files
    def load_gen_dict_to_series(load_gen_dict, element_name, quantity_name):
        quantity_dict = load_gen_dict[element_name][quantity_name]
        flat_dict = {}
        for zone, buses_dict in quantity_dict.items():
            for bus, quantity_value in buses_dict.items():
                flat_dict[f'{zone}_{bus}'] = quantity_value
        return pd.Series(flat_dict, dtype=float, name=quantity_name)
    
    # Set loads
    load_p_mw = load_gen_dict_to_series(load_gen_dict, 'load', 'p_mw')
    load_q_mvar = load_gen_dict_to_series(load_gen_dict, 'load', 'q_mvar')
    apply_load_from_series(net, load_p_mw, load_q_mvar)
    
    gen_p_mw = load_gen_dict_to_series(load_gen_dict, 'gen', 'p_mw')
    gen_vm_pu = load_gen_dict_to_series(load_gen_dict, 'gen', 'vm_pu')
    apply_gen_from_series(net, gen_p_mw, gen_vm_pu)