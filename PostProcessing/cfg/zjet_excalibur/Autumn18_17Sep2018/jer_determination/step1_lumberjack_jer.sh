#!/bin/bash

# use a version of ROOT that has RDataFrames
source `which with_root_df`

# -- 2018

# -- step1: use Lumberjack to create "pre-combination" files from Excalibur TTrees
# Note: if these already exist, they are skipped, unless `--overwrite` flag is passed

# SAMPLE_DIR="/ceph/dsavoiu/JEC/Autumn18/17Sep2018_V5_2019-02-26"
# DATA_VERSION="17Sep2018"
# JEC_VERSION="Autumn18_JECV5"
SAMPLE_DIR="/portal/ekpbms3/home/cheidecker/excalibur_work/excalibur_rootfiles"
DATA_VERSION="17Sep2018"
JEC_VERSION="Autumn18_JECV8"

# for _ch in "mm" "ee"; do
for _ch in "mm"; do
    INFILE_DATA_ABCD="${SAMPLE_DIR}/data18_${_ch}_ABCD_${DATA_VERSION}.root"
    INFILE_DATA_ABC="${SAMPLE_DIR}/data18_${_ch}_ABC_${DATA_VERSION}.root"
    INFILE_DATA_D="${SAMPLE_DIR}/data18_${_ch}_D_${DATA_VERSION}.root"
    INFILE_MC="${SAMPLE_DIR}/mc18_${_ch}_DYNJ_Madgraph.root"

    # -- MC
    for _corr_level in "L1L2L3"; do
        OUTPUT_FILE_SUFFIX="Z${_ch}_${DATA_VERSION}_${JEC_VERSION}_${_corr_level}"

        lumberjack.py -a zjet_excalibur -i "$INFILE_MC" \
            --tree "basiccuts_${_corr_level}/ntuple" \
            --input-type mc \
            --selections "alpha_jer" \
            -j10 \
            --log --progress \
            $@ \
            task JER_Binning_MC \
            --output-file-suffix "$OUTPUT_FILE_SUFFIX"
    done

    # -- DATA (runs A, B, C, D with corr level L1L2Res)

    for _corr_level in "L1L2Res"; do
        OUTPUT_FILE_SUFFIX="ABCD_Z${_ch}_${DATA_VERSION}_${JEC_VERSION}_${_corr_level}"

        lumberjack.py -a zjet_excalibur -i "$INFILE_DATA_ABCD" \
            --tree "basiccuts_${_corr_level}/ntuple" \
            --input-type data \
            --selections "alpha_jer" \
            -j10 \
            --log --progress \
            $@ \
            task JER_Binning_Data \
            --output-file-suffix "$OUTPUT_FILE_SUFFIX"
    done

    # -- DATA (runs A, B, C with corr level L1L2Res)

    for _corr_level in "L1L2Res"; do
        OUTPUT_FILE_SUFFIX="ABC_Z${_ch}_${DATA_VERSION}_${JEC_VERSION}_${_corr_level}"

        lumberjack.py -a zjet_excalibur -i "$INFILE_DATA_ABC" \
            --tree "basiccuts_${_corr_level}/ntuple" \
            --input-type data \
            --selections "alpha_jer" \
            -j10 \
            --log --progress \
            $@ \
            task JER_Binning_Data \
            --output-file-suffix "$OUTPUT_FILE_SUFFIX"
    done

    # -- DATA (run D with corr level L1L2Res)

    for _corr_level in "L1L2Res"; do
        OUTPUT_FILE_SUFFIX="D_Z${_ch}_${DATA_VERSION}_${JEC_VERSION}_${_corr_level}"

        lumberjack.py -a zjet_excalibur -i "$INFILE_DATA_D" \
            --tree "basiccuts_${_corr_level}/ntuple" \
            --input-type data \
            --selections "alpha_jer" \
            -j10 \
            --log --progress \
            $@ \
            task JER_Binning_Data \
            --output-file-suffix "$OUTPUT_FILE_SUFFIX"
    done

done
