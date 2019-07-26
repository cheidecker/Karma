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
               test_case, root):
    """
    :param channel: Muon or electron channel
    :param sample_name: Naming convention of input files
    :param jec_name: JEC version name and number
    :param run_periods: LHC runs to split up
    :param quantities: Quantities used for plotting
    :param corr_level: Choose which JEC levels are applied
    :param colors: Use specific color scheme
    :param basename: Naming convention of input files
    :param output_format: Naming of output files includes format (root, pdf, png, ...)
    :param test_case: Just use the test expansion
    :param root: Output files are root-files instead of pictures
    :return:

    creates palisade config
    """

    # Used Eta and pT binning extracted by key defined in SPLITTINGS
    # eta_binning_name = "eta_jer"
    # zpt_binning_name = "zpt_jer"
    alpha_binning_name = "alpha_exclusive_jer"
    # alpha_binning_name = "alpha_exclusive"

    # -- construct list of input files and correction level expansion dicts
    _input_files = dict()
    _input_files['data'] = "{basename}/{basename}_alpha_Z{channel}_{sample_name}_{jec_name}_{corr_level}.root".format(
        channel=channel,
        basename=basename,
        sample_name=sample_name,
        jec_name=jec_name,
        corr_level=corr_level
    )

    alpha_min, alpha_max = SPLITTINGS[alpha_binning_name]['alpha_all']['alpha']
    # alpha_max = 0.3

    if test_case:
        _expansions = {
            'zpt': [
                dict(name="zpt_gt_30", label=dict(zpt=(30, 100000))),
                # dict(name="zpt_30_50", label=dict(zpt=(30, 100000))),
                # dict(name="zpt_300_400", label=dict(zpt=(300, 400))),
                # dict(name="zpt_700_1500", label=dict(zpt=(30, 100000))),
                # dict(name="zpt_85_105", label=dict(zpt=(30, 100000))),
                # dict(name=_k, label="zpt_{}_{}".format("{:02d}".format(int(round(10*_v['zpt'][0]))),
                #                                        "{:02d}".format(int(round(10*_v['zpt'][1])))))
                # for _k, _v in SPLITTINGS['zpt_jer'].iteritems()
            ],
            'eta': [
                dict(name="absEta_all", label=dict(absjet1eta=(0, 5.191))),
                # dict(name="absEta_0000_0522", label=dict(absjet1eta=(0, 5.191))),
                # dict(name="absEta_3139_5191", label=dict(absjet1eta=(3.139, 5.191))),
                # dict(name="absEta_1305_1740", label=dict(absjet1eta=(0, 5.191))),
                # dict(name="absEta_2964_3139", label=dict(absjet1eta=(0, 5.191))),
                # dict(name=_k, label="eta_{}_{}".format("{:02d}".format(int(round(10 * _v['absjet1eta'][0]))),
                #                                        "{:02d}".format(int(round(10 * _v['absjet1eta'][1])))))
                # for _k, _v in SPLITTINGS['eta_jer'].iteritems()
            ],
        }
    else:
        _expansions = {
            'zpt': [
                dict(name=_k, label="zpt_{}_{}".format("{:02d}".format(int(round(10*_v['zpt'][0]))),
                                                       "{:02d}".format(int(round(10*_v['zpt'][1])))))
                for _k, _v in SPLITTINGS['zpt_jer'].iteritems()
            ],
            'eta': [
                dict(name=_k, label="eta_{}_{}".format("{:02d}".format(int(round(10*_v['absjet1eta'][0]))),
                                                       "{:02d}".format(int(round(10*_v['absjet1eta'][1])))))
                for _k, _v in SPLITTINGS['eta_jer'].iteritems()
            ],
        }

    def _get_file_name(type="gen_reco"):
        # append '[name]' to format keys that correspond to above expansion keys
        _return_value = output_format.format(
            basename=basename,
            channel=channel,
            sample=sample_name,
            jec=jec_name,
            corr_level=corr_level,
            extrapolation="alpha_extrapolation_{type}".format(type=type),
            # for replacing with definitions in _expansions:
            **{_expansion_key: "{{{0}[name]}}".format(_expansion_key) for _expansion_key in _expansions.keys()}
        )
        return _return_value

    def _get_plotting_quantities(type="all"):
        if type == "data_mc":
            _quantity_list = ['ptbalance-mc', 'ptbalance-data']
            _quantity_label_list = [r'jer-extracted-mc', r'jer-extracted-data']
            _quantity_color_list = ['red', 'black']
        elif type == "gen_reco":
            _quantity_list = ['ptbalance-mc']
            _quantity_label_list = [r'jer-extracted-mc']
            _quantity_color_list = ['red']
        elif type == "all_mc":
            _quantity_list = ['ptbalance-mc', 'pli-mc', 'zres-mc']
            _quantity_label_list = [r'ptbalance-mc', r'pli-mc', 'zres-mc']
            _quantity_color_list = ['royalblue', 'springgreen', 'forestgreen']
        elif type == "all_data":
            _quantity_list = ['ptbalance-data', 'pli-mc', 'zres-mc']
            _quantity_label_list = [r'ptbalance-data', r'pli-mc', 'zres-mc']
            _quantity_color_list = ['grey', 'springgreen', 'forestgreen']
        else:
            _quantity_list = ['ptbalance-mc', 'ptbalance-data', 'pli-mc', 'zres-mc']
            _quantity_label_list = [r'ptbalance-mc', r'ptbalance-data', r'pli-mc', 'zres-mc']
            _quantity_color_list = ['red', 'black', 'springgreen', 'forestgreen']
        return zip(_quantity_list, _quantity_label_list, _quantity_color_list)

    return_value = {
        'input_files': _input_files,
        'expansions': _expansions
    }

    if not root:
        return_value.update({
            'figures': [
                {
                    # Gen - Reco Comparison
                    'filename': _get_file_name(type="gen_reco"),
                    'subplots': [
                        #  JER generated in MC
                        dict(
                            expression='jer_tgrapherrors_from_th1s({quantity}, {alpha})'.format(
                                quantity=build_expression('genjer-mc'),
                                alpha=build_expression('alpha-mc')),
                            label=r'{}'.format('jer-generated-mc'), plot_method='errorbar', color='orange', marker="o",
                            marker_style="full", pad=0, mask_zero_errors=True)
                    ] + [
                        # JER extracted from MC
                        dict(expression="jer_tgrapherrors_from_th1s(jer_th1_from_quadratic_subtraction("
                                        "{minuend},[{subtrahend}]), {alpha})".format(
                                minuend=build_expression(_quantity),
                                subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')]),
                                alpha=build_expression('alpha-mc' if '-mc' in _quantity else 'alpha-data')),
                            label=_quantity_label, plot_method='errorbar', color=_quantity_color, marker="o",
                            marker_style="full", pad=0, mask_zero_errors=True)
                        for _quantity, _quantity_label, _quantity_color in _get_plotting_quantities(type="gen_reco")
                    ] + [
                        # Fit-results of JER generated in MC
                        dict(
                            expression='jer_tgrapherror_from_poly1_fit(jer_tgrapherrors_from_th1s('
                                       '{quantity}, {alpha}), 0., 0.3)'.format(
                                quantity=build_expression('genjer-mc'),
                                alpha=build_expression('alpha-mc')),
                            label=None, plot_method='step', show_yerr_as='band', color='orange', pad=0, zorder=-99,
                            mask_zero_errors=True)
                    ] + [
                        # Fit-results of JER extracted from MC
                        dict(
                            expression="jer_tgrapherror_from_poly1_fit(jer_tgrapherrors_from_th1s("
                                       "jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}]), {alpha}), "
                                       "0., 0.3)".format(
                                minuend=build_expression(_quantity),
                                subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')]),
                                alpha=build_expression('alpha-mc' if '-mc' in _quantity else 'alpha-data')),
                            label=None, plot_method='step', show_yerr_as='band', color=_quantity_color, pad=0,
                            zorder=-99, mask_zero_errors=True)
                        for _quantity, _quantity_label, _quantity_color in _get_plotting_quantities(type="gen_reco")
                    ] + [
                        # Ratio JER extracted from MC to generated JER from MC
                        dict(
                            expression="jer_tgrapherrors_from_th1s(jer_ratio({numerator},{denominator}), "
                                       "{alpha})".format(
                                numerator="jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend=build_expression('ptbalance-mc'),
                                    subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])),
                                denominator=build_expression('genjer-mc'),
                                alpha=build_expression('alpha-mc')),
                            label=None, plot_method='errorbar', color='red', marker='o', marker_style="full", pad=1,
                            mask_zero_errors=True)
                    ] + [
                        # Ratio of fits JER extracted from MC to generated JER from MC
                        dict(
                            expression="jer_ratio(jer_tgrapherror_from_poly1_fit("
                                       "jer_tgrapherrors_from_th1s({numerator}, {alpha}), 0., 0.3), "
                                       "jer_tgrapherror_from_poly1_fit("
                                       "jer_tgrapherrors_from_th1s({denominator}, {alpha}), 0., 0.3))".format(
                                numerator="jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend=build_expression("ptbalance-mc"),
                                    subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])),
                                denominator=build_expression('genjer-mc'),
                                alpha=build_expression('alpha-mc')),
                            label=None, plot_method='step', show_yerr_as='band', color='red', pad=1,
                            zorder=-99,
                            mask_zero_errors=True)
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
                            'x_range': [alpha_min, alpha_max],
                            # 'x_scale': '{quantity[scale]}',
                            'y_label': 'Resolution',
                            # 'y_range': (0.05, 0.20),
                            'y_range': (0.05, 0.25),
                            # 'axvlines': ContextValue('quantity[expected_values]'),
                            'x_ticklabels': [],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper left'),
                        },
                        # ratio pad
                        {
                            'height_share': 1,
                            'x_label': 'Second-jet activity',
                            'x_range': [alpha_min, alpha_max],
                            # 'x_scale' : '{quantity[scale]}',
                            'y_label': 'Reco/Gen',
                            'y_range': (0.75, 1.25),
                            'axhlines': [dict(values=[1.0])],
                            # 'axvlines': ContextValue('quantity[expected_values]'),
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
                    # Data - MC Comparison
                    'filename': _get_file_name(type="data_mc"),
                    'subplots': [
                        # JER extracted from Data and MC
                        dict(expression="jer_tgrapherrors_from_th1s(jer_th1_from_quadratic_subtraction({minuend},"
                                        "[{subtrahend}]), {alpha})".format(
                                minuend=build_expression(_quantity),
                                subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')]),
                                alpha=build_expression('alpha-mc' if '-mc' in _quantity else 'alpha-data')),
                            label=_quantity_label, plot_method='errorbar', color=_quantity_color, marker="o",
                            marker_style="full", pad=0, mask_zero_errors=True)
                        for _quantity, _quantity_label, _quantity_color in _get_plotting_quantities('data_mc')
                    ] + [
                        # Fit-results of JER extracted from Data and MC
                        dict(
                            expression="jer_tgrapherror_from_poly1_fit(jer_tgrapherrors_from_th1s("
                                       "jer_th1_from_quadratic_subtraction({minuend}, [{subtrahend}]), {alpha})"
                                       ", 0., 0.3)".format(
                                minuend=build_expression(_quantity),
                                subtrahend=', '.join(
                                    [build_expression('pli-mc'), build_expression('zres-mc')]),
                                alpha=build_expression('alpha-mc' if '-mc' in _quantity else 'alpha-data')),
                            label=None, plot_method='step', show_yerr_as='band', color=_quantity_color, pad=0,
                            zorder=-99, mask_zero_errors=True)
                        for _quantity, _quantity_label, _quantity_color in _get_plotting_quantities('data_mc')
                    ] + [
                        # Ratio JER extracted from data to JER extracted from MC
                        dict(
                            expression="jer_tgrapherrors_from_th1s(jer_ratio({numerator},{denominator}), "
                                       "{alpha})".format(
                                numerator="jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend=build_expression('ptbalance-data'),
                                    subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])),
                                denominator="jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend=build_expression('ptbalance-mc'),
                                    subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])),
                                alpha=build_expression('alpha-mc')),
                            label=None, plot_method='errorbar', color='black',
                            marker='o', marker_style="full", pad=1)
                    ] + [
                        # Ratio of fits JER extracted from Data to MC
                        dict(
                            expression="jer_ratio(jer_tgrapherror_from_poly1_fit("
                                       "jer_tgrapherrors_from_th1s({numerator}, {alpha}), 0., 0.3), "
                                       "jer_tgrapherror_from_poly1_fit("
                                       "jer_tgrapherrors_from_th1s({denominator}, {alpha}), 0., 0.3))".format(
                                numerator="jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend=build_expression("ptbalance-data"),
                                    subtrahend=', '.join(
                                        [build_expression('pli-mc'), build_expression('zres-mc')])),
                                denominator="jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend=build_expression("ptbalance-mc"),
                                    subtrahend=', '.join(
                                        [build_expression('pli-mc'), build_expression('zres-mc')])),
                                alpha=build_expression('alpha-mc')),
                            label=None, plot_method='step', show_yerr_as='band', color='black', pad=1,
                            zorder=-99,
                            mask_zero_errors=True)
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
                            'x_range': [alpha_min, alpha_max],
                            # 'x_scale': '{quantity[scale]}',
                            'y_label': 'Resolution',
                            # 'y_range': (0.05, 0.20),
                            'y_range': (0.05, 0.3),
                            # 'axvlines': ContextValue('quantity[expected_values]'),
                            'x_ticklabels': [],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper left'),
                        },
                        # ratio pad
                        {
                            'height_share': 1,
                            'x_label': 'Second-jet activity',
                            'x_range': [alpha_min, alpha_max],
                            # 'x_scale' : '{quantity[scale]}',
                            'y_label': 'Data/MC',
                            'y_range': (0.5, 1.5),
                            'axhlines': [dict(values=[1.0])],
                            # 'axvlines': ContextValue('quantity[expected_values]'),
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
            ] + [
                {
                    # All involved components
                    'filename': _get_file_name(type="all_"+str(_all_type)),
                    'subplots': [
                        #  all raw quantities
                        dict(
                            expression='jer_tgrapherrors_from_th1s({quantity}, {alpha})'.format(
                                quantity=build_expression(_quantity),
                                alpha=build_expression('alpha-mc' if '-mc' in _quantity else 'alpha-data')),
                            label=_quantity_label, plot_method='errorbar', color=_quantity_color, marker="o",
                            marker_style="full", pad=0, mask_zero_errors=True)
                        for _quantity, _quantity_label, _quantity_color in _get_plotting_quantities(
                            'all_'+str(_all_type))
                    ] + [
                        # Fit-results of all raw quantities
                        dict(
                            expression='jer_tgrapherror_from_poly1_fit(jer_tgrapherrors_from_th1s('
                                       '{quantity}, {alpha}), 0., 0.3)'.format(
                                quantity=build_expression(_quantity),
                                alpha=build_expression('alpha-mc' if '-mc' in _quantity else 'alpha-data')),
                            label=None, plot_method='step', show_yerr_as='band', color=_quantity_color, pad=0,
                            zorder=-99,
                            mask_zero_errors=True)
                        for _quantity, _quantity_label, _quantity_color in _get_plotting_quantities(
                            'all_'+str(_all_type))
                    ] + [
                        # JER extracted from Data and MC
                        dict(expression="jer_tgrapherrors_from_th1s(jer_th1_from_quadratic_subtraction({minuend},"
                                        "[{subtrahend}]), {alpha})".format(
                                minuend=build_expression('ptbalance-'+str(_all_type)),
                                subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')]),
                                alpha=build_expression('alpha-mc' if 'mc' in _all_type else 'alpha-data')),
                            label='jer-extracted-'+str(_all_type), plot_method='errorbar',
                            color='black' if _all_type == 'data' else 'red', marker="o",
                            marker_style="full", pad=0, mask_zero_errors=True)
                    ] + [
                        # Fit-results of JER extracted from Data and MC
                        dict(
                            expression="jer_tgrapherror_from_poly1_fit(jer_tgrapherrors_from_th1s("
                                       "jer_th1_from_quadratic_subtraction({minuend}, [{subtrahend}]), {alpha})"
                                       ", 0., 0.3)".format(
                                minuend=build_expression('ptbalance-'+str(_all_type)),
                                subtrahend=', '.join(
                                    [build_expression('pli-mc'), build_expression('zres-mc')]),
                                alpha=build_expression('alpha-mc' if 'mc' in _all_type else 'alpha-data')),
                            label=None, plot_method='step', show_yerr_as='band',
                            color='black' if _all_type == 'data' else 'red', pad=0,
                            zorder=-99, mask_zero_errors=True)
                    # ] + [
                    #     # Ratio JER extracted from data to JER extracted from MC
                    #     dict(
                    #         expression="jer_tgrapherrors_from_th1s(jer_ratio({numerator},{denominator}), "
                    #                    "{alpha})".format(
                    #             numerator="jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}])".format(
                    #                 minuend=build_expression('ptbalance-data'),
                    #                 subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])),
                    #             denominator="jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}])".format(
                    #                 minuend=build_expression('ptbalance-mc'),
                    #                 subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])),
                    #             alpha=build_expression('alpha-mc')),
                    #         label=None, plot_method='errorbar', color='black',
                    #         marker='o', marker_style="full", pad=1)
                    # ] + [
                    #     # Ratio of fits JER extracted from Data to MC
                    #     dict(
                    #         expression="jer_ratio(jer_tgrapherror_from_poly1_fit("
                    #                    "jer_tgrapherrors_from_th1s({numerator}, {alpha}), 0., 0.3), "
                    #                    "jer_tgrapherror_from_poly1_fit("
                    #                    "jer_tgrapherrors_from_th1s({denominator}, {alpha}), 0., 0.3))".format(
                    #             numerator="jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}])".format(
                    #                 minuend=build_expression("ptbalance-data"),
                    #                 subtrahend=', '.join(
                    #                     [build_expression('pli-mc'), build_expression('zres-mc')])),
                    #             denominator="jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}])".format(
                    #                 minuend=build_expression("ptbalance-mc"),
                    #                 subtrahend=', '.join(
                    #                     [build_expression('pli-mc'), build_expression('zres-mc')])),
                    #             alpha=build_expression('alpha-mc')),
                    #         label=None, plot_method='step', show_yerr_as='band', color='black', pad=1,
                    #         zorder=-99,
                    #         mask_zero_errors=True)
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
                            'x_range': [alpha_min, alpha_max],
                            'x_label': 'Second-jet activity',
                            # 'x_scale': '{quantity[scale]}',
                            'y_label': 'Resolution',
                            'y_range': (0.0, 0.35),
                            # 'axvlines': ContextValue('quantity[expected_values]'),
                            # 'x_ticklabels': [],
                            'y_scale': 'linear',
                            'legend_kwargs': dict(loc='upper left'),
                        },
                        # ratio pad
                        # {
                        #     'height_share': 1,
                        #     'x_label': 'Second-jet activity',
                        #     'x_range': [alpha_min, alpha_max],
                        #     # 'x_scale' : '{quantity[scale]}',
                        #     'y_label': 'Data/MC',
                        #     'y_range': (0., 2.),
                        #     'axhlines': [dict(values=[1.0])],
                        #     # 'axvlines': ContextValue('quantity[expected_values]'),
                        #     'y_scale': 'linear',
                        #     'legend_kwargs': dict(loc='upper right'),
                        # },
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
                } for _all_type in ['data', 'mc']
            ]
        })
    else:
        return_value.update({
            'tasks': [
                {
                    "filename": output_format.format(
                        channel=channel,
                        sample=sample_name,
                        jec=jec_name,
                        # get other possible replacements from expansions definition
                        **{_expansion_key: "{{{0}[name]}}".format(_expansion_key) for _expansion_key in _expansions.keys()}
                    ),
                    'subtasks': [
                        # JER extracted from MC
                        {
                            'expression': "jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}])".format(
                                minuend=build_expression('ptbalance-mc'),
                                subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])
                            ),
                            'output_path': '{zpt[name]}_{eta[name]}/jer_extracted_mc'
                        }
                    ] + [
                        # JER extracted from Data
                        {
                            'expression': "jer_th1_from_quadratic_subtraction({minuend},[{subtrahend}])".format(
                                minuend=build_expression('ptbalance-data'),
                                subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])
                            ),
                            'output_path': '{zpt[name]}_{eta[name]}/jer_extracted_data'
                        }
                    ] + [
                        # generated JER from MC
                        {
                            'expression': build_expression("genjer-mc"),
                            'output_path': '{zpt[name]}_{eta[name]}/jer_gen_mc'
                        }
                    ],
                },
            ]
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
                                 choices=['ptbalance-data', 'ptbalance-mc', 'pli-mc', 'zres-mc', 'genjer-mc'],
                                 metavar="QUANTITY")
    argument_parser.add_argument('-f', '--colors', help="colors of quantities to plot", nargs='+', metavar="COLOR")
    argument_parser.add_argument('--basename', help="prefix of ROOT files containing histograms", required=True)
    # optional parameters
    argument_parser.add_argument('--output-format', help="format string indicating full path to output plot",
                                 default='{basename}_Z{channel}_{jec}_{sample}_{corr_level}_{extrapolation}/{zpt}-{eta}'
                                         '.pdf')
    argument_parser.add_argument('--test', help="plot only one plot for testing configuration", dest='test',
                                 action='store_true')
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
            quantities=(args.quantities if args.quantities else
                        ['ptbalance-data', 'ptbalance-mc', 'pli-mc', 'zres-mc', 'genjer-mc']),
            colors=(args.colors if args.colors else ['grey', 'royalblue', 'springgreen', 'forestgreen', 'orange']),
            basename=args.basename,
            output_format=(args.output_format if not args.root else
                           '{basename}_Z{channel}_{jec}_{sample}_{corr_level}_{extrapolation}.root'),
            test_case=(args.test if args.test else False),
            root=(args.root if args.root else False)
        )
        if args.root:
            p = AnalyzeProcessor(_cfg, output_folder=args.output_dir)
        else:
            p = PlotProcessor(_cfg, output_folder=args.output_dir)
        p.run()
