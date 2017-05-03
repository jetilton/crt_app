# -*- coding: utf-8 -*-
from bokeh.plotting import figure, show, output_file
output_file('temp.html')
from bokeh.palettes import Spectral11
import pandas as pd
from bokeh.models import HoverTool, Legend,NumeralTickFormatter, Range1d, ColumnDataSource
df = pd.read_csv(r"data\max_outflow_plotting_positions.csv", index_col = 0)
  
location = 'BONNEVILLE'

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
    
    source = ColumnDataSource(data = {'x':[data.plotting_positions[alternative] for alternative in alternatives], 
                                      'y':[data.kCFS[alternative] for alternative in alternatives],
                                      'legend':alternatives,
                                      'colors':mypalette})
    
    return source

source = get_dataset(df, location)

p = figure(width=1000, height=500) 
p.multi_line(   
                'x',
                'y',
                source = source,
                line_color='colors',
                line_width=5,
                legend = 'legend'
            )
p.x_range = Range1d(100,0)
show(p)



