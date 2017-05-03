import pandas as pd
from bokeh.io import curdoc
from bokeh.models import Select
from bokeh.models import Range1d, ColumnDataSource
from bokeh.plotting import figure
from bokeh.palettes import Spectral11
from bokeh.layouts import row, column
from os.path import join, dirname

def get_locations(data):
    locations = list(set(data.location))
    locations.sort()
    return {'locations':locations}

def get_dataset(df, location):
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
                                      'y':[data.kcfs[alternative] 
                                                for alternative in alternatives],
                                      'legend':alternatives,
                                      'colors':mypalette})
    
    return source

def make_plot(source):
    p = figure(width=1000, height=500) 
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
    location = location_select.value
    src = get_dataset(df,location)
    source.data.update(src.data)

df = pd.read_csv(join(dirname(__file__), 'data/test_run/maxOutFlow.csv' ), index_col = 0)
 
location = 'THE DALLES'
locations = get_locations(df)
location_select = Select(value=location, title='locations', options=locations['locations'])
source = get_dataset(df, location)
plot = make_plot(source)
location_select.on_change('value', update_plot)


controls = column(location_select)


curdoc().add_root(row(controls, plot))
curdoc().title = "Max Outflow"



    


    
    