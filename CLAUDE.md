# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

viral-phylo is a set of scripts and tools for viral genome analysis: phylogenetics, annotation transfer, intrahost variant calling, and NCBI submission utilities. This is a docker-centric Python project built on top of viral-core, with wrappers for alignment tools (MAFFT, MUSCLE, MUMmer), variant callers (V-Phaser 2, LoFreq), and GenBank feature table manipulation.

## Development Commands

### Testing

**Note:** These commands assume you're inside a properly configured environment (either in a Docker container or with all dependencies installed locally). For running tests in Docker, see "Running Tests in Docker" below.

Run all unit tests:
```bash
pytest -rsxX -n auto test/unit
```

Run specific test file:
```bash
pytest test/unit/test_ncbi.py
```

Run integration tests:
```bash
pytest test/integration
```

Run with slow tests:
```bash
pytest -rsxX -n auto --runslow test/unit
```

Run with coverage:
```bash
pytest --cov
```

Show fixture durations:
```bash
pytest --fixture-durations=10 test/unit
```

### Running Tests in Docker

**IMPORTANT:** Tests must be run in a Docker container with all dependencies pre-installed. There are two approaches:

#### Option 1: Use viral-phylo Docker image (Recommended for testing)

This image has all conda dependencies pre-installed and is ready to run tests immediately:

```bash
# Run all unit tests
docker run --rm \
  -v $(pwd):/opt/viral-ngs/viral-phylo \
  -v $(pwd)/test:/opt/viral-ngs/source/test \
  quay.io/broadinstitute/viral-phylo \
  bash -c "cd /opt/viral-ngs/viral-phylo && pytest -rsxX -n auto test/unit"

# Run specific test class
docker run --rm \
  -v $(pwd):/opt/viral-ngs/viral-phylo \
  -v $(pwd)/test:/opt/viral-ngs/source/test \
  quay.io/broadinstitute/viral-phylo \
  bash -c "cd /opt/viral-ngs/viral-phylo && pytest -v test/unit/test_ncbi.py::TestFeatureTableParser"

# Run single test method
docker run --rm \
  -v $(pwd):/opt/viral-ngs/viral-phylo \
  -v $(pwd)/test:/opt/viral-ngs/source/test \
  quay.io/broadinstitute/viral-phylo \
  bash -c "cd /opt/viral-ngs/viral-phylo && pytest -v test/unit/test_ncbi.py::TestFeatureTableParser::test_parse_feature_table"
```

**Note:** Two volume mounts are required:
- `-v $(pwd):/opt/viral-ngs/viral-phylo` - Mounts source code
- `-v $(pwd)/test:/opt/viral-ngs/source/test` - Mounts test inputs (shared with viral-core)

#### Option 2: Use viral-core base image (For development with dependency changes)

If you're modifying conda dependencies, start from viral-core and install dependencies:

```bash
# Interactive shell for development
docker run -it --rm \
  -v $(pwd):/opt/viral-ngs/viral-phylo \
  -v $(pwd)/test:/opt/viral-ngs/source/test \
  quay.io/broadinstitute/viral-core

# Inside container, install dependencies:
/opt/viral-ngs/viral-phylo/docker/install-dev-layer.sh

# Then run tests:
cd /opt/viral-ngs/viral-phylo
pytest -rsxX -n auto test/unit
```

### Docker Development Workflow

The development paradigm is intentionally docker-centric.

**For quick testing without dependency changes:** Use the pre-built viral-phylo image (see "Running Tests in Docker" above).

**For development with dependency changes:**

1. Mount local checkout into viral-core container:
```bash
docker run -it --rm \
  -v $(pwd):/opt/viral-ngs/viral-phylo \
  -v $(pwd)/test:/opt/viral-ngs/source/test \
  quay.io/broadinstitute/viral-core
```

2. Inside container, install this module's dependencies:
```bash
/opt/viral-ngs/viral-phylo/docker/install-dev-layer.sh
```

3. Test interactively within container:
```bash
cd /opt/viral-ngs/viral-phylo
pytest -rsxX -n auto test/unit
```

4. Optionally snapshot your container with dependencies installed:
```bash
# From host machine, in another terminal
docker commit <container_id> local/viral-phylo-dev
```

**Important note about requirements-conda.txt changes:**
- If your branch has **no changes** to `requirements-conda.txt`, you can use the `:latest` viral-phylo Docker image for testing
- If your branch **modifies** `requirements-conda.txt`, you must wait for GitHub CI to build a branch-specific Docker image before testing, or use Option 2 above to install dependencies manually

### Common Docker Testing Issues

**Tests fail with "can't open file" or "file not found" errors:**
- Ensure you're using BOTH volume mounts: `-v $(pwd):/opt/viral-ngs/viral-phylo` AND `-v $(pwd)/test:/opt/viral-ngs/source/test`
- Test input files live in a shared location between viral-core and viral-phylo

