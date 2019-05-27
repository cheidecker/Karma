#!/bin/bash

# -- step 2: run Palisade to combine the "pre-combination" files to the full
# combination files for submission to JEC

rootfiles_truncated_rms=true
plotting_truncated_rms=false

plotting_extrapolation=false
rootfiles_extrapolation=false

plotting_dependency=false
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

    palisade.py task zjet_excalibur jer_rootfiles \
        --basename-data 'JER_Binning_Data' \
        --basename-mc 'JER_Binning_MC' \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-levels "L1L2Res" \
        --run-periods Run2018{ABCD} \
        --channel "ee"\
        --output-dir JER_truncated_RMS \
        --root
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

    palisade.py task zjet_excalibur jer_rootfiles \
        --basename-data 'JER_Binning_Data' \
        --basename-mc 'JER_Binning_MC' \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-levels "L1L2Res" \
        --run-periods Run2018{ABCD} \
        --channel "ee"\
        --output-dir JER_truncated_RMS
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

    palisade.py task zjet_excalibur jer_plot_extrapolation \
        --basename JER_truncated_RMS \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-level "L1L2Res" \
        --run-periods Run2018ABCD \
        --channel "ee" \
        --output-dir JER_Extrapolation
#        \
#        --quantities "jer-gen-mc" \
#        --colors "orange"
#        \
#        --test
        # "ptbalance-data" "ptbalance-mc" "pli-mc" "zres-mc"
        # "grey" "royalblue" "springgreen" "forestgreen"
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

    palisade.py task zjet_excalibur jer_plot_extrapolation \
        --basename JER_truncated_RMS \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-level "L1L2Res" \
        --run-periods Run2018ABCD \
        --channel "ee" \
        --output-dir JER_Extrapolation\
        --root
#         \
#        --test
fi

if $plotting_dependency; then
    echo "Plotting dependency results:"
    echo "============================="

    palisade.py task zjet_excalibur jer_plot_dependency \
        --basename JER_truncated_RMS \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-level "L1L2Res" \
        --run-periods Run2018ABCD \
        --channel "mm" \
        --output-dir JER_Dependency\
        --quantities "jer-gen-mc" \
        --colors "orange"

    palisade.py task zjet_excalibur jer_plot_dependency \
        --basename JER_truncated_RMS \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-level "L1L2Res" \
        --run-periods Run2018ABCD \
        --channel "ee" \
        --output-dir JER_Dependency\
        --quantities "jer-gen-mc" \
        --colors "orange"
fi

if $rootfiles_dependency; then
    echo "Saving dependency results:"
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

    palisade.py task zjet_excalibur jer_plot_dependency \
        --basename JER_truncated_RMS \
        --jec Autumn18_JECV5 \
        --sample 17Sep2018 \
        --corr-level "L1L2Res" \
        --run-periods Run2018ABCD \
        --channel "ee" \
        --output-dir JER_Extrapolation\
        --root
#         \
#        --test
fi
