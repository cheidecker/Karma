# -*- coding: utf8 -*-
import datetime
import itertools

import logging
logging.basicConfig(level=logging.INFO)

from Karma.PostProcessing.Palisade import ContextValue, LiteralString, PlotProcessor, AnalyzeProcessor

from Karma.PostProcessing.Lumberjack.cfg.zjet_excalibur import SPLITTINGS, QUANTITIES
from Karma.PostProcessing.Palisade.cfg.zjet_excalibur import EXPANSIONS

from matplotlib.font_manager import FontProperties


def build_expression(quantity_name):
    """
    :param quantity_name:
    :return:

    convenience function for putting together paths in input ROOT file
    """
    return '"data:{{zpt[name]}}/{{eta[name]}}/{0}"'.format(quantity_name)


LOOKUP_CHANNEL_LABEL = {
    'mm': r'Z$\rightarrow\mathrm{{\bf \mu\mu}}$',
    'ee': r'Z$\rightarrow\mathrm{{\bf ee}}$',
}


def get_config(channel, sample_name, jec_name, run_periods, quantities, corr_level, colors, basename, output_format,
               root):
    """
    :param channel:
    :param sample_name:
    :param jec_name:
    :param run_periods:
    :param quantities:
    :param corr_level:
    :param colors:
    :param basename:
    :param output_format:
    :param root:
    :return:

    creates palisade config
    """

    # -- construct list of input files and correction level expansion dicts
    _input_files = dict()
    _input_files['data'] = "{basename}/{basename}_Z{channel}_{sample_name}_{jec_name}_{corr_level}.root".format(
        channel=channel,
        basename=basename,
        sample_name=sample_name,
        jec_name=jec_name,
        corr_level=corr_level
    )

    alpha_min, alpha_max = SPLITTINGS['alpha_exclusive']['alpha_all']['alpha']
    eta_min, eta_max = SPLITTINGS['eta_jer']['absEta_all']['absjet1eta']
    zpt_min = min([_v["zpt"][0] for _k, _v in SPLITTINGS['zpt_jer'].iteritems() if _k is not "zpt_gt_30"])
    zpt_max = max([_v["zpt"][1] for _k, _v in SPLITTINGS['zpt_jer'].iteritems() if _k is not "zpt_gt_30"])

    _expansions = {
        'zpt': [
            dict(name="zpt_gt_30", label=dict(zpt=(30, 100000)))
        ],
        'eta': [
            dict(name="absEta_all", label=dict(absjet1eta=(0, 5.191)))
        ],
    }

    # Used Eta and pT binning extracted by key defined in SPLITTINGS
    eta_binning_name = "eta_jer"
    zpt_binning_name = "zpt_jer"

    # append '[name]' to format keys that correspond to above expansion keys
    output_format = output_format.format(
        basename=basename,
        channel=channel,
        sample=sample_name,
        jec=jec_name,
        corr_level=corr_level,
        dependency='{dependency}',
        # for replacing with definitions in _expansions:
        **{_expansion_key: "{{{0}[name]}}".format(_expansion_key) for _expansion_key in _expansions.keys()}
    )

    if run_periods is None or quantities is None or colors is None:
        pass

    return_value = {
        'input_files': _input_files,
        'expansions': _expansions
    }

    if not root:
        return_value.update({
            'input_files': _input_files,
            'figures': [
                {
                    # Eta dependency
                    'filename': output_format.format(dependency='eta_dependency_{}'.format(_zpt_bin)),
                    'subplots': [
                        #  Eta dependency for MC
                        {
                            'expression': "histogram_from_linear_extrapolation([{hist_list}], [{bins_list}], "
                                          "{alpha_min}, {alpha_max})".format(
                                hist_list=", ".join(["quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend='"data:{zpt}/{eta}/ptbalance-mc"'.format(zpt=_zpt_bin, eta=_k),
                                    subtrahend=', '.join(['"data:{zpt}/{eta}/pli-mc"'.format(zpt=_zpt_bin, eta=_k),
                                                          '"data:{zpt}/{eta}/zres-mc"'.format(zpt=_zpt_bin, eta=_k)
                                                          ]))
                                    for _k in SPLITTINGS[eta_binning_name]
                                    if _k is not "absEta_all"
                                    ]),
                                bins_list=", ".join(["[{}, {}]".format(_v["absjet1eta"][0], _v["absjet1eta"][1])
                                    for _k, _v in SPLITTINGS[eta_binning_name].iteritems()
                                    if _k is not "absEta_all"
                                    ]),
                                alpha_min="{}".format(alpha_min),
                                alpha_max="{}".format(alpha_max),
                            ),
                            'label': r'JER extracted from MC',
                            'plot_method': 'errorbar',
                            'color': 'red',
                            'marker': "o",
                            'marker_style': "full",
                            'pad': 0
                        }
                    ] + [
                        #  Eta dependency for data
                        {
                            'expression': "histogram_from_linear_extrapolation([{hist_list}], [{bins_list}], "
                                          "{alpha_min}, {alpha_max})".format(
                                hist_list=", ".join(["quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend='"data:{zpt}/{eta}/ptbalance-data"'.format(zpt=_zpt_bin, eta=_k),
                                    subtrahend=', '.join(['"data:{zpt}/{eta}/pli-mc"'.format(zpt=_zpt_bin, eta=_k),
                                                          '"data:{zpt}/{eta}/zres-mc"'.format(zpt=_zpt_bin, eta=_k)
                                                          ]))
                                    for _k in SPLITTINGS[eta_binning_name]
                                    if _k is not "absEta_all"
                                ]),
                                bins_list=", ".join(["[{}, {}]".format(_v["absjet1eta"][0], _v["absjet1eta"][1])
                                    for _k, _v in SPLITTINGS[eta_binning_name].iteritems()
                                    if _k is not "absEta_all"
                                    ]),
                                alpha_min="{}".format(alpha_min),
                                alpha_max="{}".format(alpha_max),
                            ),
                            'label': r'JER extracted from data',
                            'plot_method': 'errorbar',
                            'color': 'black',
                            'marker': "o",
                            'marker_style': "full",
                            'pad': 0
                        }
                    ] + [
                        #  Eta dependency for MC JER generated
                        {
                            'expression': "histogram_from_linear_extrapolation([{hist_list}], [{bins_list}], "
                                          "{alpha_min}, {alpha_max})".format(
                                hist_list=", ".join(["{minuend}".format(
                                    minuend='"data:{zpt}/{eta}/jer-gen-mc"'.format(zpt=_zpt_bin, eta=_k))
                                    for _k in SPLITTINGS[eta_binning_name]
                                    if _k is not "absEta_all"
                                ]),
                                bins_list=", ".join(["[{}, {}]".format(_v["absjet1eta"][0], _v["absjet1eta"][1])
                                    for _k, _v in SPLITTINGS[eta_binning_name].iteritems()
                                    if _k is not "absEta_all"
                                    ]),
                                alpha_min="{}".format(alpha_min),
                                alpha_max="{}".format(alpha_max),
                            ),
                            'label': r'generated JER from MC',
                            'plot_method': 'errorbar',
                            'color': 'orange',
                            'marker': "o",
                            'marker_style': "full",
                            'pad': 0
                        }
                    ] + [
                        #  Eta dependency ratio plot Data/MC
                        {
                            'expression': "histogram_from_linear_extrapolation([{hist_list}], [{bins_list}], "
                                          "{alpha_min}, {alpha_max})/histogram_from_linear_extrapolation("
                                          "[{hist_list2}], [{bins_list}], {alpha_min}, {alpha_max})".format(
                                hist_list=", ".join(["quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend='"data:{zpt}/{eta}/ptbalance-data"'.format(zpt=_zpt_bin, eta=_k),
                                    subtrahend=', '.join(['"data:{zpt}/{eta}/pli-mc"'.format(zpt=_zpt_bin, eta=_k),
                                                          '"data:{zpt}/{eta}/zres-mc"'.format(zpt=_zpt_bin, eta=_k)
                                                          ]))
                                        for _k in SPLITTINGS[eta_binning_name]
                                        if _k is not "absEta_all"
                                    ]),
                                hist_list2=", ".join(["quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend='"data:{zpt}/{eta}/ptbalance-mc"'.format(zpt=_zpt_bin, eta=_k),
                                    subtrahend=', '.join(['"data:{zpt}/{eta}/pli-mc"'.format(zpt=_zpt_bin, eta=_k),
                                                          '"data:{zpt}/{eta}/zres-mc"'.format(zpt=_zpt_bin, eta=_k)
                                                          ]))
                                    for _k in SPLITTINGS[eta_binning_name]
                                    if _k is not "absEta_all"
                                    ]),
                                bins_list=", ".join(["[{}, {}]".format(_v["absjet1eta"][0], _v["absjet1eta"][1])
                                    for _k, _v in SPLITTINGS[eta_binning_name].iteritems()
                                    if _k is not "absEta_all"
                                    ]),
                                alpha_min="{}".format(alpha_min),
                                alpha_max="{}".format(alpha_max),
                            ),
                            'label': r'JER extracted data/MC',
                            'plot_method': 'errorbar',
                            'color': 'black',
                            'marker': "o",
                            'marker_style': "full",
                            'pad': 1
                        }
                    ] + [
                        #  Eta dependency ratio plot gen/reco
                        {
                            'expression': "histogram_from_linear_extrapolation([{hist_list}], [{bins_list}], "
                                          "{alpha_min}, {alpha_max})/histogram_from_linear_extrapolation("
                                          "[{hist_list2}], [{bins_list}], {alpha_min}, {alpha_max})".format(
                                hist_list=", ".join(["{minuend}".format(
                                    minuend='"data:{zpt}/{eta}/jer-gen-mc"'.format(zpt=_zpt_bin, eta=_k))
                                        for _k in SPLITTINGS[eta_binning_name]
                                        if _k is not "absEta_all"
                                    ]),
                                hist_list2=", ".join(["quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend='"data:{zpt}/{eta}/ptbalance-mc"'.format(zpt=_zpt_bin, eta=_k),
                                    subtrahend=', '.join(['"data:{zpt}/{eta}/pli-mc"'.format(zpt=_zpt_bin, eta=_k),
                                                          '"data:{zpt}/{eta}/zres-mc"'.format(zpt=_zpt_bin, eta=_k)
                                                          ]))
                                    for _k in SPLITTINGS[eta_binning_name]
                                    if _k is not "absEta_all"
                                    ]),
                                bins_list=", ".join(["[{}, {}]".format(_v["absjet1eta"][0], _v["absjet1eta"][1])
                                    for _k, _v in SPLITTINGS[eta_binning_name].iteritems()
                                    if _k is not "absEta_all"
                                    ]),
                                alpha_min="{}".format(alpha_min),
                                alpha_max="{}".format(alpha_max),
                            ),
                            'label': r'JER generated/extracted',
                            'plot_method': 'errorbar',
                            'color': 'orange',
                            'marker': "o",
                            'marker_style': "full",
                            'pad': 1
                        }
                    ],
                    'pad_spec': {
                        'right': 0.95,
                        'bottom': 0.15,
                        'top': 0.925,
                        'hspace': 0.075,
                    },
                    'pads': [
                        # top pad
                        {
                            'height_share': 3,
                            'x_range': [eta_min, eta_max],
                            'x_scale': 'linear',
                            'y_label': 'JER',
                            'y_range': (0., 0.3),
                            'x_ticklabels': [],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper left'),
                        },
                        # ratio pad
                        {
                            'height_share': 1,
                            'x_label': r'$\eta^\mathrm{{\bf jet1}}$',
                            'x_range': [eta_min, eta_max],
                            'x_scale': 'linear',
                            'y_label': 'Ratio',
                            'y_range': (0.7, 1.3),
                            'axhlines': [dict(values=[1.0])],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='lower right'),
                        },
                    ],
                    'texts': [
                        dict(xy=(.04, 1.015), text=LOOKUP_CHANNEL_LABEL.get(channel, channel), transform='axes',
                             fontproperties=FontProperties(
                                 weight='bold',
                                 family='Nimbus Sans',
                                 size=16,
                             )),
                    ],
                    'upper_label': jec_name,
                } for _zpt_bin in SPLITTINGS[zpt_binning_name]
                # Loop over all zpt bins and create eta dependency plot for each entry.
                # "_zpt_bin" is zpt bin used for one eta dependency plot
                # ("zpt_gt_30" includes all zpt bins -> full zpt range)
            ] + [
                {
                    # Zpt dependency
                    'filename': output_format.format(dependency='zpt_dependency_{}'.format(_eta_bin)),
                    'subplots': [
                        #  Zpt dependency for MC
                        {
                            'expression': "histogram_from_linear_extrapolation([{hist_list}], [{bins_list}], "
                                          "{alpha_min}, {alpha_max})".format(
                                hist_list=", ".join(["quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend='"data:{zpt}/{eta}/ptbalance-mc"'.format(zpt=_k, eta=_eta_bin),
                                    subtrahend=', '.join(['"data:{zpt}/{eta}/pli-mc"'.format(zpt=_k, eta=_eta_bin),
                                                          '"data:{zpt}/{eta}/zres-mc"'.format(zpt=_k, eta=_eta_bin)
                                                          ]))
                                    for _k in SPLITTINGS[zpt_binning_name]
                                    if _k is not "zpt_gt_30"
                                    ]),
                                bins_list=", ".join(["[{}, {}]".format(_v["zpt"][0], _v["zpt"][1])
                                     for _k, _v in SPLITTINGS[zpt_binning_name].iteritems()
                                     if _k is not "zpt_gt_30"
                                     ]),
                                alpha_min="{}".format(alpha_min),
                                alpha_max="{}".format(alpha_max),
                            ),
                            'label': r'JER extracted from MC',
                            'plot_method': 'errorbar',
                            'color': 'red',
                            'marker': "o",
                            'marker_style': "full",
                            'pad': 0
                        }
                    ] + [
                        #  Zpt dependency for data
                        {
                            'expression': "histogram_from_linear_extrapolation([{hist_list}], [{bins_list}], "
                                          "{alpha_min}, {alpha_max})".format(
                                hist_list=", ".join(["quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend='"data:{zpt}/{eta}/ptbalance-data"'.format(zpt=_k, eta=_eta_bin),
                                    subtrahend=', '.join(['"data:{zpt}/{eta}/pli-mc"'.format(zpt=_k, eta=_eta_bin),
                                                          '"data:{zpt}/{eta}/zres-mc"'.format(zpt=_k, eta=_eta_bin)
                                                          ]))
                                    for _k in SPLITTINGS[zpt_binning_name]
                                    if _k is not "zpt_gt_30"
                                    ]),
                                bins_list=", ".join(["[{}, {}]".format(_v["zpt"][0], _v["zpt"][1])
                                     for _k, _v in SPLITTINGS[zpt_binning_name].iteritems()
                                     if _k is not "zpt_gt_30"
                                     ]),
                                alpha_min="{}".format(alpha_min),
                                alpha_max="{}".format(alpha_max),
                            ),
                            'label': r'JER extracted from data',
                            'plot_method': 'errorbar',
                            'color': 'black',
                            'marker': "o",
                            'marker_style': "full",
                            'pad': 0
                        }
                    ] + [
                        #  Zpt dependency for MC JER generated
                        {
                            'expression': "histogram_from_linear_extrapolation([{hist_list}], [{bins_list}], "
                                          "{alpha_min}, {alpha_max})".format(
                                hist_list=", ".join(["{minuend}".format(
                                    minuend='"data:{zpt}/{eta}/jer-gen-mc"'.format(zpt=_k, eta=_eta_bin))
                                    for _k in SPLITTINGS[zpt_binning_name]
                                    if _k is not "zpt_gt_30"
                                    ]),
                                bins_list=", ".join(["[{}, {}]".format(_v["zpt"][0], _v["zpt"][1])
                                     for _k, _v in SPLITTINGS[zpt_binning_name].iteritems()
                                     if _k is not "zpt_gt_30"
                                     ]),
                                alpha_min="{}".format(alpha_min),
                                alpha_max="{}".format(alpha_max),
                            ),
                            'label': r'generated JER from MC',
                            'plot_method': 'errorbar',
                            'color': 'orange',
                            'marker': "o",
                            'marker_style': "full",
                            'pad': 0
                        }
                    ] + [
                        #  Zpt dependency ratio plot Data/MC
                        {
                            'expression': "histogram_from_linear_extrapolation([{hist_list}], [{bins_list}], "
                                          "{alpha_min}, {alpha_max})/histogram_from_linear_extrapolation("
                                          "[{hist_list2}], [{bins_list}], {alpha_min}, {alpha_max})".format(
                                hist_list=", ".join(["quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend='"data:{zpt}/{eta}/ptbalance-data"'.format(zpt=_k, eta=_eta_bin),
                                    subtrahend=', '.join(['"data:{zpt}/{eta}/pli-mc"'.format(zpt=_k, eta=_eta_bin),
                                                          '"data:{zpt}/{eta}/zres-mc"'.format(zpt=_k, eta=_eta_bin)
                                                          ]))
                                    for _k in SPLITTINGS[zpt_binning_name]
                                    if _k is not "zpt_gt_30"
                                    ]),
                                hist_list2=", ".join(["quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend='"data:{zpt}/{eta}/ptbalance-mc"'.format(zpt=_k,eta=_eta_bin),
                                    subtrahend=', '.join(['"data:{zpt}/{eta}/pli-mc"'.format(zpt=_k, eta=_eta_bin),
                                                          '"data:{zpt}/{eta}/zres-mc"'.format(zpt=_k, eta=_eta_bin)
                                                          ]))
                                    for _k in SPLITTINGS[zpt_binning_name]
                                    if _k is not "zpt_gt_30"
                                    ]),
                                bins_list=", ".join(["[{}, {}]".format(_v["zpt"][0], _v["zpt"][1])
                                     for _k, _v in SPLITTINGS[zpt_binning_name].iteritems()
                                     if _k is not "zpt_gt_30"
                                     ]),
                                alpha_min="{}".format(alpha_min),
                                alpha_max="{}".format(alpha_max),
                            ),
                            'label': r'JER extracted data/MC',
                            'plot_method': 'errorbar',
                            'color': 'black',
                            'marker': "o",
                            'marker_style': "full",
                            'pad': 1
                        }
                    ] + [
                        #  Zpt dependency ratio plot gen/reco
                        {
                            'expression': "histogram_from_linear_extrapolation([{hist_list}], [{bins_list}], "
                                          "{alpha_min}, {alpha_max})/histogram_from_linear_extrapolation("
                                          "[{hist_list2}], [{bins_list}], {alpha_min}, {alpha_max})".format(
                                hist_list=", ".join(["{minuend}".format(
                                    minuend='"data:{zpt}/{eta}/jer-gen-mc"'.format(zpt=_k, eta=_eta_bin))
                                    for _k in SPLITTINGS[zpt_binning_name]
                                    if _k is not "zpt_gt_30"
                                    ]),
                                hist_list2=", ".join(["quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend='"data:{zpt}/{eta}/ptbalance-mc"'.format(zpt=_k, eta=_eta_bin),
                                    subtrahend=', '.join(['"data:{zpt}/{eta}/pli-mc"'.format(zpt=_k, eta=_eta_bin),
                                                          '"data:{zpt}/{eta}/zres-mc"'.format(zpt=_k, eta=_eta_bin)
                                                          ]))
                                    for _k in SPLITTINGS[zpt_binning_name]
                                    if _k is not "zpt_gt_30"
                                    ]),
                                bins_list=", ".join(["[{}, {}]".format(_v["zpt"][0], _v["zpt"][1])
                                     for _k, _v in SPLITTINGS[zpt_binning_name].iteritems()
                                     if _k is not "zpt_gt_30"
                                     ]),
                                alpha_min="{}".format(alpha_min),
                                alpha_max="{}".format(alpha_max),
                            ),
                            'label': r'JER generated/extracted',
                            'plot_method': 'errorbar',
                            'color': 'orange',
                            'marker': "o",
                            'marker_style': "full",
                            'pad': 1
                        }
                    ],
                    'pad_spec': {
                        'right': 0.95,
                        'bottom': 0.15,
                        'top': 0.925,
                        'hspace': 0.075,
                    },
                    'pads': [
                        # top pad
                        {
                            'height_share': 3,
                            'x_range': [zpt_min, zpt_max],
                            'x_scale': 'log',
                            'y_label': 'JER',
                            'y_range': (0., 0.3),
                            'x_ticklabels': [],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper right'),
                        },
                        # ratio pad
                        {
                            'height_share': 1,
                            'x_label': r'$\bf p_\mathrm{{\bf T}}^\mathrm{{\bf Z}}$',
                            'x_range': [zpt_min, zpt_max],
                            'x_scale': 'log',
                            'y_label': 'Ratio',
                            'y_range': (0.7, 1.3),
                            'axhlines': [dict(values=[1.0])],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='lower right'),
                        },
                    ],
                    'texts': [
                        dict(xy=(.04, 1.015), text=LOOKUP_CHANNEL_LABEL.get(channel, channel), transform='axes',
                             fontproperties=FontProperties(
                                 weight='bold',
                                 family='Nimbus Sans',
                                 size=16,
                             )),
                    ],
                    'upper_label': jec_name,
                } for _eta_bin in SPLITTINGS[eta_binning_name]
                # Loop over all eta bins and create zpt dependency plot for each entry.
                # "_eta_bin" is eta bin used for one zpt dependency plot
                # ("absEta_all" includes all eta bins -> full eta region)

            ],
        })
    else:
        return_value.update({
            'input_files': _input_files,
            'tasks': [
                {
                    'filename': output_format.format(dependency='dependency'),
                    'subtasks': [
                        #  Eta dependency
                        {
                            'expression': "histogram_from_linear_extrapolation([{hist_list}], [{bins_list}], "
                                          "{alpha_min}, {alpha_max})".format(
                                hist_list=", ".join(["quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend='"data:{zpt}/{eta}/ptbalance-mc"'.format(zpt=_zpt_bin, eta=_k),
                                    subtrahend=', '.join(['"data:{zpt}/{eta}/pli-mc"'.format(zpt=_zpt_bin, eta=_k),
                                                          '"data:{zpt}/{eta}/zres-mc"'.format(zpt=_zpt_bin, eta=_k)
                                                          ]))
                                    for _k in SPLITTINGS[eta_binning_name]
                                    if _k is not "absEta_all"
                                    ]),
                                bins_list=", ".join(["[{}, {}]".format(_v["absjet1eta"][0], _v["absjet1eta"][1])
                                    for _k, _v in SPLITTINGS[eta_binning_name].iteritems()
                                    if _k is not "absEta_all"
                                    ]),
                                alpha_min="{}".format(alpha_min),
                                alpha_max="{}".format(alpha_max)
                                ),
                            'output_path': 'jer_extracted_mc_eta_dependency_{}'.format(_zpt_bin)
                        } for _zpt_bin in SPLITTINGS[zpt_binning_name]
                        # Loop over all zpt bins and create eta dependency plot for each entry.
                        # "_zpt_bin" is zpt bin used for one eta dependency plot
                        # ("zpt_gt_30" includes all zpt bins -> full zpt range)
                    ] + [
                        #  pT dependency
                        {
                            'expression': "histogram_from_linear_extrapolation([{hist_list}], [{bins_list}], "
                                          "{alpha_min}, {alpha_max})".format(
                                hist_list=", ".join(["quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend='"data:{zpt}/{eta}/ptbalance-mc"'.format(zpt=_k, eta=_eta_bin),
                                    subtrahend=', '.join(['"data:{zpt}/{eta}/pli-mc"'.format(zpt=_k, eta=_eta_bin),
                                                          '"data:{zpt}/{eta}/zres-mc"'.format(zpt=_k, eta=_eta_bin)
                                                          ]))
                                    for _k in SPLITTINGS[zpt_binning_name]
                                    if _k is not "zpt_gt_30"
                                    ]),
                                bins_list=", ".join(["[{}, {}]".format(_v["zpt"][0], _v["zpt"][1])
                                    for _k, _v in SPLITTINGS[zpt_binning_name].iteritems()
                                    if _k is not "zpt_gt_30"
                                    ]),
                                alpha_min="{}".format(alpha_min),
                                alpha_max="{}".format(alpha_max)
                                ),
                            'output_path': 'jer_extracted_mc_zpt_dependency_{}'.format(_zpt_bin)
                        } for _eta_bin in SPLITTINGS[eta_binning_name]
                        # Loop over all eta bins and create zpt dependency plot for each entry.
                        # "_eta_bin" is eta bin used for one zpt dependency plot
                        # ("absEta_all" includes all eta bins -> full eta region)
                    ],
                },
            ],
        })
    return return_value


