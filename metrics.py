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