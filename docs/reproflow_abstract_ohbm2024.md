# ReproFlow: ReproNim tools to establish scalable and automated MRI and behavioral data acquisition and QC

## Authors
Horea-Ioan Ioanas
Vadim Melnik
Yaroslav O. Halchenko

## Introduction

In neuroimaging and behavioral research, reproducibility is a critical goal, achievable through the standardization and automation of data acquisition and quality assurance (QA) processes.
Standardization, especially in aligning data with the Brain Imaging Data Structure (BIDS) standard, is crucial as it not only facilitates efficient and thorough QA but also ensures consistency and interoperability across studies.
The ReproNim project has made significant strides in this regard, offering a suite of tools - heudiconv with reproin heuristic, ReproStim, ReproEvents, and datalad/containers - which if combined in a workflow would collectively be termed 'ReproFlow'.
ReproFlow is an approach to provide a scalable, automated approach for MRI and behavioral data acquisition, ensuring adherence to BIDS and enhancing the overall efficiency, quality and reproducibility of neuroimaging research.
Here we will present a prototypical setup at Dartmouth Brain Imaging Center, incorporating of which at other centers can establish a robust, BIDS-compliant foundation, critical for advancing the field through reproducible, high-quality studies.

## Methods

We have been developing a number of Free and Open Source software solutions and participated in BIDS standard development to ensure that not only that we have tools but have a standard to accommodate the (meta)data.
The main components of the ReproFlow are:
Heudiconv : https://github.com/nipy/heudiconv –…
ReproIn: https://github.com/repronim/reproin – heuristic for HeuDiConv and specification for organizing and naming sequences in the scanner to automate conversion of neuroimaging data from DICOMs into BIDS
ReproEvents: https://github.com/ReproNim/reprostim – audio/video capture
ReproStim: (if not to be moved) https://github.com/ReproNim/reprostim/tree/master/Events – capturing of events from Curdes
con/noisseur: https://github.com/con/noisseur  - capturing and OCRing for QC metadata entered at the scanner (e.g. sequence names, etc)
https://github.com/ReproNim/containers – to provide reusable archive of containers…

We actively participate in BIDS standard development to ensure that it provides adequate support for needed modalities, e.g. for ReproStim recorded stimuli (reference: https://github.com/bids-standard/bids-specification/issues/751 “RFC: stimuli BEP”), clarification of inheritance principle, etc.

Here Figure which has   
Stimuli laptop (of researcher) connected to projector via VGA splitter, and audio headphones via splitter
Projector connected to VGA splitter
MRI magnet + MRI console computer/display (through DVI splitter) - connected to the network
Optical trigger pulse sent to curdes
Curdes 
connected to data beast via network
Connected via USB to experimenter laptop
Data beast on the network (wifi), connected to NTP server
2 magewell devices connected to USB:
One connected to VGA splitter + audio splitter
Another to MRI console display DVI splitter
Micropython thingie connected to curdes DB-35 (or whatever it is) and to databeast via usb
Mri-inbox - server with PACS to receive DICOMs
Rolando - server having DICOMs mounted via NFS, running 
Heudiconv etc to place into BIDS datasets
Whatever we come up with to slice videos into BIDS
Whatever we come up with to slice events into BIDS _events.tsv
(not yet sure if to be there) Falkor - web server providing ///ReproNim/containers 

So pretty much more elaborate version of https://github.com/repronim/reproin#overall-workflow 

## Results

At Dartmouth Brain Imaging Center (DBIC) we had collected and converted to BIDS over 40 DICOM datasets of various sizes using HeuDiConv/ReproIn.
We have collected hours of audio/video stimuli using ReproStim, and those were already successfully used for recovery of randomization order and to check for presence of the suspected lag between audio and video in a few cases.
ReproEvents and con/noissuer is yet to be deployed on permanent basis, but we expect to have all tooling and sample datasets to present by the time of the OHBM 2024 meeting.

## Conclusions
