#!/bin/bash

########################################################################################################
##USER CONFIGURATIONS
WORKING_DIR=/work/04171/dpisner/data/ABM/MELODIC_ICA
########################################################################################################

########################################################################################################
##Prepare rsfMRI and segmented T1 anatomical images for preprocessing
########################################################################################################
for i in `ls $WORKING_DIR/FEAT_preprocessing`; do
  fsl_motion_outliers -i $WORKING_DIR/FEAT_preprocessing/"$i"/"$i"_BOLD_raw_despiked.nii -o $WORKING_DIR/FEAT_preprocessing/$i/motion_parameters.txt -p $WORKING_DIR/FEAT_preprocessing/$i/motion_plot.png -v;
done

for i in `ls $WORKING_DIR/FEAT_preprocessing`; do
  #cp $WORKING_DIR/data/ABM/indiv_analysis/$i/bold/rest1/pre/rest1_bold_raw.nii $WORKING_DIR/FEAT_preprocessing/$i/"$i"_BOLD_raw.nii &
  #sleep 1
  #cp $WORKING_DIR/data/ABM/indiv_analysis/$i/3danat_rest/pre/anat_brain.nii.gz $WORKING_DIR/FEAT_preprocessing/$i/"$i"_T1_raw.nii.gz &
  #sleep 1
  cp $WORKING_DIR/data/ABM/indiv_analysis/$i/3danat_rest/pre/anat.nii $WORKING_DIR/FEAT_preprocessing/$i/"$i"_anat.nii &
  echo $i
done

##Despike everyone's BOLD
for i in `ls $WORKING_DIR/data/ABM/indiv_analysis | grep ^s | grep -v .txt`; do
  export OMP_NUM_THREADS=4
  3dDespike -prefix $WORKING_DIR/FEAT_preprocessing/$i/"$i"_BOLD_raw_despiked.nii $WORKING_DIR/FEAT_preprocessing/"$i"/"$i"_BOLD_raw.nii &
  sleep 5
done

##Generate CSF regressor
for i in `ls $WORKING_DIR/FEAT_preprocessing`; do
  #Generate example_func2highres_inv.mat
  flirt -in $WORKING_DIR/FEAT_preprocessing/$i/"$i"_BOLD_raw_despiked.nii -ref $WORKING_DIR/FEAT_preprocessing/$i/"$i"_anat_brain.nii.gz -out $WORKING_DIR/FEAT_preprocessing/$i/example_func2highres -omat $WORKING_DIR/FEAT_preprocessing/$i/example_func2highres.mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear

  convert_xfm -inverse -omat $WORKING_DIR/FEAT_preprocessing/$i/example_func2highres_inv.mat $WORKING_DIR/FEAT_preprocessing/$i/example_func2highres.mat

  #fast -t 1 $WORKING_DIR/FEAT_preprocessing/$i/"$i"_anat_brain.nii.gz

  #Apply inverse transformation parameters from example2highres to mask with filtered_func_data.nii.gz as target using ApplyXFM For CSF
  flirt -in $WORKING_DIR/FEAT_preprocessing/$i/"$i"_anat_brain_pve_0.nii.gz -ref $WORKING_DIR/FEAT_preprocessing/$i/"$i"_BOLD_raw_despiked.nii -applyxfm -init $WORKING_DIR/FEAT_preprocessing/$i/example_func2highres_inv.mat -out $WORKING_DIR/FEAT_preprocessing/$i/t1_std_CSF_reg.nii.gz

  #threshold the probabilty a given voxel is CSF, this can be rather arbitrary. For CSF 0.95
  fslmaths $WORKING_DIR/FEAT_preprocessing/$i/t1_std_CSF_reg.nii.gz -thr 0.95 $WORKING_DIR/FEAT_preprocessing/$i/t1_std_CSF_reg_thr.nii.gz

  #Extract values
  fslmeants -i $WORKING_DIR/FEAT_preprocessing/$i/"$i"_BOLD_raw_despiked.nii -o $WORKING_DIR/FEAT_preprocessing/$i/CSF_noise.txt -m $WORKING_DIR/FEAT_preprocessing/$i/t1_std_CSF_reg_thr.nii.gz
