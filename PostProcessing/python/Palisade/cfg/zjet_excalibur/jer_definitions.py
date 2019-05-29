import uuid
import ROOT
import numpy as np

from array import array
from termcolor import colored
from rootpy import asrootpy
import root_numpy

from Karma.PostProcessing.Palisade import InputROOT
from Karma.PostProcessing.Palisade._input import _ROOTObjectFunctions


@InputROOT.add_function
def truncate_hist(tobject, truncation):
    """Truncates the ROOT histogram to a specific fraction of the integral"""
    _new_tobject = _ROOTObjectFunctions._project_or_clone(tobject, "e")
    mean = _new_tobject.GetMean()
    integral_total = _new_tobject.Integral()
    real_truncation_value = 0.
    x_value_min = 0.
    x_value_max = 0.
    if integral_total != 0.:
        mean_bin = _new_tobject.GetXaxis().FindBin(mean)
        bin_distance_from_mean = 0  # Start value for scanning width
        first_bin = 0
        last_bin = _new_tobject.GetNbinsX() - 1
        deviation = 100.0
        while deviation > (100.0 - float(truncation)) and (mean_bin - bin_distance_from_mean) > first_bin \
                and (mean_bin + bin_distance_from_mean) < last_bin:
            bin_distance_from_mean += 1
            integral_new = _new_tobject.Integral(mean_bin - bin_distance_from_mean, mean_bin +
                                                 bin_distance_from_mean)
            deviation = (integral_total - integral_new) / integral_total * 100.
        x_bin_min = mean_bin - bin_distance_from_mean
        x_bin_max = mean_bin + bin_distance_from_mean
        real_truncation_value = 100.0 - deviation
        print('Reached truncation to {}% of specified {}'.format("{:.2f}".format(real_truncation_value),
                                                                 "{:.2f}".format(truncation)))
        # Truncate range of histogram is sufficient to influence RMS, fits, etc.
        # Bins outside of range are kept, but not used for anything in ROOT
        _new_tobject.GetXaxis().SetRange(x_bin_min, x_bin_max)
        x_value_min = _new_tobject.GetBinCenter(x_bin_min)
        x_value_max = _new_tobject.GetBinCenter(x_bin_max)
    return asrootpy(_new_tobject), real_truncation_value, x_value_min, x_value_max


