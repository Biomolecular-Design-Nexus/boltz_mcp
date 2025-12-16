#!/usr/bin/env python3
"""
Use Case 3: Batch Structure Prediction for Protein Variants

This script demonstrates how to use Boltz2 for batch processing of multiple protein
variants or different configurations. This is useful for comparative analysis,
variant screening, or processing multiple structures at once.

Usage:
    python examples/use_case_3_batch_structure_prediction.py --config-dir examples/data --pattern "*.yaml"
    python examples/use_case_3_batch_structure_prediction.py --variant-file protein_variants.txt
"""

import argparse
import os
import sys
import glob
import yaml
import subprocess
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

def create_variant_yaml(sequence, variant_name, output_dir, use_msa_server=True):
    """Create a YAML file for a protein variant."""
    config = {
        "version": 1,
        "sequences": [
            {
                "protein": {
                    "id": "A",
                    "sequence": sequence
                }
            }
        ]
    }

    if not use_msa_server:
        config["sequences"][0]["protein"]["msa"] = "empty"

    output_file = Path(output_dir) / f"{variant_name}.yaml"
    with open(output_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    return output_file

def run_single_prediction(input_yaml, output_base_dir, use_msa_server=True, use_potentials=False):
    """Run Boltz prediction for a single input file."""
    input_path = Path(input_yaml)
    variant_name = input_path.stem

    # Create output directory for this variant
    variant_output = Path(output_base_dir) / f"variant_{variant_name}"
    variant_output.mkdir(parents=True, exist_ok=True)

    cmd = [
        "boltz", "predict", str(input_yaml),
        "--out_dir", str(variant_output),
        "--output_format", "pdb"
    ]

    if use_msa_server:
        cmd.append("--use_msa_server")

    if use_potentials:
        cmd.append("--use_potentials")

    start_time = time.time()
    print(f"Starting prediction for {variant_name}...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        end_time = time.time()
        duration = end_time - start_time

        return {
            "variant": variant_name,
            "status": "success",
            "duration": duration,
            "output_dir": str(variant_output),
            "stdout": result.stdout
        }
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        duration = end_time - start_time

        return {
            "variant": variant_name,
            "status": "failed",
            "duration": duration,
            "error": str(e),
            "stderr": e.stderr
        }

def run_batch_predictions(input_files, output_dir, max_workers=2, use_msa_server=True, use_potentials=False):
    """Run batch predictions using parallel processing."""
    results = []

    # Use ProcessPoolExecutor for parallel processing
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_input = {
            executor.submit(
                run_single_prediction,
                input_file,
                output_dir,
                use_msa_server,
                use_potentials
            ): input_file
            for input_file in input_files
        }

        # Collect results as they complete
        for future in as_completed(future_to_input):
            input_file = future_to_input[future]
            try:
                result = future.result()
                results.append(result)
                if result["status"] == "success":
                    print(f"✓ Completed {result['variant']} in {result['duration']:.1f}s")
                else:
                    print(f"✗ Failed {result['variant']} after {result['duration']:.1f}s")
            except Exception as exc:
                print(f"✗ {input_file} generated an exception: {exc}")
                results.append({
                    "variant": Path(input_file).stem,
                    "status": "exception",
                    "error": str(exc)
                })

    return results

def create_variants_from_file(variant_file, output_dir, use_msa_server=True):
    """Create YAML files from a variants text file."""
    """
    Expected format:
    variant_name1,PROTEIN_SEQUENCE1
    variant_name2,PROTEIN_SEQUENCE2
    """
    created_files = []

    with open(variant_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split(',', 1)
            if len(parts) != 2:
                print(f"Warning: Skipping malformed line {line_num}: {line}")
                continue

            variant_name, sequence = parts
            variant_name = variant_name.strip()
            sequence = sequence.strip()

            if not variant_name or not sequence:
                print(f"Warning: Skipping empty variant or sequence at line {line_num}")
                continue

            yaml_file = create_variant_yaml(sequence, variant_name, output_dir, use_msa_server)
            created_files.append(yaml_file)
            print(f"Created config for variant: {variant_name} (length: {len(sequence)} aa)")

    return created_files

def generate_summary_report(results, output_dir):
    """Generate a summary report of batch predictions."""
    report_file = Path(output_dir) / "batch_summary.json"

    summary = {
        "total_variants": len(results),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "exceptions": sum(1 for r in results if r["status"] == "exception"),
        "total_time": sum(r.get("duration", 0) for r in results),
        "results": results
    }

    with open(report_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*50}")
    print("BATCH PREDICTION SUMMARY")
    print('='*50)
    print(f"Total variants processed: {summary['total_variants']}")
    print(f"Successful predictions: {summary['successful']}")
    print(f"Failed predictions: {summary['failed']}")
    print(f"Exceptions: {summary['exceptions']}")
    print(f"Total processing time: {summary['total_time']:.1f} seconds")
    if summary['successful'] > 0:
        avg_time = summary['total_time'] / summary['successful']
        print(f"Average time per successful prediction: {avg_time:.1f} seconds")

    print(f"\nDetailed report saved to: {report_file}")

    # Show failed variants if any
    failed_variants = [r for r in results if r["status"] != "success"]
    if failed_variants:
        print(f"\nFailed variants:")
        for variant in failed_variants:
            print(f"  - {variant['variant']}: {variant['status']}")

def main():
    parser = argparse.ArgumentParser(
        description="Boltz2 Batch Structure Prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all YAML files in examples/data
  python examples/use_case_3_batch_structure_prediction.py --config-dir examples/data --pattern "*.yaml"

  # Process specific files
  python examples/use_case_3_batch_structure_prediction.py --input-files examples/data/prot.yaml examples/data/multimer.yaml

  # Create variants from a text file
  python examples/use_case_3_batch_structure_prediction.py --variant-file protein_variants.txt

  # Run with parallel processing (adjust based on your system)
  python examples/use_case_3_batch_structure_prediction.py --config-dir examples/data --max-workers 4

Variant file format (CSV):
  # variant_name,protein_sequence
  wild_type,QLEDSEVEAVAKGLEEMYANGVTEDNFKNYVKNNFAQQEISSVEEELNVNISDSCVANKIKDEFFAMISISAIVKAAQKKAWKELAVTVLRFAKANGLKTNAIIVAGQLALWAVQCG
  mutant_A10G,QLEDSEVEAVGKGLEEMYANGVTEDNFKNYVKNNFAQQEISSVEEELNVNISDSCVANKIKDEFFAMISISAIVKAAQKKAWKELAVTVLRFAKANGLKTNAIIVAGQLALWAVQCG
        """)

    parser.add_argument("--config-dir", type=str, help="Directory containing YAML configuration files")
    parser.add_argument("--pattern", type=str, default="*.yaml", help="File pattern to match (default: *.yaml)")
    parser.add_argument("--input-files", nargs="+", help="Specific input YAML files to process")
    parser.add_argument("--variant-file", type=str, help="Text file with variant definitions (name,sequence)")
    parser.add_argument("--output", "-o", type=str, default="./boltz_batch_output",
                       help="Output directory (default: ./boltz_batch_output)")
    parser.add_argument("--max-workers", type=int, default=2,
                       help="Maximum number of parallel workers (default: 2)")
    parser.add_argument("--no-msa-server", action="store_true",
                       help="Don't use MSA server (faster but less accurate)")
    parser.add_argument("--use-potentials", action="store_true",
                       help="Use inference-time potentials for better physical quality")

    args = parser.parse_args()

    # Validate input
    input_methods = [args.config_dir, args.input_files, args.variant_file]
    provided_methods = sum(1 for method in input_methods if method is not None)

    if provided_methods == 0:
        print("Error: Must provide one of:")
        print("  --config-dir, --input-files, or --variant-file")
        sys.exit(1)
    elif provided_methods > 1:
        print("Error: Provide only one input method")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect input files
    input_files = []

    if args.config_dir:
        if not os.path.exists(args.config_dir):
            print(f"Error: Directory {args.config_dir} does not exist")
            sys.exit(1)

        pattern_path = os.path.join(args.config_dir, args.pattern)
        input_files = glob.glob(pattern_path)

        if not input_files:
            print(f"Error: No files found matching pattern {pattern_path}")
            sys.exit(1)

        print(f"Found {len(input_files)} files in {args.config_dir}")

    elif args.input_files:
        for file_path in args.input_files:
            if not os.path.exists(file_path):
                print(f"Error: File {file_path} does not exist")
                sys.exit(1)
            input_files.append(file_path)

        print(f"Processing {len(input_files)} specified files")

    elif args.variant_file:
        if not os.path.exists(args.variant_file):
            print(f"Error: Variant file {args.variant_file} does not exist")
            sys.exit(1)

        print(f"Creating variant configs from {args.variant_file}")
        configs_dir = output_dir / "configs"
        configs_dir.mkdir(exist_ok=True)

        input_files = create_variants_from_file(
            args.variant_file,
            configs_dir,
            not args.no_msa_server
        )

        if not input_files:
            print("No valid variants found in file")
            sys.exit(1)

    print(f"Output directory: {output_dir}")
    print(f"Max parallel workers: {args.max_workers}")
    print(f"Using MSA server: {not args.no_msa_server}")
    print(f"Using potentials: {args.use_potentials}")

    # Run batch predictions
    print(f"\nStarting batch predictions...")
    start_time = time.time()

    results = run_batch_predictions(
        input_files,
        output_dir,
        max_workers=args.max_workers,
        use_msa_server=not args.no_msa_server,
        use_potentials=args.use_potentials
    )

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\nBatch processing completed in {total_time:.1f} seconds")

    # Generate summary report
    generate_summary_report(results, output_dir)

    # Count successes
    successful_results = [r for r in results if r["status"] == "success"]
    if successful_results:
        print(f"\nOutput structure files can be found in:")
        for result in successful_results[:3]:  # Show first 3 examples
            pred_dir = Path(result["output_dir"]) / "predictions"
            print(f"  - {pred_dir}")
        if len(successful_results) > 3:
            print(f"  ... and {len(successful_results) - 3} more")

if __name__ == "__main__":
    main()