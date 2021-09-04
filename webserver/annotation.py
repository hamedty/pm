import json
import glob
import os

WEB_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.dirname(WEB_PATH)
SERVER_PATH = os.path.join(BASE_PATH, 'server')
VISION_PATH = os.path.join(SERVER_PATH, 'vision')
DATASET_PATH = os.path.join(BASE_PATH, 'dataset_old')
MODELS_PATH = os.path.join(BASE_PATH, 'models')

SRC_DATA = os.path.join(VISION_PATH, 'annotaion.json')
DST_DATA = os.path.join(MODELS_PATH, 'annotaion.json')


def load_data():
    with open(SRC_DATA) as f:
        data = json.loads(f.read())
    return data


def save_data():
    global data_saved_json
    data_json = json.dumps(data, sort_keys=True, indent=4)
    if data_saved_json != data_json:
        data_saved_json = data_json
        with open(SRC_DATA, 'w') as f:
            f.write(data_saved_json)


def list_all():
    l = glob.glob(DATASET_PATH + '/*_*')
    l = [tuple(i.split('/')[-1].split('_')[:-1]) for i in l]
    for component, node, dataset_name in l:
        if node not in data:
            data[node] = {
                'dosing': {},
                'dosing_roi': {'dx': 270, 'dy': 192, 'x0': 305, 'y0': 141},
                'holder': {},
                'holder_roi': {'dx': 177, 'dy': 167, 'x0': 228, 'y0': 191},
            }
        if dataset_name not in data[node][component]:
            data[node][component][dataset_name] = {}
    for node in data:
        for component in ['holder', 'dosing']:
            dels = []
            for dataset_name in data[node][component]:
                if tuple([component, node, dataset_name]) not in l:
                    dels.append(dataset_name)
            for key in dels:
                del data[node][component][key]
    save_data()


data = load_data()
data_saved_json = ''
list_all()


def get(component, station):
    return {
        'sets': data[station][component],
        'roi': data[station][component + '_roi'],
    }


def post(component, station, data_in):
    data_in = json.loads(data_in.decode("utf-8"))
    print(data_in)
    data[station][component] = data_in
    save_data()
    return get(component, station)
