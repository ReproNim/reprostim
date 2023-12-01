# ReproFlow: a scalable environment for automated MRI and behavioral data integration

## Authors
Horea-Ioan Ioanas
Vadim Melnik
Yaroslav O. Halchenko


!!! should we make it fMRI? Would make it clearer. Sure you can potentially use behaviour as a session condition for structural/DTI measurements, but we don't want people asking themselves about that in the middle of reading the abstract... Also, has anybody actually done this?

## Introduction

Reproducibility is a critical consideration for modern neuroscience and is greatly aided by automation of data acquisition and standardization of data records.
MRI and behavioural data are two of the foremost modalities in human neuroscience, making the seamless integration of these modalities a significant concern for numerous research centers.
The Brain Imaging Data Structure (BIDS) is a preeminent data standard, well-suited for both modalities, and which ensures interoperability of data analysis tools as well as transparency of data records.
The ReproNim project has made significant contributions in improving access to BIDS conversion, data sharing, and integration with quality assurance (QA) processes.
ReproFlow is an environment which integrates numerous ReproNim tools — such as heuDiConv, ReproStim, ReproEvents, and datalad — in order to provide a scalable and automated solution for MRI and behavioural data integration.
Here we present a pilot implementation of this environment, set up at the Dartmouth Brain Imaging Center, covering both software and open hardware solutions.
The adaptation of this environment can help other centers establish a robust, multi-modal, and BIDS-compliant data acquisition pipeline, and thus significantly advance the reliability of modern neuroscience.

## Methods

We have developed a number of Free and Open Source Software (FOSS) solutions, and made extensive contributions to the BIDS standard, in order to ensure both standard support for multimodal metadata, and adequate tools to automatically populate the metadata space.
The ReproFlow environment consists of 6 core tools developed my the ReproNim project.
HeuDiConv provides automatic MRI conversion from DICOM to BIDS.
ReproIn provides user customization capabilities for HeuDiConv via an extensive heuristic syntax.
ReproEvents provides audio and video capture capabilites to integrate complex stimuli with MRI data.
ReproStim provides support for capturing behavioural events from participants.
!!! Do we have anything for non-keypress behaviour? Eye tracking maybe? if not perhaps we should be more precise and not use the word “behaviour” when we go into the details.
Con/noisseur captures and performs QA on operator input from the scanner.
ReproNim Containers provide reusable software environments to ensure reliable deployment of the above tools.


## Results

!!! Figure here, not in methods, since the environment is the result of our work, the methods are the tools we use for it.

Over the course of its development, our HeuDiConv/ReproIn implementation at the Dartmouth Brain Imaging Center has been used to collect and standardize over 40 MRI datasets, which are now openly shareable in an understandable fashion for inspection and reuse by the broader research community.
We have additionally collected corresponding audio/video stimuli using ReproStim, which were successfully used to recover previously undocumented experimental aspects (such as randomization order) and to improve data quality by identifying the presence of lag between modalities.
ReproEvents and Con/noisseur are currently in early deployment and provide incipient event time stamp synchronization between the various modalities.

## Conclusions

We argue based on our results that data integration remains a non-trivial matter for multi-modal set-ups and that significant improvements in automation and transparency are necessary to ensure data reliability.
In particular, general-purpose open-source tools are needed in order to ensure sustainability of acquisition frameworks over time, and to ensure relevant know-how is shared across centers.
We propose ReproFlow as a solution for these requirements and encourage re-use of this environment.