done

##Generate WM regressor
for i in `ls $WORKING_DIR/FEAT_preprocessing`; do

  #Apply inverse transformation parameters from example2highres to mask with filtered_func_data.nii.gz as target using ApplyXFM For CSF
  flirt -in $WORKING_DIR/FEAT_preprocessing/$i/"$i"_anat_brain_pve_1.nii.gz -ref $WORKING_DIR/FEAT_preprocessing/$i/"$i"_BOLD_raw_despiked.nii -applyxfm -init $WORKING_DIR/FEAT_preprocessing/$i/example_func2highres_inv.mat -out $WORKING_DIR/FEAT_preprocessing/$i/t1_std_WM_reg.nii.gz

  #threshold the probabilty a given voxel is CSF, this can be rather arbitrary. For WM 0.99
  fslmaths $WORKING_DIR/FEAT_preprocessing/$i/t1_std_WM_reg.nii.gz -thr 0.99 $WORKING_DIR/FEAT_preprocessing/$i/t1_std_WM_reg_thr.nii.gz

  #Extract values
  fslmeants -i $WORKING_DIR/FEAT_preprocessing/$i/"$i"_BOLD_raw_despiked.nii -o $WORKING_DIR/FEAT_preprocessing/$i/WM_noise.txt -m $WORKING_DIR/FEAT_preprocessing/$i/t1_std_WM_reg_thr.nii.gz
done


########################################################################################################
##First-level denoising with MELODIC
########################################################################################################
$WORKING_DIR/data/ABM/scripts/loop_melodic.sh

##FOLLOWING CREATION OF HAND-LABELED BAD COMPONENTS, ALONG WITH DESIGN MATRIX CREATION:
########################################################################################################
##%%%##USER CONFIGURATIONS##%%%##
###################################
##Set working directory (Should contain all of the subject .ica directories)
WORKING_DIR=/work/04171/dpisner/data/ABM/MELODIC_ICA
##Set analysis name
analysis=HC_brood

######################################
###%%%##AUTO ASSIGN PATH NAMES##%%%###
######################################
##1) Create list of subject .ica directories (e.g. s002.ica, s003.ica, etc.)
list=$WORKING_DIR/designs/$analysis/subjects_list_"$analysis".txt
##2) Create list of paths to subject clean_filtered_to_standard preprocessed BOLD files
melodic_list=$WORKING_DIR/designs/$analysis/run_list_"$analysis".txt
##3)Group melodic output directory (An arbitrary name of your choosing)
group_dir="$analysis".ica
##4) Dual regression output directory (Another arbitrary name of your choosing)
DR_output_dir=DR_"$analysis"
##5) Set number of permutations for dual_regression (5000 or 10000 are recommended, but you can do 500 for a quick run)
num_perms=10000
##6) Set design matrix paths
design_mat=$WORKING_DIR/designs/$analysis/design.mat
design_con=$WORKING_DIR/designs/$analysis/design.con
########################################################################################################

########################################################################################################
##FIX
########################################################################################################
cd $WORKING_DIR

rm $WORKING_DIR/training_list.txt
for i in `ls $WORKING_DIR | grep .ica`; do
  if [ -f $i/hand_labels_noise.txt ]; then
    echo $i >> $WORKING_DIR/training_list.txt
  fi
done

##Create training set
fix -t training -l `cat $WORKING_DIR/training_list.txt`

##Run classifier and apply cleanup after classification
##Using LOO results, determine ideal threshold (default is 20)
thresh=20
for PARTIC in `ls $WORKING_DIR | grep .ica | grep -v group`; do
  #fix -c "$PARTIC" training.RData $thresh
  #fix "$PARTIC" $FSL_FIXDIR/training_files/Standard.RData 20
  fix -a "$PARTIC"/fix4melview_training_thr"$thresh".txt -m
