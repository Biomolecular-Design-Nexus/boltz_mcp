#!/usr/bin/env python3
"""
Use Case 2: Binding Affinity Prediction with Boltz2

This script demonstrates how to use Boltz2 for predicting binding affinity between
a protein and a small molecule ligand. Boltz2 can predict both structure and binding
affinity simultaneously, making it ideal for drug discovery applications.

Usage:
    python examples/use_case_2_affinity_prediction.py --input examples/data/affinity.yaml
    python examples/use_case_2_affinity_prediction.py --protein-seq "MVTPE..." --ligand-smiles "N[C@@H](Cc1ccc(O)cc1)C(=O)O"
"""

import argparse
import os
import sys
import json
import yaml
import subprocess
from pathlib import Path

def create_affinity_yaml(protein_sequence, ligand_smiles, output_path, ligand_ccd=None):
    """Create a protein-ligand affinity prediction YAML configuration file."""
    config = {
        "version": 1,
        "sequences": [
            {
                "protein": {
                    "id": "A",
                    "sequence": protein_sequence
                }
            },
            {
                "ligand": {
                    "id": "B"
                }
            }
        ],
        "properties": [
            {
                "affinity": {
                    "binder": "B"
                }
            }
        ]
    }

    # Add ligand as either SMILES or CCD code
    if ligand_ccd:
        config["sequences"][1]["ligand"]["ccd"] = ligand_ccd
    else:
        config["sequences"][1]["ligand"]["smiles"] = ligand_smiles

    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    return output_path

def run_boltz_affinity_prediction(input_yaml, output_dir, use_msa_server=True, use_potentials=False):
    """Run Boltz affinity prediction."""
    cmd = [
        "boltz", "predict", input_yaml,
        "--out_dir", output_dir,
        "--output_format", "pdb"
    ]

    if use_msa_server:
        cmd.append("--use_msa_server")

    if use_potentials:
        cmd.append("--use_potentials")

    print(f"Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Boltz affinity prediction completed successfully!")
        print("STDOUT:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running Boltz affinity prediction: {e}")
        print("STDERR:", e.stderr)
        return False

def parse_affinity_results(output_dir):
    """Parse and display affinity prediction results."""
    pred_dir = Path(output_dir) / "predictions"

    if not pred_dir.exists():
        print("No predictions directory found.")
        return

    # Find affinity JSON files
    affinity_files = list(pred_dir.rglob("affinity_*.json"))

    if not affinity_files:
        print("No affinity prediction files found.")
        return

    print("\n" + "="*50)
    print("AFFINITY PREDICTION RESULTS")
    print("="*50)

    for affinity_file in affinity_files:
        print(f"\nResults from: {affinity_file.name}")
        print("-" * 30)

        with open(affinity_file, 'r') as f:
            data = json.load(f)

        # Display main affinity predictions
        if "affinity_pred_value" in data:
            affinity_value = data["affinity_pred_value"]
            print(f"Binding Affinity (log10(IC50)): {affinity_value:.3f}")

            # Convert to more intuitive units
            ic50_um = 10 ** affinity_value
            print(f"IC50 (μM): {ic50_um:.2e}")

            # Convert to pIC50
            pic50 = -affinity_value + 6
            print(f"pIC50: {pic50:.3f}")

            # Interpret binding strength
            if affinity_value < -2:
                strength = "Strong binder"
            elif affinity_value < 1:
                strength = "Moderate binder"
            else:
                strength = "Weak binder/Decoy"
            print(f"Binding strength: {strength}")

        if "affinity_probability_binary" in data:
            prob = data["affinity_probability_binary"]
            print(f"Binding probability: {prob:.3f}")
            print(f"Likely binder: {'Yes' if prob > 0.5 else 'No'}")

        # Show ensemble model components if available
        if "affinity_pred_value1" in data and "affinity_pred_value2" in data:
            print(f"\nEnsemble components:")
            print(f"  Model 1 - Affinity: {data['affinity_pred_value1']:.3f}, Probability: {data.get('affinity_probability_binary1', 'N/A')}")
            print(f"  Model 2 - Affinity: {data['affinity_pred_value2']:.3f}, Probability: {data.get('affinity_probability_binary2', 'N/A')}")

