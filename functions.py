# -*- coding: utf-8 -*-
import pandas as pd
from scipy.stats.mstats import plotting_positions
from CompareClass import altCompare
import os


## databases  directory

directory = r'D:\crt\data'
run_name = 'test_run'
def func(df, x):
    df['plotting_positions'] = (1- plotting_positions(df[x], 0, 0)) *100
    return df


def data_to_csv(df, data_column_name, file_name, run_name):
    df = df.groupby(['alternative','location'] ,as_index=False).apply(func, data_column_name)
    df = df.groupby(['alternative','location'],as_index=False).apply(lambda df: df.sort_values('plotting_positions', ascending = False))
    df.reset_index(drop = True, inplace = True)
    file_name = os.path.join('data', run_name, file_name + '.csv')
    df.to_csv(file_name)


##Create instance of class altCompare 
compData = altCompare(directory)

##Gather data
poolDraft = compData.draft(Max = False)
poolMaxDraft = compData.draft()
poolStorage = compData.storage(Max = False)
poolMaxStorage = compData.storage()
poolMaxStorage['MAF'] = poolMaxStorage['Acre_Feet_ace_data']/1000000
poolElevation = compData.elevation(Max = False)
poolMaxElevation = compData.elevation()
poolMaxElevation.rename(columns={'Elevation_ace_data':'Elevation'}, inplace=True) 
maxOutFlow = compData.maxOutFlow()

##For data sampled by dates filter April 30th data
poolStorage = poolStorage[(poolStorage.Label == u'dates 30Apr')].reset_index()
poolStorage['MAF'] = poolStorage['Acre_Feet_ace_data']/1000000
poolElevation = poolElevation[(poolElevation.Label == u'dates 30Apr')].reset_index()
poolElevation.rename(columns={'Elevation_ace_data':'Elevation'}, inplace=True)    
poolDraft = poolDraft[(poolDraft.Label == u'dates 30Apr')].reset_index()
maxOutFlow['kcfs'] = maxOutFlow['CFS_ace_data']/1000

maxOutFlow.name = 'maxOutFlow'
poolStorage.name = 'poolStorage'
poolMaxStorage.name = 'poolMaxStorage'
poolElevation.name = 'poolElevation'
poolMaxElevation.name = 'poolMaxElevation'
poolDraft.name = 'poolDraft' 
poolMaxDraft.name = 'poolMaxDraft'



df_list = [(poolDraft,'MAF', '-POOL'),(poolMaxDraft, 'MAF', '-POOL'),(poolStorage,'MAF', '-POOL'),
           (poolMaxStorage,'MAF', '-POOL'),(poolElevation,'Elevation', '-POOL'),(poolMaxElevation,'Elevation','-POOL'),
           (maxOutFlow, 'kcfs','_OUT')]

for toop in df_list:
    df = toop[0]
    data_column_name = toop[1]
    location_split = toop[2]
    file_name = df.name
    run_name = run_name
    df['alternative'] = df.Alternative.str.replace('_[^_]*Collected.*', '').str.replace('_', ' ')
    df = pd.DataFrame({
                        'alternative':df.alternative, 
                        'location':df.Part_B, 
                        data_column_name:df[data_column_name]
                       })
    df['location'] = [x.split(location_split)[0] for x in df['location']]
    data_to_csv(df, data_column_name, file_name, run_name)