import flask
from flask import Flask, render_template, request, jsonify
import json

import pyromat as pm
from pyrowrapper import pyrocalc_mp1 as calc

from numpy_encoder import NumpyArrayEncoder

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


def encodelist(datalist):
    return [encodedict(item) for item in datalist]

def encodedict(datadict):
    return {k: datadict[k].tolist() for k in datadict}


@app.route('/critical', methods=['POST'])
def get_info():
    json_data = request.get_json()
    subst = pm.get('mp.'+json_data['subst'])
    data = calc.compute_critical(subst)

    return json.dumps(data, cls=NumpyArrayEncoder)


@app.route('/steam_dome', methods=['POST'])
def steam_dome():
    json_data = request.get_json()
    subst = pm.get('mp.'+json_data['subst'])
    data = calc.compute_steamdome(subst)

    return json.dumps(data, cls=NumpyArrayEncoder)


@app.route('/isobars', methods=['GET', 'POST'])
def isobars():
    if request.method == 'GET':
        args = dict(request.args)
        subst = pm.get('mp.'+args['id'])
    elif request.method == 'POST':
        json_data = request.get_json()
        subst = pm.get('mp.'+json_data['subst'])
    ps = calc.get_default_lines(subst, 'p', scaling='log')
    data = []
    for p in ps:
        try:
            data.append(calc.compute_iso_line(subst, p=p))
        except pm.utility.PMParamError:
            pass
    if request.method == 'POST':
        return json.dumps(data, cls=NumpyArrayEncoder)
    else:
        outdata = {
            'id': args['id'],
            'data': encodelist(data)
        }
        return outdata

@app.route('/isobars_get', methods=['GET'])
def isobars_get():
    args = dict(request.args)
    subst = pm.get('mp.'+args['id'])
    ps = calc.get_default_lines(subst, 'p', scaling='log')
    data = []
    for p in ps:
        try:
            data.append(calc.compute_iso_line(subst, p=p))
        except pm.utility.PMParamError:
            pass
    outdata = {
        'id': args['id'],
        'data': encodelist(data)
    }
    return outdata


@app.route('/point', methods=['POST'])
def point():
    json_data = request.get_json()
    subst = pm.get('mp.'+json_data['subst'])

    props = json_data['props']

    try:
        data = calc.compute_state(subst, **props)
        return json.dumps(data, cls=NumpyArrayEncoder)
    except pm.utility.PMParamError as e:
        try:
            errdata = {'message': str(e).split(":")[1].strip(),}
        except:
            errdata = {'message': str(e),}
        return json.dumps(errdata), 500


@app.route('/getunits')
def getunits():
    length = list(pm.units.length.get())
    pressure = list(pm.units.pressure.get())
    data = {'length': length,
            'pressure': pressure}
    return json.dumps(data)


@app.route('/')
def index():  # put application's code here
    substs = pm.info('mp', verbose=False)
    substs = [i.split('.')[1] for i in substs]
    return render_template('substance.html', subst_list=substs)


if __name__ == '__main__':
    app.run()
