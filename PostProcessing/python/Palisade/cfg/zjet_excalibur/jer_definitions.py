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
def jer_truncate_hist(tobject, truncation):
    """
    :param tobject: TH1 object to truncate
    :param truncation: truncation value (in % remaining)
    :return:
    Truncates the ROOT histogram to a specific fraction of the integral
    """
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
def jer_th1_from_truncated_rms(tobjects, x_bins, truncation, correction=0):
    """
    :param tobjects: list of TH1 histograms
    :param x_bins: list of x bins
    :param truncation: truncation value (in % remaining)
    :param correction: switch correction for truncation effects on and off (default: on)
    :return:
    Get truncated RMS values of all given histograms and fill into new TH1
    """
    x_binning = [min([x[0] for x in x_bins])] + sorted([x[1] for x in x_bins])
    _hist_name = uuid.uuid4().get_hex()
    _new_tobject = ROOT.TH1D("hist_rms_"+_hist_name, "hist_rms_"+_hist_name, len(tobjects), array('d', x_binning))
    x_axis = _new_tobject.GetXaxis()
    _tobj_clones = []
    # Choose correction factor calculation method
    if correction == 0:
        _correction_v1 = True  # correct via formula only
        _correction_v2 = False  # correct via Gaussian fit and formula
    else:
        _correction_v1 = False  # correct via formula only
        _correction_v2 = False  # correct via Gaussian fit and formula
    # clone all given histograms to avoid changing the original
    for _tobj in tobjects:
        _tobj_clones.append(_ROOTObjectFunctions._project_or_clone(_tobj, "e"))
    # get RMS and correction factor to compensate for truncation effects if necessary
    for index, (_tobj_clone, x_bin) in enumerate(zip(_tobj_clones, x_bins)):
        # truncate histogram if necessary
        if truncation is not None and truncation != 100.0:
            _tobj_clone, _real_truncation, a, b = jer_truncate_hist(_tobj_clone, truncation)
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
def jer_get_gaussian_width(tobject):
    """
    :param tobject: TH1 histogram to get Gaussian with from
    :return:
    Determines the Gaussian width and uncertainty of a histogram by fitting a Gaussian function.
    """
    _new_tobject = _ROOTObjectFunctions._project_or_clone(tobject, "e")
    # _rms = _new_tobject.GetRMS()
    # _mean = _new_tobject.GetMean()
    _return_value = (0., 0.)
    # Check if truncated histogram contains enough (>10) entries
    if _new_tobject.GetEffectiveEntries() < 10.:
        print(colored("WARNING: Skipping histogram due to less statistics (<10 Entries)", 'yellow'))
    else:
        try:
            print(_new_tobject.GetBinCenter(1), _new_tobject.GetBinCenter(_new_tobject.GetNbinsX() - 1))
            _fit = _new_tobject.Fit("gaus", "S", "goff", 0., 2.)
        except Exception as err:
            print(colored('WARNING: ROOT error occured during Gaussian fit: {}'.format(err),'yellow'))
        else:
            # Check if TFitResult is not empty by testing if TFitResultPtr is not -1
            if int(_fit) >= 0:
                _return_value = (_fit.Parameter(2), _fit.ParError(2))
            else:
                print(colored("WARNING: Skipping fit due to empty fit results! Setting parameters to zero!", "yellow"))
    return _return_value


@InputROOT.add_function
def jer_th1_from_truncated_gaussian_width(tobjects, x_bins, truncation):
    """
    :param tobjects: list of TH1 histograms
    :param x_bins: list of x bins
    :param truncation: truncation value (in % remaining)
    :return:
    Get truncated Gaussian width values of all given histograms and fill into new TH1
    """
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
            _tobj_clone, _real_truncation, a, b = jer_truncate_hist(_tobj_clone, truncation)
        # Calculate index of bin in new histogram
        bin_index = x_axis.FindBin((x_bin[0] + x_bin[1]) / 2.)
        # Check if truncated histogram contains enough (>10) entries
        if _tobj_clone.GetEffectiveEntries() > 10.:
            # get Gaussian width value and uncertainty
            # x_min = _tobj_clone.GetXaxis().GetXmin()
            # x_max = _tobj_clone.GetXaxis().GetXmax()
            _gaussian_width, _gaussian_width_error = jer_get_gaussian_width(_tobj_clone)
        else:
            _gaussian_width, _gaussian_width_error = 0., 0.
        # Fill values into new histogram
        _new_tobject.SetBinContent(bin_index, _gaussian_width)
        _new_tobject.SetBinError(bin_index, _gaussian_width_error)
        print('Extracting Gaussian width:   {} +/- {}'.format(_gaussian_width, _gaussian_width_error))
    return asrootpy(_new_tobject)


