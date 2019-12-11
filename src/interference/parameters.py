import dash_core_components as dcc
import dash_bootstrap_components as dbc

pdata = [
    {"name": "file_type",
     "initial_value":"MAT",
     "constructor": dcc.Dropdown,
     "options": [{"label": k, "value": k} for k in ("MAT", "AWG", "PCAP")],
     "label": "File Type",
     "className": "update_file_path_popover_text",
     "group": "dbc_input_fields"},
    {"name": "file_path",
     "initial_value": '',
     "valid": False,
     "constructor": dbc.Input,
     "className": "validate_file_path",
     "renderer": "labeled_form_group",
     "group": "dbc_input_fields",
     "spellcheck": "false"
     },
    {"name": "interference_type",
     "initial_value": "stepchirp",
     "matlab_alias": "InterferenceType",
     "constructor": dcc.Dropdown,
      "options" : [{'label': k, 'value': k} for k in ("CW", "hop", "chirp", "stepchirp", "randFM")],
      "renderer": "labeled_form_group",
      "className" : "update_interference_options",
     },
    {"name": "num_samples",
     "initial_value": 100000,
     "constructor": dbc.Input,
     "group": "dbc_input_fields",
     "valid": True,
     "className": "validate_param update_param_visibility",
     "matlab_alias": "num_samples",
     "matlab_type": float},
    {"name": "isrdb",
     "constructor": dbc.Input,
     "group": "dbc_input_fields",
     "valid": True,
     "className": "validate_param update_param_visibility",
     "initial_value": 64,
     "matlab_alias": "ISRdB",
     "matlab_type": float},
    {
        "name": "sampling_freq",
        "initial_value": 1e3,
        "valid": True,
        "className": "validate_param update_param_visibility",
        "matlab_alias": "Fs",
        "matlab_type": float,
    },
    {
        "name": "n_steps",
        "initial_value": 5.0 * 128,
        "valid": True,
        "className": "validate_param update_param_visibility",
        "matlab_alias": "Nsteps",
        "matlab_type": float,
    },
    {
        "name": "n_sweeps",
        "initial_value": 128,
        "valid": True,
        "className": "validate_param update_param_visibility",
        "matlab_alias": "Nsweeps",
        "matlab_type": float,
    },
    {
        "name": "steps_per_chirp",
        "initial_value": 1,
        "valid": True,
        "className": "validate_param update_param_visibility",
        "matlab_alias": "Nchirps",
        "matlab_type": float,
        "to_matlab": lambda parameters: parameters.n_sweeps * parameters.steps_per_chirp,
    },
    {
        "name": "n_hops",
        "initial_value": 0,
        "valid": True,
        "className": "validate_param update_param_visibility",
        "matlab_alias": "Nhops",
        "matlab_type": float,
    },
    {
        "name": "bandwidth_denominator",
        "initial_value": 16,
        "valid": True,
        "className": "validate_param update_param_visibility",
        "matlab_alias": "BandwidthDenominator",
        "matlab_type": float,
        "min": 2,
        "tooltip": """the bandwidth over which
             the hop, chirp, or random FM is allowed to span, given as the
             inverse of the proportion to the total available bandwidth.
             The minimum value of 2.0 for real signals indicates the
             interference may span from zero to Fs/2.  The minimum value of
             1.0 for complex baseband signals indicates the interference
             may span from -Fs/2 to Fs/2.  A value of 8.0 would restrict
             the span of the interference to -Fs/16 to Fs/16 for complex,
             or 3*Fs/16 to 5*Fs/16 for real.""",
    },
    {
        "name": "cw_frequency_offset",
        "initial_value": 0,
        "matlab_alias": "CWfreqOffset",
        "valid": True,
        "className": "validate_param update_param_visibility",
        "matlab_type": float,
        "tooltip": """the offset of the frequency of the CW interferer from Fs/4 in the
             case of real samples, or from zero in the case of complex
             samples.""",
    },
    {
        "name": "randfm_moving_average",
        "initial_value": 0,
        "matlab_alias": "RandFMMovingAverage",
        "matlab_type": int,
        "valid": True,
        "className": "validate_param update_param_visibility",
        "tooltip": """a volatility selector for the frequency of the random FM
             interference.  Smaller values make the interferer more volatile
             and larger values make it move around the band more sluggishly.""",
    },
    {
        "name": "randfm_centering",
        "initial_value": 8,
        "matlab_alias": "RandomFMCentering",
        "matlab_type": float,
        "valid": True,
        "className": "validate_param update_param_visibility",
        "tooltip": """centering selector for the frequency of the
             random FM interference, controlling its propensity to move
             closer to the center of the band when out near the edge.
             Smaller values allow it to spend more time out near the edges,
             while larger values cause it to be more strongly mean-
             reverting.  Too-small values could cause it to rail at one
             edge of the band indefinitely, while too-large values could
             cause it to look almost like an on-carrier CW.""",
    },
    {
        "name": "continuous_phase",
        "initial_value": 1,
        "is_bool": True,
        "matlab_alias": "ContinuousPhase",
        "matlab_type": bool,
        "className": "print_boolswitch",
        "tooltip": """ if true, the phase of the interferer is preserved
             from one sample to the next across hops, steps, or chirp resets
             to the opposite side of the band; if false, when the interferer
             hops, steps, or resets to the opposite side of the band, the
             first sample of the new frequency is given a random phase
             unrelated to the last sample of the old frequency, or the
             StartingPhase value, depending on SpecifyStartingPhase.""",

    },
    {
        "name": "random_start_freq",
        "is_bool": True,
        "initial_value": 1,
        "className": "print_boolswitch",
        "matlab_type": bool,
        "matlab_alias": "RandomStartFreq",
        "tooltip": """if true, the first sweep of the chirp will begin
             at a random frequency within the band, sweep to the high edge
             of the band, and then reset to the low edge; if false, the
             first sweep of the chirp will always begin at the low edge of
             the band.""",
    },
    {
        "name": "use_bandpass_data",
        "is_bool": True,
        "initial_value": 0,
        "matlab_type": bool,
        "className": "print_boolswitch",
        "matlab_alias": "UseBandpassData",

    },
    { "name": "submit",
      "constructor": dbc.Button,
      "initial_value": 0,
      "children": "submit",
      "color": "primary",
      "renderer": "button_renderer",
      "block": True,
      "className": "",
      "type": "button",
      "n_clicks" : 0,
      "n_clicks_timestamp": 0,
      "group": "footer"},
    # {"name": "graph_container",
    #  "constructor": html.Div,
    #  "children": [],
    #  "initial_value": None,
    #  "className":
    {"name": "clicks",
     "constructor": dcc.Markdown,
     "children":"",
     "initial_value": "",
     "className": "update_submit_msg",
     "group": "footer"}
]

# p.to_matlab()


    #       ('BandwidthDenominator', 1, False, None, float),
    #       ('CWfreqOffset', 0, False, None, float),
    #       ('Nsweeps', 0, False, None, float),
    #       ('StepsPerChirp', 0, False, None, float),
    #       ('RandomFMMovingAverage', 0, False, None, int),
    #       ('RandomFMCentering', 0, True, None, bool),
    #       ('ContinuousPhase', 0, True, None, bool),
    #       ('RandomStartFreq', 0, True, None, bool),
    #
    #       ('Bandwidth', 0, False, None, None, None, float),
    #       ('DwellTime', 0, False, None, None, None, float),
    #       ('ChirpRate', 0, False, None, None, None, float),
    #       ('MovingAvgLength',  0, False, None, None, None, float),
    #       ('CenteringFactor', 0, False, None, None, None, float),
    #       ('Nchirps', 0, False, None, None, None, float)
# print(parameters)