@InputROOT.add_function
def truncated_rms_hist(tobjects, x_bins, truncation):
    """Get truncated RMS values of all given histograms and fill into new TProfile"""
    x_binning = [min([x[0] for x in x_bins])] + sorted([x[1] for x in x_bins])
    _hist_name = uuid.uuid4().get_hex()
    _new_tobject = ROOT.TH1D("hist_rms_"+_hist_name, "hist_rms_"+_hist_name, len(tobjects), array('d',x_binning))
    x_axis = _new_tobject.GetXaxis()
    _tobj_clones = []
    # clone all given histograms to avoid changing the original
    for _tobj in tobjects:
        _tobj_clones.append(_ROOTObjectFunctions._project_or_clone(_tobj, "e"))
    # get RMS and correction factor to compensate for truncation effects if necessary
    for index, (_tobj_clone, x_bin) in enumerate(zip(_tobj_clones, x_bins)):
        # truncate histogram if necessary
        if truncation is not None and truncation != 100.0:
            _tobj_clone, _real_truncation, a, b = truncate_hist(_tobj_clone, truncation)
        # Calculate index of bin in new histogram
        _bin_index = x_axis.FindBin((x_bin[0] + x_bin[1]) / 2.)
        # Check if truncated histogram contains enough (>10) entries
        if _tobj_clone.GetEffectiveEntries() < 10.:
            _rms, _rms_error = 0., 0.
            _correction_factor = 1.
            print(colored("WARNING: Skipping histogramm due to less statistics (<10 Entries)", 'yellow'))
        else:
            # get RMS value and uncertainty
            _rms, _rms_error = _tobj_clone.GetRMS(), _tobj_clone.GetRMSError()
            _correction_v1 = True  # correct via formula only
            _correction_v2 = False  # correct via Gaussian fit and formula
            if _correction_v1:
                if not _real_truncation == 100.:
                    # Calculate correction factor to compensate for truncation effect
                    # formula: https://en.wikipedia.org/wiki/Truncated_normal_distribution
                    alpha = -np.sqrt(2) * ROOT.TMath.ErfInverse(_real_truncation/100.)
                    beta = -alpha
                    z = ROOT.Math.gaussian_cdf(beta) - ROOT.Math.gaussian_cdf(alpha)
                    phi_alpha = ROOT.Math.gaussian_pdf(alpha)
                    phi_beta = ROOT.Math.gaussian_pdf(beta)
                    if z != 0.:
                        _correction_factor = np.sqrt(1. + (alpha * phi_alpha - beta * phi_beta) / z -
                                                     pow((phi_alpha - phi_beta) / z, 2))
                    else:
                        print(colored("WARNING: Correction factor can't be calculated!!!", 'yellow'))
                        _correction_factor = 1.
                else:
                    _correction_factor = 1.
            elif _correction_v2:
                if not _real_truncation == 100.:
                    rms = _tobj_clone.GetRMS()
                    mean = _tobj_clone.GetMean()
                    fit = ROOT.TF1('gauss_fit', "[2]/([0]*(2*pi)**(0.5))*TMath::Exp(-0.5*((x-[1])/[0])*((x-[1])/[0]))",
                                   a, b)
                    fit.SetParameters(rms, mean, 10)
                    fit.SetParNames("sigma", "mean", "n")
                    fit.SetParLimits(0, rms - 0.01 * rms, rms + 0.01 * rms)
                    fit.SetParLimits(1, mean - 0.01 * mean, mean + 0.01 * mean)
                    fit.SetParLimits(2, 0., 1000000000000.)
                    _tobj_clone.Fit(fit, '', '')
                    parameters = fit.GetParameters()
                    # parameter_errors = fit.GetParError()
                    fit.SetParameters(parameters[0], parameters[1], 1.)
                    print('Fitted sigma ' + str(parameters[0]) + ' <-> Truncated RMS ' + str(_tobj_clone.GetRMS()))
                    theoretical_truncation = fit.Integral(a, b)
                    # Calculate correction factor to compensate for truncation effect
                    # formula: https://en.wikipedia.org/wiki/Truncated_normal_distribution
                    alpha = -np.sqrt(2) * ROOT.TMath.ErfInverse(theoretical_truncation)
                    beta = -alpha
                    z = ROOT.Math.gaussian_cdf(beta) - ROOT.Math.gaussian_cdf(alpha)
                    phi_alpha = ROOT.Math.gaussian_pdf(alpha)
                    phi_beta = ROOT.Math.gaussian_pdf(beta)
                    # print(alpha, beta, z, phi_alpha, phi_beta)
                    _correction_factor = np.sqrt(1. + (alpha * phi_alpha - beta * phi_beta) / z -
                                                 pow((phi_alpha - phi_beta) / z, 2))
                else:
                    _correction_factor = 1.
            else:
                _correction_factor = 1.
        print('Truncated RMS correction factor: ' + str(_correction_factor))
        # Fill RMS values into new histogram
        _new_tobject.SetBinContent(_bin_index, _rms/_correction_factor)
        _new_tobject.SetBinError(_bin_index, _rms_error/_correction_factor)
        print('Extracted RMS {} +/- {} for bin entry {} in new histogram.'.format(
            ("{:.4f}".format(_rms) if _rms is not 0. else "0"),
            ("{:.4f}".format(_rms_error) if _rms is not 0. else "0"),
            _bin_index))
    return asrootpy(_new_tobject)
    

@InputROOT.add_function
def get_gaussian_width(tobject):
    """Determines the Gaussian width and uncertainty of a histogram by fitting a Gaussian function."""
    _new_tobject = _ROOTObjectFunctions._project_or_clone(tobject, "e")
    # _rms = _new_tobject.GetRMS()
    # _mean = _new_tobject.GetMean()
    # Check if truncated histogram contains enough (>10) entries
    if _new_tobject.GetEffectiveEntries() < 10.:
        print(colored("WARNING: Skipping histogram due to less statistics (<10 Entries)", 'yellow'))
        _return_value = (0., 0.)
    else:
        try:
            print(_new_tobject.GetBinCenter(1), _new_tobject.GetBinCenter(_new_tobject.GetNbinsX() - 1))
            _fit = _new_tobject.Fit("gaus", "results", "goff", 0., 2.).Get()
        except Exception as err:
            print('WARNING: ROOT error occured during Gaussian fit: {}'.format(err))
            _return_value = (0., 0.)
        else:
            _return_value = (_fit.Parameter(2), _fit.ParError(2))
    return _return_value