@InputROOT.add_function
def jer_get_logNormal_width(tobject):
    """
    :param tobject: TH1 histogram to get logNormal width of
    :return:
    Determines the Gaussian width and uncertainty of a histogram by fitting a Gaussian function.
    """
    _new_tobject = _ROOTObjectFunctions._project_or_clone(tobject, "e")
    # _rms = _new_tobject.GetRMS()
    # _mean = _new_tobject.GetMean()
    _return_value = (0., 0.)
    # Check if truncated histogram contains enough (>10) entries
    if _new_tobject.GetEffectiveEntries() < 10.:
        print(colored("WARNING: Skipping histogram due to less statistics (<10 Entries)", 'yellow'))
    else:
        _fit_function = ROOT.TF1("logNormal_fit", "[0]*TMath::LogNormal(x, [1], 0, [2])", 0., 2.)  # LogNormal(x, sigma, theta, m) with (x>=theta) and (sigma>0) and (m>0)
        _fit_function.SetParameters(1, 0.1, 1.)
        _fit_function.SetParNames("amplitude", "sigma", "mean")
        _fit_function.SetParLimits(1, 0.0001, 1.0)
        _fit_function.SetParLimits(2, 0.0001, 2.0)
        try:
            _fit = _new_tobject.Fit("logNormal_fit", "S", "goff")
        except Exception as err:
            print(colored('WARNING: ROOT error occured during logNormal fit: {}'.format(err), 'yellow'))
        else:
            # Check if TFitResult is not empty by testing if TFitResultPtr is not -1
            if int(_fit) >= 0:
                _return_value = (_fit.Parameter(1), _fit.ParError(1))
            else:
                print(colored("WARNING: Skipping fit due to empty fit results! Setting parameters to zero!", "yellow"))
    return _return_value


@InputROOT.add_function
def jer_th1_from_truncated_logNormal_width(tobjects, x_bins, truncation):
    """
    :param tobjects: list of TH1 histograms
    :param x_bins: list of x bins
    :param truncation: truncation value (in % remaining)
    Get truncated logNormal width values of all given histograms and fill into new TH1
    """
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
            _tobj_clone, _real_truncation, a, b = jer_truncate_hist(_tobj_clone, truncation)
        # Calculate index of bin in new histogram
        bin_index = x_axis.FindBin((x_bin[0] + x_bin[1]) / 2.)
        # Check if truncated histogram contains enough (>10) entries
        if _tobj_clone.GetEffectiveEntries() > 10.:
            # get logNormal width value and uncertainty
            # x_min = _tobj_clone.GetXaxis().GetXmin()
            # x_max = _tobj_clone.GetXaxis().GetXmax()
            _logNormal_width, _logNormal_width_error = jer_get_logNormal_width(_tobj_clone)
        else:
            _logNormal_width, _logNormal_width_error = 0., 0.
        # Fill values into new histogram
        _new_tobject.SetBinContent(bin_index, _logNormal_width)
        _new_tobject.SetBinError(bin_index, _logNormal_width_error)
        print('Extracting logNormal width:   {} +/- {}'.format(_logNormal_width, _logNormal_width_error))
    return asrootpy(_new_tobject)


@InputROOT.add_function
def jer_th1_from_quadratic_subtraction(minuend_tobject, subtrahend_tobjects):
    """
    :param minuend_tobject: TH1 histogram used as minuend
    :param subtrahend_tobjects: list of TH1 histograms used as subtrahends
    :return:
    Create new TH1 by subtracting a list of subtrahend histograms from a minuend histogram.
    This assumes same binning in all involved histograms.
    """
    # clone all given histograms to avoid changing the original
    _new_tobject = _ROOTObjectFunctions._project_or_clone(minuend_tobject, "e")
    _minuend_tobject = _ROOTObjectFunctions._project_or_clone(minuend_tobject, "e")
    binning_list = list(_minuend_tobject.GetXaxis().GetXbins())
    _subtrahend_tobjects = []
    for _tobj in subtrahend_tobjects:
        _subtrahend_tobjects.append(_ROOTObjectFunctions._project_or_clone(_tobj, "e"))
        # check if all histograms have hte same binning
        if list(_tobj.GetXaxis().GetXbins()) != binning_list:
            print(colored("ERROR: Different binning in histograms for quadratic subtraction!", "red"))
            return None
    # subtract bin by bin
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
def jer_get_mean(tobject):
    """
    :param tobject:
    :return:
    Get mean of histogram as value
    """
    return tobject.GetMean()


@InputROOT.add_function
def jer_get_rms(tobject):
    """
    :param tobject:
    :return:
    Get rms of histogram as value
    """
    return tobject.GetRMS()