done

##Register cleaned functionals to standard space and send paths to a list (melodic_list)
rm $WORKING_DIR/run_file.txt
for sub in `ls $WORKING_DIR | grep .ica`; do
    if [ ! -f $WORKING_DIR/$sub/filtered_func_data_clean_standard.nii.gz ]; then
         echo "applywarp -r $WORKING_DIR/$sub/reg/standard.nii.gz -i $WORKING_DIR/$sub/filtered_func_data_clean.nii.gz -o $WORKING_DIR/$sub/filtered_func_data_clean_standard.nii.gz --postmat=$WORKING_DIR/$sub/reg/example_func2standard.mat" >> $WORKING_DIR/run_file.txt
    fi
done

command_count=`cat $WORKING_DIR/run_file.txt | wc -l`
cores_count=`echo $(echo $command_count*2 | bc)`
fsl_sub -T 120 -s mpi,"$cores_count" -N clean_to_standard -l $WORKING_DIR -t $WORKING_DIR/run_file.txt

########################################################################################################
##Group ICA
########################################################################################################

cd $WORKING_DIR

rm $melodic_list 2>/dev/null
for i in `cat $list`; do
  echo "$WORKING_DIR/$i/filtered_func_data_clean_standard.nii.gz" >> $melodic_list
done

##Run group melodic
fsl_sub -T 1000 -s mpi,14 -N melodic_MDD_VS_HC_brood -l $WORKING_DIR melodic -i $melodic_list -o $group_dir -v --bgthreshold=10 --tr=2.0 --report -d 25 --mmthresh=0.5 --Ostats -a concat

##Run slices summary
slices_summary $group_dir/melodic_IC 4 $FSLDIR/data/standard/MNI152_T1_2mm $group_dir/melodic_IC.sum
#slices_summary melodic_IC.sum grot.png `ls -1 | sed -e 's/\..*$//'`

########################################################################################################
##Dual Regression
########################################################################################################
dual_regression $WORKING_DIR/$group_dir/melodic_IC 1 $design_mat $design_con $num_perms $WORKING_DIR/$DR_output_dir `cat $melodic_list`

##Pull significant connectivity clusters from tfce_corrp outputs
cd $WORKING_DIR/$DR_output_dir
for i in `ls $WORKING_DIR/$DR_output_dir | grep tfce_corrp_tstat | grep -v .txt`; do
  rm "$i".txt* 2>/dev/null
  if [ ! -d RESULTS ]; then
    mkdir RESULTS
  fi
  echo 1 - `fslstats $i -R | awk '{print $2}'` | bc > "$i".txt;
  j=`cat "$i".txt` 2>/dev/null
  if (( $(echo "$j < 0.06" | bc -l) )); then
    IC=`echo $i | sed 's/_tfce.*//' | rev | cut -c1-2 | rev`
    echo "IC Network "$IC"";
    echo "$i"
    echo "p=`echo $j | cut -c1-4`";
    for k in `cluster --in="$i" --thresh=0.95 --oindex=RESULTS/"$i".clusterindex.nii.gz | sed -n '1!p' | awk '{print $1}'`; do
      voxels=`cluster --in="$i" --thresh=0.95 --oindex=RESULTS/"$i".clusterindex.nii.gz | sed -n '1!p' | sed -n "${k}p" | awk '{print $2}'`
      fslmaths RESULTS/"$i".clusterindex.nii.gz -thr $k -uthr $k -bin RESULTS/"$i"_mask_"$k".nii.gz
      echo -e "CLUSTER $k ..."
      echo -e "$voxels VOXElS $DR_output_dir..."
      atlasquery -a "Harvard-Oxford Cortical Structural Atlas" -m RESULTS/"$i"_mask_"$k".nii.gz
      echo -e "\n"
    done
  else
    continue
  fi
done


#fslstats -t dr_stage2_ic0016.nii.gz -k RESULTS/dr_stage3_ic0016_tfce_corrp_tstat1.nii.gz_mask_1.nii.gz -m
