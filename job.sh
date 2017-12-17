#!/bin/sh

# You must specify a valid email address!
#SBATCH --mail-user=martin.wigger@students.unibe.ch
# Mail on (b)egin, (e)nd, (a)bort or (n)one
#SBATCH --mail-type=begin,end,fail
# Mandatory resources (h_cpu=hh:mm:ss)
#SBATCH --time=03:59:00
#SBATCH --cpus-per-task=16
#SBATCH --mem-per-cpu=2G
#SBATCH --job-name="MIALab_Job"

#### Your shell commands below this line ####

# folders
workdir=${PWD}

# activate environment
source activate mialab
python -V

python ${workdir}/bin/main.py

#### END ####

