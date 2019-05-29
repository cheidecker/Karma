#!/bin/bash

# -- step 2: run Palisade to combine the "pre-combination" files to the full
# combination files for submission to JEC

plotting_truncated_rms=false
plotting_truncated_Gaussian=false
plotting_truncated_logNormal=false

rootfiles_truncated_rms=false
rootfiles_truncated_Gaussian=false
rootfiles_truncated_logNormal=false

plotting_extrapolation=false
rootfiles_extrapolation=false

plotting_dependency=true
plotting_dependency_Gaussian=true
plotting_dependency_logNormal=true

rootfiles_dependency=false

if $rootfiles_truncated_rms; then
    echo "Saving truncated RMS results"
    echo "==================================="

    palisade.py task zjet_excalibur jer_rootfiles \
        --basename-data 'JER_Binning_Data' \
        --basename-mc 'JER_Binning_MC' \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-levels "L1L2Res" \
        --run-periods Run2018{ABCD} \
        --channel "mm"\
        --output-dir JER_truncated_RMS \
        --root

#    palisade.py task zjet_excalibur jer_rootfiles \
#        --basename-data 'JER_Binning_Data' \
#        --basename-mc 'JER_Binning_MC' \
#        --jec Autumn18_JECV5 \
#        --sample 17Sep2018 \
#        --corr-levels "L1L2Res" \
#        --run-periods Run2018{ABCD} \
#        --channel "ee"\
#        --output-dir JER_truncated_RMS \
#        --root
fi

if $rootfiles_truncated_Gaussian; then
    echo "Saving truncated Gaussian results"
    echo "==================================="

    palisade.py task zjet_excalibur jer_rootfiles_Gaussian \
        --basename-data 'JER_Binning_Data' \
        --basename-mc 'JER_Binning_MC' \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-levels "L1L2Res" \
        --run-periods Run2018{ABCD} \
        --channel "mm"\
        --output-dir JER_truncated_Gaussian \
        --root

#    palisade.py task zjet_excalibur jer_rootfiles \
#        --basename-data 'JER_Binning_Data' \
#        --basename-mc 'JER_Binning_MC' \
#        --jec Autumn18_JECV5 \
#        --sample 17Sep2018 \
#        --corr-levels "L1L2Res" \
#        --run-periods Run2018{ABCD} \
#        --channel "ee"\
#        --output-dir JER_truncated_Gaussian \
#        --root
fi

if $rootfiles_truncated_logNormal; then
    echo "Saving truncated logNormal results"
    echo "==================================="

    palisade.py task zjet_excalibur jer_rootfiles_logNormal \
        --basename-data 'JER_Binning_Data' \
        --basename-mc 'JER_Binning_MC' \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-levels "L1L2Res" \
        --run-periods Run2018{ABCD} \
        --channel "mm"\
        --output-dir JER_truncated_logNormal \
        --root

#    palisade.py task zjet_excalibur jer_rootfiles \
#        --basename-data 'JER_Binning_Data' \
#        --basename-mc 'JER_Binning_MC' \
#        --jec Autumn18_JECV5 \
#        --sample 17Sep2018 \
#        --corr-levels "L1L2Res" \
#        --run-periods Run2018{ABCD} \
#        --channel "ee"\
#        --output-dir JER_truncated_logNormal \
#        --root
fi

if $plotting_truncated_rms; then
    echo "Plotting truncated RMS results"
    echo "==================================="

    palisade.py task zjet_excalibur jer_rootfiles \
        --basename-data 'JER_Binning_Data' \
        --basename-mc 'JER_Binning_MC' \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-levels "L1L2Res" \
        --run-periods Run2018{ABCD} \
        --channel "mm"\
        --output-dir JER_truncated_RMS

#    palisade.py task zjet_excalibur jer_rootfiles \
#        --basename-data 'JER_Binning_Data' \
#        --basename-mc 'JER_Binning_MC' \
#        --jec Autumn18_JECV5 \
#        --sample 17Sep2018 \
#        --corr-levels "L1L2Res" \
#        --run-periods Run2018{ABCD} \
#        --channel "ee"\
#        --output-dir JER_truncated_RMS
fi

if $plotting_extrapolation; then
    echo "Plotting extrapolation results:"
    echo "==============================="

    palisade.py task zjet_excalibur jer_plot_extrapolation \
        --basename JER_truncated_RMS \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-level "L1L2Res" \
        --run-periods Run2018ABCD \
        --channel "mm" \
        --output-dir JER_Extrapolation
#        \
#        --quantities "jer-gen-mc" \
#        --colors "orange"
#        \
#        --test
        # "ptbalance-data" "ptbalance-mc" "pli-mc" "zres-mc"
        # "black" "royalblue" "springgreen" "forestgreen"

