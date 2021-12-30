import pandas as pd
import numpy as np
from datetime import datetime as dt, timedelta

import init as util
from helpers import *

emr_cols = ['Date', 'Province_Id', 'Daily_Total', 'Daily_100k', 'N_Day_Rate','N_Day_Rate_Change','N_Day_Rate_Change_Sliding_Window']
ref_cols = ['Date', 'Province_Id', 'Holiday', 'Vacation']

# cumulative total to daily total
def daily_incident_rate(df, totalCol):
    df_c = df.copy()
    for province in df_c['Province_Id'].unique():
        mask = df_c['Province_Id'] == province 
        df_c.loc[mask, 'Daily_Total'] = df_c.loc[mask, totalCol].rolling(2).apply(lambda x : x[1]-x[0], raw=True )
    return df_c


def daily_per_100k(df):
    df_c = df.copy()
    for province in df_c['Province_Id'].unique():
        mask = df_c['Province_Id'] == province 
        df_c.loc[mask, 'Daily_100k'] = (df_c.loc[mask, 'Daily_Total'] / util.province_size[province]) * 100000
    return df_c

def calc_change_factor(window):
    return window[1]/window[0]

# Change rate
def incident_rate_change(df):
    df_c = df.copy()
    for province in df_c['Province_Id'].unique():
        mask = df_c['Province_Id'] == province 
        df_c.loc[mask, 'N_Day_Rate_Change'] = df_c.loc[mask, 'N_Day_Rate'].rolling(2).apply(calc_change_factor, raw=True )
    return df_c

# Add sliding window change rate
def sliding_window_change_rate(df):
    df_c = df.copy()
    for province in df_c['Province_Id'].unique():
        mask = df_c['Province_Id'] == province
        df_c.loc[mask, 'N_Day_Rate_Change_Sliding_Window'] = df_c.loc[mask, 'N_Day_Rate_Change'].rolling(util.change_rate_window_size).mean()
    return df_c

def reIndex(df, fillNan=True):
    df_c = df.copy()
    df_c = addDateTypeColumn(df, colName='Date')
    df_c = df_c.set_index('Date')
    if fillNan:
        df_c = df_c.asfreq('D', fill_value=0)
    else:
        df_c = df_c.asfreq('D')
    df_c = df_c.sort_index()

    return df_c

def loadBelgianData():
    be_provs = ['Liège','Limburg']
    be_df = pd.DataFrame(columns=emr_cols)

    be_raw = pd.read_csv(util.data_dir + 'orig/COVID19BE_CASES_AGESEX.csv', sep=',')
    be_raw = be_raw[be_raw['PROVINCE'].isin(be_provs)]
    be_raw = be_raw[be_raw.DATE.notnull()]
    be_raw.loc[be_raw['PROVINCE']=='Liège','Province_Id'] = 11
    be_raw.loc[be_raw['PROVINCE']=='Limburg','Province_Id'] = 12

    be_raw = be_raw.rename(columns={"DATE":"Date", "CASES": "Daily_Total"})

    be_raw = be_raw.groupby(['Date','Province_Id']).sum().reset_index()
    be_df = be_df.append(be_raw, ignore_index=True)

    be_total = be_raw.groupby(['Date']).sum().reset_index()
    be_total['Province_Id'] = 10
    be_df = be_df.append(be_total, ignore_index=True)
    be_df = be_df.loc[be_df.Province_Id == 10]
    be_df = reIndex(be_df)
    # added days need a new Province_Id
    be_df['Province_Id'] = 10
    return be_df

def loadDutchData():
    nl_provs = ['Limburg']
    nl_df = pd.DataFrame(columns=emr_cols)

    nl_raw = pd.read_csv(util.data_dir + 'orig/COVID-19_aantallen_gemeente_cumulatief.csv', sep=';')
    nl_raw = nl_raw[nl_raw['Province'].isin(nl_provs)]
    nl_raw = nl_raw.rename(columns={"Date_of_report":"Date","Total_reported":"Daily_Total"})
    nl_raw = nl_raw.groupby(['Date']).sum().reset_index()
    nl_raw['Province_Id'] = 20

    nl_raw = daily_incident_rate(nl_raw, 'Daily_Total')
    nl_raw['Date'] = nl_raw['Date'].str[:10]
    nl_raw['Daily_Total'] = nl_raw['Daily_Total'].shift(periods=-1)
    nl_raw = nl_raw[nl_raw.Daily_Total.notnull()]

    nl_df = nl_df.append(nl_raw, ignore_index=True)
    nl_df = reIndex(nl_df)
    # added days need a new Province_Id
    nl_df['Province_Id'] = 20
    return nl_df