**Tests fail with "command not found" for tools like mafft, mummer, etc.:**
- Use the `quay.io/broadinstitute/viral-phylo` image, not `viral-core`
- Or run `install-dev-layer.sh` inside the viral-core container before testing

**Platform warnings (linux/amd64 vs linux/arm64):**
- These warnings are expected on ARM Macs and can be ignored
- Docker will use emulation automatically

### Docker Build

Build docker image:
```bash
docker build -t viral-phylo .
```

The Dockerfile layers viral-phylo on top of viral-core:2.5.21, installing conda dependencies first, then copying source code.

## Architecture

### Main Entry Points

- **`intrahost.py`** - Intrahost variant calling and annotation for viral genomes
- **`interhost.py`** - SNP calling, multi-alignment, and phylogenetics for inter-host analysis
- **`ncbi.py`** - NCBI GenBank/SRA submission utilities, feature table transfer, and data retrieval

All use argparse for CLI and util.cmd for command registration via `__commands__` list.

### Core Intrahost Commands (intrahost.py)

Key subcommands available via `intrahost.py <command>`:
- `vphaser_one_sample` - Call variants using V-Phaser 2 on a single sample
- `vphaser` - Wrapper for V-Phaser 2 variant caller
- `tabfile_rename` - Rename values in tab-separated files
- `merge_to_vcf` - Merge variant data from multiple sources into VCF format
- `Fws` - Compute F_ws (within-sample) diversity statistics
- `iSNV_table` - Generate intra-SNV summary table from VCF
- `iSNP_per_patient` - Aggregate SNP counts per patient

### Core Interhost Commands (interhost.py)

Key subcommands available via `interhost.py <command>`:
- `snpEff` - Annotate variant effects using SnpEff
- `align_mafft` - Align sequences using MAFFT multiple sequence aligner
- `multichr_mafft` - Multi-chromosome MAFFT alignment

### Core NCBI Commands (ncbi.py)

Key subcommands available via `ncbi.py <command>`:
- `tbl_transfer` - Transfer feature annotations between aligned sequences
- `tbl_transfer_multichr` - Multi-chromosome feature table transfer
- `tbl_transfer_prealigned` - Feature transfer for pre-aligned sequences
- `fetch_fastas` - Download FASTA sequences from NCBI
- `fetch_feature_tables` - Download feature tables from NCBI
- `fetch_genbank_records` - Download GenBank records
- `biosample_to_genbank` - Convert BioSample metadata to GenBank format
- `prep_genbank_files` - Prepare files for GenBank submission
- `prep_sra_table` - Prepare SRA submission table

### Module Structure

- **`phylo/`** - Core modules for phylogenetic analysis and annotation
  - `feature_table.py` - GenBank feature table parsing and manipulation
  - `feature_table_types.py` - ASN.1-like data structures for feature tables
  - `mummer.py` - MUMmer sequence alignment wrapper
  - `mafft.py` - MAFFT multiple alignment wrapper
  - `muscle.py` - MUSCLE alignment wrapper
  - `vcf.py` - VCF file utilities (intervals, genome positioning)
  - `snpeff.py` - SnpEff variant effect prediction wrapper
  - `genbank.py` - GenBank accession parsing and NCBI Entrez fetching
  - `vphaser2.py` - V-Phaser 2 variant caller wrapper
  - `tbl2asn.py` - tbl2asn format conversion wrapper

- **`test/`** - pytest-based test suite
  - `test/unit/` - Unit tests for all modules
  - `test/integration/` - Integration tests for full workflows
  - `conftest.py` - pytest fixtures and configuration
  - `test/input/` - Static test input files organized by test class name

### Dependencies from viral-core

viral-phylo imports core utilities from viral-core (not in this repository):
- `util.cmd` - Command-line parsing and command registration
- `util.file` - File handling utilities
- `util.misc` - Miscellaneous utilities
- `read_utils` - Read processing utilities
- `tools.*` - Tool wrapper base classes and common tools (picard, samtools, bwa, etc.)
  - All tool wrappers inherit from `tools.Tool` base class

### Conda Dependencies

Tool dependencies are specified in `requirements-conda.txt` and installed via conda:
- **Alignment:** mafft, muscle, mummer4 - Multiple sequence alignment tools
- **Variant Calling:** vphaser2, lofreq - Variant detection
- **Annotation:** snpeff, table2asn, tbl2asn-forever - Variant annotation and GenBank submission
- **Utilities:** bamtools - BAM file manipulation

## Testing Requirements

