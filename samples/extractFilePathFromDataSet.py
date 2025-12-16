#! /usr/bin/python3

import os

def get_file_list(dataset_name):
    """
    Queries the CMS Data Aggregation System (DAS) to get the list of files
    for a given dataset and prepends the XRootD redirector.
    """
    
    # Construct the DAS query command.
    # 'limit=0' ensures we fetch all files, not just a partial list.
    query = f'dasgoclient --query="file dataset={dataset_name}" --limit=0'
    
    print(f"Executing DAS query: {query}")
    print("Please wait, this might take a moment...")

    # Execute the command in the shell and read the output.
    # returning a list of file paths (Logical File Names - LFN).
    files = os.popen(query).read().split()
    
    if not files:
        print("Error: No files found. Please check your proxy (voms-proxy-init) or the dataset name.")
        return []

    # Define the Global Redirector.
    # This allows ROOT to access files via XRootD from any location.
    redirector = "root://cms-xrd-global.cern.ch/"
##    redirector = "root://xrootd-cms.infn.it//"

    # Prepend the redirector to each file path (LFN -> PFN).
    full_paths = [redirector + f for f in files]
    
    return full_paths

if __name__ == "__main__":
    # --- Configuration ---
    # The specific dataset you requested
    target_dataset = "/TTHHTo4b_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v2/NANOAODSIM"
    output_filename = "file_list.txt"

    # --- Execution ---
    # Get the list of files
    file_list = get_file_list(target_dataset)

    # Save the result to a text file
    if file_list:
        with open(output_filename, "w") as f_out:
            for file_path in file_list:
                f_out.write(file_path + "\n")
        
        print(f"Success! Found {len(file_list)} files.")
        print(f"File list saved to: {output_filename}")
        
        # Print the first 3 files as a sanity check
        print("\n[Preview of first 3 files]")
        for i in range(min(3, len(file_list))):
            print(file_list[i])
