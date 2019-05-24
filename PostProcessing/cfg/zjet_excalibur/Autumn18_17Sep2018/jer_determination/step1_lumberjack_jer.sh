#!/bin/bash

# use a version of ROOT that has RDataFrames
source `which with_root_df`

# -- 2018

# -- step1: use Lumberjack to create "pre-combination" files from Excalibur TTrees
# Note: if these already exist, they are skipped, unless `--overwrite` flag is passed

SAMPLE_DIR="/ceph/dsavoiu/JEC/Autumn18/17Sep2018_V5_2019-02-26"

for _ch in "mm" "ee"; do
    INFILE_DATA="${SAMPLE_DIR}/data18_${_ch}_ABCD_17Sep2018.root"
    INFILE_MC="${SAMPLE_DIR}/mc18_${_ch}_DYNJ_Madgraph.root"

    # -- MC
    for _corr_level in "L1L2L3"; do
        OUTPUT_FILE_SUFFIX="Z${_ch}_17Sep2018_Autumn18_JECV5_${_corr_level}"

        lumberjack.py -a zjet_excalibur -i "$INFILE_MC" \
            --tree "basiccuts_${_corr_level}/ntuple" \
            --type mc \
            --selections "alpha" \
            -j10 \
            --log --progress \
            $@ \
            task JER_Binning_MC \
            --output-file-suffix "$OUTPUT_FILE_SUFFIX"
    done

    # -- DATA (runs A, B, C with corr level L1L2Res)

    for _corr_level in "L1L2Res"; do
        OUTPUT_FILE_SUFFIX="Z${_ch}_17Sep2018_Autumn18_JECV5_${_corr_level}"

        lumberjack.py -a zjet_excalibur -i "$INFILE_DATA" \
            --tree "basiccuts_${_corr_level}/ntuple" \
            --type data \
            --selections "alpha" \
            -j10 \
            --log --progress \
            $@ \
            task JER_Binning_Data \
            --output-file-suffix "$OUTPUT_FILE_SUFFIX"
    done

done
