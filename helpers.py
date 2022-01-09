import matplotlib.pyplot as plt

from datetime import datetime as dt, timedelta

import pandas as pd
import numpy as np

import init as util

from sklearn.ensemble import GradientBoostingRegressor

def addDateTypeColumn(df, sourceCol='Date', colName='Date'):
    dfc = df.copy()
    dfc[colName] = dfc.apply(lambda x: dt.strptime(x[sourceCol],"%Y-%m-%d"), axis=1)
    return dfc

def reIndexToDate(df, colName='Date'):
    dfc = df.copy()
    dfc = dfc.set_index('Date')
    dfc = dfc.asfreq('D')
    dfc = dfc.sort_index()
    return dfc

def addDayOffStreaks(df, ax = None, streakLabel='Off days'):
    dfc = df.copy()
    # dfc['OffDay'] = ( dfc['Holiday'] + dfc['Vacation'] ) > 0
    dfc['start_of_streak'] = dfc.OffDay.ne(dfc['OffDay'].shift())
    dfc['streak_id'] = dfc['start_of_streak'].cumsum()
    dfc['streak_counter'] = dfc.groupby('streak_id').cumcount() + 1
    dfc = dfc.groupby('streak_id').max().reset_index()
    dfc = dfc.loc[dfc['OffDay']]

    labeled = False

    for idx, streak in dfc.iterrows():
        end = streak['Date']
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
        
def addProvince(df, provinceId, settings, ax=None):
    x = df.loc[df['Province_Id']== provinceId, 'Date']
    y = df.loc[df['Province_Id']== provinceId, 'NDRC_Sliding_Window']
    if ax is None:
        plt.xlabel( str(settings.timeframe_start) + " - " + str(settings.timeframe_end), fontdict=util.font)
        plt.ylabel( str(settings.incident_window_size)+"-day infection rate change (sliding window)", fontdict=util.font)
        plt.plot(x,y, label = util.class_labels[provinceId], color = util.class_colors[provinceId])
    else:
        xlabel =  str(settings.timeframe_start + " - " + settings.timeframe_end)
        ylabel = str(settings.incident_window_size)+"-day infection rate change (sliding window)"
        ax.plot(x,y, label = util.class_labels[provinceId], color = util.class_colors[provinceId])
        ax.set_xlabel(xlabel, fontdict=util.font)
        ax.set_ylabel(ylabel, fontdict=util.font)

def sketchGraph(df, provinces, settings, refDf = None, streakLabel='Off days', offDayStreak=False, offDayFactor = False):
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    if refDf is not None and offDayStreak:
        addDayOffStreaks(refDf, streakLabel=streakLabel, ax=ax1)

    for prov in provinces:
        addProvince(df, prov, settings, ax=ax1)
    
    if refDf is not None and offDayFactor:
        x = refDf['Date']
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

def loadEmrData(settings):
    emr_df = pd.read_csv(settings.emr_infection_data)
    emr_df = addDateTypeColumn(emr_df,'Date')

    return emr_df
    
def loadRefData(settings):
    de_ref_df = pd.read_csv(settings.de_reference_data)
    nl_ref_df = pd.read_csv(settings.nl_reference_data)
    be_ref_df = pd.read_csv(settings.be_reference_data)

    # add date typ columns
    de_ref_df = addDateTypeColumn(de_ref_df,'Date')
    nl_ref_df = addDateTypeColumn(nl_ref_df,'Date')
    be_ref_df = addDateTypeColumn(be_ref_df,'Date')
    
    return be_ref_df, nl_ref_df, de_ref_df

def prepareDf(base_df, provinceId, mergeDf=None):
    loc_df = base_df.copy()
    loc_df = loc_df.loc[loc_df.Province_Id == provinceId]
    loc_df['NDRC_SW_Yesterday'] = loc_df['NDRC_Sliding_Window'].rolling(2, min_periods=1).apply(lambda x: x[0], raw=True )
    loc_df = loc_df.loc[loc_df.NDRC_SW_Yesterday.notna() & loc_df.NDRC_Sliding_Window.notna()]
    if mergeDf is not None:
        loc_df = pd.merge(loc_df, mergeDf, on='Date', how='left')

    loc_df = loc_df.set_index('Date')
    loc_df = loc_df.asfreq('D')
    loc_df = loc_df.sort_index()

    return loc_df