def loadGermanData():
    de_df = pd.DataFrame(columns=emr_cols)
    de_raw = pd.read_csv(util.data_dir + 'orig/RKI_COVID19.csv', sep=',')

    de_raw = de_raw[de_raw['Landkreis'].isin(util.province_id.keys())]
    for lk, id in util.province_id.items():
        de_raw.loc[de_raw['Landkreis'] == lk, 'Province_Id'] = id

    de_raw = de_raw.rename(columns={"Refdatum":"Date","AnzahlFall":"Daily_Total"})
    de_raw['Date'] = de_raw['Date'].str[:4] + '-' + de_raw['Date'].str[5:7]+ '-' + de_raw['Date'].str[8:10]

    de_raw = de_raw.groupby(['Date', 'Province_Id']).sum().reset_index()

    de_df = de_df.append(de_raw, ignore_index=True)

    de_total = de_raw.groupby(['Date']).sum().reset_index()
    de_total['Province_Id'] = 30
    de_df = de_df.append(de_total, ignore_index=True)
    de_df = de_df.loc[de_df.Province_Id == 30]
    de_df = reIndex(de_df)
    # added days need a new Province_Id
    de_df['Province_Id'] = 30
    return de_df

def loadEmrData():
    emr_df = pd.DataFrame(columns=emr_cols)

    emr_df = emr_df.append(loadBelgianData().reset_index(), ignore_index=True)
    emr_df = emr_df.append(loadDutchData().reset_index(), ignore_index=True)
    emr_df = emr_df.append(loadGermanData().reset_index(), ignore_index=True)

    emr_df = emr_df.loc[:,:'N_Day_Rate_Change_Sliding_Window']

    # Add EMR total
    emr_total = emr_df.groupby(['Date']).sum().reset_index()
    emr_total['Province_Id'] = 40
    emr_df = emr_df.append(emr_total, ignore_index=True)

    emr_df = emr_df.loc[emr_df['Date'] >= dt.strptime(util.timeframe_start,"%Y-%m-%d")]
    emr_df = emr_df.loc[emr_df['Date'] <= dt.strptime(util.timeframe_end,"%Y-%m-%d")]
    emr_df = emr_df.sort_values(by=['Date', 'Province_Id'])
    
    return emr_df

def prepareData(save=True):
    emr_df = loadEmrData()
    emr_df = emr_df.sort_values(by=['Date'])

    # scale to 100k
    emr_df = daily_per_100k(emr_df)

    # N-Day Rate
    emr_df['N_Day_Rate'] = emr_df['Daily_100k'].rolling(util.incident_window_size).sum()

    # Rate Change
    emr_df = incident_rate_change(emr_df)

    emr_df = sliding_window_change_rate(emr_df)

    if save:
        emr_df.to_csv(util.emr_infection_data)

    return emr_df


def initCal(Province_Id):
    df = pd.DataFrame(columns=ref_cols)
    df['Date'] = pd.date_range(start=util.timeframe_start,end=util.timeframe_end)
    df['Province_Id'] = Province_Id
    # df['Work_Commute_Allowed'] = 1
    # df['Leisure_Travel_Allowed'] = 1
    df['Holiday'] = 0
    df['Vacation'] = 0
    return df

def setRefDates(df, dates, targetColumn, setTo = 1):
    dfc = df.copy()
    for date in dates:
        dfc.loc[df['Date']== date, targetColumn] = setTo

    return dfc

