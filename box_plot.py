# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, show, output_file

box_data 


# generate some synthetic time series for six different categories


df = box_data.copy()
alternatives = list(set(df.alternative))
unit = 'MAF'

# find the quartiles and IQR for each category
groups = df.groupby('alternative')
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
for alternative in alternatives:
    # only add outliers if they exist
    if not out.loc[alternative].empty:
        for value in out[alternative]:
            outx.append(alternative)
            outy.append(value)

p = figure(tools="save", background_fill_color="#EFE8E2", title="", x_range=alternatives)

# if no outliers, shrink lengths of stems to be no longer than the minimums or maximums
qmin = groups.quantile(q=0.00)
qmax = groups.quantile(q=1.00)
upper.score = [min([x,y]) for (x,y) in zip(list(qmax.loc[:,unit]),upper[unit])]
lower.score = [max([x,y]) for (x,y) in zip(list(qmin.loc[:,unit]),lower[unit])]


source = ColumnDataSource(
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


# stems
p.segment('alternatives', 'upper', 'alternatives', 'q3', source = source, line_color="black")
p.segment('alternatives', 'lower', 'alternatives', 'q1', source = source, line_color="black")

# boxes
p.vbar('alternatives', 0.7, 'q2', 'q3',source = source, fill_color="#E08E79", line_color="black")
p.vbar('alternatives', 0.7, 'q1', 'q2', source = source, fill_color="#3B8686", line_color="black")

# whiskers (almost-0 height rects simpler than segments)
p.rect('alternatives', 'lower',  0.2, 0.01, source = source,line_color="black")
p.rect('alternatives', 'upper',  0.2, 0.01,source = source, line_color="black")


p.circle('outx', 'outy', source = source_outlier, size=6, color="#F38630", fill_alpha=0.6)

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = "white"
p.grid.grid_line_width = 2
p.xaxis.major_label_text_font_size="12pt"

output_file("boxplot.html", title="boxplot.py example")

show(p)


 