@InputROOT.add_function
def jer_th1_from_mean(tobjects, x_bins):
    """
    :param tobjects: list of tobjects to get mean and RMS from
    :param x_bins: list of x bins for resulting histogram
    :return:
    Get TH1 with Mean as values and RMS as uncertainties of
    """
    binning_list = list(tobjects[0].GetXaxis().GetXbins())
    _tobjects = [_ROOTObjectFunctions._project_or_clone(tobjects[0], "e")]
    # Check if binning of all input histograms is the same
    for _tobj in tobjects[1:]:
        _tobjects.append(_ROOTObjectFunctions._project_or_clone(_tobj, "e"))
        # check if all histograms have hte same binning
        if list(_tobj.GetXaxis().GetXbins()) != binning_list:
            print(colored("ERROR: Different binning in histograms for quadratic subtraction!", "red"))
            return None
    # Create new TH1 for filling results into
    x_binning = [min([x[0] for x in x_bins])] + sorted([x[1] for x in x_bins])
    _hist_name = uuid.uuid4().get_hex()
    _new_tobject = ROOT.TH1D("hist_rms_" + _hist_name, "hist_rms_" + _hist_name, len(tobjects), array('d', x_binning))
    x_axis = _new_tobject.GetXaxis()
    for index, (_tobj, x_bin) in enumerate(zip(_tobjects, x_bins)):
        # Calculate index of bin in new histogram
        _bin_index = x_axis.FindBin((x_bin[0] + x_bin[1]) / 2.)
        # Fill new TH1 with mean and RMS values
        _new_tobject.SetBinContent(_bin_index, _tobj.GetMean())
        _new_tobject.SetBinError(_bin_index, _tobj.GetRMS())
    return _new_tobject


@InputROOT.add_function
def jer_tgrapherrors_from_th1s(y_tobject, x_tobject):
    """
    :param y_tobject: TH1 histogram to use for y values
    :param x_tobject: TH1 histogram to use for x values
    :return:
    Create new TGraphErrors from TH1 using x values and uncertainties
    """
    # Check if binning of all input histograms is the same
    if list(y_tobject.GetXaxis().GetXbins()) != list(x_tobject.GetXaxis().GetXbins()):
        print(colored("ERROR: Different binning in histograms for conversion to TGraphError!", "red"))
        return None
    _x_tobject = _ROOTObjectFunctions._project_or_clone(x_tobject, "e")
    _y_tobject = _ROOTObjectFunctions._project_or_clone(y_tobject, "e")
    _x_array = []
    _x_err_array = []
    _y_array = []
    _y_err_array = []
    _n = len(list(_y_tobject.GetXaxis().GetXbins()))
    for index in range(_n):
        _x = _x_tobject.GetBinContent(index)
        _x_err = _x_tobject.GetBinError(index)
        _y = _y_tobject.GetBinContent(index)
        _y_err = _y_tobject.GetBinError(index)
        # if _y != 0. and _y_err != 0.:
        if _y_err != 0. and _x_err != 0.:
            _x_array.append(_x)
            _x_err_array.append(_x_err)
            _y_array.append(_y)
            _y_err_array.append(_y_err)
    _new_tobject = ROOT.TGraphErrors(len(_x_array))
    for _index in range(len(_x_array)):
        _new_tobject.SetPoint(_index, _x_array[_index], _y_array[_index])
        _new_tobject.SetPointError(_index, _x_err_array[_index], _y_err_array[_index])
    return asrootpy(_new_tobject)


@InputROOT.add_function
def jer_poly1_fit(tobject, x_min, x_max, start_param_m=0., start_param_c=0.):
    """
    :param tobject: TH1 histogram to fit poly1 to
    :param x_min: lower limit for fitting
    :param x_max: upper limit for fitting
    :return:
    """
    # new_tobject = _ROOTObjectFunctions._project_or_clone(tobject, "e")
    _skip = True
    _parameter = [0., 0.]
    _parameter_errors = [0., 0.]
    if isinstance(tobject, ROOT.TH1):
        _n_entries = len(list(filter(lambda a: a != 0, root_numpy.hist2array(tobject, include_overflow=False, copy=True,
                                                                             return_edges=False)[:-1])))
    elif isinstance(tobject, ROOT.TGraph):
        _y_buff = tobject.GetX()
        _y_buff.SetSize(tobject.GetN())
        _y = array('d', _y_buff)
        _n_entries = len(list(filter(lambda a: a != 0, _y)))
    else:
        print(colored("ERROR: No valid input format (TGraphError or TH1!", "red"))
        return None
    if _n_entries < 3:
        print(colored("WARNING: Skipping histogram due to low statistic! Setting parameters to zero!", "yellow"))
    else:
        _fit = ROOT.TF1('fit_function', "[0]*x+[1]", x_min, x_max)
        _fit.SetParameters(start_param_m, start_param_c)
        _fit.SetParNames("m", "c")
        # fit.SetParLimits(0, 1. - 0.01 * 1., 1. + 0.01 * 1.)
        # fit.SetParLimits(1, 1. - 0.01 * 1., 1. + 0.01 * 1.)
        _results = tobject.Fit(_fit, 'S', '', x_min, x_max)
        # Check if TFitResult is not empty by testing if TFitResultPtr is not -1
        if int(_results) == 0:
            _skip = False
            _parameter = _fit.GetParameters()
            _parameter_errors = _fit.GetParErrors()
        else:
            print(colored("WARNING: Skipping fit due to empty fit results! Setting parameters to zero!", "yellow"))
    return _skip, _parameter, _parameter_errors


