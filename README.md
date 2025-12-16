# CMS Analysis Framework Generator

This tool (`setup_framework.py`) is a wrapper that automates the initialization of a ROOT-based analysis framework. It replaces the manual process of running `MakeClass`, writing a `main` function, and creating a `Makefile`. 

And You can use more advanced version (`setup_framework_advanced.py`) to create more detail C++ framework and also has more arguments.

## Prerequisites

* **ROOT** (v6.x)
* **Python 3**
* **VOMS Proxy** (For accessing files via XRootD)
   ```bash
   voms-proxy-init --voms cms
   ```

## Usage

### 1. Get File List
First, generate a list of file paths from a dataset name using `dasgoclient`.
```bash
# Edit the dataset name in get_file_list.py before running
python3 get_file_list.py
# Output: file_list.txt
```

### 2. Generate the Code
Run the python script. You must provide a sample file.

```bash
# Basic Usage (Default class name: CMSAnalyzer, Tree: Events)
python3 setup_framework.py -f root://cms-xrd-global.cern.ch///store/mc/.../sample.root
# --> This will create a folder named "CMSAnalyzer" and put all code inside it.

# Custom Usage
python3 setup_framework.py -f root://.../sample.root -t Events -c MyPhysicsAnalyzer
# --> This will create a folder named "MyPhysicsAnalyzer" and put all code inside it.
```

**Output:** The script will generate the following files in your current directory:

Directory Structure Created:
```
.
├── setup_framework.py
├── get_file_list.py
├── file_list.txt
├── README.md
└── CMSAnalyzer/          <-- Created Directory
    ├── Makefile
    ├── main.cc
    ├── submit_condor.py          # HTCondor Job Submitter
    ├── include/
    │   └── CMSAnalyzer.h     # Header (Auto-injected with settings)
    └── src/
    │   └── CMSAnalyzer.C     # Source (Loop with Histograms)
    └── condor/                   # [NEW] Directory for Condor logs & files
            └── (job folders...)

```

- `CMSAnalyzer.h`: Header file defining the Tree structure.
    
- `CMSAnalyzer.C`: Source file containing the `Loop()` function (Where you write your cuts/histograms).
    
- `main.cc`: C++ runner that handles file lists and TChains.
    
- `Makefile`: Configuration to compile everything.
    

### 2. Compile

Simply run `make` in the Analyzer directory.

Bash

```
cd CMSAnalyzer
make
```

This will produce an executable named **`runAnalysis`**.

### 3. Run

Prepare a text file containing the list of ROOT files you want to analyze (e.g., `file_list.txt`).

Bash

```
./runAnalysis file_list.txt
```

---

## Workflow Example

1. **Get File List:** Use your DAS script to get files.
    
    ```Bash
    python3 get_file_list.py
    ```
    
2. **Setup Framework:** (Only needed once)
    
    ```Bash
    # Use one of the files from the list as a template
    python3 setup_framework.py -f "root://cms-xrd-global.cern.ch///store/mc/RunIISummer20UL17NanoAODv9/TTHHTo4b_TuneCP5_13TeV-madgraph-pythia8/NANOAODSIM/106X_mc2017_realistic_v9-v2/30000/C038057C-3788-BE43-92E1-D4395DE47AF3.root"
    cd CMSAnalyzer
    ```
    
3. **Edit Code:** Open `CMSAnalyzer.C` and modify the `Loop()` function to add your physics logic.
    
4. **Build & Run:**
    
    ```Bash
    mv ../file_list.txt .
    make
    ./runAnalysis file_list.txt
    ```
 
## Workflow Example for detail version

1. **Get File List:** Use your DAS script to get files.
    
    ```Bash
    python3 get_file_list.py
    ```
    
2. **Setup Framework:** (Only needed once)
    
    ```Bash
    # Use one of the files from the list as a template
    python3 setup_framework_advanced.py -f "root://cms-xrd-global.cern.ch///store/mc/RunIISummer20UL17NanoAODv9/TTHHTo4b_TuneCP5_13TeV-madgraph-pythia8/NANOAODSIM/106X_mc2017_realistic_v9-v2/30000/C038057C-3788-BE43-92E1-D4395DE47AF3.root"
    cd CMSAnalyzer
    ```
    
3. **Edit Code:** Open `CMSAnalyzer.C` and modify the `Loop()` function to add your physics logic.
    
4. **Build & Run:**
    
    ```Bash
    mv ../file_list.txt .

    # Run on MC (Weight 0.5, Process ttbar)
    ./runAnalysis file_list.txt output_test.root 0.5 0 ttbar

    # Run on Data (Weight 1.0, IsData 1)
    ./runAnalysis data_list.txt output_data.root 1.0 1 data
    ```
    
  
---

## Key Features of this Wrapper

1.  **Automated `MakeClass`**: It performs the exact same operation as opening ROOT and typing `tree->MakeClass()`, but does it silently in the background.
2.  **Integrated `main.cc`**: You don't need to write the C++ boilerplate code to read `std::ifstream` or setup `TChain`. It creates a robust `main.cc` that links to your Analyzer.
3.  **Smart Makefile**: It creates a `Makefile` that handles the linking between the `.cc` (main) and `.C` (Analyzer) files automatically using `root-config`.
4.  **Flexibility**: You can change the class name (`-c`) or the tree name (`-t`) via arguments without changing the python code.



