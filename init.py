

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
    'LK Euskirchen':34,
    'Euregio Maas-Rhine': 40
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
    34: 194359,
    40: 0           # EMR total
}

for key, val in province_size.items():
    if key < 20:
        province_size[10] += val
    if key > 30 and key < 40:
        province_size[30] += val

province_size[40] = province_size[10]+province_size[20]+province_size[30]

class_colors = {
    10: 'xkcd:dark blue',
    11: 'xkcd:blue',
    12: 'xkcd:light blue',
    20: 'xkcd:red',
    30: 'xkcd:dark green' ,
    31: 'xkcd:aqua',
    32: 'xkcd:teal',
    33: 'xkcd:green',
    34: 'xkcd:sea green',
    40: 'xkcd:eggplant'
}

class_labels = {
    10: 'Belgium',
    11: 'Liege, BE',
    12: 'Limburg, BE',
    20: 'Netherlands',
    30: 'Germany',
    31: 'StädteRegion Aachen, DE',
    32: 'LK Düren, DE',
    33: 'LK Heinsberg, DE',
    34: 'LK Euskirchen, DE',
    40: 'Euregio Maas-Rhine'
}

font = {#'family': 'serif',
        'color':  'black',
        'weight': 'normal',
        'fontsize': 'small'
        }