@InputROOT.add_function
def truncated_gaussian_width_hist(tobjects, x_bins, truncation):
    """Get truncated Gaussian width values of all given histograms and fill into new TProfile"""
    x_binning = [min([x[0] for x in x_bins])] + sorted([x[1] for x in x_bins])
    _hist_name = uuid.uuid4().get_hex()
    _new_tobject = ROOT.TH1D("hist_gaus_"+_hist_name, "hist_gaus_"+_hist_name, len(tobjects), array('d', x_binning))
    x_axis = _new_tobject.GetXaxis()
    _tobj_clones = []
    # clone all given histograms to avoid changing the original
    for _tobj in tobjects:
        _tobj_clones.append(_ROOTObjectFunctions._project_or_clone(_tobj, "e"))
    # get RMS and correction factor to compensate for truncation effects if necessary
    for index, (_tobj_clone, x_bin) in enumerate(zip(_tobj_clones, x_bins)):
        # truncate histogram if necessary
        if truncation is not None and truncation != 100.0:
            _tobj_clone, _real_truncation, a, b = truncate_hist(_tobj_clone, truncation)
        # Calculate index of bin in new histogram
        bin_index = x_axis.FindBin((x_bin[0] + x_bin[1]) / 2.)
        # Check if truncated histogram contains enough (>10) entries
        if _tobj_clone.GetEffectiveEntries() > 10.:
            # get Gaussian width value and uncertainty
            # x_min = _tobj_clone.GetXaxis().GetXmin()
            # x_max = _tobj_clone.GetXaxis().GetXmax()
            _gaussian_width, _gaussian_width_error = get_gaussian_width(_tobj_clone)
        else:
            _gaussian_width, _gaussian_width_error = 0., 0.
        # Fill values into new histogram
        _new_tobject.SetBinContent(bin_index, _gaussian_width)
        _new_tobject.SetBinError(bin_index, _gaussian_width_error)
        print('Extracting Gaussian width:   {} +/- {}'.format(_gaussian_width, _gaussian_width_error))
    return asrootpy(_new_tobject)


@InputROOT.add_function
def get_logNormal_width(tobject):
    """Determines the Gaussian width and uncertainty of a histogram by fitting a Gaussian function."""
    _new_tobject = _ROOTObjectFunctions._project_or_clone(tobject, "e")
    # _rms = _new_tobject.GetRMS()
    # _mean = _new_tobject.GetMean()
    # Check if truncated histogram contains enough (>10) entries
    if _new_tobject.GetEffectiveEntries() < 10.:
        print(colored("WARNING: Skipping histogram due to less statistics (<10 Entries)", 'yellow'))
        _return_value = (0., 0.)
    else:
        _fit_function = ROOT.TF1("logNormal_fit", "[0]*TMath::LogNormal(x, [1], 0, [2])", 0., 2.)  # LogNormal(x, sigma, theta, m) with (x>=theta) and (sigma>0) and (m>0)
        _fit_function.SetParameters(1, 0.1, 1.)
        _fit_function.SetParNames("amplitude", "sigma", "mean")
        _fit_function.SetParLimits(1, 0.0001, 1.0)
        _fit_function.SetParLimits(2, 0.0001, 2.0)
        try:
            _fit = _new_tobject.Fit("logNormal_fit", "results", "goff").Get()
        except Exception as err:
            print('WARNING: ROOT error occured during logNormal fit: {}'.format(err))
            _return_value = (0., 0.)
        else:
            _return_value = (_fit.Parameter(1), _fit.ParError(1))
    return _return_value

@InputROOT.add_function
def truncated_logNormal_width_hist(tobjects, x_bins, truncation):
    """Get truncated logNormal width values of all given histograms and fill into new TProfile"""
    x_binning = [min([x[0] for x in x_bins])] + sorted([x[1] for x in x_bins])
    _hist_name = uuid.uuid4().get_hex()
    _new_tobject = ROOT.TH1D("hist_logNormal_"+_hist_name, "hist_logNormal_"+_hist_name, len(tobjects), array('d', x_binning))
    x_axis = _new_tobject.GetXaxis()
    _tobj_clones = []
    # clone all given histograms to avoid changing the original
    for _tobj in tobjects:
        _tobj_clones.append(_ROOTObjectFunctions._project_or_clone(_tobj, "e"))
    # get RMS and correction factor to compensate for truncation effects if necessary
    for index, (_tobj_clone, x_bin) in enumerate(zip(_tobj_clones, x_bins)):
        # truncate histogram if necessary
        if truncation is not None and truncation != 100.0:
            _tobj_clone, _real_truncation, a, b = truncate_hist(_tobj_clone, truncation)
        # Calculate index of bin in new histogram
        bin_index = x_axis.FindBin((x_bin[0] + x_bin[1]) / 2.)
        # Check if truncated histogram contains enough (>10) entries
        if _tobj_clone.GetEffectiveEntries() > 10.:
            # get logNormal width value and uncertainty
            # x_min = _tobj_clone.GetXaxis().GetXmin()
            # x_max = _tobj_clone.GetXaxis().GetXmax()
            _logNormal_width, _logNormal_width_error = get_logNormal_width(_tobj_clone)
        else:
            _logNormal_width, _logNormal_width_error = 0., 0.
        # Fill values into new histogram
        _new_tobject.SetBinContent(bin_index, _logNormal_width)
        _new_tobject.SetBinError(bin_index, _logNormal_width_error)
        print('Extracting logNormal width:   {} +/- {}'.format(_logNormal_width, _logNormal_width_error))
    return asrootpy(_new_tobject)