@InputROOT.add_function
def histogram_from_linear_extrapolation(tobjects, x_bins, x_min, x_max):
    """
    :param tobjects: list of root TH1 histograms
    :param x_bins: list of ...
    :param x_min:
    :param x_max:
    :return:
    Create new histogram from fitted parameters of a
    """
    # create binning for histogram
    _x_binning = [min([x[0] for x in x_bins])] + sorted([x[1] for x in x_bins])
    # x_min = min([x[0] for x in x_bins])
    # x_max = max([x[1] for x in x_bins])
    # clone tobjects to avoid data corruption
    _tobjects = []
    for _tobject in tobjects:
        _tobjects.append(_ROOTObjectFunctions._project_or_clone(_tobject, "e"))
    # create new histogram to fill results into
    _hist_name = "hist_1d_" + str(uuid.uuid4().get_hex())
    _new_tobject = ROOT.TH1D(_hist_name, _hist_name, len(_tobjects), array('d', _x_binning))
    # access x_axis of new histogram for bin by bin access
    _x_axis = _new_tobject.GetXaxis()
    # Fit function to each histogram
    for index, (_tobject, x_bin) in enumerate(zip(_tobjects, x_bins)):
        _bin_index = _x_axis.FindBin((x_bin[0]+x_bin[1])/2.)
        skip, _parameter, _parameter_errors = jer_poly1_fit(_tobject, x_min, x_max)
        _new_tobject.SetBinContent(_bin_index, _parameter[1])
        _new_tobject.SetBinError(_bin_index, _parameter_errors[1])
        print('Linear extrapolation to {} +/- {}'.format(_parameter[1], _parameter_errors[1]))
    return asrootpy(_new_tobject)


@InputROOT.add_function
def th2_from_linear_extrapolation(tobjects, x_bins, y_bins, x_min, x_max):
    """
    :param tobjects: list of lists of root TH1 histograms [[], []]
    :param x_bins: list of ...
    :param x_min:
    :param x_max:
    :return:
    Create new histogram from fitted parameters of a
    """
    print("XBINS", x_bins)
    print("YBINS", y_bins)
    # check length of input lists:
    _y_len_tobjects = len(tobjects)
    _x_len_tobjects = len(tobjects[0])
    _len_x_bins = len(x_bins)
    _len_y_bins = len(y_bins)
    _fail = False
    if _y_len_tobjects != _len_y_bins:
        print(colored("ERROR: Number of y-bins does not correspond to number of y-entries in tobjects-list", "red"))
        _fail = True
    for _y_index in range(_y_len_tobjects):
        if len(tobjects[_y_index]) != _len_x_bins:
            _x_len_tobjects = len(tobjects[_y_index])
            print(colored("ERROR: Number of x-bins does not correspond to number of x-entries in tobjects-list", "red"))
            _fail = True
    if _fail:
        print("Number of bins: (x: {}, y: {})".format(len(x_bins), len(y_bins)))
        print("Number of tobject entries: (x: {}, y: {})".format(_x_len_tobjects, _y_len_tobjects))
        exit(-1)
    # create binning for histogram
    _x_binning = [min([x[0] for x in x_bins])] + sorted([x[1] for x in x_bins])
    _y_binning = [min([y[0] for y in y_bins])] + sorted([y[1] for y in y_bins])
    # clone tobjects to avoid data corruption
    _tobjects = dict()
    for _y_index in range(len(y_bins)):
        for _x_index in range(len(x_bins)):
            # print("Cloning bin: (x: {}, y: {})".format(_x_index, _y_index))
            _tobjects.update({(_x_index, _y_index): _ROOTObjectFunctions._project_or_clone(tobjects[_y_index][_x_index], "e")})
    # create new histogram to fill results into
    _hist_name = "hist_2d_" + str(uuid.uuid4().get_hex())
    _new_tobject = ROOT.TH2D(_hist_name, _hist_name, len(_x_binning)-1, array('d', _x_binning), len(_y_binning)-1,
                             array('d', _y_binning))
    # get x and y axis for finding the correct bin
    _x_axis = _new_tobject.GetXaxis()
    _y_axis = _new_tobject.GetYaxis()

    # access x_axis, y_axis of new histogram for bin by bin access
    _x_axis = _new_tobject.GetXaxis()
    _y_axis = _new_tobject.GetYaxis()
    # Fit function to each histogram
    for _y_index, _y_bin in enumerate(y_bins):
        _y_bin_index = _y_axis.FindBin((_y_bin[0] + _y_bin[1]) / 2.)
        for _x_index, _x_bin in enumerate(x_bins):
            _x_bin_index = _x_axis.FindBin((_x_bin[0] + _x_bin[1]) / 2.)
            skip, _parameter, _parameter_errors = jer_poly1_fit(_tobjects[(_x_index, _y_index)], x_min, x_max)
            print("Set bin ({}, {}) to {} +/- {}".format(_x_index, _y_index, _parameter[1], _parameter_errors[1]))
            _new_tobject.SetBinContent(_x_bin_index, _y_bin_index, _parameter[1])
            _new_tobject.SetBinError(_x_bin_index, _y_bin_index, _parameter_errors[1])
            print('Linear extrapolation to {} +/- {}'.format(_parameter[1], _parameter_errors[1]))
    return asrootpy(_new_tobject)