def cli(argument_parser):
    """
    :param argument_parser: general argument parser to add arguments
    :return:

    command-line interface. builds on an existing `argparse.ArgumentParser` instance.
    """

    # define CLI arguments
    argument_parser.add_argument('-s', '--sample', help="name of the sample, e.g. '17Sep2018'", required=True)
    argument_parser.add_argument('-j', '--jec', help="name of the JEC, e.g. 'Autumn18_JECV5'", required=True)
    argument_parser.add_argument('-r', '--run-periods', help="names of the run periods, e.g. 'Run2018A'", required=True,
                                 nargs='+')
    argument_parser.add_argument('-c', '--channels', help="name of the JEC, e.g. 'Autumn18_JECV5'", nargs='+',
                                 default=['mm', 'ee'], choices=['mm', 'ee'], metavar="CHANNEL")
    argument_parser.add_argument('-l', '--corr-level', help="name of JEC correction level to include, e.g. 'L1L2L3'",
                                 choices=['L1', 'L1L2L3', 'L1L2L3Res', 'L1L2Res'], metavar="CORR_LEVEL")
    argument_parser.add_argument('-q', '--quantities', help="quantities to plot", nargs='+',
                                 choices=['ptbalance-data', 'ptbalance-mc', 'pli-mc', 'zres-mc', 'jer-gen-mc'],
                                 metavar="QUANTITY")
    argument_parser.add_argument('-f', '--colors', help="colors of quantities to plot", nargs='+', metavar="COLOR")
    argument_parser.add_argument('--basename', help="prefix of ROOT files containing histograms", required=True)
    # optional parameters
    argument_parser.add_argument('--output-format', help="format string indicating full path to output plot",
                                 default='{basename}_Z{channel}_{jec}_{sample}_{corr_level}_{dependency}.pdf')
    argument_parser.add_argument('--root', help="Switch output to root files instead of plots ", dest='root',
                                 action='store_true')


def run(args):
    """
    :param args: arguments specified in function cli
    :return:

    function for starting processing
    """

    from Karma.PostProcessing.Palisade.cfg.zjet_excalibur.jer_definitions import *

    if args.output_dir is None:
        args.output_dir = "plots_{}".format(datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f"))

    for channel in args.channels:
        print("Making plots for channel '{}'...".format(channel))
        _cfg = get_config(
            channel=channel,
            sample_name=args.sample,
            jec_name=args.jec,
            corr_level=args.corr_level,
            run_periods=args.run_periods,
            quantities=(args.quantities if args.quantities else ['ptbalance-data', 'ptbalance-mc', 'pli-mc', 'zres-mc',
                                                                 'jer-gen-mc']),
            colors=(args.colors if args.colors else ['grey', 'royalblue', 'springgreen', 'forestgreen', 'orange']),
            basename=args.basename,
            output_format=(args.output_format if not args.root else
                           '{basename}_Z{channel}_{jec}_{sample}_{corr_level}_{dependency}.root'),
            root=(args.root if args.root else False)
        )
        if args.root:
            p = AnalyzeProcessor(_cfg, output_folder=args.output_dir)
        else:
            p = PlotProcessor(_cfg, output_folder=args.output_dir)
        p.run()
