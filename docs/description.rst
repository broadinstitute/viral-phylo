Description of the methods
==========================


Viral genome analysis
---------------------


Intrahost variant identification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Intrahost variants (iSNVs) were called from each sample's read alignments using
`V-Phaser2 <https://doi.org/10.1186/1471-2164-14-674>`_
and subjected to an initial set of filters:
variant calls with fewer than five forward or reverse reads
or more than a 10-fold strand bias were eliminated.
iSNVs were also removed if there was more than a five-fold difference
between the strand bias of the variant call and the strand bias of the reference call.
Variant calls that passed these filters were additionally subjected
to a 0.5% frequency filter.
The final list of iSNVs contains only variant calls that passed all filters in two
separate library preparations.
These files infer 100% allele frequencies for all samples at an iSNV position where
there was no intra-host variation within the sample, but a clear consensus call during
assembly. Annotations are computed with snpEff_.

.. _snpEff: http://snpeff.sourceforge.net/


