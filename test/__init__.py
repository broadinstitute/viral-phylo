'''utilities for tests'''

__author__ = "irwin@broadinstitute.org"

# built-ins
import filecmp
import os
import re
import shutil
import subprocess
import tempfile
import unittest
import hashlib
import logging

# third-party
import Bio.SeqIO
import pytest

# intra-project
import util.file
from util.misc import available_cpu_count
from tools.samtools import SamtoolsTool

logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)


if 'PYTEST_XDIST_WORKER_COUNT' in os.environ:
    _CPUS = 1
else:
    _CPUS = available_cpu_count()


def assert_equal_contents(testCase, filename1, filename2):
    'Assert contents of two files are equal for a unittest.TestCase'
    testCase.assertTrue(filecmp.cmp(filename1, filename2, shallow=False))


def validate_feature_table_with_table2asn(tbl_path, fasta_path, work_dir=None):
    """
    Validate a feature table using NCBI's table2asn tool.

    This function creates a temporary directory with matching .fsa and .tbl files,
    runs table2asn validation, and checks for syntax errors in the feature table.

    Args:
        tbl_path: Path to the .tbl feature table file to validate
        fasta_path: Path to the FASTA file (will be converted to .fsa format)
        work_dir: Optional working directory to use (defaults to a new temp dir)

    Returns:
        dict with keys:
            - 'valid': bool - True if no feature table syntax errors
            - 'exit_code': int - table2asn exit code
            - 'errors': list - parsed error messages related to feature syntax
            - 'val_content': str - content of .val file if it exists
    """
    table2asn_path = shutil.which('table2asn')
    if not table2asn_path:
        raise FileNotFoundError("table2asn not found in PATH")

    work_dir = work_dir or tempfile.mkdtemp()
    base_name = os.path.splitext(os.path.basename(tbl_path))[0]

    # Create .fsa file (FASTA without gaps, matching base name)
    # table2asn requires matching prefixes for .fsa and .tbl files
    fsa_path = os.path.join(work_dir, base_name + '.fsa')
    with open(fasta_path, 'r') as inf:
        for rec in Bio.SeqIO.parse(inf, 'fasta'):
            # Write the sequence that matches the tbl file (typically the sample, not ref)
            seq_no_gaps = str(rec.seq).replace('-', '')
            # Use the base_name as the sequence ID to match the tbl header
            with open(fsa_path, 'w') as outf:
                outf.write('>{}\n{}\n'.format(base_name, seq_no_gaps))
            break  # Only need first non-ref sequence

    # Copy .tbl file with matching name (may already have correct name)
    work_tbl = os.path.join(work_dir, base_name + '.tbl')
    if os.path.abspath(tbl_path) != os.path.abspath(work_tbl):
        shutil.copy(tbl_path, work_tbl)

    # Run table2asn validation
    result = subprocess.run(
        [table2asn_path, '-i', fsa_path, '-V', 'vb'],
        capture_output=True,
        text=True,
        cwd=work_dir
    )

    # Parse validation file if it exists
    val_path = os.path.join(work_dir, base_name + '.val')
    val_content = ''
    if os.path.exists(val_path):
        with open(val_path, 'r') as f:
            val_content = f.read()

    # Check for feature table SYNTAX errors only, not biological validity errors.
    # We want to catch format issues like internal partials, bad intervals, etc.
    # but NOT biological errors like wrong start codons, missing stop codons, etc.
    # Issue #74 specifically produces "internal partials" and "Bad feature interval".
    error_patterns = [
        'Bad feature interval',             # Invalid coordinate format
        'Feature bad start and/or stop',    # Invalid start/stop coordinates
        'internal partials',                # Partial symbol on internal interval
        'SEQ_FEAT.Range',                   # Coordinate range errors
        'SEQ_FEAT.BadLocation',             # Bad location format
    ]

    all_output = result.stdout + '\n' + val_content
    errors = []
    for line in all_output.split('\n'):
        if any(pattern in line for pattern in error_patterns):
            stripped = line.strip()
            if stripped and stripped not in errors:
                errors.append(stripped)

    return {
        'valid': len(errors) == 0,
        'exit_code': result.returncode,
        'errors': errors,
        'val_content': val_content
    }


