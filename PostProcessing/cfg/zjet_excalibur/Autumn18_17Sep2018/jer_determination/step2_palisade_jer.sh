#!/bin/bash

# -- step 2: run Palisade to combine the "pre-combination" files to the full
# combination files for submission to JEC

#channels="mm ee"
channels="mm"

rootfiles_truncated_rms=false
rootfiles_truncated_Gaussian=false
rootfiles_truncated_LogNormal=false

plotting_truncated_rms=false
plotting_truncated_Gaussian=false
plotting_truncated_LogNormal=false

plotting_truncation_scan=false

plotting_extrapolation_RMS=false
plotting_extrapolation_Gaussian=false
plotting_extrapolation_LogNormal=false

rootfiles_extrapolation_RMS=false
rootfiles_extrapolation_Gaussian=false
rootfiles_extrapolation_LogNormal=false

plotting_dependency_RMS=false
plotting_dependency_Gaussian=false
plotting_dependency_LogNormal=false

rootfiles_dependency=false

plotting_2d_dependency_RMS=true
plotting_2d_dependency_Gaussian=false
plotting_2d_dependency_LogNormal=false

# settings:
DATA_VERSION='ABCD'
JEC_VERSION='Autumn18_JECV8'

# for debugging use command:
# python -m cProfile -s tottime -o debug.prof /home/christoph/.local/bin/palisade.py ...

if ${rootfiles_truncated_rms}; then
    echo "Saving truncated RMS results"
    echo "==================================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_rootfiles \
            --basename-data "JER_Binning_Data_${DATA_VERSION}" \
            --basename-mc 'JER_Binning_MC' \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-levels "L1L2Res" \
            --run-periods Run2018{ABCD} \
            --channel "${channel}"\
            --output-dir JER_truncated_RMS \
            --root \
            --extraction-method "R"
    done
fi

if ${rootfiles_truncated_Gaussian}; then
    echo "Saving truncated Gaussian results"
    echo "==================================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_rootfiles \
            --basename-data "JER_Binning_Data_${DATA_VERSION}" \
            --basename-mc 'JER_Binning_MC' \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-levels "L1L2Res" \
            --run-periods Run2018{ABCD} \
            --channel "${channel}"\
            --output-dir JER_truncated_Gaussian_fit \
            --root \
            --extraction-method "G"
    done
fi

if ${rootfiles_truncated_LogNormal}; then
    echo "Saving truncated logNormal results"
    echo "==================================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_rootfiles \
            --basename-data "JER_Binning_Data_${DATA_VERSION}" \
            --basename-mc 'JER_Binning_MC' \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-levels "L1L2Res" \
            --run-periods Run2018{ABCD} \
            --channel "${channel}"\
            --output-dir JER_truncated_LogNormal_fit \
            --root \
            --extraction-method "L"
    done
fi

if ${plotting_truncated_rms}; then
    echo "Plotting truncated RMS results"
    echo "==================================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_rootfiles \
            --basename-data "JER_Binning_Data_${DATA_VERSION}" \
            --basename-mc 'JER_Binning_MC' \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-levels "L1L2Res" \
            --run-periods Run2018{ABCD} \
            --channel "${channel}"\
            --output-dir JER_truncated_RMS
    done
fi

if ${plotting_truncation_scan}; then
    echo "Plotting truncation scan results"
    echo "==================================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_truncationscan \
            --basename-data "JER_Binning_Data_${DATA_VERSION}" \
            --basename-mc 'JER_Binning_MC' \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-levels "L1L2Res" \
            --run-periods Run2018{ABCD} \
            --channel "${channel}"\
            --output-dir JER_Truncation_Scan
    done
fi

if ${plotting_extrapolation_RMS}; then
    echo "Plotting RMS extrapolation results:"
    echo "==============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_extrapolation \
            --basename JER_truncated_RMS \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_Extrapolation
#            --test \
    done
fi

if ${plotting_extrapolation_Gaussian}; then
    echo "Plotting Gaussian extrapolation results:"
    echo "==============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_extrapolation \
            --basename JER_truncated_Gaussian_fit \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_Extrapolation
#            --test \
    done
fi

if ${plotting_extrapolation_LogNormal}; then
    echo "Plotting LogNormal extrapolation results:"
    echo "==============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_extrapolation \
            --basename JER_truncated_LogNormal_fit \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_Extrapolation
#            --test \
    done
fi

if ${rootfiles_extrapolation_RMS}; then
    echo "Saving extrapolation results:"
    echo "============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_extrapolation \
            --basename JER_truncated_RMS \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_Extrapolation\
            --root
    #         \
    #        --test
    done
fi

if ${rootfiles_extrapolation_Gaussian}; then
    echo "Saving extrapolation results:"
    echo "============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_extrapolation \
            --basename JER_truncated_Gaussian_fit \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_Extrapolation\
            --root
    #         \
    #        --test
    done
fi

if ${rootfiles_extrapolation_LogNormal}; then
    echo "Saving extrapolation results:"
    echo "============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_extrapolation \
            --basename JER_truncated_LogNormal_fit \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_Extrapolation\
            --root
    #         \
    #        --test
    done
fi

if ${plotting_dependency_RMS}; then
    echo "Plotting RMS dependency results:"
    echo "============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_dependency \
            --basename JER_truncated_RMS \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_truncated_RMS_Dependency\
            --quantities "jer-gen-mc" \
            --colors "orange"
    done
fi

if ${plotting_dependency_Gaussian}; then
    echo "Plotting Gaussian dependency results:"
    echo "============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_dependency \
            --basename JER_truncated_Gaussian_fit \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_truncated_Gaussian_Dependency\
            --quantities "jer-gen-mc" \
            --colors "orange"
    done
fi

if ${plotting_dependency_LogNormal}; then
    echo "Plotting logNormal dependency results:"
    echo "============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_dependency \
            --basename JER_truncated_LogNormal_fit \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_truncated_LogNormal_Dependency\
            --quantities "jer-gen-mc" \
            --colors "orange"
    done
fi

if ${rootfiles_dependency}; then
    echo "Saving RMS dependency results:"
    echo "============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_dependency \
            --basename JER_truncated_RMS \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_truncated_RMS_Dependency\
            --root
    #         \
    #        --test
    done
fi

if ${plotting_2d_dependency_RMS}; then
    echo "Plotting RMS 2D dependency results:"
    echo "============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_2d_dependency \
            --basename JER_truncated_RMS \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_truncated_RMS_Dependency\
            --quantities "jer-gen-mc" \
            --colors "orange"
    done
fi

if ${plotting_2d_dependency_Gaussian}; then
    echo "Plotting RMS 2D dependency results:"
    echo "============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_2d_dependency \
            --basename JER_truncated_Gaussian_fit \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_truncated_Gaussian_Dependency\
            --quantities "jer-gen-mc" \
            --colors "orange"
    done
fi

if ${plotting_2d_dependency_LogNormal}; then
    echo "Plotting RMS 2D dependency results:"
    echo "============================="

    for channel in ${channels}; do
        echo "Processing channel: ${channel}"

        palisade.py task zjet_excalibur jer_plot_2d_dependency \
            --basename JER_truncated_LogNormal_fit \
            --jec ${JEC_VERSION} \
            --sample 17Sep2018 \
            --corr-level "L1L2Res" \
            --run-periods Run2018ABCD \
            --channel "${channel}" \
            --output-dir JER_truncated_LogNormal_Dependency\
            --quantities "jer-gen-mc" \
            --colors "orange"
    done
fi