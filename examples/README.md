# Boltz2 MCP Examples

This directory contains example scripts and data for using Boltz2 through the MCP server. Boltz2 is a state-of-the-art biomolecular structure and affinity prediction model.

## Available Use Cases

### 1. Structure Prediction (`use_case_1_structure_prediction.py`)
Basic protein structure prediction using Boltz2.

**Capabilities:**
- Single protein structure prediction
- Support for MSA server or custom MSA files
- Confidence scoring and quality assessment

**Examples:**
```bash
# Use provided example
python examples/use_case_1_structure_prediction.py --input examples/data/prot.yaml

# Predict from sequence
python examples/use_case_1_structure_prediction.py --sequence "QLEDSEVEAVAKGLEEMYANG..."

# Fast prediction without MSA (less accurate)
python examples/use_case_1_structure_prediction.py --input examples/data/prot.yaml --no-msa-server

# High quality with potentials
python examples/use_case_1_structure_prediction.py --input examples/data/prot.yaml --use-potentials
```

### 2. Affinity Prediction (`use_case_2_affinity_prediction.py`)
Binding affinity prediction for protein-ligand complexes.

**Capabilities:**
- Simultaneous structure and affinity prediction
- Support for SMILES and CCD ligand formats
- Dual affinity metrics: binding strength and binary classification

**Examples:**
```bash
# Use provided example
python examples/use_case_2_affinity_prediction.py --input examples/data/affinity.yaml

# Custom protein-ligand pair
python examples/use_case_2_affinity_prediction.py \
  --protein-seq "MVTPEGNVSLVDES..." \
  --ligand-smiles "N[C@@H](Cc1ccc(O)cc1)C(=O)O"

# Use CCD ligand code
python examples/use_case_2_affinity_prediction.py \
  --protein-seq "MVTPEGNVSLVDES..." \
  --ligand-ccd "ATP"
```

### 3. Batch Structure Prediction (`use_case_3_batch_structure_prediction.py`)
Batch processing for multiple protein variants or configurations.

**Capabilities:**
- Parallel processing of multiple structures
- Variant analysis from text files
- Comprehensive reporting and comparison

**Examples:**
```bash
# Process all YAML files in data directory
python examples/use_case_3_batch_structure_prediction.py --config-dir examples/data

# Process specific files
python examples/use_case_3_batch_structure_prediction.py \
  --input-files examples/data/prot.yaml examples/data/multimer.yaml

# Process variants from file
python examples/use_case_3_batch_structure_prediction.py --variant-file examples/protein_variants.txt

# Parallel processing (adjust workers based on system)
python examples/use_case_3_batch_structure_prediction.py \
  --config-dir examples/data --max-workers 4
```

### 4. Complex Structure Prediction (`use_case_4_complex_structure_prediction.py`)
Prediction of biomolecular complexes including protein-protein, protein-ligand, and protein-nucleic acid interactions.

**Capabilities:**
- Protein-protein complex prediction
- Protein-ligand complex modeling
- Multimer structure prediction
- Interface confidence assessment

**Examples:**
```bash
# Protein-ligand complex
python examples/use_case_4_complex_structure_prediction.py --input examples/data/ligand.yaml

# Protein multimer
python examples/use_case_4_complex_structure_prediction.py --input examples/data/multimer.yaml

# Custom protein-ligand complex
python examples/use_case_4_complex_structure_prediction.py \
  --create protein_ligand \
  --protein-seq "MVTPEGNVSLVDES..." \
  --ligand-smiles "CC(=O)OC1=CC=CC=C1C(=O)O"

# Custom protein dimer
python examples/use_case_4_complex_structure_prediction.py \
  --create protein_protein \
  --seq1 "MVTPEGNVSLVDES..." \
  --seq2 "QLEDSEVEAVAKGL..."
```

## Data Directory Structure

```
examples/data/
├── affinity.yaml          # Protein-ligand affinity example
├── cyclic_prot.yaml       # Cyclic protein example
├── ligand.fasta          # Legacy FASTA format (deprecated)
├── ligand.yaml           # Multi-ligand complex example
├── multimer.yaml         # Protein-protein complex example
├── pocket.yaml           # Pocket-constrained prediction
├── prot_custom_msa.yaml  # Custom MSA example
├── prot.fasta           # Legacy FASTA format (deprecated)
├── prot_no_msa.yaml     # Single-sequence mode example
├── prot.yaml            # Basic protein structure example
└── msa/                  # MSA files
    ├── seq1.a3m
    └── seq2.a3m
```

## Example Variants File Format

For batch processing, create a CSV file with variant definitions:

```csv
# protein_variants.txt
# Format: variant_name,protein_sequence
wild_type,QLEDSEVEAVAKGLEEMYANGVTEDNFKNYVKNNFAQQEISSVEEELNVNISDSCVANKIKDEFFAMISISAIVKAAQKKAWKELAVTVLRFAKANGLKTNAIIVAGQLALWAVQCG
mutant_A10G,QLEDSEVEAVGKGLEEMYANGVTEDNFKNYVKNNFAQQEISSVEEELNVNISDSCVANKIKDEFFAMISISAIVKAAQKKAWKELAVTVLRFAKANGLKTNAIIVAGQLALWAVQCG
mutant_K35A,QLEDSEVEAVAKGLEEMYANGVTEDNFKNYVKNNFAAQEISSVEEELNVNISDSCVANKIKDEFFAMISISAIVKAAQKKAWKELAVTVLRFAKANGLKTNAIIVAGQLALWAVQCG
```

## Understanding Output

### Structure Files
- `.pdb` or `.cif` files contain predicted 3D coordinates
- Multiple samples may be generated, ranked by confidence

### Confidence Files (`confidence_*.json`)
```json
{
  "confidence_score": 0.84,     // Overall confidence (0-1)
  "ptm": 0.85,                  // Predicted TM score
  "iptm": 0.82,                 // Interface TM score
  "complex_plddt": 0.83,        // Average confidence score
  "chains_ptm": {...},          // Per-chain confidence
  "pair_chains_iptm": {...}     // Pairwise interface confidence
}
```

### Affinity Files (`affinity_*.json`)
```json
{
  "affinity_pred_value": -1.2,         // Binding affinity (log10(IC50))
  "affinity_probability_binary": 0.85   // Binding probability (0-1)
}
```

**Affinity Interpretation:**
- `affinity_pred_value`: log10(IC50) in μM
  - < -2: Strong binder (IC50 < 10 nM)
  - -2 to 1: Moderate binder (10 nM - 10 μM)
  - > 1: Weak binder/Decoy (> 10 μM)
- `affinity_probability_binary`: Probability that ligand is a binder
  - > 0.5: Likely binder
  - < 0.5: Likely non-binder

## Performance Tips

1. **MSA Server**: Use `--use_msa_server` for best accuracy (requires internet)
2. **Potentials**: Add `--use_potentials` for better physical quality
3. **Parallel Processing**: Adjust `--max-workers` based on available CPU/GPU resources
4. **GPU Memory**: Reduce batch size if running out of GPU memory

## Common Issues

1. **CUDA out of memory**: Reduce sequence length or use CPU mode
2. **MSA server timeout**: Use `--no-msa-server` for faster processing
3. **Large ligands**: Boltz2 works best with ligands <128 atoms (optimal <56 atoms)
4. **Old GPUs**: Use `--no_kernels` flag if encountering cuequivariance errors

## Requirements

- Conda environment with Boltz2 installed
- GPU recommended for faster predictions
- Internet access for MSA server (optional but recommended)
- Python 3.10+