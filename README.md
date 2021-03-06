# clues_script
step.py creates .traj files for mssel 

case1.py runs inference with only --times specified (modern samples only)
case2.py runs inference with only --ancientSamps specified (ancient samples only)
case3.py runs inference with both --times and --ancientSamps specified (modern and ancient samples only)

LAUNCH OPTIONS:

**CASE 2 (no --times, --ancientSamps):**
~~~
rm -rf output3 && DEBUG=1 python3 case2.py -p0 0.2 -s 0.05 -n 10000 --nanc 100 --ton 100 --toff 50 \
--converted-filename relate_input \
--inference-script-output-filename clues_output \
--output-directory output --mutation-rate 1.25e-8 \
--create-ancient-samples --step2-script-ancient-samples-generation-gap 500 \
--step2-script-number-of-ancient-samples 500 --inference-script-time-bins-file-path /Users/zaid/Desktop/popgen/clues/example/timeBins.txt  --runs 1
~~~

Installation/dependencies
clues has developed for python 3; use python 2 at your own risk (visit the Issues section for tips on using python 2).

The programs require the following dependencies, which can be installed using conda/pip: numba, progressbar, biopython

Previous implementation (clues-v0)
To find the previous version of clues, which uses ARGweaver output (Rasmussen et al, 2014; Hubisz, et al, 2019; docs here), please go to https://github.com/35ajstern/clues-v0. We are no longer maintaining clues-v0