#    palisade.py task zjet_excalibur jer_plot_extrapolation \
#        --basename JER_truncated_RMS \
#        --jec Autumn18_JECV5 \
#        --sample 17Sep2018 \
#        --corr-level "L1L2Res" \
#        --run-periods Run2018ABCD \
#        --channel "ee" \
#        --output-dir JER_Extrapolation
##        \
##        --quantities "jer-gen-mc" \
##        --colors "orange"
##        \
##        --test
#        # "ptbalance-data" "ptbalance-mc" "pli-mc" "zres-mc"
#        # "grey" "royalblue" "springgreen" "forestgreen"
fi

if $rootfiles_extrapolation; then
    echo "Saving extrapolation results:"
    echo "============================="

    palisade.py task zjet_excalibur jer_plot_extrapolation \
        --basename JER_truncated_RMS \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-level "L1L2Res" \
        --run-periods Run2018ABCD \
        --channel "mm" \
        --output-dir JER_Extrapolation\
        --root
#         \
#        --test

#    palisade.py task zjet_excalibur jer_plot_extrapolation \
#        --basename JER_truncated_RMS \
#        --jec Autumn18_JECV5 \
#        --sample 17Sep2018 \
#        --corr-level "L1L2Res" \
#        --run-periods Run2018ABCD \
#        --channel "ee" \
#        --output-dir JER_Extrapolation\
#        --root
##         \
##        --test
fi

if $plotting_dependency; then
    echo "Plotting RMS dependency results:"
    echo "============================="

    palisade.py task zjet_excalibur jer_plot_dependency \
        --basename JER_truncated_RMS \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-level "L1L2Res" \
        --run-periods Run2018ABCD \
        --channel "mm" \
        --output-dir JER_truncated_RMS_Dependency\
        --quantities "jer-gen-mc" \
        --colors "orange"

#    palisade.py task zjet_excalibur jer_plot_dependency \
#        --basename JER_truncated_RMS \
#        --jec Autumn18_JECV5 \
#        --sample 17Sep2018 \
#        --corr-level "L1L2Res" \
#        --run-periods Run2018ABCD \
#        --channel "ee" \
#        --output-dir JER_truncated_RMS_Dependency\
#        --quantities "jer-gen-mc" \
#        --colors "orange"
fi

if $plotting_dependency_Gaussian; then
    echo "Plotting Gaussian dependency results:"
    echo "============================="

    palisade.py task zjet_excalibur jer_plot_dependency \
        --basename JER_truncated_Gaussian \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-level "L1L2Res" \
        --run-periods Run2018ABCD \
        --channel "mm" \
        --output-dir JER_truncated_Gaussian_Dependency\
        --quantities "jer-gen-mc" \
        --colors "orange"

#    palisade.py task zjet_excalibur jer_plot_dependency \
#        --basename JER_truncated_Gaussian \
#        --jec Autumn18_JECV5 \
#        --sample 17Sep2018 \
#        --corr-level "L1L2Res" \
#        --run-periods Run2018ABCD \
#        --channel "ee" \
#        --output-dir JER_truncated_Gaussian_Dependency\
#        --quantities "jer-gen-mc" \
#        --colors "orange"
fi

if $plotting_dependency_logNormal; then
    echo "Plotting logNormal dependency results:"
    echo "============================="

    palisade.py task zjet_excalibur jer_plot_dependency \
        --basename JER_truncated_logNormal \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-level "L1L2Res" \
        --run-periods Run2018ABCD \
        --channel "mm" \
        --output-dir JER_truncated_logNormal_Dependency\
        --quantities "jer-gen-mc" \
        --colors "orange"

#    palisade.py task zjet_excalibur jer_plot_dependency \
#        --basename JER_truncated_logNormal \
#        --jec Autumn18_JECV5 \
#        --sample 17Sep2018 \
#        --corr-level "L1L2Res" \
#        --run-periods Run2018ABCD \
#        --channel "ee" \
#        --output-dir JER_truncated_logNormal_Dependency\
#        --quantities "jer-gen-mc" \
#        --colors "orange"
fi

if $rootfiles_dependency; then
    echo "Saving RMS dependency results:"
    echo "============================="

    palisade.py task zjet_excalibur jer_plot_dependency \
        --basename JER_truncated_RMS \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-level "L1L2Res" \
        --run-periods Run2018ABCD \
        --channel "mm" \
        --output-dir JER_Extrapolation\
        --root
#         \
#        --test

#    palisade.py task zjet_excalibur jer_plot_dependency \
#        --basename JER_truncated_RMS \
#        --jec Autumn18_JECV5 \
#        --sample 17Sep2018 \
#        --corr-level "L1L2Res" \
#        --run-periods Run2018ABCD \
#        --channel "ee" \
#        --output-dir JER_Extrapolation\
#        --root
##         \
##        --test
fi


