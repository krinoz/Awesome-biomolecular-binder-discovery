import os
import torch as pt
import importlib
from tqdm import tqdm
from glob import glob
import argparse

from src.dataset import StructuresDataset, collate_batch_features
from src.data_encoding import encode_structure, encode_features, extract_topology
from src.structure import encode_bfactor, concatenate_chains, split_by_chain
from src.structure_io import save_pdb

from model import Model

# Command-line argument parsing
def parse_args():
    parser = argparse.ArgumentParser(description="Apply model to PDB structures")

    # Add arguments
    parser.add_argument('--config_model_name', type=str, required=True,
                        choices=['ps-s', 'ps-g', 'pesto'],
                        help="Model configuration name: 'ps-s', 'ps-g', or 'pesto'")
    parser.add_argument('--device', type=str, default='cpu',
                        choices=['cpu', 'cuda'],
                        help="Device to use: 'cpu' or 'cuda'")
    parser.add_argument('--output_folder', type=str, required=True,
                        help="Output folder to save model checkpoints and predictions")
    parser.add_argument('--input_folder', type=str, required=True,
                        help="Input folder containing the .pdb files")
    parser.add_argument('--checkpoint', type=str, required=True,
                        help="External PeSTo i_v4_1 model_ckpt.pt path")

    return parser.parse_args()

# Function to apply model
def apply_model(data_path, config_model_name, device, output_folder, checkpoint_path):
    # Set the device based on user input
    # device = pt.device(device if pt.cuda.is_available() else 'cpu')
    device = pt.device(device)
    if device.type == 'cuda':
        print("Using GPU")
    else:
        print("Using CPU")

    # Dynamically load the correct configuration module
    config_module = importlib.import_module(f"config.config_model_{config_model_name}")
    config_model = config_module.config_model

    if not os.path.isfile(checkpoint_path):
        raise FileNotFoundError(f"PeSTo checkpoint not found: {checkpoint_path}")
    os.makedirs(output_folder, exist_ok=True)

    # Create model
    model = Model(config_model)

    # Reload model from checkpoint
    model.load_state_dict(pt.load(checkpoint_path, map_location=pt.device("cpu")))

    # Set model to evaluation mode and move to the correct device
    model = model.eval().to(device)

    # Find all .pdb files
    pdb_filepaths = glob(os.path.join(data_path, "*.pdb"), recursive=True)
    pdb_filepaths = [
        fp for fp in pdb_filepaths if "_i" not in os.path.basename(fp)
    ]  # Ignore already predicted files without rejecting parent directory names.

    # Create dataset loader with preprocessing
    dataset = StructuresDataset(pdb_filepaths, with_preprocessing=True)

    # Debug print
    print(f"Processing: {len(dataset)} files")

    # Run model on all subunits
    with pt.no_grad():
        for subunits, filepath in tqdm(dataset):
            # print(filepath)

            # Concatenate all chains together
            structure = concatenate_chains(subunits)

            # Encode structure and features
            X, M = encode_structure(structure)
            q = encode_features(structure)[0]

            # Extract topology
            ids_topk, _, _, _, _ = extract_topology(X, 64)

            # Pack data and setup sink
            X, ids_topk, q, M = collate_batch_features([[X, ids_topk, q, M]])

            # Run model
            z = model(X.to(device), ids_topk.to(device), q.to(device), M.float().to(device))

            # Save results for all predictions
            for i in range(z.shape[1]):
                p = pt.sigmoid(z[:, i])
                structure = encode_bfactor(structure, p.cpu().numpy())

                output_filename = os.path.basename(filepath).replace('.pdb', f'_i{i}.pdb')
                print(output_filename)
                output_filepath = os.path.join(output_folder, output_filename)

                save_pdb(split_by_chain(structure), output_filepath)

if __name__ == '__main__':
    # Parse command-line arguments
    args = parse_args()

    # Apply model using provided arguments
    apply_model(
        args.input_folder,
        args.config_model_name,
        args.device,
        args.output_folder,
        args.checkpoint,
    )
