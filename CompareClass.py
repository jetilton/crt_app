# -*- coding: utf-8 -*-

"""
Need to make a function to make calls easily
"""
"""
Created on Sun Dec 11 14:32:02 2016

@author: Jeff Tilton 503.808.3970 jeffrey.p.tilton@usace.army.mil
"""
import pandas as pd
import sqlite3
import glob
import itertools
from itertools import cycle
from scipy.interpolate import interp1d
import sys
import plotTools
from scipy.stats.mstats import plotting_positions 
import os
from plotTools import acePlot
from bokeh.plotting import show, output_file
import numpy as np
##load external data
#data for interpolating damage
dataHistoric = pd.read_csv(r"X:\CRT2014\PDT\WAT\FRA-Results\Dataprocessing_tools\Post Processing Scripts - R and Python\TiltonPython\data\flowDamageData.csv")
#data for location->reach
ccpData = pd.DataFrame(pd.read_table(r"X:\CRT2014\PDT\WAT\FRA-Results\Dataprocessing_tools\Post Processing Scripts - R and Python\TiltonPython\data\damage_ccp_classifications.txt"))

#Curent forecast data
forecastData = pd.DataFrame(pd.read_csv(r"X:\CRT2014\PDT\WAT\FRA-Results\Dataprocessing_tools\Post Processing Scripts - R and Python\TiltonPython\data\forecast.csv"))[['EVENT', 'FCST.VOL']]
forecastData['PROB'] = plotting_positions(forecastData['FCST.VOL'],0,0)
fcstVol = dict(zip(forecastData['EVENT'],forecastData['FCST.VOL']))
fcstProb = dict(zip(forecastData['EVENT'],forecastData['PROB']))


def returnForecastDist(fileLoc, forecastFileName):
   forecast = pd.DataFrame(pd.read_csv(os.path.join(fileLoc, forecastFileName)))
   forecast = forecast[['EVENT', 'FCST.VOL']]
   forecast['PROB'] = plotting_positions(forecast['FCST.VOL'],0,0)
   return forecast


ex = "SELECT Path_ID, Part_A, Part_B, Part_C, Part_D, Part_E, Part_F, Label FROM master_plot WHERE "
paramDict = {    'maxOutFlow':      {'execute':ex +  "(instr(Part_B, 'OUT') OR instr(Part_C, 'OUT')) AND Part_D ='SAMPLED BY MAX - APR-JUL';", 'value': 'CFS_ace_data'},
                 'poolElevation':   {'execute':ex +  "(instr(Part_B, 'POOL') OR instr(Part_D, 'POOL')) AND Part_D = 'SAMPLED BY DATES - OCT-SEP' AND Part_C = 'ELEV'AND (instr(Part_F, 'F1') OR instr(Part_F, 'FLOOD'));", 'value': 'Elevation_ace_data' },
                 'poolMaxElevation':{'execute':ex +  "(instr(Part_B, 'POOL') OR instr(Part_D, 'POOL')) AND Part_D = 'SAMPLED BY MAX - JAN-JUL' AND Part_C = 'ELEV'AND (instr(Part_F, 'F1') OR instr(Part_F, 'FLOOD'));", 'value': 'Elevation_ace_data' },
                 'poolStorage':     {'execute':ex +  "(instr(Part_B, 'POOL') OR instr(Part_D, 'POOL')) AND Part_D = 'SAMPLED BY DATES - OCT-SEP' AND Part_C = 'STOR' AND (instr(Part_F, 'F1') OR instr(Part_F, 'FLOOD'));",'value':'Acre_Feet_ace_data'},
                 'poolMaxStorage':  {'execute':ex +  "(instr(Part_B, 'POOL') OR instr(Part_D, 'POOL')) AND Part_D = 'SAMPLED BY MAX - JAN-JUL' AND Part_C = 'STOR' AND (instr(Part_F, 'F1') OR instr(Part_F, 'FLOOD'));" , 'value': 'Acre_Feet_ace_data'},
                 'maxFlow':         {'execute':ex +  "Part_C = 'FLOW' AND Part_D = 'SAMPLED BY MAX - APR-JUL'", 'value': 'CFS_ace_data'},
                 'customCall' :     {'execute':'empty','value' : 'empty'}
}    

