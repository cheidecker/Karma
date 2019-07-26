# -*- coding: utf8 -*-
import datetime
import itertools
import logging
from matplotlib.font_manager import FontProperties

logging.basicConfig(level=logging.INFO)

from Karma.PostProcessing.Palisade import ContextValue, LiteralString, PlotProcessor, AnalyzeProcessor
from Karma.PostProcessing.Lumberjack.cfg.zjet_excalibur import SPLITTINGS, QUANTITIES


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


def get_config(channel, sample_name, jec_name, run_periods, corr_levels, basename_data='TestData',
               basename_mc='TestMC', output_format='test.root', root=True, extraction_method='R'):
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
    :param extraction_method:
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

    _expansions = {
        'corr_level': _corr_level_dicts,
        'zpt': [
            dict(name=_k, label="zpt_{}_{}".format("{:04d}".format(int(round(_v['zpt'][0]))),
                                                   "{:04d}".format(int(round(_v['zpt'][1])))))
            for _k, _v in SPLITTINGS['zpt_jer'].iteritems()
        ],
        'eta': [
            dict(name=_k, label="eta_{}_{}".format("{:04d}".format(int(round(10 * _v['absjet1eta'][0]))),
                                                   "{:04d}".format(int(round(10 * _v['absjet1eta'][1])))))
            for _k, _v in SPLITTINGS['eta_jer'].iteritems()
        ],
    }

    if extraction_method == 'R':
        _extraction_function = 'jer_th1_from_truncated_rms'
        _extraction_name = 'RMS'
    elif extraction_method == 'G':
        _extraction_function = 'jer_th1_from_truncated_gaussian_width'
        _extraction_name = 'Gaussian_fit'
    elif extraction_method == 'L':
        _extraction_function = 'jer_th1_from_truncated_logNormal_width'
        _extraction_name = 'LogNormal_fit'
    else:
        print('No valid extraction method found')
        raise ValueError

    if run_periods is None:
        pass

    _alpha_binning = "alpha_exclusive_jer"

    # define truncation values for different channels
    # _truncation = 98.5 if channel == 'mm' else 90.
    _truncation = 98.5
    # _truncation = 95.
    # _truncation_binning = [85., 88, 90, 92., 94., 95., 96., 97., 98., 99, 100., 101.]
    # _truncation_binning = [99., 101.]
    _truncation_binning = [x / 2. for x in range(70 * 2, 100 * 2, 1)] + [100.]
    _truncation_values = [(_i + _j) / 2 for _i, _j in zip(_truncation_binning[:-1], _truncation_binning[1:])]
    _truncation_bins = ["[{}, {}]".format(_i, _j) for _i, _j in zip(_truncation_binning[:-1], _truncation_binning[1:])]

    ratio_range = (0.8, 1.)

    return_value = {
        'input_files': _input_files,
        'expansions': _expansions
    }

    # append '[name]' to format keys that correspond to above expansion keys
    output_format = output_format.format(
        extraction_method=_extraction_name,
        channel=channel,
        sample=sample_name,
        jec=jec_name,
        plot_label='{plot_label}',
        # for replacing with definitions in _expansions:
        **{_expansion_key: "{{{0}[name]}}".format(_expansion_key) for _expansion_key in _expansions.keys()}
    )

    if not root:
        return_value.update({
            'figures': [
                {
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
                            'expression': '{extraction_function}([{file_list}], [{x_bins}], {truncation})'.format(
                                extraction_function=_extraction_function,
                                file_list=", ".join([
                                    build_expression(source_type='data', alpha_folder=_k,
                                                     quantity_path='h_ptbalance_weight')
                                    for _k in SPLITTINGS[_alpha_binning] if _k is not "alpha_all"
                                ]),
                                x_bins=", ".join(["[{}, {}]".format(_v["alpha"][0], _v["alpha"][1])
                                                  for _k, _v in SPLITTINGS[_alpha_binning].iteritems()
                                                  if _k is not "alpha_all"
                                                  ]),
                                truncation=_truncation
                            ),
                            'output_path': '{zpt[name]}/{eta[name]}/ptbalance-data'
                        }
                    ] + [
                        # pT-balance from MC
                        {
                            'expression': '{extraction_function}([{file_list}], [{x_bins}], {truncation})'.format(
                                extraction_function=_extraction_function,
                                file_list=", ".join([
                                    build_expression(source_type='mc', alpha_folder=_k,
                                                     quantity_path='h_ptbalance_weight')
                                    for _k in SPLITTINGS[_alpha_binning] if _k is not "alpha_all"
                                ]),
                                x_bins=", ".join(["[{}, {}]".format(_v["alpha"][0], _v["alpha"][1])
                                                  for _k, _v in SPLITTINGS[_alpha_binning].iteritems() if
                                                  _k is not "alpha_all"
                                                  ]),
                                truncation=_truncation
                            ),
                            'output_path': '{zpt[name]}/{eta[name]}/ptbalance-mc'
                        }
                    ] + [
                        # PLI from MC
                        {
                            'expression': '{extraction_function}([{file_list}], [{x_bins}], {truncation})'.format(
                                extraction_function=_extraction_function,
                                file_list=", ".join([
                                    build_expression(source_type='mc', alpha_folder=_k,
                                                     quantity_path='h_pli_weight')
                                    for _k in SPLITTINGS[_alpha_binning] if _k is not "alpha_all"
                                ]),
                                x_bins=", ".join(["[{}, {}]".format(_v["alpha"][0], _v["alpha"][1])
                                                  for _k, _v in SPLITTINGS[_alpha_binning].iteritems() if
                                                  _k is not "alpha_all"
                                                  ]),
                                truncation=_truncation
                            ),
                            'output_path': '{zpt[name]}/{eta[name]}/pli-mc'
                        }
                    ] + [
                        # Z-Res from MC
                        {
                            'expression': '{extraction_function}([{file_list}], [{x_bins}], {truncation})'.format(
                                extraction_function=_extraction_function,
                                file_list=", ".join([
                                    build_expression(source_type='mc', alpha_folder=_k,
                                                     quantity_path='h_zres_weight')
                                    for _k in SPLITTINGS[_alpha_binning] if _k is not "alpha_all"
                                ]),
                                x_bins=", ".join(["[{}, {}]".format(_v["alpha"][0], _v["alpha"][1])
                                                  for _k, _v in SPLITTINGS[_alpha_binning].iteritems() if
                                                  _k is not "alpha_all"
                                                  ]),
                                truncation=_truncation
                            ),
                            'output_path': '{zpt[name]}/{eta[name]}/zres-mc'
                        }
                    ] + [
                        # generated JER from MC
                        {
                            'expression': '{extraction_function}([{file_list}], [{x_bins}], {truncation})'.format(
                                extraction_function=_extraction_function,
                                file_list=", ".join([
                                    build_expression(source_type='mc', alpha_folder=_k,
                                                     quantity_path='h_genjer_weight')
                                    for _k in SPLITTINGS[_alpha_binning] if _k is not "alpha_all"
                                ]),
                                x_bins=", ".join(["[{}, {}]".format(_v["alpha"][0], _v["alpha"][1])
                                                  for _k, _v in SPLITTINGS[_alpha_binning].iteritems() if
                                                  _k is not "alpha_all"
                                                  ]),
                                truncation=_truncation
                            ),
                            'output_path': '{zpt[name]}/{eta[name]}/genjer-mc'
                        }
                    ] + [
                        # alpha histograms for correct binning in alpha extrapolation
                        {
                            'expression': 'jer_th1_from_mean([{file_list}], [{x_bins}])'.format(
                                extraction_function=_extraction_function,
                                file_list=", ".join([
                                    build_expression(source_type=_type, alpha_folder=_k,
                                                     quantity_path='h_alpha_weight')
                                    for _k in SPLITTINGS[_alpha_binning] if _k is not "alpha_all"
                                ]),
                                x_bins=", ".join(["[{}, {}]".format(_v["alpha"][0], _v["alpha"][1])
                                                  for _k, _v in SPLITTINGS[_alpha_binning].iteritems() if
                                                  _k is not "alpha_all"
                                                  ]),
                            ),
                            'output_path': '{zpt[name]}/{eta[name]}/alpha-'+_type
                        } for _type in ["data", "mc"]
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
                                 default='JER_truncated_{extraction_method}_Z{channel}_{sample}_{jec}_{corr_level}/'
                                         '{plot_label}_{zpt}_{eta}.pdf')
    argument_parser.add_argument('--root', help="Switch output to root files instead of plots ", dest='root',
                                 action='store_true')
    argument_parser.add_argument('--extraction-method',
                                 help="Switch between RMS (R), Gaussian fit (G), and logNormal fit (L) ",
                                 dest='extraction_method', choices=['R', 'G', 'L'], default='R')


def run(args):
    """
    :param args: arguments specified in function cli
    :return:

    function for starting processing
    """

    from Karma.PostProcessing.Palisade.cfg.zjet_excalibur.jer_definitions import *

    if args.output_dir is None:
        args.output_dir = "JER_rootfiles_{date}".format(datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f"))

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
                           'JER_truncated_{extraction_method}_alpha_Z{channel}_{sample}_{jec}_{corr_level}.root'),
            root=args.root,
            extraction_method=args.extraction_method,
        )
        if args.root:
            p = AnalyzeProcessor(_cfg, output_folder=args.output_dir)
        else:
            p = PlotProcessor(_cfg, output_folder=args.output_dir)
        p.run()