def assert_valid_feature_table(testCase, tbl_path, fasta_path, work_dir=None):
    """
    Assert that a feature table passes table2asn validation.

    Args:
        testCase: unittest.TestCase instance for assertions
        tbl_path: Path to the .tbl feature table file
        fasta_path: Path to the FASTA file (sequences, may contain gaps)
        work_dir: Optional working directory
    """
    result = validate_feature_table_with_table2asn(tbl_path, fasta_path, work_dir)
    if not result['valid']:
        error_msg = (
            "Feature table validation failed:\n"
            "  TBL: {}\n"
            "  Errors: {}".format(tbl_path, result['errors'])
        )
        testCase.fail(error_msg)


def assert_equal_bam_reads(testCase, bam_filename1, bam_filename2):
    ''' Assert that two bam files are equivalent

        This function converts each file to sam (plaintext) format,
        without header, since the header can be variable.

        Test data should be stored in bam format rather than sam
        to save space, and to ensure the bam->sam conversion
        is the same for both files.
    '''

    samtools = SamtoolsTool()

    sam_one = util.file.mkstempfname(".sam")
    sam_two = util.file.mkstempfname(".sam")

    # write the bam files to sam format, without header (no -h)
    samtools.view(args=[], inFile=bam_filename1, outFile=sam_one)
    samtools.view(args=[], inFile=bam_filename2, outFile=sam_two)

    try:
        testCase.assertTrue(filecmp.cmp(sam_one, sam_two, shallow=False))
    finally:
        for fname in [sam_one, sam_two]:
            if os.path.exists(fname):
                os.unlink(fname)

def assert_md5_equal_to_line_in_file(testCase, filename, checksum_file, msg=None):
    ''' Compare the checksum of a test file with the expected checksum
        stored in a second file
          compare md5(test_output.bam) with expected_output.bam.md5:1
    '''

    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    expected_checksum = ""
    with open(checksum_file, "rb") as f:
        expected_checksum = str(f.readline().decode("utf-8"))

    expected_checksum = expected_checksum.replace("\r","").replace("\n","")

    assert len(expected_checksum) > 0

    testCase.assertEqual(hash_md5.hexdigest(), expected_checksum, msg=msg)

@pytest.mark.usefixtures('tmpdir_class')
class TestCaseWithTmp(unittest.TestCase):
    'Base class for tests that use tempDir'

    def assertEqualContents(self, f1, f2):
        assert_equal_contents(self, f1, f2)

    def assertEqualFasta(self, f1, f2):
        '''Check that two fasta files have the same sequence ids and bases'''
        def seqIdPairs(f):
            return [(rec.id, rec.seq) for rec in Bio.SeqIO.parse(f, 'fasta')]
        self.assertEqual(seqIdPairs(f1), seqIdPairs(f2))

    def assertEqualFastaSeqs(self, f1, f2):
        '''Check that two fasta files have the same sequence bases (sequence ids may differ)'''
        def seqs(f):
            return [rec.seq for rec in Bio.SeqIO.parse(f, 'fasta')]
        self.assertEqual(seqs(f1), seqs(f2))

    def input(self, fname):
        '''Return the full filename for a file in the test input directory for this test class'''
        return os.path.join(util.file.get_test_input_path(self), fname)

    def inputs(self, *fnames):
        '''Return the full filenames for files in the test input directory for this test class'''
        return [self.input(fname) for fname in fnames]

"""
When "nose" executes python scripts for automated testing, it excludes ones with
the executable bit set (in case they aren't import safe). To prevent any of the
tests in this folder from being silently excluded, assure this bit is not set.
"""


def assert_none_executable():
    testDir = os.path.dirname(__file__)
    assert all(not os.access(os.path.join(testDir, filename), os.X_OK) for filename in os.listdir(testDir)
               if filename.endswith('.py'))
