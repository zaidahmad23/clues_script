"""
Automate running of different scripts

python3 case2.py -p0 0.2 -s 0.04 -n 4000 --nanc 100 --ton 100 --toff 0 \
--converted-filename relate_input \
--path-to-relate-bin ./relate_v1.1.2_x86_64_static/bin/Relate \
--relate-output-filename relate_step_1 \
--relate-map-file-path clues/example/genetic_map.txt \
--inference-script-output-filename clues_output \
--output-directory output3 --mutation-rate 1.25e-8 \
--create-ancient-samples --step2-script-ancient-samples-generation-gap 500 --step2-script-number-of-ancient-samples 100
"""
import subprocess
import argparse
import os
import sys
import shutil

from pathlib import Path

import numpy as np

EXTERNAL_DEPENDENCIES = ["git", "gcc", "Rscript"]


def is_debug_mode_active():
    return os.environ.get("DEBUG", False)

def print_if_debug_mode_active(obj):
    if is_debug_mode_active():
        print(obj)


def execute_command(args, cwd=None):
    try:
        print_if_debug_mode_active(args)
        subprocess.run(args, cwd=cwd, check=True, capture_output=True)
    except subprocess.CalledProcessError as err:
        stderr = err.stderr.decode("utf-8")
        stdout = err.stdout.decode("utf-8")
        if stderr:
            print(stderr)
        elif stdout is not None:
            print(stdout)
        else:
            print(f"Error occurred while executing {args}")
        sys.exit(1)


def clone_rhps_coalescent_repo():
    if not os.path.isdir("rhps_coalescent"):
        execute_command(["git", "clone", "https://github.com/mdedge/rhps_coalescent.git"])


def clone_clues_repo():
    if not os.path.isdir("clues"):
        execute_command(["git", "clone", "https://github.com/35ajstern/clues.git"])


def compile_mssel():
    execute_command(
        ["gcc", "-O2", "-o", "mssel", "mssel.c", "rand1.c", "streecsel.c", "-lm"], cwd="./rhps_coalescent/msseldir"
    )


def run_step(p_initial, s, n, output_file_path, ton, toff):
    command = list(
        map(
            str,
            ['python3', 'step.py', '-p0', p_initial, '-s', s, '-n', n, '--output-file-path', output_file_path, '--ton', ton, '--toff', toff]
        )
    )
    execute_command(command)

def run_step2(p_initial, s, n, ton, toff, ancient_sample_generation_gap, number_of_ancient_samples, output_file_path):
    command = list(
        map(
            str,
            [
                'python3', 'step2.py', '--initial-allele-freq', p_initial, '--selection-coefficient', s,
                '--ton', ton, '--toff', toff, '--effective-population-size', n,
                '--ancient-samples-generation-gap', ancient_sample_generation_gap,
                '--number-of-ancient-samples', number_of_ancient_samples,
                '--output-file-path', output_file_path
            ]
        )
    )
    execute_command(command)


def run_mssel(
    nchroms,
    nreps,
    nder,
    nanc,
    path_to_trajfile,
    sel_spot,
    recombination_rate,
    genome_length,
    mutation_rate,
    output_file,
):
    command = list(
        map(
            str,
            [
                "./rhps_coalescent/msseldir/mssel",
                nanc + nder,
                nreps,
                nanc,
                nder,
                path_to_trajfile,
                sel_spot,
                "-r",
                recombination_rate,
                genome_length,
                "-t",
                mutation_rate,
            ],
        )
    )
    with open(output_file, "w") as f:
        try:
            print_if_debug_mode_active(command)
            subprocess.run(command, stdout=f, check=True)
        except subprocess.CalledProcessError as err:
            print(err.stderr if err.stderr else err.stdout)
            sys.exit(1)


def convert_txt_to_haps_and_sample(r_script_path, input_txt_file_path, output_file_name):
    execute_command(f"Rscript {r_script_path} {input_txt_file_path} {output_file_name} 1000000 400".split(" "))


def run_inference(ancient_samples_file_path, inference_output_filename):
    command = ["python3", "inference.py"]
    if ancient_samples_file_path is not None:
        command += ["--ancientSamps", ancient_samples_file_path]

    command += ["--out", inference_output_filename]
    execute_command(command, cwd="./clues")


def plot(mssel_traj_file_path, input_file_path, output_file_path, effective_population_size):
    execute_command(
        [
            "python3",
            "plot_traj.py",
            input_file_path,
            output_file_path,
            mssel_traj_file_path,
            str(int(effective_population_size)),
        ]
    )


def fill_defaults(args):
    args.nder = np.random.binomial(args.nchroms, args.initial_allele_freq)
    if args.nanc is None:
        args.nanc = args.nchroms - args.nder


def ensure_external_dependencies():
    for program in EXTERNAL_DEPENDENCIES:
        if shutil.which(program) is None:
            print(f"{program} is a required dependency. Please install it before running the script.")
            sys.exit(1)

    clone_rhps_coalescent_repo()
    clone_clues_repo()
    compile_mssel()


def ensure_internal_dependencies(args):
    required_files = [
        args.step_script_path,
        args.path_to_converter_script
    ]

    for _file in required_files:
        if not os.path.isfile(_file):
            print("Error: File {args.step_script_path} not found!")


