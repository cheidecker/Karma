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
               testcase, root):
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
    :param testcase:
    :return:

    creates palisade config
    """

    # -- construct list of input files and correction level expansion dicts
    _input_files = dict()
    _input_files['data'] = "{basename}/JER_truncated_RMS_Z{channel}_{sample_name}_{jec_name}_{corr_level}.root".format(
        channel=channel,
        basename=basename,
        sample_name=sample_name,
        jec_name=jec_name,
        corr_level=corr_level
    )

    alpha_min, alpha_max = SPLITTINGS['alpha_exclusive']['alpha_all']['alpha']
    alpha_max = 0.3

    if testcase:
        _expansions = {
            'zpt': [
                dict(name="zpt_gt_30", label=dict(zpt=(30, 100000)))
            ],
            'eta': [
                dict(name="absEta_all", label=dict(absjet1eta=(0, 5.191)))
            ],
        }
    else:
        _expansions = {
            'zpt': [
                dict(name=_k, label="zpt_{}_{}".format("{:02d}".format(int(round(10*_v['zpt'][0]))),
                                                       "{:02d}".format(int(round(10*_v['zpt'][1])))))
                for _k, _v in SPLITTINGS['zpt'].iteritems()
            ],
            'eta': [
                dict(name=_k, label="eta_{}_{}".format("{:02d}".format(int(round(10*_v['absjet1eta'][0]))),
                                                       "{:02d}".format(int(round(10*_v['absjet1eta'][1])))))
                for _k, _v in SPLITTINGS['eta_wide'].iteritems()
            ],
        }

    # append '[name]' to format keys that correspond to above expansion keys
    output_format = output_format.format(
        channel=channel,
        sample=sample_name,
        jec=jec_name,
        corr_level=corr_level,
        # for replacing with definitions in _expansions:
        **{_expansion_key: "{{{0}[name]}}".format(_expansion_key) for _expansion_key in _expansions.keys()}
    )

    return_value = {
        'input_files': _input_files,
        'expansions': _expansions
    }
    if not root:
        return_value.update({
            'figures': [
                {
                    'filename': output_format,
                    'subplots': [
                        #  Data and MC values
                        dict(
                            expression='{}'.format(build_expression(_quantity)),
                            label=r'{}'.format(_quantity), plot_method='errorbar', color=_color, marker="o",
                            marker_style="full", pad=0)
                        for _quantity, _color in zip(quantities, colors)
                    ] + [
                        # JER extracted from MC
                        dict(expression="quadratic_subtraction({minuend},[{subtrahend}])".format(
                                minuend=build_expression('ptbalance-mc'),
                                subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])),
                             label=r'jer-extracted-mc', plot_method='errorbar', color="red", marker="o",
                             marker_style="full", pad=0)  # , zorder=-99, alpha=0.5)
                    # ] + [
                    #     # JER extracted from data
                    #     dict(expression="quadratic_subtraction({minuend},[{subtrahend}])".format(
                    #             minuend=build_expression('ptbalance-data'),
                    #             subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])),
                    #          label=r'jer-extracted-data', plot_method='errorbar', color="black", marker="o",
                    #          marker_style="full", pad=0)  # , zorder=-99, alpha=0.5)
                    ] + [
                        # Ratio JER extracted from MC to generated JER from MC
                        dict(
                            expression="{numerator}/{denominator}".format(
                                numerator="quadratic_subtraction({minuend},[{subtrahend}])".format(
                                    minuend=build_expression('ptbalance-mc'),
                                    subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])),
                                denominator=build_expression('jer-gen-mc')),
                            label=None, plot_method='errorbar', color='red',
                            marker='o', marker_style="full", pad=1)
                    # ] + [
                    #
                    #     # Ratio JER extracted from data to generated JER from MC
                    #     dict(
                    #         expression="{numerator}/{denominator}".format(
                    #             numerator="quadratic_subtraction({minuend},[{subtrahend}])".format(
                    #                 minuend=build_expression('ptbalance-data'),
                    #                 subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])),
                    #             denominator=build_expression('jer-gen-mc')),
                    #         label=None, plot_method='errorbar', color='black',
                    #         marker='o', marker_style="full", pad=1)
                    # ] + [
                    #     #  Uncertainty shadow of ratio JER extracted from MC to generated JER from MC
                    #     dict(
                    #         expression="{numerator}/{denominator}".format(
                    #             numerator="quadratic_subtraction({minuend},[{subtrahend}])".format(
                    #                 minuend=build_expression('ptbalance-mc'),
                    #                 subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])),
                    #             denominator=build_expression('jer-gen-mc')),
                    #         label=None, plot_method='step', show_yerr_as='band', color='salmon', pad=1, zorder=-99)
                    # ] + [
                    #     #  Uncertainty shadow of ratio JER extracted from data to generated JER from MC
                    #     dict(
                    #         expression="{numerator}/{denominator}".format(
                    #             numerator="quadratic_subtraction({minuend},[{subtrahend}])".format(
                    #                 minuend=build_expression('ptbalance-data'),
                    #                 subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])),
                    #             denominator=build_expression('jer-gen-mc')),
                    #         label=None, plot_method='step', show_yerr_as='band', color='gray', pad=1, zorder=-99)
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
                            # 'y_range': (0.05, 0.2),
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
                            'y_label': 'JER Data/MC',
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
                },
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
                            'expression': "quadratic_subtraction({minuend},[{subtrahend}])".format(
                                minuend=build_expression('ptbalance-mc'),
                                subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])
                            ),
                            'output_path': '{zpt[name]}_{eta[name]}/jer_extracted_mc'
                        }
                    ] + [
                        # JER extracted from Data
                        {
                            'expression': "quadratic_subtraction({minuend},[{subtrahend}])".format(
                                minuend=build_expression('ptbalance-data'),
                                subtrahend=', '.join([build_expression('pli-mc'), build_expression('zres-mc')])
                            ),
                            'output_path': '{zpt[name]}_{eta[name]}/jer_extracted_data'
                        }
                    ] + [
                        # generated JER from MC
                        {
                            'expression': build_expression("jer-gen-mc"),
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
                                 choices=['ptbalance-data', 'ptbalance-mc', 'pli-mc', 'zres-mc', 'jer-gen-mc'],
                                 metavar="QUANTITY")
    argument_parser.add_argument('-f', '--colors', help="colors of quantities to plot", nargs='+', metavar="COLOR")
    argument_parser.add_argument('--basename', help="prefix of ROOT files containing histograms", required=True)
    # optional parameters
    argument_parser.add_argument('--output-format', help="format string indicating full path to output plot",
                                 default='JER_Extrapolations_Z{channel}_{jec}_{sample}_{corr_level}/{zpt}-{eta}.pdf')
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
                        ['ptbalance-data', 'ptbalance-mc', 'pli-mc', 'zres-mc', 'jer-gen-mc']),
            colors=(args.colors if args.colors else ['grey', 'royalblue', 'springgreen', 'forestgreen', 'orange']),
            basename=args.basename,
            output_format=(args.output_format if not args.root else
                           'JER_Extrapolations_Z{channel}_{jec}_{sample}_{corr_level}.root'),
            testcase=(args.test if args.test else False),
            root=(args.root if args.root else False)
        )
        if args.root:
            p = AnalyzeProcessor(_cfg, output_folder=args.output_dir)
        else:
            p = PlotProcessor(_cfg, output_folder=args.output_dir)
        p.run()