## Implement Analysis Logic

Go into the generated directory. Open the `.C` file (e.g., `MyPhysicsAnalyzer.C`) and modify the `Loop()` function.

#### **Example Code Snippet**

Copy and paste the following code into your `Loop()` function to plot **Muon, Electron, and Jet** kinematics.

**Don't forget to add headers at the top of the `.C` file:**

C++

```
#include <TH2.h>
#include <TStyle.h>
#include <TCanvas.h>
#include <iostream>
```

**Implementation inside `Loop()`:**

C++

```
void MyPhysicsAnalyzer::Loop()
{
   if (fChain == 0) return;

   Long64_t nentries = fChain->GetEntriesFast();

   // --- [1] Define Histograms ---
   TH1F *h_mu_pt   = new TH1F("h_mu_pt",   "Muon p_{T};p_{T} (GeV);Events", 100, 0, 200);
   TH1F *h_mu_eta  = new TH1F("h_mu_eta",  "Muon #eta;#eta;Events", 50, -2.5, 2.5);
   
   TH1F *h_ele_pt  = new TH1F("h_ele_pt",  "Electron p_{T};p_{T} (GeV);Events", 100, 0, 200);
   TH1F *h_ele_eta = new TH1F("h_ele_eta", "Electron #eta;#eta;Events", 50, -2.5, 2.5);
   
   TH1F *h_jet_pt  = new TH1F("h_jet_pt",  "Jet p_{T};p_{T} (GeV);Events", 100, 0, 400);
   TH1F *h_jet_phi = new TH1F("h_jet_phi", "Jet #phi;#phi;Events", 50, -3.14, 3.14);

   Long64_t nbytes = 0, nb = 0;
   
   // --- [2] Event Loop ---
   for (Long64_t jentry=0; jentry<nentries;jentry++) {
      Long64_t ientry = LoadTree(jentry);
      if (ientry < 0) break;
      nb = fChain->GetEntry(jentry);   nbytes += nb;

      // Print progress
      if(jentry % 10000 == 0) std::cout << "Processing Entry: " << jentry << std::endl;

      // --- [3] Muon Loop (Example) ---
      for (int i = 0; i < nMuon; i++) {
          if (Muon_pt[i] > 20) { 
              h_mu_pt->Fill(Muon_pt[i]);
              h_mu_eta->Fill(Muon_eta[i]);
          }
      }

      // --- [4] Electron Loop (Example) ---
      for (int i = 0; i < nElectron; i++) {
          h_ele_pt->Fill(Electron_pt[i]);
          h_ele_eta->Fill(Electron_eta[i]);
      }

      // --- [5] Jet Loop (Example) ---
      for (int i = 0; i < nJet; i++) {
          if (Jet_pt[i] > 30) {
              h_jet_pt->Fill(Jet_pt[i]);
              h_jet_phi->Fill(Jet_phi[i]);
          }
      }
   }

   // --- [6] Save Histograms ---
   TFile *f_out = new TFile("output.root", "RECREATE");
   h_mu_pt->Write();
   h_mu_eta->Write();
   h_ele_pt->Write();
   h_ele_eta->Write();
   h_jet_pt->Write();
   h_jet_phi->Write();
   
   f_out->Close();
   std::cout << "Analysis Complete. Output saved to 'output.root'" << std::endl;
}
```

## Compile and Run

Once your code is ready, use the generated `Makefile`.

```BASH
cd MyPhysicsAnalyzer
make
./runAnalysis file_list.txt
```

or for more detail version

```BASH
# Run on MC (Weight 0.5, Process ttbar)
./runAnalysis file_list.txt output_test.root 0.5 0 ttbar

# Run on Data (Weight 1.0, IsData 1)
./runAnalysis data_list.txt output_data.root 1.0 1 data
```

## 3. How to Submit to Condor

### Step 1: Prepare Config File

Create a text file (e.g., `job_config.txt`) where each line represents a dataset job. **Format:** `ListFile OutputDirName Weight IsData(0/1) ProcessName`

Plaintext

```
# job_config.txt (Example)
lists/ttbar.txt   ttbar_2017   1.23   0   ttbar
lists/data.txt    data_2017    1.00   1   data
lists/dy.txt      dy_2017      0.89   0   dy
```

### Step 2: Check `submit_condor.py`

Open `submit_condor.py` and ensure the `EOS_BASE` variable matches your EOS directory.

Python

```
EOS_BASE = "/eos/user/j/junghyun/ttHH/AnalyzerOutput"
```

### Step 3: Submit Jobs

Run the python script with your config file.

Bash

```
voms-proxy-init --voms cms
python3 submit_condor.py job_config.txt
```

### Step 4: Check Logs

The script will **not** clutter your root directory. All job files are created inside `condor/`.

- **Logs & Error**: `condor/<OutputDirName>/job.*.out` / `.err`
    
- **Submit File**: `condor/<OutputDirName>/job.sub`
    
- **Wrapper**: `condor/<OutputDirName>/wrapper.sh`
    

Bash

```
ls -l condor/ttbar_2017/
```