def prepareGermanRefCal():
    de_ref_cal_df = initCal(30)

    de_holidays = {
        '2020-01-01',
        '2020-04-10',
        '2020-04-11', # Added weekend
        '2020-04-12', # Added weekend
        '2020-04-13',
        '2020-05-01',
        '2020-05-02', # Added weekend
        '2020-05-03', # Added weekend
        '2020-05-21',
        '2020-05-22', # Added weekend
        '2020-05-23', # Added weekend
        '2020-05-24', # Added weekend
        '2020-06-01',
        '2020-06-11',
        '2020-06-12', #
        '2020-06-13', #
        '2020-06-14', #
        '2020-10-03',
        '2020-11-01',
        '2020-12-25',
        '2020-12-26',
        '2020-12-27', #
        '2021-01-01',
        '2021-01-02', #
        '2021-01-03', #
        '2021-04-02',
        '2021-04-03', #
        '2021-04-04', #
        '2021-04-05',
        '2021-05-01',
        '2021-05-13',
        '2021-05-14', #
        '2021-05-15', #
        '2021-05-16', #
        '2021-05-22', #
        '2021-05-23', #
        '2021-05-24',
        '2021-06-03',
        '2021-06-04', #
        '2021-06-05', #
        '2021-06-06', #
        '2021-10-03',
        '2021-10-30', #
        '2021-10-31', #
        '2021-11-01',
        '2021-12-25',
        '2021-12-26'
    }

    de_vacation = pd.date_range(start='2020-01-01',end='2020-01-06')
    de_vacation = de_vacation.append(pd.date_range(start='2020-03-14',end='2020-04-19'))
    de_vacation = de_vacation.append(pd.date_range(start='2020-05-30',end='2020-06-02'))
    de_vacation = de_vacation.append(pd.date_range(start='2020-06-27',end='2020-08-11'))
    de_vacation = de_vacation.append(pd.date_range(start='2020-10-10',end='2020-10-25'))
    de_vacation = de_vacation.append(pd.date_range(start='2020-12-16',end='2021-02-21'))
    de_vacation = de_vacation.append(pd.date_range(start='2021-03-27',end='2021-04-11'))
    de_vacation = de_vacation.append(pd.date_range(start='2021-05-22',end='2021-05-25'))
    de_vacation = de_vacation.append(pd.date_range(start='2021-07-03',end='2021-08-17'))
    de_vacation = de_vacation.append(pd.date_range(start='2021-10-09',end='2021-10-24'))
    de_vacation = de_vacation.append(pd.date_range(start='2021-12-24',end='2021-12-31'))

    de_ref_cal_df = setRefDates(de_ref_cal_df, de_holidays, 'Holiday')
    de_ref_cal_df = setRefDates(de_ref_cal_df, de_vacation, 'Vacation')

    return de_ref_cal_df

def prepareDutchRefCal():
    nl_ref_cal_df = initCal(20)

    nl_holidays = {
        '2020-01-01',
        '2020-04-10',
        '2020-04-11', # Added weekend
        '2020-04-12', # Added weekend
        '2020-04-13',
        '2020-05-02', # Added weekend
        '2020-05-03', # Added weekend
        '2020-05-04', #
        '2020-05-05',
        '2020-05-21',
        '2020-05-22', # Added weekend
        '2020-05-23', # Added weekend
        '2020-05-24', # Added weekend
        '2020-06-01',
        '2020-12-25',
        '2020-12-26',
        '2020-12-27', #
        '2021-01-01',
        '2021-01-02', #
        '2021-01-03', #
        '2021-04-02',
        '2021-04-03', #
        '2021-04-04', #
        '2021-04-05',
        '2021-04-24', #
        '2021-04-25', #
        '2021-04-26', #
        '2021-04-27',
        '2021-05-13',
        '2021-05-14', #
        '2021-05-15', #
        '2021-05-16', #
        '2021-05-22', #
        '2021-05-23', #
        '2021-05-24',
        '2021-12-25',
        '2021-12-26'
    }

    nl_vacation = pd.date_range(start='2020-01-01',end='2020-01-05')
    nl_vacation = nl_vacation.append(pd.date_range(start='2020-02-22',end='2020-03-01'))
    nl_vacation = nl_vacation.append(pd.date_range(start='2020-03-14',end='2020-05-03'))
    nl_vacation = nl_vacation.append(pd.date_range(start='2020-05-21',end='2020-05-24'))
    nl_vacation = nl_vacation.append(pd.date_range(start='2020-05-30',end='2020-06-01'))
    nl_vacation = nl_vacation.append(pd.date_range(start='2020-07-01',end='2020-08-31'))
    nl_vacation = nl_vacation.append(pd.date_range(start='2020-10-01',end='2020-11-15'))
    nl_vacation = nl_vacation.append(pd.date_range(start='2020-12-19',end='2021-01-03'))

    nl_vacation = nl_vacation.append(pd.date_range(start='2021-02-13',end='2021-02-21'))
    nl_vacation = nl_vacation.append(pd.date_range(start='2021-04-03',end='2021-04-18'))
    nl_vacation = nl_vacation.append(pd.date_range(start='2021-05-13',end='2021-05-16'))
    nl_vacation = nl_vacation.append(pd.date_range(start='2021-07-01',end='2021-08-31'))
    nl_vacation = nl_vacation.append(pd.date_range(start='2021-10-30',end='2021-11-07'))
    nl_vacation = nl_vacation.append(pd.date_range(start='2021-11-11',end='2021-11-14'))
    nl_vacation = nl_vacation.append(pd.date_range(start='2021-12-25',end='2022-01-09'))

    nl_ref_cal_df = setRefDates(nl_ref_cal_df, nl_holidays, 'Holiday')
    nl_ref_cal_df = setRefDates(nl_ref_cal_df, nl_vacation, 'Vacation')
    return nl_ref_cal_df

