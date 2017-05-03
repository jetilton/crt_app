import pandas as pd
from bokeh.io import curdoc
from bokeh.models import Select
from bokeh.models import Range1d, ColumnDataSource
from bokeh.plotting import figure
from bokeh.palettes import Spectral11
from bokeh.layouts import layout
from os.path import join, dirname

def get_locations(data):
    locations = list(set(data.location))
    locations.sort()
    return {'locations':locations}

def get_dataset(df, location, data_column_name):
    data = df[df.location == location].copy()
    alternatives = list(set(data['alternative']))
    data = data.drop('location', 1)
    number_of_alternatives = len(alternatives)
    alternatives = list(set(data.alternative))
    number_of_alternatives = len(alternatives)
    mypalette=Spectral11[0:number_of_alternatives]
    data_length = len(data)
    index = data_length / number_of_alternatives
    index = range(0, index) * number_of_alternatives
    data['index'] = index
    data.set_index('index', drop = True, inplace = True)
    data.set_index('alternative', append = True, inplace = True)
    data = data.unstack()
    
    source = ColumnDataSource(data = {'x':[data.plotting_positions[alternative] 
                                                for alternative in alternatives], 
                                      'y':[data[data_column_name][alternative] 
                                                for alternative in alternatives],
                                      'legend':alternatives,
                                      'colors':mypalette})
    
    return source

def make_plot(source, title):
    p = figure(width=1000, height=500) 
    p.title.text = title
    p.multi_line(   
                    'x',
                    'y',
                    source = source,
                    line_color='colors',
                    line_width=3,
                    legend = 'legend'
                )
    p.x_range = Range1d(100,0)
    return p

def update_plot(attrname, old, new):
    location_maxOutFlow = location_select_maxOutFlow.value
    src_maxOutFlow = get_dataset(df_maxOutFlow,location_maxOutFlow, 'kcfs')
    source_maxOutFlow.data.update(src_maxOutFlow.data)

    location_poolDraft = location_select_poolDraft.value
    src_poolDraft = get_dataset(df_poolDraft,location_poolDraft, 'MAF')
    source_poolDraft.data.update(src_poolDraft.data)
    
    location_poolMaxDraft = location_select_poolMaxDraft.value
    src_poolMaxDraft = get_dataset(df_poolMaxDraft,location_poolMaxDraft, 'MAF')
    source_poolMaxDraft.data.update(src_poolMaxDraft.data)
 
location = 'LIBBY'


df_maxOutFlow = pd.read_csv(join(dirname(__file__), 'data/test_run/maxOutFlow.csv' ), index_col = 0)
locations_maxOutFlow = get_locations(df_maxOutFlow)
location_select_maxOutFlow = Select(value=location, title='locations', options=locations_maxOutFlow['locations'])
source_maxOutFlow = get_dataset(df_maxOutFlow, location, 'kcfs')
plot_maxOutFlow = make_plot(source_maxOutFlow, 'Max Outflow')
location_select_maxOutFlow.on_change('value', update_plot)

df_poolDraft = pd.read_csv(join(dirname(__file__), 'data/test_run/poolDraft.csv' ), index_col = 0)
locations_poolDraft = get_locations(df_poolDraft)
location_select_poolDraft = Select(value=location, title='locations', options=locations_poolDraft['locations'])
source_poolDraft = get_dataset(df_poolDraft, location, 'MAF')
plot_poolDraft = make_plot(source_poolDraft, 'Pool Draft')
location_select_poolDraft.on_change('value', update_plot)

df_poolMaxDraft = pd.read_csv(join(dirname(__file__), 'data/test_run/poolMaxDraft.csv' ), index_col = 0)
locations_poolMaxDraft = get_locations(df_poolMaxDraft)
location_select_poolMaxDraft = Select(value=location, title='locations', options=locations_poolMaxDraft['locations'])
source_poolMaxDraft = get_dataset(df_poolMaxDraft, location, 'MAF')
plot_poolMaxDraft = make_plot(source_poolMaxDraft, 'Pool Max Draft')
location_select_poolMaxDraft.on_change('value', update_plot)



curdoc().add_root(
                    layout
                        (
                            [
                                [location_select_maxOutFlow, plot_maxOutFlow],
                                [location_select_poolDraft, plot_poolDraft],
                                [location_select_poolMaxDraft, plot_poolMaxDraft]
                            ]
                        )
                    )
curdoc().title = "CRT"



    


    
    