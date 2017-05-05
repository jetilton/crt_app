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

def get_dataset(df, location, unit):
    data = df[df.location == location].copy()
    data_boxplot = data.copy()
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
    
    source_ace = ColumnDataSource(
                                data = {
                                        'x':[data.plotting_positions[alternative] 
                                                for alternative in alternatives], 
                                        'y':[data[unit][alternative] 
                                                for alternative in alternatives],
                                        'legend':alternatives,
                                        'colors':mypalette
                                      }
                                )
    
    
    groups = data_boxplot.groupby('alternative')
    q1 = groups.quantile(q=0.25)
    q2 = groups.quantile(q=0.5)
    q3 = groups.quantile(q=0.75)
    iqr = q3 - q1
    upper = q3 + 1.5*iqr
    lower = q1 - 1.5*iqr
    
    # find the outliers for each category
    def outliers(group):
        alternative = group.name
        return group[(group[unit] > upper.loc[alternative][unit]) | (group[unit] < lower.loc[alternative][unit])][unit]
    out = groups.apply(outliers).dropna()
    
    # prepare outlier data for plotting, we need coordinates for every outlier.
    outx = []
    outy = []
    if not out.empty:
        for alternative in alternatives:
            # only add outliers if they exist
            if not out.loc[alternative].empty:
                for value in out.loc[alternative]:
                    outx.append(alternative)
                    outy.append(value)
    
    
    
    # if no outliers, shrink lengths of stems to be no longer than the minimums or maximums
    qmin = groups.quantile(q=0.00)
    qmax = groups.quantile(q=1.00)
    upper.score = [min([x,y]) for (x,y) in zip(list(qmax.loc[:,unit]),upper[unit])]
    lower.score = [max([x,y]) for (x,y) in zip(list(qmin.loc[:,unit]),lower[unit])]
    
    
    source_box = ColumnDataSource(
                                    data = {
                                        'alternatives' : alternatives,
                                        'upper' : upper[unit],
                                        'lower' : lower[unit],
                                        'q1': q1[unit],
                                        'q2': q2[unit],
                                        'q3': q3[unit],
                                        
                                        }
            )
    
    source_outlier = ColumnDataSource(
                                        data = {
                                                'outx':outx,
                                                'outy':outy
                                                })

    
    
    
    
    
    return (source_ace, source_box, source_outlier)

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

def boxplot(source_box, source_outlier, alternatives):
    p = figure(tools="save", background_fill_color="#EFE8E2", title="", x_range=alternatives)
    p.segment('alternatives', 'upper', 'alternatives', 'q3', source = source_box, line_color="black")
    p.segment('alternatives', 'lower', 'alternatives', 'q1', source = source_box, line_color="black")
    
    # boxes
    p.vbar('alternatives', 0.7, 'q2', 'q3',source = source_box, fill_color="#E08E79", line_color="black")
    p.vbar('alternatives', 0.7, 'q1', 'q2', source = source_box, fill_color="#3B8686", line_color="black")
    
    # whiskers (almost-0 height rects simpler than segments)
    p.rect('alternatives', 'lower',  0.2, 0.01, source = source_box,line_color="black")
    p.rect('alternatives', 'upper',  0.2, 0.01,source = source_box, line_color="black")
    
    
    p.circle('outx', 'outy', source = source_outlier, size=6, color="#F38630", fill_alpha=0.6)
    
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = "white"
    p.grid.grid_line_width = 2
    p.xaxis.major_label_text_font_size="12pt"
    return p

def update_plot(attrname, old, new):
    location_max_outflow = dictionary['Max outflow']['location_select'].value
    source_max_outflow = get_dataset(dictionary['Max outflow']['df'],
                                     location_max_outflow, 
                                     dictionary['Max outflow']['data_units'])
    source_max_outflow_ace = source_max_outflow[0]
    dictionary['Max outflow']['source'].data.update(source_max_outflow_ace.data)

    location_pool_draft = dictionary['Pool draft']['location_select'].value
    source_pool_draft = get_dataset(dictionary['Pool draft']['df'],
                                    location_pool_draft, 
                                    dictionary['Pool draft']['data_units'])
    source_pool_draft_ace = source_pool_draft[0]
    dictionary['Pool draft']['source'].data.update(source_pool_draft_ace.data)
    
    location_pool_max_draft = dictionary['Pool max draft']['location_select'].value
    source_pool_max_draft = get_dataset(dictionary['Pool max draft']['df'],
                                        location_pool_max_draft, 
                                        dictionary['Pool max draft']['data_units'])
    source_pool_max_draft_ace = source_pool_max_draft[0]
    dictionary['Pool max draft']['source'].data.update(source_pool_max_draft_ace.data)
    
    location_pool_storage = dictionary['Pool storage']['location_select'].value
    source_pool_storage = get_dataset(dictionary['Pool storage']['df'],
                                      location_pool_storage, 
                                      dictionary['Pool storage']['data_units'])
    source_pool_storage_ace = source_pool_storage[0]
    dictionary['Pool storage']['source'].data.update(source_pool_storage_ace.data)
    
    location_pool_max_storage = dictionary['Pool max storage']['location_select'].value
    source_pool_max_storage = get_dataset(dictionary['Pool max storage']['df'],
                                          location_pool_max_storage, 
                                          dictionary['Pool max storage']['data_units'])
    source_pool_max_storage_ace = source_pool_max_storage[0]
    dictionary['Pool max storage']['source'].data.update(source_pool_max_storage_ace.data)
    
    location_pool_elevation = dictionary['Pool elevation']['location_select'].value
    source_pool_elevation = get_dataset(dictionary['Pool elevation']['df'],
                                        location_pool_elevation, 
                                        dictionary['Pool elevation']['data_units'])
    source_pool_elevation_ace = source_pool_elevation[0]
    dictionary['Pool elevation']['source'].data.update(source_pool_elevation_ace.data)
    
    location_pool_max_elevation = dictionary['Pool max elevation']['location_select'].value
    source_pool_max_elevation = get_dataset(dictionary['Pool max elevation']['df'],
                                            location_pool_max_elevation, 
                                            dictionary['Pool max elevation']['data_units'])
    source_pool_max_elevation_ace = source_pool_max_elevation[0]
    dictionary['Pool max elevation']['source'].data.update(source_pool_max_elevation_ace.data)



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
    source_ace = source[0]
    plot = make_plot(source_ace, name)
    select_plot_list = [location_select, plot]
   
    dictionary.update(
                        {name:
                            {
                                 'df':df,
                                 'name':name,
                                 'data_units':data_units,
                                 'locations':locations,
                                 'source':source_ace,
                                 'plot':plot,
                                 'select_plot_list':select_plot_list,
                                 'location_select':location_select
                            }
                        }
                    )
    print dictionary.keys()


dictionary['Max outflow']['location_select'].on_change('value', update_plot)
dictionary['Pool draft']['location_select'].on_change('value', update_plot)
dictionary['Pool max draft']['location_select'].on_change('value', update_plot)
dictionary['Pool storage']['location_select'].on_change('value', update_plot)
dictionary['Pool max storage']['location_select'].on_change('value', update_plot)
dictionary['Pool elevation']['location_select'].on_change('value', update_plot)
dictionary['Pool max elevation']['location_select'].on_change('value', update_plot)

layout_list = [dictionary[key]['select_plot_list'] for key in dictionary.keys()]



curdoc().add_root(
                    layout
                        (
                            layout_list
                        )
                    )
curdoc().title = "CRT"




      
      
      
      
      

    
    