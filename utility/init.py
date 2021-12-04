# Some constants
base_dir = "./"
data_dir = base_dir + "datasets/"
emr_infection_data = data_dir + "EMR_prepared.csv"

de_reference_data = data_dir + "de_ref_cal.csv"
nl_reference_data = data_dir + "nl_ref_cal.csv"
be_reference_data = data_dir + "be_ref_cal.csv"


incident_window_size = 7
change_rate_window_size = 7

timeframe_start = '2020-03-15'
timeframe_end = '2021-11-15'


province_id = {
    'Belgium': 10,
    'Liege, Belgium': 11,
    'Limburg, Belgium': 12,
    'Netherlands':20,
    'Limburg, Netherlands':20,
    'Germany': 30,
    'StädteRegion Aachen':31,
    'LK Düren':32,
    'LK Heinsberg':33,
    'LK Euskirchen':34
}

# inhabitants
province_size = {
    10: 0,          # BE total
    11: 1109800,
    12: 877370,
    20: 1115895,
    30: 0,          # DE total
    31: 556631,
    32: 265140,
    33: 256458,
    34: 194359
}

for key, val in province_size.items():
    if key < 20:
        province_size[10] += val
    if key > 30:
        province_size[30] += val

class_colors = {
    10: 'xkcd:dark blue',
    11: 'xkcd:blue',
    12: 'xkcd:light blue',
    20:'xkcd:red',
    30: 'xkcd:sea green' ,
    31:'xkcd:aqua',
    32:'xkcd:teal',
    33:'xkcd:green',
    34:'xkcd:dark green' 
    }

# emr_cols = ['Date', 'Province_Id', 'Daily_Total', 'Daily_100k', 'N_Day_Rate','N_Day_Rate_Change','N_Day_Rate_Change_Sliding_Window']

# ref_cols = ['Date', 'Province_Id', 'Work_Commute_Allowed', 'Leisure_Travel_Allowed', 'Holiday', 'Vacation']