maxDraft = pd.DataFrame({'Part_B':  [u'DUNCAN-POOL', u'HUNGRY HORSE-POOL', u'MICA-POOL', u'ARROW LAKES-POOL', u'BROWNLEE-POOL', u'DWORSHAK-POOL', u'LIBBY-POOL', u'GRAND COULEE-POOL'], 
                         'ac_ft': [1420892,3468000,20075500,7327300,1420101,3468000,5869953,5349560]})
def dbScrape(db, param):
    """
    Function that pullls data from a compiled database.  The param 
    dictionary can be used to create additional executions to add to the func
    """
   
    parameters = paramDict[param]
    conn = sqlite3.connect(db) 
    c = conn.cursor()
    c.execute("PRAGMA database_list;")
    alternative = str(c.fetchall()[0][2].split('\\')[3])
    c.execute(parameters['execute'])
    data = c.fetchall()
    data = pd.DataFrame.from_records(data, columns = ['Path_ID', 'Part_A', 'Part_B', 'Part_C', 'Part_D', 'Part_E', 'Part_F', 'Label']) 
    myDF = pd.DataFrame()
    i = 0
    for path in data['Path_ID']:
        c.execute("SELECT Value_Array FROM master_plot_data WHERE Path_ID =" +  str(path) + ";")
        df = [x[0].encode('UTF8').split(',') for x in c.fetchall()[1:12]]
        df = list(itertools.chain.from_iterable(df))
        df = pd.DataFrame({parameters['value']:[float(x) for x in df]})
        df['Part_A'] = str(data.iloc[i]['Part_A'])
        df['Part_B'] = str(data.iloc[i]['Part_B'])
        df['Part_C'] = str(data.iloc[i]['Part_C'])
        df['Part_D'] = str(data.iloc[i]['Part_D'])
        df['Part_E'] = str(data.iloc[i]['Part_E'])
        df['Part_F'] = str(data.iloc[i]['Part_F'])
        df['Label']  = str(data.iloc[i]['Label'])
        df['Alternative'] = alternative
        df = df.reindex(columns = ['Alternative','Part_A','Part_B','Part_C', 'Part_D', 'Part_E', 'Part_F', 'Label',parameters['value'] ])
        myDF = myDF.append(df)
        i += 1     
    return myDF

def cdFunc(df, baseline = 0 ):
        """
        Helper function to be used in the cumulative damage method
        multiple times takes in self.damage and returns cumulative damage table
        """
        df = pd.DataFrame(df.groupby(['Alternative','Event'], as_index=False)['Damage'].sum())
        df['forecastVolume_MAF'] =  df['Event'].map(fcstVol)/1000
        df['forecastProbability'] =  df['Event'].map(fcstProb)
        df = df.groupby('Alternative',as_index=False).apply(lambda df: df.sort_values('forecastProbability')).reset_index(drop=True)
        df['cumulativeDamage_milDol'] = df.groupby('Alternative',as_index=False).Damage.cumsum()/1000000 
        
        if baseline !=0:
            
            newDF = pd.DataFrame()
            base = df[(df.Alternative == baseline)].reset_index(drop = True)
            df = df[(df.Alternative != baseline)].reset_index(drop = True)
            for alt in list(set(df['Alternative'])):
                d = df[(df.Alternative == alt )].reset_index(drop = True).copy()
                d['diffBwCumAndBase_milDol'] = d['cumulativeDamage_milDol'] - base['cumulativeDamage_milDol']
                d['baseDamage_milDol'] = base['Damage']/1000000
                
                newDF = newDF.append(d)   
            df = newDF.copy()   
        return df  
        