- pytest is used with parallelized execution (`-n auto`)
- Tests use fixtures from `conftest.py` providing scoped temp directories
- Test input files are in `test/input/<TestClassName>/`
- Access test inputs via `util.file.get_test_input_path(self)` in test classes
- **New tests should add no more than ~20-30 seconds to testing time**
- **Tests taking longer must be marked with `@pytest.mark.slow`**
- Run slow tests with `pytest --runslow`
- **New functionality must include unit tests covering basic use cases and confirming successful execution of underlying binaries**

### Test Fixtures and Utilities

From `conftest.py`:
- `tmpdir_session`, `tmpdir_module`, `tmpdir_class`, `tmpdir_function` - Scoped temp directories
- `monkeypatch_function_result` - Patch function results for specific args
- `--runslow` option to enable slow/integration tests
- `--fixture-durations` to profile fixture performance
- Set `VIRAL_NGS_TMP_DIRKEEP` environment variable to preserve temp dirs for debugging

## CI/CD

GitHub Actions workflow (`.github/workflows/build.yml`) runs on push/PR:
- Docker image build and push to quay.io/broadinstitute/viral-phylo
  - Master branch: tagged as `latest` and with version number
  - Non-master branches: tagged with branch name (ephemeral, expires after ~10 weeks)
- Unit and integration tests with pytest
- Coverage reporting to coveralls.io
- Documentation build validation (actual docs hosted on Read the Docs)

## Key Design Patterns

### Command Registration

Commands are registered by appending `(command_name, parser_function)` tuples to `__commands__`. Each command has:
- A parser function (`parser_<command_name>`) that creates argparse parser
- A main function (`main_<command_name>`) that implements the logic
- Connection via `util.cmd.attach_main(parser, main_function)`

Example:
```python
def parser_tbl_transfer(parser=argparse.ArgumentParser()):
    parser.add_argument('ref_fasta', help='Reference FASTA with annotations')
    parser.add_argument('alt_fasta', help='Target FASTA to receive annotations')
    parser.add_argument('out_tbl', help='Output feature table')
    util.cmd.attach_main(parser, main_tbl_transfer)
    return parser

def main_tbl_transfer(args):
    # Implementation
    pass

__commands__.append(('tbl_transfer', parser_tbl_transfer))
```

### Feature Table Processing

The feature table system handles GenBank annotation transfer:
1. Parse feature table from reference sequence (`feature_table.py`)
2. Align reference and target sequences (MUMmer via `mummer.py`)
3. Map coordinates using `CoordMapper` class (`interhost.py`)
4. Transfer features to new coordinates, handling:
   - Truncations at sequence boundaries
   - Multi-interval features (joins)
   - Fuzzy positions (<, >)
5. Output new feature table for GenBank submission

### Coordinate Mapping

The `CoordMapper` class in `interhost.py` provides bidirectional coordinate mapping between aligned sequences:
- Maps positions accounting for insertions/deletions
- Handles gaps by mapping to closest upstream base
- Returns intervals for ambiguous regions
- Used extensively for feature table transfer

### Tool Wrapper Pattern

All tools in `phylo/` inherit from `tools.Tool`:
- Define `subtool_name` or executable attributes
- Implement `version()` method
- Implement tool-specific methods
- Use `self.execute()` to run commands with proper option formatting
- Define install methods (usually `tools.PrexistingUnixCommand` for conda-installed tools)

## Code Style and Linting

Configuration files in repository root:
- `.flake8` - Flake8 linting configuration
- `.pylintrc` - Pylint configuration
- `.style.yapf` - YAPF code formatting style

## Documentation

Documentation is built with Sphinx and hosted on Read the Docs:
- Source files in `docs/` directory (reStructuredText format)
- Uses `sphinx-argparse` to auto-generate CLI documentation from argparse parsers
- GitHub Actions validates docs build, but deployment is handled separately by Read the Docs

## Common Development Tasks

### Adding a New Command

1. Create parser function (`parser_<command_name>`) in appropriate script (intrahost.py, interhost.py, or ncbi.py)
2. Create main function (`main_<command_name>`) implementing the logic
3. Connect parser to main via `util.cmd.attach_main(parser, main_function)`
4. Register command: `__commands__.append(('command_name', parser_command_name))`
5. Add unit tests to `test/unit/`
6. Add test input files to `test/input/<TestClassName>/`

### Adding a New Tool Wrapper

1. Create wrapper class in `phylo/<tool>.py` inheriting from `tools.Tool`
2. Define tool executables and version method
3. Add conda dependency to `requirements-conda.txt`
4. Add unit tests for tool functionality
5. Document in this file under Module Structure

### Debugging Test Failures

1. Set `VIRAL_NGS_TMP_DIRKEEP=1` to preserve temp directories
2. Run single test: `pytest -v test/unit/test_file.py::TestClass::test_method`
3. Use `pytest -s` to see stdout/stderr
4. Use `--fixture-durations` to identify slow fixtures
5. Check test input files in `test/input/<TestClassName>/`