def prepareBelgianRefCal():
    be_ref_cal_df = initCal(10)

    be_holidays = {
        '2020-01-01',
        '2020-04-11', # Added weekend
        '2020-04-12', # Added weekend
        '2020-04-13',
        '2020-05-01',
        '2020-05-02', # Added weekend
        '2020-05-03', # Added weekend
        '2020-05-21',
        '2020-05-22', # Added weekend
        '2020-05-23', # Added weekend
        '2020-05-24', # Added weekend
        '2020-05-30', #
        '2020-05-31', #
        '2020-06-01',
        '2020-07-18', #
        '2020-07-19', #
        '2020-07-20', #
        '2020-07-21',
        '2020-11-11',
        '2020-12-25',
        '2020-12-26', #
        '2020-12-27', #
        '2021-01-01',
        '2021-01-02', #
        '2021-01-03', #
        '2021-04-03', #
        '2021-04-04', #
        '2021-04-05',    
        '2021-05-13', 
        '2021-05-14', #
        '2021-05-15', #
        '2021-05-16', #
        '2021-05-22', #
        '2021-05-23', #
        '2021-05-24',
        '2021-07-21',
        '2021-10-30',
        '2021-10-31',
        '2021-11-01',
        '2021-11-11',
        '2021-11-12', #
        '2021-11-13', #
        '2021-11-14', #
        '2021-12-25',
        '2021-12-26',
        '2021-12-27'
    }

    be_vacation = pd.date_range(start='2020-01-01',end='2020-01-05')
    be_vacation = be_vacation.append(pd.date_range(start='2020-02-22',end='2020-03-01'))
    be_vacation = be_vacation.append(pd.date_range(start='2020-03-14',end='2020-05-03'))
    be_vacation = be_vacation.append(pd.date_range(start='2020-05-21',end='2020-05-24'))
    be_vacation = be_vacation.append(pd.date_range(start='2020-07-01',end='2020-08-31'))
    be_vacation = be_vacation.append(pd.date_range(start='2020-10-31',end='2020-11-15'))
    be_vacation = be_vacation.append(pd.date_range(start='2020-12-19',end='2021-01-03'))

    be_vacation = be_vacation.append(pd.date_range(start='2021-02-13',end='2021-02-21'))
    be_vacation = be_vacation.append(pd.date_range(start='2021-04-03',end='2021-04-18'))
    be_vacation = be_vacation.append(pd.date_range(start='2021-05-13',end='2021-05-16'))
    be_vacation = be_vacation.append(pd.date_range(start='2021-07-01',end='2021-08-31'))
    be_vacation = be_vacation.append(pd.date_range(start='2021-10-30',end='2021-11-07'))
    be_vacation = be_vacation.append(pd.date_range(start='2021-12-25',end='2022-01-09'))



    be_ref_cal_df = setRefDates(be_ref_cal_df, be_holidays, 'Holiday')
    be_ref_cal_df = setRefDates(be_ref_cal_df, be_vacation, 'Vacation')
    return be_ref_cal_df

def addVacationWeightFactor(df):
    dfc = df.copy()
    dfc['Day_Off'] = ( dfc['Holiday'] + dfc['Vacation'] ) > 0
    dfc['OffDayFactor'] = dfc['Day_Off'].rolling(14, min_periods=1).apply(lambda x : np.sum(x, dtype=int), raw=True)
    return dfc

def prepareRefCals(save=True):
    be_ref_cal_df = prepareBelgianRefCal()
    de_ref_cal_df = prepareGermanRefCal()
    nl_ref_cal_df = prepareDutchRefCal()

    be_ref_cal_df = addVacationWeightFactor(be_ref_cal_df)
    de_ref_cal_df = addVacationWeightFactor(de_ref_cal_df)
    nl_ref_cal_df = addVacationWeightFactor(nl_ref_cal_df)

    if save:
        de_ref_cal_df.to_csv(util.de_reference_data)
        nl_ref_cal_df.to_csv(util.nl_reference_data)
        be_ref_cal_df.to_csv(util.be_reference_data)

    return be_ref_cal_df, nl_ref_cal_df, de_ref_cal_df