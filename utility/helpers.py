
def addDateTypeColumn(df, colName='XDate'):
    from datetime import datetime as dt

    dfc = df.copy()
    dfc[colName] = dfc.apply(lambda x: dt.strptime(x['Date'],"%Y-%m-%d"), axis=1)
    return dfc

def addDayOffStreaks(df):
    import pandas as pd
    import numpy as np

    import matplotlib.pyplot as plt

    from datetime import datetime as dt, timedelta

    dfc = df.copy()
    dfc['Day_Off'] = ( dfc['Holiday'] + dfc['Vacation'] ) > 0
    dfc['start_of_streak'] = dfc.Day_Off.ne(dfc['Day_Off'].shift())
    dfc['streak_id'] = dfc['start_of_streak'].cumsum()
    dfc['streak_counter'] = dfc.groupby('streak_id').cumcount() + 1
    dfc = dfc.groupby('streak_id').max().reset_index()
    dfc = dfc.loc[dfc['Day_Off']]

    for idx, streak in dfc.iterrows():
        end = streak['XDate']
        start = end - timedelta(days = streak['streak_counter'])
        plt.axvspan(start,end, facecolor='grey', alpha=0.5)