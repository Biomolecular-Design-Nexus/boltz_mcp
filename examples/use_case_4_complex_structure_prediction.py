#!/usr/bin/env python3
"""
Use Case 4: Complex Structure Prediction with Boltz2

This script demonstrates how to use Boltz2 for predicting complex structures
including protein-protein complexes, protein-ligand complexes, and protein-nucleic acid
complexes. This showcases Boltz2's ability to model biomolecular interactions.

Usage:
    python examples/use_case_4_complex_structure_prediction.py --input examples/data/ligand.yaml
    python examples/use_case_4_complex_structure_prediction.py --input examples/data/multimer.yaml
    python examples/use_case_4_complex_structure_prediction.py --input examples/data/pocket.yaml
"""

import argparse
import os
import sys
import json
import yaml
import subprocess
from pathlib import Path

def create_complex_yaml(config_type, output_path, **kwargs):
    """Create different types of complex YAML configurations."""

    if config_type == "protein_ligand":
        protein_seq = kwargs.get("protein_seq")
        ligand_smiles = kwargs.get("ligand_smiles")
        ligand_ccd = kwargs.get("ligand_ccd")

        config = {
            "version": 1,
            "sequences": [
                {
                    "protein": {
                        "id": "A",
                        "sequence": protein_seq
                    }
                },
                {
                    "ligand": {
                        "id": "B"
                    }
                }
            ]
        }

        if ligand_ccd:
            config["sequences"][1]["ligand"]["ccd"] = ligand_ccd
        else:
            config["sequences"][1]["ligand"]["smiles"] = ligand_smiles

    elif config_type == "protein_protein":
        seq1 = kwargs.get("seq1")
        seq2 = kwargs.get("seq2")

        config = {
            "version": 1,
            "sequences": [
                {
                    "protein": {
                        "id": "A",
                        "sequence": seq1
                    }
                },
                {
                    "protein": {
                        "id": "B",
                        "sequence": seq2
                    }
                }
            ]
        }

    elif config_type == "multimer":
        sequence = kwargs.get("sequence")
        chain_count = kwargs.get("chain_count", 2)

        chain_ids = [chr(65 + i) for i in range(chain_count)]  # A, B, C, ...

        config = {
            "version": 1,
            "sequences": [
                {
                    "protein": {
                        "id": chain_ids,
                        "sequence": sequence
                    }
                }
            ]
        }

    else:
        raise ValueError(f"Unknown config type: {config_type}")

    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    return output_path

def run_boltz_complex_prediction(input_yaml, output_dir, use_msa_server=True, use_potentials=False):
    """Run Boltz complex structure prediction."""
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
        print("Boltz complex prediction completed successfully!")
        print("STDOUT:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running Boltz complex prediction: {e}")
        print("STDERR:", e.stderr)
        return False

def analyze_complex_results(output_dir):
    """Analyze and display complex prediction results."""
    pred_dir = Path(output_dir) / "predictions"

    if not pred_dir.exists():
        print("No predictions directory found.")
        return

    print("\n" + "="*50)
    print("COMPLEX STRUCTURE PREDICTION RESULTS")
    print("="*50)

    # Find confidence files
    confidence_files = list(pred_dir.rglob("confidence_*.json"))

    for conf_file in confidence_files:
        print(f"\nResults from: {conf_file.name}")
        print("-" * 40)

        with open(conf_file, 'r') as f:
            data = json.load(f)

        # Overall confidence metrics
        if "confidence_score" in data:
            print(f"Overall confidence score: {data['confidence_score']:.3f}")

        if "complex_plddt" in data:
            print(f"Complex average pLDDT: {data['complex_plddt']:.3f}")

        if "ptm" in data:
            print(f"Predicted TM score: {data['ptm']:.3f}")

        # Interface-specific metrics
        if "iptm" in data:
            print(f"Interface TM score (ipTM): {data['iptm']:.3f}")

        if "complex_iplddt" in data:
            print(f"Interface-weighted pLDDT: {data['complex_iplddt']:.3f}")

        # Chain-specific metrics
        if "chains_ptm" in data:
            print("\nPer-chain confidence:")
            for chain_id, ptm_score in data["chains_ptm"].items():
                print(f"  Chain {chain_id}: {ptm_score:.3f}")

        # Interface metrics between chain pairs
        if "pair_chains_iptm" in data:
            print("\nPairwise interface confidence:")
            for chain1, chain_data in data["pair_chains_iptm"].items():
                for chain2, iptm_score in chain_data.items():
                    if chain1 != chain2:  # Only show inter-chain interfaces
                        print(f"  Chain {chain1} ↔ Chain {chain2}: {iptm_score:.3f}")

        # Ligand-specific metrics if available
        if "ligand_iptm" in data:
            print(f"Protein-ligand interface confidence: {data['ligand_iptm']:.3f}")

        if "protein_iptm" in data:
            print(f"Protein-protein interface confidence: {data['protein_iptm']:.3f}")

        # Distance-based confidence if available
        if "complex_pde" in data:
            print(f"Complex distance error (PDE): {data['complex_pde']:.3f} Å")

