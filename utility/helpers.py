
def addDateTypeColumn(df, colName='XDate'):
    from datetime import datetime as dt

    dfc = df.copy()
    dfc[colName] = dfc.apply(lambda x: dt.strptime(x['Date'],"%Y-%m-%d"), axis=1)
    return dfc

def addDayOffStreaks(df, legLabel='Off days'):
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
            plt.axvspan(start,end, facecolor='grey', alpha=0.5)
        else:
            plt.axvspan(start,end, facecolor='grey', alpha=0.5, label=legLabel)
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
        
def addProvince(df, provinceId):
    import pandas as pd
    import numpy as np

    import matplotlib.pyplot as plt
    import utility.init as util

    x = df.loc[df['Province_Id']== provinceId, 'XDate']
    y = df.loc[df['Province_Id']== provinceId, 'N_Day_Rate_Change_Sliding_Window']
    plt.xlabel( util.timeframe_start + " - " + util.timeframe_end ,fontdict=util.font)
    plt.ylabel( str(util.incident_window_size)+"-day infection rate change (sliding window)" ,fontdict=util.font)
    plt.plot(x,y, label = util.class_labels[provinceId], color = util.class_colors[provinceId])

def sketchGraph(df, provinces, ref_df, legLabel='Off days'):
    import matplotlib.pyplot as plt

    for prov in provinces:
        addProvince(df, prov)
    
    addDayOffStreaks(ref_df, legLabel)
    plt.legend()
    plt.show()