@InputROOT.add_function
def jer_tgrapherror_from_poly1_fit(tobject, x_min, x_max):
    # Clone input object for data safety
    _tobject = _ROOTObjectFunctions._project_or_clone(tobject, "e")
    # Use 100 sampling points for TGraphErrors
    sampling_points = 100
    # Create TGraphErrors
    _confidence_interval = ROOT.TGraphErrors(sampling_points)
    # Determine x-value and error used for TGraphErrors
    for _bin_index, x_value in enumerate(np.arange(x_min, x_max, (float(x_max) - float(x_min)) / sampling_points)):
        _confidence_interval.SetPoint(_bin_index, x_value, 0.)
        _confidence_interval.SetPointError(_bin_index, 0., 0.)
    skip, _parameter, _parameter_errors = jer_poly1_fit(_tobject, x_min, x_max)
    if not skip:
        ROOT.TVirtualFitter.GetFitter().GetConfidenceIntervals(_confidence_interval, 0.683)
    else:
        print(colored("WARNING: Skipping extraction of confidence interval, fit not valid!", "yellow"))
    return asrootpy(_confidence_interval)


@InputROOT.add_function
def jer_tgraph_get_point(tgraph, i):
    tmpX, tmpY = ROOT.Double(0), ROOT.Double(0)
    tgraph.GetPoint(i, tmpX, tmpY)
    return float(tmpX), float(tmpY)

@InputROOT.add_function
def jer_tgrapherr_get_binedges(tgraph):
    bin_edges = []
    for i in range(tgraph.GetN()):
        lowedge  = jer_tgraph_get_point(tgraph, i)[0] - tgraph.GetErrorXlow(i)
        highedge = jer_tgraph_get_point(tgraph, i)[0] + tgraph.GetErrorXhigh(i)
        if i == 0:
            bin_edges.append(lowedge)
        bin_edges.append(highedge)
    return bin_edges


@InputROOT.add_function
def jer_to_histogram(root_object):
    if isinstance(root_object, ROOT.TProfile2D):
        return root_object.ProjectionXY()
    elif isinstance(root_object, ROOT.TProfile):
        return root_object.ProjectionX()
    elif isinstance(root_object, ROOT.TH1):
        return root_object
    elif isinstance(root_object, ROOT.TGraph):
        if isinstance(root_object, ROOT.TGraph2D):
            print(colored("Conversion of objects of type %s into histograms is not yet implemented!" % str(type(
                root_object))), "yellow")
            return root_object
        else:
            # first retrieve all values and errors (if available) and then sort them by increasing x values
            x_values = root_object.GetX()
            x_values = [x_values[index] for index in xrange(root_object.GetN())]

            y_values = root_object.GetY()
            y_values = [y_values[index] for index in xrange(root_object.GetN())]

            y_errors = [0.0] * root_object.GetN()
            if isinstance(root_object, ROOT.TGraphAsymmErrors):
                y_errors_high = root_object.GetEYhigh()
                y_errors_low = root_object.GetEYlow()
                y_errors = [(y_errors_high[index] + y_errors_low[index]) / 2.0 for index in xrange(root_object.GetN())]
            elif isinstance(root_object, ROOT.TGraphErrors):
                y_errors = root_object.GetEY()
                y_errors = [y_errors[index] for index in xrange(root_object.GetN())]

            x_values, y_values, y_errors = (list(values) for values in zip(*sorted(zip(x_values, y_values, y_errors))))

            # determining the bin edges for the histogram
            bin_edges = [(x_low + x_high) / 2.0 for x_low, x_high in zip(x_values[:-1], x_values[1:])]
            bin_edges.insert(0, x_values[0] - ((bin_edges[0] - x_values[0]) / 2.0))
            bin_edges.append(x_values[-1] + ((x_values[-1] - bin_edges[-1]) / 2.0))
            if isinstance(root_object, ROOT.TGraphAsymmErrors) or isinstance(root_object, ROOT.TGraphErrors):
                bin_edges = jer_tgrapherr_get_binedges(root_object)

            root_histogram = ROOT.TH1F("histogram_" + root_object.GetName(), root_object.GetTitle(), len(bin_edges) - 1,
                                       array.array("d", bin_edges))
            for index, (y_value, y_error) in enumerate(zip(y_values, y_errors)):
                root_histogram.SetBinContent(index + 1, y_value)
                root_histogram.SetBinError(index + 1, y_error)
            return root_histogram
    else:
        print(colored("Conversion of objects of type %s into histograms is not yet implemented!" % str(type(
            root_object))), "yellow")
        return root_object


