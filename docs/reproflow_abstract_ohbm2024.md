# ReproFlow: a scalable environment for automated MRI and behavioral data integration

## Authors
Horea-Ioan Ioanas
Vadim Melnik
Yaroslav O. Halchenko


## Introduction

Reproducibility is a critical consideration for modern neuroscience and is greatly aided by automation of data acquisition and standardization of data records.
MRI and behavioral data are two of the foremost modalities in human neuroscience, making the seamless integration of these modalities a significant concern for numerous research centers.
The Brain Imaging Data Structure (BIDS) is a preeminent data standard, well-suited for both modalities, and which ensures interoperability of data analysis tools as well as transparency of data records.
The ReproNim project has made significant contributions in improving BIDS standard itself, access to BIDS conversion, data sharing, and integration with quality assurance (QA) processes.
ReproFlow is an environment which integrates numerous ReproNim tools — such as HeuDiConv, ReproIn, ReproStim, ReproEvents, ReproMon, con/noisseur, ///repronim/containers, DataLad, and datalad-containers extension — in order to provide a scalable and automated solution for MRI and behavioral data acquisition and integration in a standardized form.
Here we present a pilot implementation of this environment, set up at the Dartmouth Brain Imaging Center, covering both software and open hardware solutions.
The adaptation of this environment can help other centers establish a robust, multi-modal, and BIDS-compliant data acquisition pipeline, and thus significantly advance the reliability of modern neuroscience.

## Methods

We have developed a number of Free and Open Source Software (FOSS) solutions, and made extensive contributions to the BIDS standard, in order to ensure both standard support for multimodal metadata, and adequate tools to automatically populate the metadata space.
The ReproFlow environment consists of 7 core tools developed my the ReproNim project.
HeuDiConv provides configurable MRI conversion from DICOM to a desired layout.
ReproIn provides configuration for HeuDiConv for HeuDiConv via an extensive heuristic syntax, and an assistance utility.
ReproEvents provides audio and video capture capabilites to integrate complex stimuli with MRI data.
ReproStim provides support for capturing behavioral events from participants.
Con/noisseur captures and performs QA on operator input at the scanner console.
ReproMon complements the QA capabilities by providing support for online operator feedback and alerts in case of incidents or anomalous metadata input.
///ReproNim//containers provides DataLad dataset with popular containers and assistance scripts to ensure reproducible execution.
DataLad and datalad-containers provide logistics for data and containers manipulations and provenance tracking.


## Results

Over the course of its development, our HeuDiConv/ReproIn implementation at the Dartmouth Brain Imaging Center has been used to collect and standardize over 40 MRI datasets, which are now openly shareable in an understandable fashion for inspection and reuse by the broader research community.
We have additionally collected corresponding audio/video stimuli using ReproStim, which were successfully used to recover previously undocumented experimental aspects (such as randomization order) and to improve data quality by identifying the presence of lag between modalities.
ReproEvents, ReproMon, and Con/noisseur are currently in early deployment and provide incipient event time stamp synchronization between the various modalities.
///ReproNim/containers contains all BIDS-Apps, NeuroDesk application, and other containers.


## Conclusions

We argue based on our results that data integration remains a non-trivial matter for multi-modal set-ups and that significant improvements in automation and transparency are necessary to ensure data reliability.
In particular, general-purpose open-source tools are needed in order to ensure sustainability of acquisition frameworks over time, and to ensure relevant know-how is shared across centers.
We propose ReproFlow as a solution for these requirements and encourage re-use of this environment.
