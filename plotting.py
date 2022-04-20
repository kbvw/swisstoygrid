import seaborn as sns
import matplotlib.pyplot as plt

LABELS = {'max_loading_inner': 'Max loading inner (%)',
          'max_loading_all': 'Max loading all (%)',
          'avg_loading_inner': 'Average loading inner (%)',
          'avg_loading_all': 'Average loading all (%)',
          'total_current_inner': 'Total current inner (kA)',
          'total_current_all': 'Total current all (kA)'}

HUE_LABELS = {'line_cuts': 'Number of lines cut',
              'node_split': 'Number of substations split'}

def compare_to_main(res_df, metrics_to_compare, topo_metric, hue=None, height=4, **kwargs):
    x, y = [], []
    for metric in metrics_to_compare:
        x.append(f'{metric}')
        y.append(f'{metric}_best_{topo_metric}')
    data_subset = x + y
    if hue:
        data_subset.append(f'{hue}_best_{topo_metric}')
        
    res_df = res_df[data_subset].copy()
    
    x = [f'{LABELS[metric]}, main topology' for metric in metrics_to_compare]
    y = [f'{LABELS[metric]}, best topology' for metric in metrics_to_compare]
    new_labels = x + y
    if hue:
        hue = HUE_LABELS[hue]
        new_labels.append(hue)
        
    res_df.columns = new_labels

    grid = sns.pairplot(res_df, x_vars=x, y_vars=y, height=8, hue=hue)
    grid.map(lambda x, y, **kwargs: plt.gca().axline(xy1=(0, 0), xy2=(1, 1), color='r', dashes=(5, 2)))
    grid.set(**kwargs)
    grid.fig.subplots_adjust(top=0.9)
    grid.fig.suptitle(f'Best: {LABELS[topo_metric]}', fontsize=20)
    return grid