def identify_complex_type(yaml_file):
    """Identify the type of complex from YAML file."""
    with open(yaml_file, 'r') as f:
        config = yaml.safe_load(f)

    sequences = config.get("sequences", [])

    protein_chains = []
    ligand_chains = []
    dna_chains = []
    rna_chains = []

    for seq in sequences:
        if "protein" in seq:
            chain_ids = seq["protein"]["id"]
            if isinstance(chain_ids, list):
                protein_chains.extend(chain_ids)
            else:
                protein_chains.append(chain_ids)
        elif "ligand" in seq:
            chain_ids = seq["ligand"]["id"]
            if isinstance(chain_ids, list):
                ligand_chains.extend(chain_ids)
            else:
                ligand_chains.append(chain_ids)
        elif "dna" in seq:
            chain_ids = seq["dna"]["id"]
            if isinstance(chain_ids, list):
                dna_chains.extend(chain_ids)
            else:
                dna_chains.append(chain_ids)
        elif "rna" in seq:
            chain_ids = seq["rna"]["id"]
            if isinstance(chain_ids, list):
                rna_chains.extend(chain_ids)
            else:
                rna_chains.append(chain_ids)

    # Determine complex type
    if len(protein_chains) > 1 and not ligand_chains and not dna_chains and not rna_chains:
        return f"Protein multimer ({len(protein_chains)} chains)"
    elif len(protein_chains) >= 1 and ligand_chains:
        return f"Protein-ligand complex ({len(protein_chains)} protein, {len(ligand_chains)} ligand)"
    elif len(protein_chains) >= 1 and dna_chains:
        return f"Protein-DNA complex ({len(protein_chains)} protein, {len(dna_chains)} DNA)"
    elif len(protein_chains) >= 1 and rna_chains:
        return f"Protein-RNA complex ({len(protein_chains)} protein, {len(rna_chains)} RNA)"
    elif len(protein_chains) == 1:
        return "Single protein"
    else:
        return "Mixed/Other complex"