@InputROOT.add_function
def jer_ratio(tobject_numerator, tobject_denominator):
    """
    :param tobject_numerator: TH1 histogram used as numerator
    :param tobject_denominator: TH1 histogram used as denominator
    :return:
    Divide two tobjects (TH1, TGraph, TGraphError
    """
    # Clone input objects for not changing the originals
    _tobject_numerator = _ROOTObjectFunctions._project_or_clone(tobject_numerator, "e")
    _tobject_denominator = _ROOTObjectFunctions._project_or_clone(tobject_denominator, "e")

    if isinstance(_tobject_numerator, ROOT.TGraph) and isinstance(_tobject_denominator, ROOT.TGraph):
        # Check if input is TGraphAsymmErrors
        if isinstance(_tobject_numerator, ROOT.TGraphAsymmErrors) and isinstance(_tobject_denominator,
                                                                                 ROOT.TGraphAsymmErrors):
            _tobject_ratio = ROOT.TGraphAsymmErrors()
        # Check if input is TGraphErrors
        elif isinstance(_tobject_numerator, ROOT.TGraphErrors) and isinstance(_tobject_denominator, ROOT.TGraphErrors):
            _tobject_ratio = ROOT.TGraphErrors()
        else:
            _tobject_ratio = ROOT.TGraph()

        successful_division = True
        for point in range(0, _tobject_numerator.GetN()):
            x_value = ROOT.Double(0)
            y_value_numerator = ROOT.Double(0)
            _tobject_numerator.GetPoint(point, x_value, y_value_numerator)
            y_value_denominator = _tobject_denominator.Eval(x_value)
            if y_value_denominator != 0.:
                _tobject_ratio.SetPoint(point, x_value, y_value_numerator/y_value_denominator)
                if isinstance(_tobject_ratio, ROOT.TGraphAsymmErrors):
                    x_err_high = _tobject_numerator.GetErrorXhigh(point)
                    x_err_low = _tobject_numerator.GetErrorXlow(point)
                    y_err_high_numerator = _tobject_numerator.GetErrorYhigh(point)
                    y_err_high_denominator = _tobject_denominator.GetErrorYhigh(point)
                    y_err_low_numerator = _tobject_numerator.GetErrorYlow(point)
                    y_err_low_denominator = _tobject_denominator.GetErrorYlow(point)
                    y_err_high_ratio = np.sqrt(pow(y_err_high_numerator/y_value_denominator, 2) +
                                               (pow(y_value_numerator*y_err_high_denominator, 2) /
                                               pow(y_value_denominator, 4)))
                    y_err_low_ratio = np.sqrt(pow(y_err_low_numerator/y_value_denominator, 2) +
                                              (pow(y_value_numerator*y_err_low_denominator, 2) /
                                              pow(y_value_denominator, 4)))
                    _tobject_ratio.SetPointEXhigh(point, x_err_high)
                    _tobject_ratio.SetPointEXlow(point, x_err_low)
                    _tobject_ratio.SetPointEYhigh(point, y_err_high_ratio)
                    _tobject_ratio.SetPointEYlow(point, y_err_low_ratio)
                elif isinstance(_tobject_ratio, ROOT.TGraphErrors):
                    x_err = _tobject_numerator.GetErrorX(point)
                    y_err_numerator = _tobject_numerator.GetErrorY(point)
                    y_err_denominator = _tobject_denominator.GetErrorY(point)
                    y_err_ratio = np.sqrt(pow(y_err_numerator/y_value_denominator, 2) +
                                          (pow(y_value_numerator*y_err_denominator, 2) / pow(y_value_denominator, 4)))
                    _tobject_ratio.SetPointError(point, x_err, y_err_ratio)
            else:
                successful_division = False
    else:
        _tobject_ratio = jer_to_histogram(_tobject_numerator)
        successful_division = _tobject_ratio.Divide(jer_to_histogram(_tobject_denominator))
    if not successful_division:
        if isinstance(_tobject_ratio, ROOT.TGraph):
            print(colored("WARNING: Could not successfully divide all points of the graphs '{0}' and '{1}'!".format(
                type(_tobject_numerator), type(_tobject_denominator)), "yellow"))
        else:
            print(colored("WARNING: Could not successfully divide histogram(s) '{0}' by '{1}'!".format(
                type(_tobject_numerator), type(_tobject_denominator)), "yellow"))
    # _nPoints = _tobject_ratio.GetN()
    # test_x = _tobject_ratio.GetX()
    # test_xerr = _tobject_ratio.GetEX()
    # test_y = _tobject_ratio.GetY()
    # test_yerr = _tobject_ratio.GetEY()
    # test_x.SetSize(_nPoints)
    # test_xerr.SetSize(_nPoints)
    # test_y.SetSize(_nPoints)
    # test_yerr.SetSize(_nPoints)
    # print(list(test_x))
    # print(list(test_xerr))
    # print(list(test_y))
    # print(list(test_yerr))
    return asrootpy(_tobject_ratio)