def main():
    parser = argparse.ArgumentParser(
        description="Boltz2 Binding Affinity Prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use provided example file
  python examples/use_case_2_affinity_prediction.py --input examples/data/affinity.yaml

  # Predict affinity for custom protein-ligand pair
  python examples/use_case_2_affinity_prediction.py \\
    --protein-seq "MVTPEGNVSLVDESLLVGVT..." \\
    --ligand-smiles "N[C@@H](Cc1ccc(O)cc1)C(=O)O"

  # Use CCD code instead of SMILES
  python examples/use_case_2_affinity_prediction.py \\
    --protein-seq "MVTPEGNVSLVDESLLVGVT..." \\
    --ligand-ccd "ATP"

  # Use potentials for better structure quality
  python examples/use_case_2_affinity_prediction.py \\
    --input examples/data/affinity.yaml --use-potentials
        """)

    parser.add_argument("--input", "-i", type=str, help="Input YAML file")
    parser.add_argument("--protein-seq", type=str, help="Protein sequence")
    parser.add_argument("--ligand-smiles", type=str, help="Ligand SMILES string")
    parser.add_argument("--ligand-ccd", type=str, help="Ligand CCD code (alternative to SMILES)")
    parser.add_argument("--output", "-o", type=str, default="./boltz_affinity_output",
                       help="Output directory (default: ./boltz_affinity_output)")
    parser.add_argument("--no-msa-server", action="store_true",
                       help="Don't use MSA server (faster but less accurate)")
    parser.add_argument("--use-potentials", action="store_true",
                       help="Use inference-time potentials for better physical quality")

    args = parser.parse_args()

    # Validate input
    if not args.input:
        if not args.protein_seq or (not args.ligand_smiles and not args.ligand_ccd):
            print("Error: Must provide either:")
            print("  1. --input file, OR")
            print("  2. --protein-seq AND (--ligand-smiles OR --ligand-ccd)")
            sys.exit(1)

        if args.ligand_smiles and args.ligand_ccd:
            print("Error: Provide either --ligand-smiles OR --ligand-ccd, not both")
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
        # Create temporary YAML file from sequences
        temp_yaml = output_dir / "temp_affinity.yaml"
        input_yaml = create_affinity_yaml(
            args.protein_seq,
            args.ligand_smiles,
            temp_yaml,
            args.ligand_ccd
        )
        print(f"Created temporary input file: {input_yaml}")
        print(f"Protein sequence length: {len(args.protein_seq)} residues")
        if args.ligand_smiles:
            print(f"Ligand SMILES: {args.ligand_smiles}")
        if args.ligand_ccd:
            print(f"Ligand CCD: {args.ligand_ccd}")

    print(f"Output directory: {output_dir}")
    print(f"Using MSA server: {not args.no_msa_server}")
    print(f"Using potentials: {args.use_potentials}")

    # Run prediction
    success = run_boltz_affinity_prediction(
        input_yaml,
        str(output_dir),
        use_msa_server=not args.no_msa_server,
        use_potentials=args.use_potentials
    )

    if success:
        print(f"\nPrediction completed! Check output in: {output_dir}")

        # Parse and display results
        parse_affinity_results(output_dir)

        print(f"\nDetailed output files:")
        print("  - predictions/[input_name]/[input_name]_model_0.pdb  # Predicted complex structure")
        print("  - predictions/[input_name]/affinity_[input_name].json  # Binding affinity predictions")
        print("  - predictions/[input_name]/confidence_[input_name]_model_0.json  # Structure confidence scores")

        # List actual output files
        pred_dir = output_dir / "predictions"
        if pred_dir.exists():
            print(f"\nAll output files in {pred_dir}:")
            for file in pred_dir.rglob("*"):
                if file.is_file():
                    print(f"  - {file.relative_to(output_dir)}")
    else:
        print("Prediction failed. Check error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()