def main():
    parser = argparse.ArgumentParser(
        description="Boltz2 Complex Structure Prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Predict protein-ligand complex
  python examples/use_case_4_complex_structure_prediction.py --input examples/data/ligand.yaml

  # Predict protein-protein complex (heterodimer)
  python examples/use_case_4_complex_structure_prediction.py --input examples/data/multimer.yaml

  # Predict with pocket constraints
  python examples/use_case_4_complex_structure_prediction.py --input examples/data/pocket.yaml

  # Create custom protein-ligand complex
  python examples/use_case_4_complex_structure_prediction.py \\
    --create protein_ligand \\
    --protein-seq "MVTPEGNVSLVDES..." \\
    --ligand-smiles "CC(=O)OC1=CC=CC=C1C(=O)O"

  # Create custom protein dimer
  python examples/use_case_4_complex_structure_prediction.py \\
    --create protein_protein \\
    --seq1 "MVTPEGNVSLVDES..." \\
    --seq2 "QLEDSEVEAVAKGL..."

  # Create multimer (same sequence, multiple chains)
  python examples/use_case_4_complex_structure_prediction.py \\
    --create multimer \\
    --sequence "MVTPEGNVSLVDES..." \\
    --chain-count 4
        """)

    parser.add_argument("--input", "-i", type=str, help="Input YAML file")
    parser.add_argument("--create", type=str, choices=["protein_ligand", "protein_protein", "multimer"],
                       help="Create custom complex configuration")
    parser.add_argument("--protein-seq", type=str, help="Protein sequence (for protein_ligand)")
    parser.add_argument("--ligand-smiles", type=str, help="Ligand SMILES")
    parser.add_argument("--ligand-ccd", type=str, help="Ligand CCD code")
    parser.add_argument("--seq1", type=str, help="First protein sequence (for protein_protein)")
    parser.add_argument("--seq2", type=str, help="Second protein sequence (for protein_protein)")
    parser.add_argument("--sequence", type=str, help="Protein sequence (for multimer)")
    parser.add_argument("--chain-count", type=int, default=2, help="Number of chains (for multimer)")
    parser.add_argument("--output", "-o", type=str, default="./boltz_complex_output",
                       help="Output directory (default: ./boltz_complex_output)")
    parser.add_argument("--no-msa-server", action="store_true",
                       help="Don't use MSA server (faster but less accurate)")
    parser.add_argument("--use-potentials", action="store_true",
                       help="Use inference-time potentials for better physical quality")

    args = parser.parse_args()

    # Validate input
    if not args.input and not args.create:
        print("Error: Must provide either --input file or --create configuration")
        sys.exit(1)

    if args.input and args.create:
        print("Error: Provide either --input file OR --create, not both")
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
        complex_type = identify_complex_type(input_yaml)
        print(f"Using input file: {input_yaml}")
        print(f"Detected complex type: {complex_type}")
    else:
        # Create custom configuration
        temp_yaml = output_dir / f"temp_{args.create}.yaml"

        if args.create == "protein_ligand":
            if not args.protein_seq or (not args.ligand_smiles and not args.ligand_ccd):
                print("Error: protein_ligand requires --protein-seq and (--ligand-smiles OR --ligand-ccd)")
                sys.exit(1)
            input_yaml = create_complex_yaml(
                "protein_ligand", temp_yaml,
                protein_seq=args.protein_seq,
                ligand_smiles=args.ligand_smiles,
                ligand_ccd=args.ligand_ccd
            )
        elif args.create == "protein_protein":
            if not args.seq1 or not args.seq2:
                print("Error: protein_protein requires --seq1 and --seq2")
                sys.exit(1)
            input_yaml = create_complex_yaml(
                "protein_protein", temp_yaml,
                seq1=args.seq1,
                seq2=args.seq2
            )
        elif args.create == "multimer":
            if not args.sequence:
                print("Error: multimer requires --sequence")
                sys.exit(1)
            input_yaml = create_complex_yaml(
                "multimer", temp_yaml,
                sequence=args.sequence,
                chain_count=args.chain_count
            )

        print(f"Created temporary input file: {input_yaml}")

    print(f"Output directory: {output_dir}")
    print(f"Using MSA server: {not args.no_msa_server}")
    print(f"Using potentials: {args.use_potentials}")

    # Run prediction
    success = run_boltz_complex_prediction(
        input_yaml,
        str(output_dir),
        use_msa_server=not args.no_msa_server,
        use_potentials=args.use_potentials
    )

    if success:
        print(f"\nPrediction completed! Check output in: {output_dir}")

        # Analyze results
        analyze_complex_results(output_dir)

        print(f"\nOutput files:")
        print("  - predictions/[input_name]/[input_name]_model_0.pdb  # Predicted complex structure")
        print("  - predictions/[input_name]/confidence_[input_name]_model_0.json  # Structure confidence")

        # Check for affinity results if it was a ligand complex
        pred_dir = output_dir / "predictions"
        affinity_files = list(pred_dir.rglob("affinity_*.json")) if pred_dir.exists() else []
        if affinity_files:
            print("  - predictions/[input_name]/affinity_[input_name].json  # Binding affinity (if applicable)")

        # List actual output files
        if pred_dir and pred_dir.exists():
            print(f"\nAll output files in {pred_dir}:")
            for file in pred_dir.rglob("*"):
                if file.is_file():
                    print(f"  - {file.relative_to(output_dir)}")
    else:
        print("Prediction failed. Check error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()