@InputROOT.add_function
def jer_get_error_hist(tobject):
    if isinstance(tobject, ROOT.TH1D) or isinstance(tobject, ROOT.TH1F):
        _n_bins = tobject.GetNbinsX()
        _tobject = _ROOTObjectFunctions._project_or_clone(tobject, "e")
        for _bin_index in range(_n_bins):
            _bin_index += 1
            _tobject.SetBinContent(_bin_index, _tobject.GetBinError(_bin_index))
    elif isinstance(tobject, ROOT.TH2D) or isinstance(tobject, ROOT.TH2F):
        _n_bins_x = tobject.GetNbinsX()
        _n_bins_y = tobject.GetNbinsY()
        _tobject = _ROOTObjectFunctions._project_or_clone(tobject, "e")
        for _bin_index_x in range(_n_bins_x):
            _bin_index_x += 1
            for _bin_index_y in range(_n_bins_y):
                _bin_index_y += 1
                _tobject.SetBinContent(_bin_index_x, _bin_index_y, _tobject.GetBinError(_bin_index_x, _bin_index_y))
    else:
        print(colored("WARNING: No valid input histogram '{0}'!".format(type(tobject))))
    return asrootpy(_tobject)


@InputROOT.add_function
def jer_get_pull(tobject_a, tobject_b):
    _tobject_a = _ROOTObjectFunctions._project_or_clone(tobject_a, "e")
    _tobject_b = _ROOTObjectFunctions._project_or_clone(tobject_b, "e")
    _new_tobject = _ROOTObjectFunctions._project_or_clone(tobject_a, "e")
    if isinstance(_tobject_a, (ROOT.TH1D, ROOT.TH1F)) and isinstance(_tobject_b, (ROOT.TH1D, ROOT.TH1F)):
        if list(_tobject_a.GetXaxis().GetXbins()) == list(_tobject_b.GetXaxis().GetXbins()):
            _n_bins = _tobject_a.GetNbinsX()
            for _bin_index in range(_n_bins):
                _bin_index += 1
                _numerator = abs(_tobject_a.GetBinContent(_bin_index) - _tobject_b.GetBinContent(_bin_index))
                _denominator = np.sqrt(abs(np.power(_tobject_a.GetBinError(_bin_index), 2) +
                                           np.power(_tobject_b.GetBinError(_bin_index), 2)))
                _pull = _numerator / _denominator if _denominator != 0. else 0.
                _new_tobject.SetBinContent(_bin_index, _pull)
                _new_tobject.SetBinError(_bin_index, 0.)
        else:
            print(colored("Error: Input histograms have different number of bins!"))
    if isinstance(_tobject_a, (ROOT.TH2D, ROOT.TH2F)) and isinstance(_tobject_b, (ROOT.TH2D, ROOT.TH2F)):
        _n_bins_x = _tobject_a.GetNbinsX()
        _n_bins_y = _tobject_a.GetNbinsY()
        # if (list(_tobject_a.GetXaxis().GetXbins()) == list(_tobject_b.GetXaxis().GetXbins())) and \
        #         (list(_tobject_a.GetYaxis().GetYbins()) == list(_tobject_b.GetYaxis().GetYbins())):
        if _n_bins_x == _tobject_b.GetNbinsX() and _n_bins_y == _tobject_b.GetNbinsY():
            for _bin_index_x in range(_n_bins_x):
                _bin_index_x += 1
                for _bin_index_y in range(_n_bins_y):
                    _bin_index_y += 1
                    _numerator = abs(_tobject_a.GetBinContent(_bin_index_x, _bin_index_y) -
                             _tobject_b.GetBinContent(_bin_index_x, _bin_index_y))
                    _denominator = np.sqrt(abs(np.power(_tobject_a.GetBinError(_bin_index_x, _bin_index_y), 2) +
                                               np.power(_tobject_b.GetBinError(_bin_index_x, _bin_index_y), 2)))
                    # _ratio_tobject = _tobject_a/_tobject_b
                    # _numerator = abs(_ratio_tobject.GetBinContent(_bin_index_x, _bin_index_y) - 1)
                    # _denominator = abs(_ratio_tobject.GetBinError(_bin_index_x, _bin_index_y))
                    _pull = _numerator / _denominator if _denominator != 0. else 0.
                    # print("a: {}".format(_tobject_a.GetBinContent(_bin_index_x, _bin_index_y)))
                    # print("b: {}".format(_tobject_b.GetBinContent(_bin_index_x, _bin_index_y)))
                    # print("a_err: {}".format(_tobject_a.GetBinError(_bin_index_x, _bin_index_y)))
                    # print("b_err: {}".format(_tobject_b.GetBinError(_bin_index_x, _bin_index_y)))
                    # print("pull: {}".format(_pull))
                    _new_tobject.SetBinContent(_bin_index_x, _bin_index_y, _pull)
                    _new_tobject.SetBinError(_bin_index_x, _bin_index_y, 0.)
        else:
            print(colored("Error: Input histograms have different number of bins!"))
    else:
        print(colored("WARNING: No valid input histogram '{0}'!".format(type(tobject_a))))
    return asrootpy(_new_tobject)


