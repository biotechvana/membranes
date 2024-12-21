# Membrane CLI Tool

A command-line tool for processing Membranes model structure and its rules [text/ini] input files and generate membrane plot and rule network dynamics plot.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/biotechvana/membranes.git
cd membranes
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate # On Windows, use: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

The tool requires two mandatory arguments:
- `--input`: Path to the input text/ini file
- `--output`: Output path and prefix for generated files

Basic usage:
```bash
python membrane.py --input input/example1.ini --output output/example1
```

Examples:
```bash
# Using current directory with default prefix 'output'
python membrane.py --input input/example1.ini --output .

# Using just a prefix in current directory
python membrane.py --input input/example1.ini --output myprefix

# Using a path and prefix
python membrane.py --input input/example1.ini --output path/to/myprefix

# Using a path with default prefix 'output'
python membrane.py --input input/example1.ini --output path/to/
```

The tool will:
1. Extract the directory path and file prefix from the output argument
2. Create the output directory if it doesn't exist
3. Generate files using the specified prefix in the specified location

## Input Format

The input file should be in this format. Example:
```ini
skin:SK
membranes:
[
    2Vac1,
    10[PRR]DCsk,     
    10000[PRR]Monosk,
    [
        1000CA, 2000CHOL,
        []LS,
        10[PRR]DCcs,
        [
            500[BCR]BLln,
            1000[TCR]TL4ln
        ]LyS
    ]CS
]SK
rules:
[2Vac1]SK -> [5IL-8]SK (Name=r1)

[5IL-8]SK -> []SK (Name=r2)

[5IL-8, []CS]SK -> [[5IL-8]CS]SK (Name=r3)

[1Vac1, 10[PRR]DCsk, 10000[PRR]Monosk]SK -> [10[1Vac1, PRRa]DCsk, 10000[1Vac1, PRRa]Monosk]SK (Name=r4)
```

## Output

The tool will generate membrane plot and rule network dynamics plot in the output directory.

