#!/usr/bin/env python3
import sys
import os
import argparse
import shutil
import textwrap

def main():
    """
    CMS Analysis Framework Generator (Basic)
    Structure:
      - main.cc, Makefile, submit_condor.py (Root)
      - include/ (.h)
      - src/ (.C)
      - condor/ (Logs and submission files will be created here)
    """
    parser = argparse.ArgumentParser(description="Generate a Basic CMS Analysis Framework")
    parser.add_argument("-f", "--file", required=True, help="Sample ROOT file path")
    parser.add_argument("-t", "--tree", default="Events", help="TTree name (default: Events)")
    parser.add_argument("-c", "--class", dest="classname", default="CMSAnalyzer", help="Class Name")
    args = parser.parse_args()

    sample_file = args.file
    tree_name = args.tree
    class_name = args.classname
    output_dir = class_name

    print(f"[INFO] Initializing Basic Framework in: {output_dir}/")

    # 1. Check ROOT
    try: import ROOT
    except ImportError: sys.exit("[ERROR] ROOT not found.")

    # 2. Open File & Get Tree
    ROOT.gROOT.SetBatch(True)
    f = ROOT.TFile.Open(sample_file, "READ")
    if not f or f.IsZombie(): sys.exit(f"[ERROR] Cannot open {sample_file}")
    tree = f.Get(tree_name)
    if not tree: sys.exit(f"[ERROR] Tree '{tree_name}' not found.")

    # 3. Create Directories
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        os.makedirs(os.path.join(output_dir, "src"))
        os.makedirs(os.path.join(output_dir, "include"))
        # We don't necessarily need to create 'condor' here, submitter will do it, 
        # but creating it ensures the structure is visible.
        os.makedirs(os.path.join(output_dir, "condor"))

    original_cwd = os.getcwd()
    os.chdir(output_dir)

    # 4. Run MakeClass
    print(f"[INFO] Running MakeClass('{class_name}')...")
    tree.MakeClass(class_name)
    f.Close()

    # 5. Move Files
    if os.path.exists(f"{class_name}.C"): shutil.move(f"{class_name}.C", f"src/{class_name}.C")
    if os.path.exists(f"{class_name}.h"): shutil.move(f"{class_name}.h", f"include/{class_name}.h")

    # 6. Generate main.cc (At Root)
    with open("main.cc", "w") as f_main:
        f_main.write(f"""/**
 * @file main.cc
 * @brief Main driver for {class_name}
 */
#include "{class_name}.h"
#include <iostream>
#include <fstream>
#include "TChain.h"

int main(int argc, char* argv[]) {{
    if (argc < 2) {{
        std::cout << "Usage: " << argv[0] << " <file_list.txt> [output_file_name]" << std::endl;
        return 1;
    }}
    std::string listFileName = argv[1];
    // Output filename argument (optional in basic version)
    std::string outFileName = (argc > 2) ? argv[2] : "output.root";
    
    TChain *chain = new TChain("{tree_name}");
    std::ifstream infile(listFileName);
    std::string line;
    while (std::getline(infile, line)) {{
        if (line.empty() || line[0] == '#') continue;
        chain->Add(line.c_str());
    }}

    {class_name} t(chain);
    t.Loop();
    return 0;
}}
""")

    # 7. Generate Makefile
    with open("Makefile", "w") as f_make:
        f_make.write(f"""CXX = g++
INC = -Iinclude
CXXFLAGS = -O2 -Wall -fPIC $(shell root-config --cflags) $(INC)
LDFLAGS = $(shell root-config --libs)
TARGET = runAnalysis

# main.cc is in Root, Analyzer.C is in src
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
""")

    # 8. Generate submit_condor.py (Pointing to 'condor/' directory)
    condor_script = textwrap.dedent(f"""\
    #!/usr/bin/env python3
    import os, sys, subprocess

    # --- Config ---
    EXE_NAME = "runAnalysis"
    EOS_BASE = "/eos/user/{os.getlogin()[0]}/{os.getlogin()}/AnalyzerOutput" # Default: User's EOS
    
    def main(config_file):
        with open(config_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    submit_job(line.strip())

    def submit_job(line):
        parts = line.split()
        input_list, output_subdir = parts[0], parts[1]
        
        # All files go into 'condor/<output_subdir>'
        job_dir = f"condor/{{output_subdir}}"
        os.makedirs(job_dir, exist_ok=True)
        
        # Split input list
        with open(input_list) as f_in:
            files = [l.strip() for l in f_in if l.strip()]
        
        arg_file = f"{{job_dir}}/arguments.txt"
        with open(arg_file, 'w') as f_args:
            for i, f_path in enumerate(files):
                chunk_name = f"{{job_dir}}/chunk_{{i}}.txt"
                with open(chunk_name, 'w') as f_chunk: f_chunk.write(f_path)
                # Args: [InputList] [OutputName] [EOSDir]
                # Absolute path for chunk name to be safe
                f_args.write(f"{{os.path.abspath(chunk_name)}} output_{{i}}.root {{EOS_BASE}}/{{output_subdir}}\\n")

        # Create wrapper
        with open(f"{{job_dir}}/wrapper.sh", 'w') as f_sh:
            f_sh.write(f"#!/bin/bash\\ncd {{os.getcwd()}}\\n")
            f_sh.write("source /cvmfs/cms.cern.ch/cmsset_default.sh\\ncmsenv\\n")
            f_sh.write(f"./{{EXE_NAME}} $1 $2\\n") # $1=Input, $2=OutputName
            f_sh.write("xrdcp -f $2 root://eosuser.cern.ch/$3/$2\\nrm $2\\n")
        os.chmod(f"{{job_dir}}/wrapper.sh", 0o755)

        # Create Submit file
        with open(f"{{job_dir}}/job.sub", 'w') as f_sub:
            f_sub.write(f"executable={{job_dir}}/wrapper.sh\\narguments=$(args)\\n")
            f_sub.write(f"output={{job_dir}}/job.$(ClusterId).out\\nerror={{job_dir}}/job.$(ClusterId).err\\nlog={{job_dir}}/job.log\\n")
            f_sub.write(f"getenv=True\\n+JobFlavour=\\"tomorrow\\"\\nqueue args from {{arg_file}}\\n")
        
        print(f"[INFO] Submitting {{output_subdir}} -> Logs in {{job_dir}}")
        subprocess.call(["condor_submit", f"{{job_dir}}/job.sub"])

    if __name__ == "__main__":
        if len(sys.argv) < 2: exit("Usage: python3 submit_condor.py <config.txt>")
        main(sys.argv[1])
    """)
    
    with open("submit_condor.py", "w") as f_condor:
        f_condor.write(condor_script)
    os.chmod("submit_condor.py", 0o755)

    os.chdir(original_cwd)
    print("[DONE] Basic Framework Generated.")

if __name__ == "__main__":
    main()
