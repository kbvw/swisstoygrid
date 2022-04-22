METRICS = {'max_loading_inner':   lambda net: net.res_line
                                                 .loc[:7, 'loading_percent']
                                                 .max(),
           'max_loading_all':     lambda net: net.res_line
                                                 .loc[:, 'loading_percent']
                                                 .max(),
           'avg_loading_inner':   lambda net: net.res_line
                                                 .loc[net.line['in_service'] == True]
                                                 .loc[:7, 'loading_percent'].mean(),
           'avg_loading_all':     lambda net: net.res_line
                                                 .loc[net.line['in_service'] == True]
                                                 .loc[:, 'loading_percent']
                                                 .mean(),
           'total_current_inner': lambda net: net.res_line
                                                 .loc[:7, 'i_ka']
                                                 .sum(),
           'total_current_all':   lambda net: net.res_line
                                                 .loc[:, 'i_ka']
                                                 .sum()}

def create_metrics(metric_names):
    return [(metric_name, METRICS[metric_name]) for metric_name in metric_names]

def apply_load_gen_noise(net, mean_outer_mw=10000, std_outer_mw=2000, mean_inner_mw=5000, std_inner_mw=1000):
    import numpy as np
    
    # Total deviation in MW
    dev_outer_mw = np.random.normal(mean_outer_mw, std_outer_mw)
    dev_inner_mw = np.random.normal(mean_inner_mw, std_inner_mw)
    
    # Outer loads and generators
    
    # Generate noise
    load_noise_outer = np.random.uniform(0, net.load.loc[5:8, 'p_mw'])
    gen_noise_outer = np.random.uniform(0, net.gen.loc[5:8, 'p_mw'])
    
    # Normalize to distribution
    load_noise_outer /= load_noise_outer.sum()
    gen_noise_outer /= gen_noise_outer.sum()
    
    # Compute load and generator deviations in MW
    load_noise_outer *= dev_outer_mw
    gen_noise_outer *= dev_outer_mw
    
    # Apply noise to network
    net.load.loc[5:8, 'p_mw'] += load_noise_outer
    net.gen.loc[5:8, 'p_mw'] += gen_noise_outer
    
    # Inner loads and generators
    
    # Generate noise
    load_noise_inner = np.random.uniform(0, net.load.loc[:4, 'p_mw'])
    gen_noise_inner = np.random.uniform(0, net.gen.loc[:4, 'p_mw'])
    
    # Normalize to distribution
    load_noise_inner /= load_noise_inner.sum()
    gen_noise_inner /= gen_noise_inner.sum()
    
    # Compute load and generator deviations in MW
    load_noise_inner *= dev_inner_mw
    gen_noise_inner *= dev_inner_mw
    
    # Apply noise to network
    net.load.loc[:4, 'p_mw'] += load_noise_inner
    net.gen.loc[:4, 'p_mw'] += gen_noise_inner