@InputROOT.add_function
def quadratic_subtraction(minuend_tobject, subtrahend_tobjects):
    # clone all given histograms to avoid changing the original
    _new_tobject = _ROOTObjectFunctions._project_or_clone(minuend_tobject, "e")
    _minuend_tobject = _ROOTObjectFunctions._project_or_clone(minuend_tobject, "e")
    _subtrahend_tobjects = []
    for _tobj in subtrahend_tobjects:
        _subtrahend_tobjects.append(_ROOTObjectFunctions._project_or_clone(_tobj, "e"))
    # subtract bin by bin:
    for current_bin in range(_new_tobject.GetNbinsX() + 1):
        _error = False
        # skip the underflow bin
        if current_bin == 0:
            _error = True
            continue
        # Determine result of quadratic subtraction for BinContent
        bin_value = pow(_minuend_tobject.GetBinContent(current_bin), 2)
        for _subtrahend_tobject in _subtrahend_tobjects:
            # check if subtrahend is not zero
            if _subtrahend_tobject.GetBinContent(current_bin) is 0.:
                _error = True
                break
            bin_value -= pow(_subtrahend_tobject.GetBinContent(current_bin), 2)
        if bin_value < 0. or _error:
            _error = True
            continue
        bin_value = pow(bin_value, 0.5)

        # Calculate uncertainty for BinError
        if bin_value == 0.:
            _error = True
            continue
        bin_error = pow(_minuend_tobject.GetBinContent(current_bin) * _minuend_tobject.GetBinError(current_bin) /
                        bin_value, 2)

        for _subtrahend_tobject in _subtrahend_tobjects:
            bin_error += pow(_subtrahend_tobject.GetBinContent(current_bin) *
                             _subtrahend_tobject.GetBinError(current_bin) /
                             bin_value, 2)
        if bin_error < 0.:
            _error = True
            continue
        bin_error = pow(bin_error, 0.5)
        # check if an error happened
        if _error:
            _new_tobject.SetBinContent(current_bin, 0.)
            _new_tobject.SetBinError(current_bin, 0.)
        else:
            _new_tobject.SetBinContent(current_bin, bin_value)
            _new_tobject.SetBinError(current_bin, bin_error)
        # print('Bin' + str(current_bin) + ' content was set to ' + str(bin_value) + '+/-' + str(bin_error))
    return asrootpy(_new_tobject)


@InputROOT.add_function
def histogram_from_linear_extrapolation(tobjects, x_bins, x_min,x_max):
    """
    :param tobjects:
    :param x_bins:
    :param x_min:
    :param x_max:
    :return:
    Create new histogram from fitted parameters of a
    """
    # create binning for histogram
    x_binning = [min([x[0] for x in x_bins])] + sorted([x[1] for x in x_bins])
    # x_min = min([x[0] for x in x_bins])
    # x_max = max([x[1] for x in x_bins])
    print(x_min, x_max)
    # clone tobjects to avoid data corruption
    _tobjects = []
    for _tobject in tobjects:
        _tobjects.append(_ROOTObjectFunctions._project_or_clone(_tobject, "e"))
    # create new histogram to fill results into
    _new_tobject = ROOT.TH1D("hist_rms_", "hist_rms", len(_tobjects), array('d',x_binning))
    # access x_axis of new histogram for bin by bin access
    _x_axis = _new_tobject.GetXaxis()
    # Fit function to each histogram
    for index, (_tobject, x_bin) in enumerate(zip(_tobjects, x_bins)):
        _bin_index = _x_axis.FindBin((x_bin[0]+x_bin[1])/2.)
        if len(root_numpy.hist2array(_tobject, include_overflow=False, copy=True, return_edges=False)[:-1]) < 3:
            print("WARNING: Skipping histogram due to low statistic! Setting bin to zero!")
            _parameter = 0.
            _parameter_errors = 0.
        else:
            _fit = ROOT.TF1('fit_function', "[0]+[1]*x", x_min, x_max)
            _fit.SetParameters(0., 0.)
            _fit.SetParNames("m", "c")
            # fit.SetParLimits(0, 1. - 0.01 * 1., 1. + 0.01 * 1.)
            # fit.SetParLimits(1, 1. - 0.01 * 1., 1. + 0.01 * 1.)
            _tobject.Fit(_fit, '', '', x_min, x_max)
            _parameters = _fit.GetParameters()[0]
            _parameter_errors = _fit.GetParErrors()[0]
            # Fill RMS values into new histogram
        _new_tobject.SetBinContent(_bin_index, _parameters)
        _new_tobject.SetBinError(_bin_index, _parameter_errors)
        print('Linear extrapolation to {} +/- {}'.format(_parameters, _parameter_errors))
    return asrootpy(_new_tobject)
