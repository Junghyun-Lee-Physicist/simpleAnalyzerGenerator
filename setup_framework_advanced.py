#!/usr/bin/env python3
import sys
import os
import argparse
import shutil
import textwrap

def main():
    """
    CMS Analysis Framework Generator (Advanced - Final Fix)
    
    Fixes:
      1. Wrapper script now uses 'eval $(scramv1 runtime -sh)' instead of 'cmsenv'.
      2. Wrapper checks if 'runAnalysis' exists before running.
      3. Analyzer code uses UInt_t to avoid compiler warnings.
    """
    parser = argparse.ArgumentParser(description="Generate an Advanced CMS Analysis Framework")
    parser.add_argument("-f", "--file", required=True, help="Sample ROOT file path")
    parser.add_argument("-t", "--tree", default="Events", help="TTree name (default: Events)")
    parser.add_argument("-c", "--class", dest="classname", default="CMSAnalyzer", help="Class Name")
    args = parser.parse_args()

    sample_file = args.file
    tree_name = args.tree
    class_name = args.classname
    output_dir = class_name

    print("-" * 60)
    print(f"[INFO] Initializing ADVANCED Framework in: {output_dir}/")
    print("-" * 60)

    # 1. Setup ROOT
    try: import ROOT
    except ImportError: sys.exit("[ERROR] ROOT not found.")
    ROOT.gROOT.SetBatch(True)

    # 2. Get Tree & MakeClass
    f = ROOT.TFile.Open(sample_file, "READ")
    if not f or f.IsZombie(): sys.exit(f"[ERROR] Cannot open {sample_file}")
    tree = f.Get(tree_name)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        os.makedirs(os.path.join(output_dir, "src"))
        os.makedirs(os.path.join(output_dir, "include"))
        os.makedirs(os.path.join(output_dir, "condor"))

    original_cwd = os.getcwd()
    os.chdir(output_dir)

    print(f"[INFO] Running MakeClass...")
    tree.MakeClass(class_name)
    f.Close()

    # 3. [Advanced] Inject Member Variables into Header (.h)
    header_path = f"{class_name}.h"
    with open(header_path, "r") as f_h:
        lines = f_h.readlines()
    
    with open(f"include/{class_name}.h", "w") as f_h_new:
        inserted = False
        for line in lines:
            f_h_new.write(line)
            # Robust check for public section
            if "public" in line and ":" in line and not inserted:
                f_h_new.write("\n   // --- [Advanced] User Settings ---\n")
                f_h_new.write("   float fWeight = 1.0;\n")
                f_h_new.write("   bool fIsData = false;\n")
                f_h_new.write("   TString fProcess = \"\";\n")
                f_h_new.write("   TString fOutputFileName = \"output.root\";\n")
                f_h_new.write("   // --------------------------------\n\n")
                inserted = True
    
    if os.path.exists(header_path): os.remove(header_path)

    # 4. [Advanced] Fully Implemented Source (.C)
    source_content = f"""#define {class_name}_cxx
#include "{class_name}.h"
#include <TH1.h>
#include <TH2.h>
#include <TStyle.h>
#include <TCanvas.h>
#include <iostream>

void {class_name}::Loop()
{{
   if (fChain == 0) return;

   Long64_t nentries = fChain->GetEntriesFast();

   // --- [1] Setup Output File ---
   std::cout << "[Analyzer] Output File: " << fOutputFileName << std::endl;
   TFile *f_out = new TFile(fOutputFileName, "RECREATE");
   
   // --- [2] Define Histograms ---
   TH1F *h_mu_pt   = new TH1F("h_mu_pt",   "Muon p_{{T}};p_{{T}} (GeV);Events", 200, 0.0, 2000.0);
   TH1F *h_mu_eta  = new TH1F("h_mu_eta",  "Muon #eta;#eta;Events", 60, -5.0, 5.0);
   TH1F *h_mu_phi  = new TH1F("h_mu_phi",  "Muon #phi;#phi;Events", 60, -5.0, 5.0);
   TH1F *h_ele_pt  = new TH1F("h_ele_pt",  "Electron p_{{T}};p_{{T}} (GeV);Events", 200, 0.0, 2000.0);
   TH1F *h_ele_eta = new TH1F("h_ele_eta", "Electron #eta;#eta;Events", 100, -5.0, 5.0);
   TH1F *h_ele_phi = new TH1F("h_ele_phi", "Electron #phi;#phi;Events", 100, -5.0, 5.0);
   TH1F *h_jet_pt  = new TH1F("h_jet_pt",  "Jet p_{{T}};p_{{T}} (GeV);Events", 200, 0, 2000.0);
   TH1F *h_jet_eta = new TH1F("h_jet_eta", "Jet #eta;#eta;Events", 100, -5.0, 5.0);
   TH1F *h_jet_phi = new TH1F("h_jet_phi", "Jet #phi;#phi;Events", 100, -5.0, 5.0);

   std::cout << "[Analyzer] Info: " << fProcess << " | Weight: " << fWeight << " | IsData: " << fIsData << std::endl;

   Long64_t nbytes = 0, nb = 0;
   
   for (Long64_t jentry=0; jentry<nentries;jentry++) {{
      Long64_t ientry = LoadTree(jentry);
      if (ientry < 0) break;
      nb = fChain->GetEntry(jentry);   nbytes += nb;

      if(jentry % 10000 == 0) std::cout << "Processing Entry " << jentry << " / " << nentries << std::endl;

      float w = (fIsData) ? 1.0 : fWeight;

      // --- [Muon Loop] ---
      // Uses UInt_t to prevent signed/unsigned warnings
      for (UInt_t i = 0; i < nMuon; i++) {{
          #if (Muon_pt[i] > 10.0) {{ 
              h_mu_pt->Fill(Muon_pt[i], w);
              h_mu_eta->Fill(Muon_eta[i], w);
              h_mu_phi->Fill(Muon_phi[i], w);
          #}}
      }}

      // --- [Electron Loop] ---
      for (UInt_t i = 0; i < nElectron; i++) {{
          #if (Electron_pt[i] > 10.0) {{ 
              h_ele_pt->Fill(Electron_pt[i], w);
              h_ele_eta->Fill(Electron_eta[i], w);
              h_ele_phi->Fill(Electron_phi[i], w);
          #}}
      }}

      // --- [Jet Loop] ---
      for (UInt_t i = 0; i < nJet; i++) {{
          #if (Jet_pt[i] > 30.0) {{
              h_jet_pt->Fill(Jet_pt[i], w);
              h_jet_eta->Fill(Jet_eta[i], w);
              h_jet_phi->Fill(Jet_phi[i], w);
          #}}
      }}
   }}

   f_out->Write();
   f_out->Close();
   std::cout << "[Analyzer] Finished." << std::endl;
}}
"""
    with open(f"src/{class_name}.C", "w") as f_src:
        f_src.write(source_content)
    if os.path.exists(f"{class_name}.C"): os.remove(f"{class_name}.C")


    # 5. Generate Advanced main.cc
    main_code = f"""/**
 * @file main.cc
 * @brief Advanced driver for {class_name}
 */
#include "{class_name}.h"
#include <iostream>
#include <fstream>
#include <string>
#include <cstdlib>
#include "TChain.h"

int main(int argc, char* argv[]) {{
    if (argc < 2) {{
        std::cout << "Usage: " << argv[0] << " <file_list> [output] [weight] [isData] [process]" << std::endl;
        return 1;
    }}

    std::string listFileName = argv[1];
    std::string outFileName  = (argc > 2) ? argv[2] : "output.root";
    float weight             = (argc > 3) ? atof(argv[3]) : 1.0;
    bool isData              = (argc > 4) ? (bool)atoi(argv[4]) : false;
    std::string process      = (argc > 5) ? argv[5] : "Unknown";

    TChain *chain = new TChain("{tree_name}");
    std::ifstream infile(listFileName);
    std::string line;
    while (std::getline(infile, line)) {{
        if (line.empty() || line[0] == '#') continue;
        chain->Add(line.c_str());
    }}

    {class_name} t(chain);
    t.fOutputFileName = outFileName;
    t.fWeight = weight;
    t.fIsData = isData;
    t.fProcess = process;

    t.Loop();
    return 0;
}}
"""
    with open("main.cc", "w") as f_main:
        f_main.write(main_code)


    # 6. Generate Makefile
    makefile_code = f"""CXX = g++
INC = -Iinclude
CXXFLAGS = -O2 -Wall -fPIC $(shell root-config --cflags) $(INC)
LDFLAGS = $(shell root-config --libs)
TARGET = runAnalysis

SRCS = main.cc src/{class_name}.C
OBJS = $(SRCS:.cc=.o)
OBJS := $(OBJS:.C=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) -o $@ $^ $(LDFLAGS)

%.o: %.cc
	$(CXX) $(CXXFLAGS) -c $< -o $@

src/%.o: src/%.C
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f *.o src/*.o $(TARGET)
"""
    with open("Makefile", "w") as f_make:
        f_make.write(makefile_code)


    # 7. Generate Advanced submit_condor.py (Wrapper Fixes Included)
    condor_script = textwrap.dedent(f"""\
    #!/usr/bin/env python3
    import os
    import sys
    import subprocess
    import shutil

    # --- Configuration ---
    EXE_NAME = "runAnalysis"
    EOS_BASE = "/eos/user/{os.getlogin()[0]}/{os.getlogin()}/AnalyzerOutput" 

    def main(config_file):
        print(f"[INFO] Reading config: {{config_file}}")
        with open(config_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    submit_job(line.strip())

    def submit_job(line):
        parts = line.split()
        if len(parts) < 5:
            print(f"[WARNING] Skipping invalid line: {{line}}")
            return

        input_list  = parts[0]
        output_dir  = parts[1]
        weight      = parts[2]
        is_data     = parts[3]
        process     = parts[4]

        job_dir = f"condor/{{output_dir}}"
        os.makedirs(job_dir, exist_ok=True)
        
        if not os.path.exists(input_list):
            print(f"[ERROR] List not found: {{input_list}}")
            return
            
        with open(input_list) as f_in:
            files = [l.strip() for l in f_in if l.strip()]

        print(f"[JOB] Preparing {{process}} ({{output_dir}}) with {{len(files)}} files.")

        arg_file = f"{{job_dir}}/arguments.txt"
        with open(arg_file, 'w') as f_args:
            for i, f_path in enumerate(files):
                chunk_name = f"chunk_{{i}}.txt"
                chunk_path = os.path.join(os.getcwd(), job_dir, chunk_name)
                with open(chunk_path, 'w') as f_chunk: f_chunk.write(f_path)
                
                output_name = f"output_{{i}}.root"
                eos_dest = f"{{EOS_BASE}}/{{output_dir}}"
                
                f_args.write(f"{{chunk_path}} {{output_name}} {{eos_dest}} {{weight}} {{is_data}} {{process}}\\n")

        # --- Wrapper Script (FIXED) ---
        wrapper_path = f"{{job_dir}}/wrapper.sh"
        with open(wrapper_path, 'w') as f_sh:
            f_sh.write(f"#!/bin/bash\\n")
            f_sh.write(f"cd {{os.getcwd()}}\\n")  # Go to Analyzer Directory
            f_sh.write(f"source /cvmfs/cms.cern.ch/cmsset_default.sh\\n")
            f_sh.write(f"eval $(scramv1 runtime -sh)\\n") # FIXED: Use eval instead of cmsenv
            
            f_sh.write(f"# Verify Executable\\n")
            f_sh.write(f"if [ ! -f ./{{EXE_NAME}} ]; then\\n")
            f_sh.write(f"    echo 'ERROR: {{EXE_NAME}} not found! Please run \\\"make\\\" first.'\\n")
            f_sh.write(f"    exit 1\\n")
            f_sh.write(f"fi\\n")
            
            f_sh.write(f"# Run Analyzer\\n")
            f_sh.write(f"./{{EXE_NAME}} $1 $2 $4 $5 $6\\n") # $1=Input $2=OutName $4=Weight $5=IsData $6=Process
            f_sh.write(f"# Copy to EOS\\n")
            f_sh.write(f"xrdcp -f $2 root://eosuser.cern.ch/$3/$2\\n")
            f_sh.write(f"rm $2\\n")
            
        os.chmod(wrapper_path, 0o755)

        sub_path = f"{{job_dir}}/job.sub"
        with open(sub_path, 'w') as f_sub:
            f_sub.write(f"executable = {{wrapper_path}}\\narguments = $(args)\\n")
            f_sub.write(f"output = {{job_dir}}/job.$(ClusterId).$(ProcId).out\\n")
            f_sub.write(f"error = {{job_dir}}/job.$(ClusterId).$(ProcId).err\\n")
            f_sub.write(f"log = {{job_dir}}/job.log\\n")
            f_sub.write(f"getenv = True\\n+JobFlavour = \\"tomorrow\\"\\n")
            # Force EL9 if compiling on EL9, or try to run anyway
            f_sub.write(f"queue args from {{arg_file}}\\n")
        
        print(f"[INFO] Submitting... Logs: {{job_dir}}")
        subprocess.call(["condor_submit", sub_path])

    if __name__ == "__main__":
        if len(sys.argv) < 2: 
            print("Usage: python3 submit_condor.py <config.txt>")
            sys.exit(1)
        main(sys.argv[1])
    """)
    
    with open("submit_condor.py", "w") as f_condor:
        f_condor.write(condor_script)
    os.chmod("submit_condor.py", 0o755)

    os.chdir(original_cwd)
    print(f"[DONE] Advanced Framework generated in: {output_dir}/")

if __name__ == "__main__":
    main()
