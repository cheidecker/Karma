# -*- coding: utf8 -*-
import datetime
import itertools

import logging
logging.basicConfig(level=logging.INFO)

from Karma.PostProcessing.Palisade import ContextValue, LiteralString, PlotProcessor, AnalyzeProcessor

from Karma.PostProcessing.Lumberjack.cfg.zjet_excalibur import SPLITTINGS, QUANTITIES

from matplotlib.font_manager import FontProperties


def build_expression(source_type, alpha_folder, quantity_path):
    """
    :param source_type:
    :param alpha_folder:
    :param quantity_path:
    :return:

    convenience function for putting together paths in input ROOT file
    """
    source_type = source_type.strip().lower()
    assert source_type in ('data', 'mc')
    if source_type == 'data':
        return '"{0}_{{corr_level[{0}]}}:{{zpt[name]}}/{{eta[name]}}/{1}/{2}"'.format(source_type, alpha_folder,
                                                                                      quantity_path)
    elif source_type == 'mc':
        return '"{0}_{{corr_level[{0}]}}:{{zpt[name]}}/{{eta[name]}}/{1}/{2}"'.format(source_type, alpha_folder,
                                                                                      quantity_path)


LOOKUP_MC_CORR_LEVEL = {
    'L1L2Res': 'L1L2L3',
    'L1L2L3Res': 'L1L2L3',
}


LOOKUP_CHANNEL_LABEL = {
    'mm': r'Z$\rightarrow\mathrm{{\bf \mu\mu}}$',
    'ee': r'Z$\rightarrow\mathrm{{\bf ee}}$',
}