def main():
    # Argument parsing/validation

    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("--output-directory", type=str, default='./')
    argparser.add_argument("--step-script-path", type=str, default="step.py", help="Path to step.py script")
    argparser.add_argument("--step-script-output-file-path", type=str, default="mssel.traj")
    argparser.add_argument(
        "-p0", "--initial-allele-freq", type=float, required=True, help="Present-day allele frequency."
    )
    argparser.add_argument("-s", "--selection-coefficient", type=float, required=True, help="Selection coefficient.")
    argparser.add_argument(
        "-n", "--effective-population-size", type=float, required=True, help="Effective population size."
    )
    argparser.add_argument("--ton", type=int, required=True, help="Time before present that selection starts.")
    argparser.add_argument("--toff", type=int, required=True, help="Time before present that selection ends.")

    argparser.add_argument("--nchroms", type=int, default=400, help="Sample size (in # of chromosomes).")
    argparser.add_argument("--nreps", type=int, default=1, help="Number of independent, identical replicates to run.")
    argparser.add_argument("--nanc", type=int, help="The number of chromosomes that carry the ancestral allele.")

    argparser.add_argument(
        "--genome-length", type=int, default=1000000, help="Length of the genome sequence, in base pairs."
    )
    argparser.add_argument(
        "--sel-spot",
        type=int,
        default=500000,
        help="Position of the allele with the trajectory specified by the trajfile.",
    )
    argparser.add_argument("--mutation-rate-for-mssel", type=float, default=400, help="Population-scaled mutation rate for mssel.")
    argparser.add_argument("--mutation-rate", type=float, default=1.25e-8, help="Population-scaled mutation rate.")
    argparser.add_argument("--recombination-rate", type=int, default=400, help="Population-scaled recombination rate.")
    argparser.add_argument("--massel-output", type=str, default="mssel_output.txt", help="Massel output filename/path.")

    argparser.add_argument(
        "--path-to-converter-script",
        type=str,
        default="ms2haps_mod.R",
        help="Path/filename of R script that converts .txt to .haps and .sample",
    )
    argparser.add_argument("--converted-filename", type=str, help="Filename of converted .haps and .sample")

    argparser.add_argument("--inference-script-output-filename", type=str, required=True)
    argparser.add_argument("--create-ancient-samples", action="store_true")
    argparser.add_argument("--step2-script-ancient-samples-generation-gap", type=str, required=True)
    argparser.add_argument("--step2-script-number-of-ancient-samples", type=int, required=True)

    args = argparser.parse_args()
    fill_defaults(args)

    # Ensuring internal/external dependencies
    ensure_internal_dependencies(args)
    ensure_external_dependencies()

    # Create output directory
    args.output_directory = os.path.abspath(args.output_directory)
    os.makedirs(args.output_directory, exist_ok=True)

    # Update output files
    args.step_script_output_file_path = os.path.join(args.output_directory, args.step_script_output_file_path)
    args.massel_output = os.path.join(args.output_directory, args.massel_output)
    args.converted_filename = os.path.join(args.output_directory, args.converted_filename)
    args.inference_script_output_filename = os.path.join(args.output_directory, args.inference_script_output_filename)
    step2_script_ancient_samples_file_path = None

    # Actual Computation
    run_step(
        p_initial=args.initial_allele_freq,
        s=args.selection_coefficient,
        n=args.effective_population_size,
        output_file_path=args.step_script_output_file_path,
        ton=args.ton,
        toff=args.toff
    )
    run_mssel(
        nchroms=args.nchroms,
        nreps=args.nreps,
        nder=args.nder,
        nanc=args.nanc,
        path_to_trajfile=args.step_script_output_file_path,
        genome_length=args.genome_length,
        sel_spot=args.sel_spot,
        mutation_rate=args.mutation_rate_for_mssel,
        recombination_rate=args.recombination_rate,
        output_file=args.massel_output,
    )
    convert_txt_to_haps_and_sample(
        r_script_path=args.path_to_converter_script,
        input_txt_file_path=args.massel_output,
        output_file_name=args.converted_filename,
    )

    if args.create_ancient_samples:
        step2_script_ancient_samples_file_path = os.path.join(args.output_directory, "ancientSamples.txt")
        run_step2(
            p_initial=args.initial_allele_freq,
            s=args.selection_coefficient,
            n=args.effective_population_size,
            ton=args.ton,
            toff=args.toff,
            ancient_sample_generation_gap=args.step2_script_ancient_samples_generation_gap,
            number_of_ancient_samples=args.step2_script_number_of_ancient_samples,
            output_file_path=step2_script_ancient_samples_file_path
        )
    run_inference(
        ancient_samples_file_path=step2_script_ancient_samples_file_path,
        inference_output_filename=args.inference_script_output_filename,
    )
    plot(
        mssel_traj_file_path=args.step_script_output_file_path,
        input_file_path=args.inference_script_output_filename,
        output_file_path=os.path.join(args.output_directory, "plot"),
        effective_population_size=args.effective_population_size
    )

if __name__ == "__main__":
    main()