def recursiveWindowForecast(df, start, end, settings, params = {'learning_rate': 0.075, 'max_depth': 3, 'min_samples_leaf': 10, 'min_samples_split': 2, 'n_estimators': 80, 'subsample': 0.85 }, refDf=None, visualize=True, visualWindow=20):
    startDate = dt.strptime(start,"%Y-%m-%d")
    endDate = dt.strptime(end,"%Y-%m-%d")
    delta = timedelta(days=visualWindow)
    oneDay = timedelta(days=1)

    rec_fk_df = df.copy()

    train, test, train2 = rec_fk_df[:startDate-oneDay] , rec_fk_df[startDate:endDate], rec_fk_df[endDate+oneDay:]

    train= train.append(train2)

    X_train, y_train = train.loc[:, settings.training_columns], train.loc[:,'NDRC_Sliding_Window']
    X_test, y_test = test.loc[:, settings.training_columns], test.loc[:,'NDRC_Sliding_Window']

    gbr = GradientBoostingRegressor( random_state=0, **params)

    gbr.fit(X_train, y_train)
    # gbr.score(X_test, y_test) # R2

    predictions = test.copy()
    NDRC_yest = predictions['NDRC_SW_Yesterday'][0]
    predictions.NDRC_Sliding_Window = np.NAN
    predictions.NDRC_SW_Yesterday = np.NAN

    for idx, row in predictions.iterrows():
        predictions.loc[predictions.index == idx,'NDRC_SW_Yesterday'] = NDRC_yest
        inRow = predictions.loc[predictions.index == idx, settings.training_columns]
        predictions.loc[predictions.index == idx,'NDRC_Sliding_Window'] = NDRC_yest = gbr.predict( np.array(inRow).reshape(1,-1) )

    if visualize:
        fig, ax = plt.subplots()
        timeframe_start = startDate - delta
        timeframe_end = endDate + delta
        train[timeframe_start : timeframe_end].append(test).NDRC_Sliding_Window.plot(ax=ax, label='train')
        test.NDRC_Sliding_Window.plot(ax=ax, label='test')
        predictions.NDRC_Sliding_Window.plot(ax=ax, label='predictions')
        if refDf is not None:
            refDfC = refDf.copy()
            mask = (refDfC.Date > timeframe_start) & (refDfC.Date < timeframe_end)
            addDayOffStreaks(refDfC.loc[mask], ax = ax, streakLabel='Off days')
        ax.legend()

    return predictions

def addToMatrixPlot(df, ax, id, ref_df):
    x = df.loc[df['Province_Id']== id, 'Date']
    y = df.loc[df['Province_Id']== id, 'NDRC_Sliding_Window']
    ax.plot(x, y, color=util.class_colors[id])
    addDayOffStreaks(ref_df, ax)
    ax.set_ylabel(util.class_labels[id])

def scatterInfectionComparison(emr_df, be_ref_df, nl_ref_df, de_ref_df, settings):
    fig, axs = plt.subplots(4,3, sharex=True, sharey=True)

    for id in range(0,4):
        addToMatrixPlot(emr_df, axs[id, 0], (id+1)*10, be_ref_df)
        addToMatrixPlot(emr_df, axs[id, 1], (id+1)*10, nl_ref_df)
        addToMatrixPlot(emr_df, axs[id, 2], (id+1)*10, de_ref_df)

    axs[3, 2].set_xlabel("German off-days")
    axs[3, 1].set_xlabel("Dutch off-days")
    axs[3, 0].set_xlabel("Belgian off-days")

    #for ax in axs.flat:
    #    ax.set(xlabel='x-label', ylabel='y-label')

    # Hide x labels and tick labels for top plots and y ticks for right plots.
    for ax in axs.flat:
        ax.label_outer()
        show = True
        for label in ax.xaxis.get_ticklabels():
            # label is a Text instance
            label.set_rotation(45)
            if not show:
                label.set_visible(False)
                show = True
            else:
                show = False

    fig.suptitle(str(settings.incident_window_size)+"-day infection rate change (sliding window) for " + str(settings.timeframe_start) + " - " + str(settings.timeframe_end))
    plt.show()