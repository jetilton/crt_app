import pandas as pd
from bokeh.io import curdoc
from bokeh.models import Select
from bokeh.models import Range1d, ColumnDataSource
from bokeh.plotting import figure
from bokeh.palettes import Spectral11
from bokeh.layouts import layout
from os.path import join, dirname
import glob

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
    
    source = ColumnDataSource(
                                data = {
                                        'x':[data.plotting_positions[alternative] 
                                                for alternative in alternatives], 
                                        'y':[data[data_column_name][alternative] 
                                                for alternative in alternatives],
                                        'legend':alternatives,
                                        'colors':mypalette
                                      }
                                )
    
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
    for key in dictionary.keys():
        location = dictionary[key]['location_select'].value
        src = get_dataset(dictionary[key]['df'],
                                 location, 
                                 dictionary[key]['data_units'])
        source.data.update(src.data)

    
   
 
location = 'LIBBY'

run_name = 'test_run'
data_directory = join(dirname(__file__), 'data', run_name,'*.csv' )
print data_directory
data_list = glob.glob(data_directory)
data_list = [x.split('\\')[-1] for x in data_list]
print data_list
dictionary = {}
for csv in data_list:
    name = csv.split('.csv')[0].replace('_',' ')
    print name
    
    df = pd.read_csv(join(dirname(__file__), 'data', run_name, csv),index_col=0)
    print 'df created'
    columns = list(df.columns)
    print columns
    data_units = [x for x in columns if   x != 'alternative' and 
                                          x != 'location' and 
                                          x != 'plotting_positions'][0]
    print data_units
    locations = get_locations(df)
    location_select = Select(value=location, title='locations', options=locations['locations'])
    source = get_dataset(df, location, data_units)
    plot = make_plot(source, name)
    select_plot_list = [location_select, plot]
    dictionary.update(
                        {name:
                            {
                                 'df':df,
                                 'name':name,
                                 'data_units':data_units,
                                 'locations':locations,
                                 'source':source,
                                 'plot':plot,
                                 'select_plot_list':select_plot_list,
                                 'location_select':location_select
                            }
                        }
                    )
    print dictionary.keys()
    location_select.on_change('value', update_plot)


layout_list = [dictionary[key]['select_plot_list'] for key in dictionary.keys()]




curdoc().add_root(
                    layout
                        (
                            layout_list
                        )
                    )
curdoc().title = "CRT"




      
      
      
      
      

    
    