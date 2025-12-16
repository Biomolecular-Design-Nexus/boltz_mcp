#!/usr/bin/env python3
"""
Use Case 1: Structure Prediction with Boltz2

This script demonstrates how to use Boltz2 for basic protein structure prediction.
It takes a protein sequence and predicts its 3D structure using Boltz2's state-of-the-art
deep learning models.

Usage:
    python examples/use_case_1_structure_prediction.py --input examples/data/prot.yaml --output output_dir
    python examples/use_case_1_structure_prediction.py --sequence "QLEDSEVEAVAKGLEEMYANG..." --output output_dir
"""

import argparse
import os
import sys
import tempfile
import yaml
import subprocess
from pathlib import Path

def create_protein_yaml(sequence, output_path, use_msa_server=True):
    """Create a protein YAML configuration file."""
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

    # If not using MSA server, set MSA to empty (not recommended for best accuracy)
    if not use_msa_server:
        config["sequences"][0]["protein"]["msa"] = "empty"

    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    return output_path

def run_boltz_prediction(input_yaml, output_dir, use_msa_server=True, use_potentials=False):
    """Run Boltz structure prediction."""
    cmd = [
        "boltz", "predict", str(input_yaml),
        "--out_dir", str(output_dir),
        "--output_format", "pdb"  # Use PDB format for easier visualization
    ]

    if use_msa_server:
        cmd.append("--use_msa_server")

    if use_potentials:
        cmd.append("--use_potentials")

    print(f"Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Boltz prediction completed successfully!")
        print("STDOUT:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running Boltz prediction: {e}")
        print("STDERR:", e.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Boltz2 Structure Prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use provided example file
  python examples/use_case_1_structure_prediction.py --input examples/data/prot.yaml

  # Predict structure from sequence
  python examples/use_case_1_structure_prediction.py --sequence "QLEDSEVEAVAKGLEEMYANGVTEDNFKNYVKNNFAQQEISSVEEELNVNISDSCVANKIKDEFFAMISISAIVKAAQKKAWKELAVTVLRFAKANGLKTNAIIVAGQLALWAVQCG"

  # Use without MSA server (faster but less accurate)
  python examples/use_case_1_structure_prediction.py --input examples/data/prot.yaml --no-msa-server

  # Use inference-time potentials (better physical quality)
  python examples/use_case_1_structure_prediction.py --input examples/data/prot.yaml --use-potentials
        """)

    parser.add_argument("--input", "-i", type=str, help="Input YAML file")
    parser.add_argument("--sequence", "-s", type=str, help="Protein sequence (alternative to input file)")
    parser.add_argument("--output", "-o", type=str, default="./boltz_structure_output",
                       help="Output directory (default: ./boltz_structure_output)")
    parser.add_argument("--no-msa-server", action="store_true",
                       help="Don't use MSA server (faster but less accurate)")
    parser.add_argument("--use-potentials", action="store_true",
                       help="Use inference-time potentials for better physical quality")

    args = parser.parse_args()

    # Validate input
    if not args.input and not args.sequence:
        print("Error: Must provide either --input file or --sequence")
        sys.exit(1)

    if args.input and args.sequence:
        print("Error: Provide either --input file OR --sequence, not both")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle input
    if args.input:
        if not os.path.exists(args.input):
            print(f"Error: Input file {args.input} does not exist")
            sys.exit(1)
        input_yaml = args.input
        print(f"Using input file: {input_yaml}")
    else:
        # Create temporary YAML file from sequence
        temp_yaml = output_dir / "temp_input.yaml"
        input_yaml = create_protein_yaml(args.sequence, temp_yaml, not args.no_msa_server)
        print(f"Created temporary input file: {input_yaml}")
        print(f"Protein sequence length: {len(args.sequence)} residues")

    print(f"Output directory: {output_dir}")
    print(f"Using MSA server: {not args.no_msa_server}")
    print(f"Using potentials: {args.use_potentials}")

    # Run prediction
    success = run_boltz_prediction(
        input_yaml,
        str(output_dir),
        use_msa_server=not args.no_msa_server,
        use_potentials=args.use_potentials
    )

    if success:
        print(f"\nPrediction completed! Check output in: {output_dir}")
        print("\nExpected output files:")
        print("  - predictions/[input_name]/[input_name]_model_0.pdb  # Predicted structure")
        print("  - predictions/[input_name]/confidence_[input_name]_model_0.json  # Confidence scores")
        print("  - Lightning logs and processed data")

        # List actual output files if they exist
        pred_dir = output_dir / "predictions"
        if pred_dir.exists():
            print(f"\nActual output files in {pred_dir}:")
            for file in pred_dir.rglob("*"):
                if file.is_file():
                    print(f"  - {file.relative_to(output_dir)}")
    else:
        print("Prediction failed. Check error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()