class altCompare:
    
    def __init__(self, directory):
        self.dbFiles = glob.glob(directory + r'\*.db')
        self.alternatives =  [x.split("\\")[-1] for x in self.dbFiles]
        self.paramList = paramDict.keys() 
        
        self.dfList = []
        for key in paramDict.keys():
            self.key = pd.DataFrame()
            self.dfList.append(self.key)
        
        self.dfDict = dict(zip(self.paramList, self.dfList))
        dictUpdate = {'poolDraft': pd.DataFrame(), 'poolMaxDraft': pd.DataFrame(), 'damage': pd.DataFrame()}
        self.dfDict.update(dictUpdate)
        
    def dbGrab(self, param):
        """
        Method that compiles databases' data into single pd df
        """
        for alt in self.dbFiles:
            self.dfDict[param] = self.dfDict[param].append(dbScrape(alt, param), ignore_index = True)
        return self.dfDict[param].copy()
    
    def customCall(self, call, value):
        """
        function that allows a custom function call
        """
        paramDict['customCall']['value'] = value
        paramDict['customCall']['execute'] = ex + call
        param = 'customCall'
        self.dbGrab(param)
        return self.dfDict['customCall'].copy()
    
    def storage(self, Max = True):
        if Max:
            param ='poolMaxStorage'
        else:
            param = 'poolStorage'
        if len(self.dfDict[param]) < 5000:
            self.dbGrab(param)
        return self.dfDict[param].copy()
    
    def elevation(self, Max = True):
        if Max:
            param ='poolMaxElevation'
        else:
            param = 'poolElevation'
        if len(self.dfDict[param]) < 5000:
            self.dbGrab(param)
        return self.dfDict[param].copy()
    
    def maxOutFlow(self):
        param = 'maxOutFlow'
        if len(self.dfDict[param]) < 5000:
            self.dbGrab(param)
        return self.dfDict[param].copy()

    def flow(self):
        param = 'maxFlow'
        if len(self.dfDict[param]) < 5000:
            self.dbGrab(param)
        return self.dfDict[param].copy()
        
    def draft(self, Max = True):
        if Max:
            param = 'poolMaxStorage'
            paramDraft = 'poolMaxDraft'
        else:
            param = 'poolStorage'
            paramDraft = 'poolDraft'
        if len(self.dfDict[param]) < 5000:
            df= self.dbGrab(param)
        else:
            df = self.dfDict[param]
        y_data_column = [col for col in df.columns if '_ace_data' in col][0]
        i = 0
        ##I don't like this for loop, should be made more pythonic
        for b in maxDraft['Part_B']:
            draft =  maxDraft[(maxDraft.Part_B == b)].loc[i,'ac_ft']
            data = df.groupby('Part_B').get_group(b).copy()
            data['MAF'] = (draft - data[y_data_column])/1000000 
            i += 1
            self.dfDict[paramDraft] = self.dfDict[paramDraft].append(data, ignore_index = True)
        return self.dfDict[paramDraft].copy()
    
    def damage(self):
        """
        Method that returns the flow df with the associated reach, event and damage columns
        """
        param = 'damage'
        
        ##check if damage df is alread full return flow df if not 
        if len(self.dfDict[param]) < 5000:
            print 'This may take awhile'
            df = self.flow()
        else:
            return self.dfDict[param].copy()

        ##get a list of all the loactions within the historic dataset
        dCols = list(dataHistoric.columns)
        wordList = [' Year', ' FLOW', ' DAMAGE']
        for word in wordList:
            dCols = [t.replace(word, '') for t in dCols]   
        dCols = list(set(dCols))
        dCols.sort()
        
        ##filter flow data by the areas in the historical dataset
        newFlowData = pd.DataFrame()    
        for loc in dCols:
            newFlowData = newFlowData.append(df[(df.Part_B == loc)], ignore_index = True)
        locs = list(set(newFlowData['Part_B']))
        locs.sort()
        
        ##There is a Yakima model that shows up in some runs, want to filter that out as well 
        ##(done in the collection flows, but I was told we use the Yakima model), unsure of what is right
        fPart = [f for f in list(set(newFlowData['Part_F'])) if 'YAKIMA' in f]
        if len(fPart) > 0:
            grouped = newFlowData.groupby(['Part_F'])
        for f in fPart:
            newFlowData = newFlowData.drop(grouped.get_group(f).index)      
        
         ##Check to see that there are 5000 events at each location per alternative, if not throw error   
        try:     
            if len(newFlowData)/(len(locs)*len(set(newFlowData['Alternative']))) != 5000:
                raise ValueError
        except ValueError:
            print 'There are not 5000 events associated within all alternative locations'
            sys.exit(1)
        
        ##Interpolate the damage using flow values and historical dataset
        for loc in locs:
            intrpTbl = dataHistoric.filter(like = loc)
            x = intrpTbl.filter(like = 'FLOW').values.squeeze()
            y = intrpTbl.filter(like = 'DAMAGE').values.squeeze()
            myDF = df.groupby('Part_B').get_group(loc).copy()
            myDF['damCFS'] = myDF['CFS_ace_data']               ###Some of the cfs is out of the range of the data to interpolate.  
            myDF.loc[myDF.damCFS>max(x), 'damCFS'] = max(x)     ###This is how I took care of it, but do not know if this is the right approach
            myDF.loc[myDF.damCFS<min(x), 'damCFS'] = min(x)     ###
            interp = interp1d(x, y)
            myDF['Damage'] = myDF['damCFS'].apply(interp)
            self.dfDict[param] = self.dfDict[param].append(myDF, ignore_index = True)
            
        ##Add the reach and events columns
        ccpData.columns = ['Part_B', 'RIVER_SYS', 'CONTROL_PROJ', 'REACH']    
        self.dfDict[param] = pd.merge(left = self.dfDict[param], right = ccpData, how = 'left', on='Part_B')
        events =  cycle(range(1,5001,1))
        self.dfDict[param]['Event'] =[next(events) for count in range(self.dfDict[param].shape[0])]
        self.dfDict[param] = self.dfDict[param].reindex(columns = ['Alternative','Part_B', 'Part_D', 'Part_E', 'Part_F', 'Label', 'CONTROL_PROJ', 'RIVER_SYS', 'REACH','Event', 'CFS', 'damCFS', 'Damage'])
        
        ##Add forecast volume and probability from the forecast data
        self.dfDict[param]['forecastVolume_MAF'] =  self.dfDict[param]['Event'].map(fcstVol)/1000
        self.dfDict[param]['forecastProbability'] =  self.dfDict[param]['Event'].map(fcstProb)
        
        
        return self.dfDict[param].copy()
        
    
    def cumDamage(self, baseline = 0):
        """
        Method that returns dictionary of two cumulative damage plots
        one by total the other by reach. the cumulative damage compared to a baseline, needs alternative to use as baseline
        """
        df = self.damage()
            
        ##Cumulative damage by event for all reaches
        df1 = cdFunc(df, baseline)
        
        ##Cumulative damage by event by reach
        df2 = pd.DataFrame()
        
        for reach in list(set(df['REACH'])):
            r = df[(df.REACH==reach)].reset_index(drop = True).copy()
            r = cdFunc(r, baseline)
            r['reach']=reach
            df2 = df2.append(r)
             
        return {'cumulativeDamage':df1,'cumulativeDamageByReach':df2}  

    def damageCompare(self, baseline):
        """
        Method that returns a dataframe of the max difference and mean difference between alternatives and baseline 
        damages by reach and forecast probability
        """
        df = self.damage()[self.damage().Part_F.str.contains('YAKIMA')==False].copy()
        df = df[['Alternative', 'Part_B', 'Part_D', 'REACH', 'Event', 'Damage', 'forecastProbability']]
        
        alts = df[(df.Alternative != baseline)].reset_index(drop = True)
        baseline = df[(df.Alternative == baseline)].reset_index(drop = True).copy()

        newDF = pd.DataFrame()
        for alt in list(set(alts['Alternative'])):
            d = alts[(alts.Alternative==alt)].copy()
            d['baselineDamage'] = baseline['Damage'].copy()
            newDF = newDF.append(d) 
        newDF['DiffBwAltAndBaseDamage_milDol'] = (newDF['Damage'] - newDF['baselineDamage'])/1000000
        newDF['baselineDamage_milDol']= newDF['baselineDamage']/1000000
        

        df = newDF.groupby(['Alternative', 'REACH', 'forecastProbability'], as_index = False).DiffBwAltAndBaseDamage_milDol.max().copy()
        
        df = df.rename(columns = {'DiffBwAltAndBaseDamage_milDol':'maxDiff_milDol'})
        
        df['meanDiff_milDol'] = newDF.groupby(['Alternative', 'REACH', 'forecastProbability'], as_index = False).DiffBwAltAndBaseDamage_milDol.mean()['DiffBwAltAndBaseDamage_milDol'].copy()
        df['meanBaseDamage_milDol'] = newDF.groupby(['Alternative', 'REACH', 'forecastProbability'], as_index = False).baselineDamage_milDol.mean()['baselineDamage_milDol'].copy()
        df['percentChange'] = df['meanDiff_milDol']/df['meanBaseDamage_milDol'] * 100
        return df

    def cumDamPlot(self, xData = 'forecastVolume_MAF', title = 'title', baseline = False,  save_directory = False):
                 
        df = self.cumDamage(baseline)['cumulativeDamage']
        alts = list(set(df['Alternative']))
        
        if baseline == False:
            yData =  'cumulativeDamage_milDol'
            yAxis = 'Damage (Millions of Dollars)'
        else:
            yData = 'diffBwCumAndBase_milDol'
            yAxis = 'Alternative - Baseline, (Damages Millions of $)'
        p = plotTools.damPlot(df, alts, title,xData,xAxis = 'TDA fcst (MAF)', yData= yData, yAxis = yAxis, scatterWidth = 1600, scatterHeight = 500)
        if save_directory != False:
            plotTitle = title.split(' ')
            fileName = '_'.join(plotTitle)
            output_file(os.path.join(save_directory, fileName + '.html'), title=title +' Plots', mode='cdn', root_dir=None)
        show(p)
        return p

    def cumDamPlotByReach(self, baseline = 0, save_directory = False):
        
        df = self.cumDamage(baseline)
        dfAll = df['cumulativeDamage']
        dfReach = df['cumulativeDamageByReach']

        if baseline == 0:
            yData = 'cumulativeDamage_milDol'
        else:
            yData = 'diffBwCumAndBase_milDol'
        pList = plotTools.plotByReach(dfReach,dfAll,yData)
        if save_directory != False:
            i = 1
            for p in pList:
                fileName = 'cumDamPlotByReach_'+str(i)
                output_file(os.path.join(save_directory, fileName + '.html'), title='CumulativeDamagePlotByReach', mode='cdn', root_dir=None)
                i+=1
        for p in pList:
            show(p)
        return pList
            
    def ace(self, data_type, location, plot_title, Max = True, plot_width = 1000, plot_height = 500, save_directory = False):
        data_type_dict = {'maxOutFlow':self.maxOutFlow(),
                          'flow':self.flow(),
                          'poolElevation':self.elevation(Max = Max),
                          'draft':self.draft(Max = Max),
                          'storage': self.storage(Max = Max)}
        df = data_type_dict[data_type]
        if Max != True:
            df = df[(df.Label == u'dates 30Apr')].reset_index()
        df = df[df.Part_B.str.contains(location.upper())]
        alternatives = pd.Series(df.Alternative.copy())
        df.loc[:,'alts']= alternatives.str.replace('_[^_]*Collected.*', '').str.replace('_', ' ')
        y_data_column = [col for col in df.columns if '_ace_data' in col]
        y_data_column = y_data_column[0]
        if df[y_data_column].median()>1000000:
            new_label = 'Million_'+y_data_column
            df[new_label]=df[y_data_column]/1000000
            y_data_column = new_label
        y_axis_title = y_data_column.replace('_ace_data', '').replace('_',' ')
        p = acePlot(df, alternative='alts', y_Data = y_data_column, xAxis= 'A.C.E [%]', yAxis = y_axis_title, title = plot_title, width = plot_width, height = plot_height)
        if save_directory != False:
            loc = location.split(' ')
            plotTitle = plot_title.split(' ')
            fileName = loc + plotTitle
            fileName = '_'.join(fileName)
            output_file(os.path.join(save_directory, fileName + '.html'), title=location +' Plots', mode='cdn', root_dir=None)
        
        return p
        
        
        
