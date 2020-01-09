import time
import os
import ast
import json
import plotly.graph_objects as go
import numpy as np
import plotly.io as pio
pio.renderers.default='browser'

def matlab_serializer(val):
    _t = val.base_class
    try:
        _val = val.matlab_type(val.to_matlab())
    except TypeError:
        # grr why is None not coercible to 0
        _val = 0
    if val.is_boolean:
        _val = str(bool(_val)).lower()
    else:
        _val = _val.__repr__()
    try:
        return _t(_val)
    except ValueError:
        return _val
    except TypeError:
        return 0

def print_vals(*vals):
    def _wrapped(func):
        return func
    return _wrapped


def write_to_mat2(d, visible_params):
    lines = []
    print(f"Write to mat called")
    lines.append(f"NumSamples = {d.num_samples.value};")
    for k,v in d.items():
        print(f"Value of {k} is {v}")
        name = k
        if name in visible_params:
            lines.append(f"InterferenceConfig.{v.matlab_alias} = {matlab_serializer(v)};")
    return lines

def write_to_mat(d, visible_params):
    lines = []
    print(f"Write to mat called")
    lines.append(f"NumSamples = {d.num_samples.value};")
    for k,v in d.items():
        print(f"Value of {k} is {v}")
        name = v.name
        if name in visible_params:
            lines.append(f"InterferenceConfig.{v.matlab_alias} = {matlab_serializer(v)};")
    return lines

def load_mat(filepath='/home/kz/share/my_results1575870300.6698883.json', root_key='Results',keys=['input_fig', 'output_fig'], save_to_svg=True):
    print(f'loading {filepath}')
    with open(filepath, 'r') as f:
        mat = json.load(f)['Results']
    figs = []
    os.makedirs("/home/kz/share/images", exist_ok=True)
    if keys:
        for k in keys:
            print(f"Loading {k}")

            arr = np.array(mat[k])
            if save_to_svg:
                try:
                    arr2svg(arr, f"/home/kz/share/images/{k}{time.time()}.svg")
                except Exception as e:
                    print(f"Failed to save svg image: {e.__class__.__name__} :: {e}")
            print(f"generating {k} heatmap")
            fig = go.Figure(data=go.Heatmap(
                z=arr.tolist()))
            # fig.show()
            figs.append(fig)

    else:
        print(f"generating heatmap")
        fig = go.Figure(data=go.Heatmap(z=np.array(mat).tolist()))
        # fig.show()
        figs = [fig]
    return figs


import os
import plotly.graph_objs as go


def arr2svg(arr, output_fp, width=3800, height=1680, scale=2):
    if not isinstance(arr, np.ndarray):
        arr = np.array(arr)
    zmax = arr.max()

    arr = arr.tolist()
    arr = go.Figure(data=go.Heatmap(z=arr, showscale=False, zmin=0, zmax=zmax))
    path, ext = os.path.splitext(output_fp)
    arr.layout.showlegend = False
    arr.layout.margin = {'b': 0, 'l': 0, 'pad': 0, 'r': 0, 't': 0}
    arr.update_xaxes(showticklabels=False)
    arr.update_yaxes(showticklabels=False)
    arr.layout.xaxis = dict(showgrid=False, zeroline=False, showticklabels=False)
    arr.layout.yaxis = dict(showgrid=False, zeroline=False, showticklabels=False)
    img = arr.to_image(format=ext, width=width, height=height, scale=scale)
    with open(output_fp, 'wb') as f:
        f.write(img)
    print(f"Wrote {len(img)} bytes to {output_fp}")
    return output_fp
# def load_mat