def get_config(channel, sample_name, jec_name, run_periods, corr_levels,
               basename_data='CombinationData2018ABC',
               basename_mc='CombinationMC',
               output_format='test.root',
               root=True):
    """
    :param channel:
    :param sample_name:
    :param jec_name:
    :param run_periods:
    :param corr_levels:
    :param basename_data:
    :param basename_mc:
    :param output_format:
    :param root:
    :return:

    creates palisade config
    """

    # -- construct list of input files and correction level expansion dicts
    _input_files = dict()
    _corr_level_dicts = []
    for _cl in corr_levels:
        _input_files['data_{}'.format(_cl)] = "{}_Z{}_{}_{}_{}.root".format(
            basename_data, channel, sample_name, jec_name, _cl
        )

        # MC: lookup sample w/o residuals first
        _cl_for_mc = LOOKUP_MC_CORR_LEVEL.get(_cl, _cl)
        _input_files['mc_{}'.format(_cl)] = _input_files['mc_{}'.format(_cl_for_mc)] = "{}_Z{}_{}_{}_{}.root".format(
            basename_mc, channel, sample_name, jec_name, _cl_for_mc
        )

        _corr_level_dicts.append(
            dict(name=_cl, data=_cl, mc=_cl_for_mc)
        )
    if not root:
        _expansions = {
            'corr_level': _corr_level_dicts,
            'zpt': [
                dict(name="zpt_gt_30", label=dict(zpt=(30, 100000)))
            ],
            'eta': [
                dict(name="absEta_all", label=dict(absjet1eta=(0, 5.191)))
            ],
        }
    else:
        _expansions = {
            'corr_level': _corr_level_dicts,
            'zpt': [
                dict(name=_k, label="zpt_{}_{}".format("{:04d}".format(int(round(_v['zpt'][0]))),
                                                       "{:04d}".format(int(round(_v['zpt'][1])))))
                for _k, _v in SPLITTINGS['zpt'].iteritems()
            ],
            'eta': [
                dict(name=_k, label="eta_{}_{}".format("{:04d}".format(int(round(10*_v['absjet1eta'][0]))),
                                                       "{:04d}".format(int(round(10*_v['absjet1eta'][1])))))
                for _k, _v in SPLITTINGS['eta_wide'].iteritems()
            ],
        }

    # define truncation values for different channels
    _truncation = 98.5 if channel == 'mm' else 90.
    # _truncation = 98.5
    # _truncation_binning = [85., 88, 90, 92., 94., 95., 96., 97., 98., 99, 100., 101.]
    # _truncation_binning = [99., 101.]
    _truncation_binning = [x/2. for x in range(70*2, 100*2, 1)] + [100.]
    _truncation_values = [(_i+_j)/2 for _i, _j in zip(_truncation_binning[:-1], _truncation_binning[1:])]
    _truncation_bins = ["[{}, {}]".format(_i, _j) for _i, _j in zip(_truncation_binning[:-1], _truncation_binning[1:])]

    ratio_range = (0.8, 1.)

    return_value = {
        'input_files': _input_files,
        'expansions': _expansions
    }

    # append '[name]' to format keys that correspond to above expansion keys
    output_format = output_format.format(
        channel=channel,
        sample=sample_name,
        jec=jec_name,
        plot_label='{plot_label}',
        # for replacing with definitions in _expansions:
        **{_expansion_key: "{{{0}[name]}}".format(_expansion_key) for _expansion_key in _expansions.keys()}
    )

    if not root:
        return_value.update({
            'figures': [{
                    'filename': output_format.replace('{plot_label}', 'JER_input_check_{}_{}'.format(_quantity,
                                                                                                     _type)),
                    'subplots': [
                        #
                        dict(
                            expression='{}'.format(build_expression(_type, alpha_folder='alpha_all',
                                                                    quantity_path='h_{}_weight'.format(_quantity))),
                            label=r''.format(_quantity),
                            plot_method='errorbar',
                            color=_color,
                            marker="o",
                            marker_style="full",
                            pad=0
                        )
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
                            'height_share': 1,
                            'x_range': [0., 2.] if _quantity is not 'zres' else [0.9, 1.1],
                            'x_scale': 'linear',
                            'x_label': r'{}'.format(_label),
                            'y_label': r'Events',
                            # 'y_range': (0., 0.3),
                            # 'x_ticklabels': [],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper right'),
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
                } for _quantity, _color, _type, _label in zip(['ptbalance', 'ptbalance', 'zres', 'pli', 'genjer'],
                                                              ['black', 'blue', 'forestgreen', 'springgreen', 'orange'],
                                                              ['data', 'mc', 'mc', 'mc', 'mc'],
                                                              ['p$_\mathrm{{T}}$-balance', 'p$_\mathrm{{T}}$-balance',
                                                               'Z boson momentum resolution',
                                                               'Particle level imbalance (PLI)',
                                                               'generated jet momentum resolution'])
            ] + [
                {
                    'filename': output_format.replace('{plot_label}', 'JER_truncation_scan_ptbalance'),
                    'subplots': [
                        # ptbalance RMS resolution scan
                        dict(
                            expression='truncated_rms_hist([{file_list}], [{x_bins}], {truncation})'.format(
                                file_list=", ".join([build_expression('mc', alpha_folder='alpha_all',
                                                                      quantity_path='h_ptbalance_weight')]),
                                x_bins=", ".join([x_bins]),
                                truncation=_truncation
                                ),
                            label=r'ptbalance RMS',
                            plot_method='errorbar',
                            color='blue',
                            marker="o",
                            marker_style="full",
                            pad=0
                        ) for _truncation, x_bins in zip(_truncation_values, _truncation_bins)
                    ]+[
                        # ptbalance Gaussian resolution scan
                        dict(
                            expression='truncated_gaussian_width_hist([{file_list}], [{x_bins}], '
                                       '{truncation})'.format(
                                file_list=", ".join([build_expression('mc', alpha_folder='alpha_all',
                                                                      quantity_path='h_ptbalance_weight')]),
                                x_bins=", ".join([x_bins]),
                                truncation=_truncation
                                ),
                            label=r'ptbalance Gaussian fit',
                            plot_method='errorbar',
                            color='grey',
                            marker="o",
                            marker_style="full",
                            pad=0
                        ) for _truncation, x_bins in zip(_truncation_values, _truncation_bins)
                    ]+[
                        # ptbalance Ratio plot RMS/Gaussian
                        dict(
                            expression='truncated_rms_hist([{file_list}], [{x_bins}], {truncation})/'
                                       'truncated_gaussian_width_hist([{file_list}], [{x_bins}], '
                                       '{truncation})'.format(
                                file_list=", ".join([build_expression('mc', alpha_folder='alpha_all',
                                                                      quantity_path='h_ptbalance_weight')]),
                                x_bins=", ".join([x_bins]),
                                truncation=_truncation
                                ),
                            label=r'',
                            plot_method='errorbar',
                            color='blue',
                            marker="o",
                            marker_style="full",
                            pad=1
                        ) for _truncation, x_bins in zip(_truncation_values, _truncation_bins)
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
                            'x_range': [min(_truncation_binning), max(_truncation_binning)],
                            'x_scale': 'linear',
                            'y_label': r'Resolution',
                            # 'y_range': (0., 0.3),
                            'x_ticklabels': [],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper left'),
                        },
                        # ratio pad
                        {
                            'height_share': 1,
                            'x_label': r'truncation',
                            'x_range': [min(_truncation_binning), max(_truncation_binning)],
                            'x_scale': 'linear',
                            'y_label': 'RMS/Gaussian',
                            'y_range': ratio_range,
                            'axhlines': [dict(values=[1.0])],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper right'),
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
                }, {
                    'filename': output_format.replace('{plot_label}', 'JER_truncation_scan_zres'),
                    'subplots':
                        [
                            # zres RMS resolution scan
                            dict(
                                expression='truncated_rms_hist([{file_list}], [{x_bins}], {truncation})'.format(
                                    file_list=", ".join([build_expression('mc', alpha_folder='alpha_all',
                                                                          quantity_path='h_zres_weight')]),
                                    x_bins=", ".join([x_bins]),
                                    truncation=_truncation
                                    ),
                                label=r'Z-Res RMS',
                                plot_method='errorbar',
                                color='forestgreen',
                                marker="o",
                                marker_style="full",
                                pad=0
                            ) for _truncation, x_bins in zip(_truncation_values, _truncation_bins)
                        ]+[

                            # zres Gaussian resolution scan
                            dict(
                                expression='truncated_gaussian_width_hist([{file_list}], [{x_bins}], '
                                           '{truncation})'.format(
                                    file_list=", ".join([build_expression('mc', alpha_folder='alpha_all',
                                                                          quantity_path='h_zres_weight')]),
                                    x_bins=", ".join([x_bins]),
                                    truncation=_truncation
                                    ),
                                label=r'Z-Res Gaussian fit',
                                plot_method='errorbar',
                                color='grey',
                                marker="o",
                                marker_style="full",
                                pad=0
                            ) for _truncation, x_bins in zip(_truncation_values, _truncation_bins)
                        ]+[

                            # zres Ratio plot RMS/Gaussian
                            dict(
                                expression='truncated_rms_hist([{file_list}], [{x_bins}], {truncation})/'
                                           'truncated_gaussian_width_hist([{file_list}], [{x_bins}], '
                                           '{truncation})'.format(
                                    file_list=", ".join([build_expression('mc', alpha_folder='alpha_all',
                                                                          quantity_path='h_zres_weight')]),
                                    x_bins=", ".join([x_bins]),
                                    truncation=_truncation
                                    ),
                                label=r'',
                                plot_method='errorbar',
                                color='forestgreen',
                                marker="o",
                                marker_style="full",
                                pad=1
                            ) for _truncation, x_bins in zip(_truncation_values, _truncation_bins)
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
                            'x_range': [min(_truncation_binning), max(_truncation_binning)],
                            'x_scale': 'linear',
                            'y_label': r'Resolution',
                            # 'y_range': (0., 0.3),
                            'x_ticklabels': [],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper left'),
                        },
                        # ratio pad
                        {
                            'height_share': 1,
                            'x_label': r'truncation',
                            'x_range': [min(_truncation_binning), max(_truncation_binning)],
                            'x_scale': 'linear',
                            'y_label': 'RMS/Gaussian',
                            'y_range': ratio_range,
                            'axhlines': [dict(values=[1.0])],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper right'),
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
                }, {
                    'filename': output_format.replace('{plot_label}', 'JER_truncation_scan_pli'),
                    'subplots':
                        [
                            # PLI RMS resolution scan
                            dict(
                                expression='truncated_rms_hist([{file_list}], [{x_bins}], {truncation})'.format(
                                    file_list=", ".join([build_expression('mc', alpha_folder='alpha_all',
                                                                          quantity_path='h_pli_weight')]),
                                    x_bins=", ".join([x_bins]),
                                    truncation=_truncation
                                    ),
                                label=r'PLI RMS',
                                plot_method='errorbar',
                                color='springgreen',
                                marker="o",
                                marker_style="full",
                                pad=0
                            ) for _truncation, x_bins in zip(_truncation_values, _truncation_bins)
                        ]+[

                            # PLI Gaussian resolution scan
                            dict(
                                expression='truncated_gaussian_width_hist([{file_list}], [{x_bins}], '
                                           '{truncation})'.format(
                                    file_list=", ".join([build_expression('mc', alpha_folder='alpha_all',
                                                                          quantity_path='h_pli_weight')]),
                                    x_bins=", ".join([x_bins]),
                                    truncation=_truncation
                                    ),
                                label=r'PLI Gaussian fit',
                                plot_method='errorbar',
                                color='grey',
                                marker="o",
                                marker_style="full",
                                pad=0
                            ) for _truncation, x_bins in zip(_truncation_values, _truncation_bins)
                        ]+[

                            # PLI Ratio plot RMS/Gaussian
                            dict(
                                expression='truncated_rms_hist([{file_list}], [{x_bins}], {truncation})/'
                                           'truncated_gaussian_width_hist([{file_list}], [{x_bins}], '
                                           '{truncation})'.format(
                                    file_list=", ".join([build_expression('mc', alpha_folder='alpha_all',
                                                                          quantity_path='h_pli_weight')]),
                                    x_bins=", ".join([x_bins]),
                                    truncation=_truncation
                                    ),
                                label=r'',
                                plot_method='errorbar',
                                color='springgreen',
                                marker="o",
                                marker_style="full",
                                pad=1
                            ) for _truncation, x_bins in zip(_truncation_values, _truncation_bins)
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
                            'x_range': [min(_truncation_binning), max(_truncation_binning)],
                            'x_scale': 'linear',
                            'y_label': r'Resolution',
                            # 'y_range': (0., 0.3),
                            'x_ticklabels': [],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper left'),
                        },
                        # ratio pad
                        {
                            'height_share': 1,
                            'x_label': r'truncation',
                            'x_range': [min(_truncation_binning), max(_truncation_binning)],
                            'x_scale': 'linear',
                            'y_label': 'RMS/Gaussian',
                            'y_range': ratio_range,
                            'axhlines': [dict(values=[1.0])],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper right'),
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
                }, {
                    'filename': output_format.replace('{plot_label}', 'JER_truncation_scan_genjer'),
                    'subplots':
                        [
                            # Generated JER RMS resolution scan
                            dict(
                                expression='truncated_rms_hist([{file_list}], [{x_bins}], {truncation})'.format(
                                    file_list=", ".join([build_expression('mc', alpha_folder='alpha_all',
                                                                          quantity_path='h_genjer_weight')]),
                                    x_bins=", ".join([x_bins]),
                                    truncation=_truncation
                                    ),
                                label=r'GenJER RMS',
                                plot_method='errorbar',
                                color='orange',
                                marker="o",
                                marker_style="full",
                                pad=0
                            ) for _truncation, x_bins in zip(_truncation_values, _truncation_bins)
                        ]+[

                            # Generated JER Gaussian resolution scan
                            dict(
                                expression='truncated_gaussian_width_hist([{file_list}], [{x_bins}], '
                                           '{truncation})'.format(
                                    file_list=", ".join([build_expression('mc', alpha_folder='alpha_all',
                                                                          quantity_path='h_genjer_weight')]),
                                    x_bins=", ".join([x_bins]),
                                    truncation=_truncation
                                    ),
                                label=r'GenJER Gaussian fit',
                                plot_method='errorbar',
                                color='grey',
                                marker="o",
                                marker_style="full",
                                pad=0
                            ) for _truncation, x_bins in zip(_truncation_values, _truncation_bins)
                        ]+[

                            # Generated JER Ratio plot RMS/Gaussian
                            dict(
                                expression='truncated_rms_hist([{file_list}], [{x_bins}], {truncation})/'
                                           'truncated_gaussian_width_hist([{file_list}], [{x_bins}], '
                                           '{truncation})'.format(
                                    file_list=", ".join([build_expression('mc', alpha_folder='alpha_all',
                                                                          quantity_path='h_genjer_weight')]),
                                    x_bins=", ".join([x_bins]),
                                    truncation=_truncation
                                    ),
                                label=r'',
                                plot_method='errorbar',
                                color='orange',
                                marker="o",
                                marker_style="full",
                                pad=1
                            ) for _truncation, x_bins in zip(_truncation_values, _truncation_bins)
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
                            'x_range': [min(_truncation_binning), max(_truncation_binning)],
                            'x_scale': 'linear',
                            'y_label': r'Resolution',
                            # 'y_range': (0., 0.3),
                            'x_ticklabels': [],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper left'),
                        },
                        # ratio pad
                        {
                            'height_share': 1,
                            'x_label': r'truncation',
                            'x_range': [min(_truncation_binning), max(_truncation_binning)],
                            'x_scale': 'linear',
                            'y_label': 'RMS/Gaussian',
                            'y_range': ratio_range,
                            'axhlines': [dict(values=[1.0])],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper right'),
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
                }
            ]
        })
    else:
        return_value.update({
            'tasks': [
                {
                    "filename": output_format,
                    'subtasks': [
                        # pT-balance from Data
                        {
                            'expression': 'truncated_rms_hist([{file_list}], [{x_bins}], {truncation})'.format(
                                file_list=", ".join([
                                    build_expression(source_type='data', alpha_folder=_k,
                                                     quantity_path='h_ptbalance_weight')
                                    for _k in SPLITTINGS['alpha_exclusive'] if _k is not "alpha_all"
                                ]),
                                x_bins=", ".join(["[{}, {}]".format(_v["alpha"][0], _v["alpha"][1])
                                                  for _k, _v in SPLITTINGS['alpha_exclusive'].iteritems()
                                                  if _k is not "alpha_all"
                                                  ]),
                                truncation=_truncation
                            ),
                            'output_path': '{zpt[name]}/{eta[name]}/ptbalance-data'
                        }
                    ] + [
                        # pT-balance from MC
                        {
                            'expression': 'truncated_rms_hist([{file_list}], [{x_bins}], {truncation})'.format(
                                file_list=", ".join([
                                    build_expression(source_type='mc', alpha_folder=_k,
                                                     quantity_path='h_ptbalance_weight')
                                    for _k in SPLITTINGS['alpha_exclusive'] if _k is not "alpha_all"
                                ]),
                                x_bins=", ".join(["[{}, {}]".format(_v["alpha"][0], _v["alpha"][1])
                                                  for _k, _v in SPLITTINGS['alpha_exclusive'].iteritems() if
                                                  _k is not "alpha_all"
                                                  ]),
                                truncation=_truncation
                            ),
                            'output_path': '{zpt[name]}/{eta[name]}/ptbalance-mc'
                        }
                    ] + [
                        # PLI from MC
                        {
                            'expression': 'truncated_rms_hist([{file_list}], [{x_bins}], {truncation})'.format(
                                file_list=", ".join([
                                    build_expression(source_type='mc', alpha_folder=_k,
                                                     quantity_path='h_pli_weight')
                                    for _k in SPLITTINGS['alpha_exclusive'] if _k is not "alpha_all"
                                ]),
                                x_bins=", ".join(["[{}, {}]".format(_v["alpha"][0], _v["alpha"][1])
                                                  for _k, _v in SPLITTINGS['alpha_exclusive'].iteritems() if
                                                  _k is not "alpha_all"
                                                  ]),
                                truncation=_truncation
                            ),
                            'output_path': '{zpt[name]}/{eta[name]}/pli-mc'
                        }
                    ] + [
                        # Z-Res from MC
                        {
                            'expression': 'truncated_rms_hist([{file_list}], [{x_bins}], {truncation})'.format(
                                file_list=", ".join([
                                    build_expression(source_type='mc', alpha_folder=_k,
                                                     quantity_path='h_zres_weight')
                                    for _k in SPLITTINGS['alpha_exclusive'] if _k is not "alpha_all"
                                ]),
                                x_bins=", ".join(["[{}, {}]".format(_v["alpha"][0], _v["alpha"][1])
                                                  for _k, _v in SPLITTINGS['alpha_exclusive'].iteritems() if
                                                  _k is not "alpha_all"
                                                  ]),
                                truncation=_truncation
                            ),
                            'output_path': '{zpt[name]}/{eta[name]}/zres-mc'
                        }
                    ] + [
                        # generated JER from MC
                        {
                            'expression': 'truncated_rms_hist([{file_list}], [{x_bins}], {truncation})'.format(
                                file_list=", ".join([
                                    build_expression(source_type='mc', alpha_folder=_k,
                                                     quantity_path='h_genjer_weight')
                                    for _k in SPLITTINGS['alpha_exclusive'] if _k is not "alpha_all"
                                ]),
                                x_bins=", ".join(["[{}, {}]".format(_v["alpha"][0], _v["alpha"][1])
                                                  for _k, _v in SPLITTINGS['alpha_exclusive'].iteritems() if
                                                  _k is not "alpha_all"
                                                  ]),
                                truncation=_truncation
                            ),
                            'output_path': '{zpt[name]}/{eta[name]}/jer-gen-mc'
                        }
                    ],
                }
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
    argument_parser.add_argument('-l', '--corr-levels',
                                 help="name of the JEC correction levels to include, e.g. 'L1L2L3'",
                                 nargs='+', choices=['L1', 'L1L2L3', 'L1L2L3Res', 'L1L2Res'], metavar="CORR_LEVEL")
    argument_parser.add_argument('--basename-data', help="prefix of ROOT files containing Data histograms",
                                 required=True)
    argument_parser.add_argument('--basename-mc', help="prefix of ROOT files containing MC histograms", required=True)
    # optional parameters
    argument_parser.add_argument('--output-format',
                                 help="format string defining name of output ROOT files. Default: '{%(default)s}'",
                                 default='JER_truncated_RMS_Z{channel}_{sample}_{jec}_{corr_level}/{plot_label}.pdf')
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
        args.output_dir = "JER_truncated_RMS_{}".format(datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f"))

    for channel in args.channels:
        print("Making root file for channel '{}'...".format(channel))
        _cfg = get_config(
            channel=channel, 
            sample_name=args.sample, 
            jec_name=args.jec,
            corr_levels=(args.corr_levels if args.corr_levels is not '' else ["L1L2L3", "L1L2Res"]),
            run_periods=args.run_periods, 
            basename_data=args.basename_data,
            basename_mc=args.basename_mc,
            output_format=(args.output_format if not args.root else
                           'JER_truncated_RMS_Z{channel}_{sample}_{jec}_{corr_level}.root'),
            root=args.root
        )
        if args.root:
            p = AnalyzeProcessor(_cfg, output_folder=args.output_dir)
        else:
            p = PlotProcessor(_cfg, output_folder=args.output_dir)
        p.run()