@InputROOT.add_function
def jer_th2_from_th1s(tobjects, y_bins):
    """
    :param tobjects: list of lists of root TH1 histograms [ , ]
    :param y_bins: list of bin borders tuples [(1,2), (2,3)] used for y-axis
    :param x_min:
    :param x_max:
    :return:
    Create new 2D histogramm from multiple 1D histograms
    """
    # check length of input lists:
    _y_len_tobjects = len(tobjects)
    _len_y_bins = len(y_bins)
    _fail = False
    if _y_len_tobjects != _len_y_bins:
        print(colored("ERROR: Number of y-bins does not correspond to number of y-entries in tobjects-list", "red"))
        _fail = True
    # TODO: Check that all histograms in list have same x-binning
    # print(colored("ERROR: Number of x-bins does not correspond to number of x-entries in tobjects-list", "red"))
    # _fail = True
    if _fail:
        print("Number of bins: (x: {}, y: {})".format('-not-known-', len(y_bins)))
        print("Number of tobject entries: (x: {}, y: {})".format('-not-known-', _y_len_tobjects))
        exit(-1)
    # create binning for histogram
    _y_binning = [min([y[0] for y in y_bins])] + sorted([y[1] for y in y_bins])
    _x_binning = tobjects[0].GetXaxis().GetXbins()
    # clone tobjects to avoid data corruption
    _tobjects = dict()
    for _y_index in range(len(y_bins)):
        # print("Cloning bin: (x: {}, y: {})".format('-not-known-', _y_index))
        _tobjects.update({_y_index: _ROOTObjectFunctions._project_or_clone(tobjects[_y_index], "e")})
    # create new histogram to fill results into
    _hist_name = "hist_2d_" + str(uuid.uuid4().get_hex())
    _new_tobject = ROOT.TH2D(_hist_name, _hist_name, len(_x_binning) - 1, array('d', _x_binning), len(_y_binning) - 1,
                             array('d', _y_binning))
    # access x_axis, y_axis of new histogram for bin by bin access
    _x_axis = _new_tobject.GetXaxis()
    _y_axis = _new_tobject.GetYaxis()
    # Fit function to each histogram
    for _y_index, _y_bin in enumerate(y_bins):
        _y_bin_index = _y_axis.FindBin((_y_bin[0] + _y_bin[1]) / 2.)
        for _x_bin_index in range(_x_axis.GetNbins()):
            _x_bin_index+=1
            value = _tobjects[_y_index].GetBinContent(_x_bin_index)
            uncertainty = _tobjects[_y_index].GetBinError(_x_bin_index)
            print("Set bin ({}, {}) to {} +/- {}".format(_x_bin_index, _y_bin_index, value, uncertainty))
            _new_tobject.SetBinContent(_x_bin_index, _y_bin_index, value)
            _new_tobject.SetBinError(_x_bin_index, _y_bin_index, uncertainty)
    return asrootpy(_new_tobject)