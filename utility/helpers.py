
def addDateTypeColumn(df, colName='XDate'):
    from datetime import datetime as dt

    dfc = df.copy()
    dfc[colName] = dfc.apply(lambda x: dt.strptime(x['Date'],"%Y-%m-%d"), axis=1)
    return dfc

def addDayOffStreaks(df,ax = None, streakLabel='Off days'):
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

    labeled = False

    for idx, streak in dfc.iterrows():
        end = streak['XDate']
        start = end - timedelta(days = streak['streak_counter'])
        if labeled:
            if ax is None:
                plt.axvspan(start,end, facecolor='grey', alpha=0.5)
            else:
                ax.axvspan(start,end, facecolor='grey', alpha=0.5)
        else:
            if ax is None:
                plt.axvspan(start,end, facecolor='grey', alpha=0.5, label=streakLabel)
            else:
                ax.axvspan(start,end, facecolor='grey', alpha=0.5, label=streakLabel)
            labeled = True

def addDayOffStreaksToAx(df, ax):
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
        ax.axvspan(start,end, facecolor='grey', alpha=0.5)
        
def addProvince(df, provinceId, ax=None):
    import pandas as pd
    import numpy as np

    import matplotlib.pyplot as plt
    import utility.init as util

    x = df.loc[df['Province_Id']== provinceId, 'XDate']
    y = df.loc[df['Province_Id']== provinceId, 'N_Day_Rate_Change_Sliding_Window']
    if ax is None:
        plt.xlabel( util.timeframe_start + " - " + util.timeframe_end ,fontdict=util.font)
        plt.ylabel( str(util.incident_window_size)+"-day infection rate change (sliding window)" ,fontdict=util.font)
        plt.plot(x,y, label = util.class_labels[provinceId], color = util.class_colors[provinceId])
    else:
        xlabel =  str(util.timeframe_start + " - " + util.timeframe_end)
        ylabel = str(util.incident_window_size)+"-day infection rate change (sliding window)"
        ax.plot(x,y, label = util.class_labels[provinceId], color = util.class_colors[provinceId])
        ax.set_xlabel(xlabel, fontdict=util.font)
        ax.set_ylabel(ylabel, fontdict=util.font)

def sketchGraph(df, provinces, refDf = None, streakLabel='Off days', offDayStreak=False, offDayFactor = False):
    import matplotlib.pyplot as plt

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    if refDf is not None and offDayStreak:
        addDayOffStreaks(refDf, streakLabel=streakLabel, ax=ax1)

    for prov in provinces:
        addProvince(df, prov, ax=ax1)
    
    if refDf is not None and offDayFactor:
        x = refDf['XDate']
        y = refDf['OffDayFactor']
        ax2.plot(x,y, color='xkcd:maroon', label="Vacation weight factor", linewidth=3)

    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

    plt.legend()
    plt.show()


def cutToTimeframe(df, start='2020-06-15', end='2020-09-01'):
    df_c = df.copy()
    df_c = df_c.loc[df_c['Date'] >= start]
    df_c = df_c.loc[df_c['Date'] <= end]
    return df_c