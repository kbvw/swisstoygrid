import pandapower as pp
import yaml

COORDS_PATH = {1: 'config/one_sub_coords.yaml', 
               2: 'config/two_sub_coords.yaml',
               4: 'config/four_sub_coords.yaml'}
PQ_PATH = {1: 'config/one_sub_pq.yaml',
           2: 'config/two_sub_pq.yaml'}

# Hard-coded mapping from zone to line type
LINE_PARAMS_MAP = {('center', 'center'): 'internal',
                   ('center', 'inner'): 'internal',
                   ('inner', 'inner'): 'internal',
                   ('inner', 'outer'): 'internal_external',
                   ('outer', 'outer'): 'external'}

def create_toy_model(config='config/example_config.yaml'):
    
    # Load configuration files
    config = yaml.safe_load(open(config))
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
    
    #pq_config = yaml.safe_load(open(PQ_PATH[n_subs]))
    
    # Unpack line parameters to pandapower, setting length to 1 km
    line_params = line_params_to_pp(line_params)
    
    # Create Pandapower Network object
    net = pp.create_empty_network()
    
    # Create buses from center outwards and store indices
    bus_idx_map = {}
    for zone in ['center', 'inner', 'outer']:
        bus_idx_map[zone] = add_buses(net, zone, bus_coords[zone], 
                                      center_order, ring_order, voltage)
    
    # Add lines from center outwards and store indices
    add_center_lines(net, ('center', 'center'), bus_idx_map, 
                     n_subs, center_order, line_params)
    add_radial_lines(net, ('center', 'inner'), bus_idx_map, 
                     center_order, ring_order, line_params)
    add_tangential_lines(net, ('inner', 'inner'), bus_idx_map,
                         ring_order, line_params)
    add_radial_lines(net, ('inner', 'outer'), bus_idx_map, 
                     center_order, ring_order, line_params)
    add_tangential_lines(net, ('outer', 'outer'), bus_idx_map, 
                         ring_order, line_params)
    
    return net

def line_params_to_pp(params):
    pp_params = {}
    for (line_type, line_type_params) in params.items():
        pp_params[line_type] = {}
        pp_params[line_type]['length_km'] = 1.
        pp_params[line_type]['r_ohm_per_km'] = line_type_params['r_ohm']
        pp_params[line_type]['x_ohm_per_km'] = line_type_params['x_ohm']
        pp_params[line_type]['c_nf_per_km'] = line_type_params['c_nf']
        pp_params[line_type]['max_i_ka'] = line_type_params['max_i_ka']
        
    return pp_params

def add_buses(net, zone, bus_coords, center_order, ring_order, voltage):
    bus_idx_map = {}
    
    # Specific order for adding center buses
    if zone == 'center':
        buses = center_order
    
    # General order for adding all ring buses
    else:
        buses = ring_order
    
    # Store bus indices after creating buses
    for bus in buses:
        bus_idx = pp.create_bus(net, vn_kv=voltage, name=bus, 
                                zone=zone, geodata=bus_coords[bus])
        bus_idx_map[bus] = bus_idx
        
        # Add a zero-P-and-Q load to every bus
        pp.create_load(net, bus_idx, p_mw=0, name=bus, )
        
        # Add a zero-P generator to every bus, slack if in center
        if zone == 'center':
            slack = True
        else:
            slack = False 
        pp.create_gen(net, bus_idx, p_mw=0, name=bus, slack=slack)

    return bus_idx_map

def add_center_lines(net, zones, bus_idx_map, 
                     n_subs, center_order, line_params):

    # Map zones to correct line parameters
    params = line_params[LINE_PARAMS_MAP[zones]]
    
    # No line if only one center bus
    if n_subs == 1:
        return
    
    # Line endpoints hard-coded as each of two center buses
    if n_subs == 2:
        from_buses_idx = [bus_idx_map[zones[0]][center_order[0]]]
        to_buses_idx = [bus_idx_map[zones[0]][center_order[1]]]
        names = [f'{center_order[0]}_{center_order[1]}']

    # Lines connect from one bus to the next bus in the provided order
    if n_subs > 2:
        to_buses = center_order[:]
        to_buses.append(to_buses.pop(0))
        
        from_buses_idx = [bus_idx_map[zones[0]][bus] for bus in center_order]
        to_buses_idx = [bus_idx_map[zones[1]][bus] for bus in to_buses]
        names = [f'{f}_{t}' for (f, t) in zip(center_order, to_buses)]
      
    for (from_bus, to_bus, name) in zip(from_buses_idx, to_buses_idx, names): 
        pp.create_line_from_parameters(net, 
                                       from_bus=from_bus, to_bus=to_bus,
                                       name=name,
                                       **params)

def add_radial_lines(net, zones, bus_idx_map, 
                     center_order, ring_order, line_params):
    
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
    names = [f'{f}_{t}' for (f, t) in zip(from_buses, ring_order)]
    
    for (from_bus, to_bus, name) in zip(from_buses_idx, to_buses_idx, names): 
        pp.create_line_from_parameters(net, 
                                       from_bus=from_bus, to_bus=to_bus,
                                       name=name,
                                       **params)

def add_tangential_lines(net, zones, bus_idx_map, 
                         ring_order, line_params):
    
    # Map zones to correct line parameters
    params = line_params[LINE_PARAMS_MAP[zones]]
    
    # Lines connect from one bus to the next bus in the provided order
    to_buses = ring_order[:]
    to_buses.append(to_buses.pop(0))
    
    from_buses_idx = [bus_idx_map[zones[0]][bus] for bus in ring_order]
    to_buses_idx = [bus_idx_map[zones[1]][bus] for bus in to_buses]
    names = [f'{f}_{t}' for (f, t) in zip(ring_order, to_buses)]
    
    for (from_bus, to_bus, name) in zip(from_buses_idx, to_buses_idx, names): 
        pp.create_line_from_parameters(net, 
                                       from_bus=from_bus, to_bus=to_bus,
                                       name=name,
                                       **params)