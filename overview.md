The RepoStim project provides a data solution for archiving and cataloging stimulus presentation records for fMRI experiments.
A “record” in this context refers to a digital media file that contains the audio and visual stimulation presented to a subject while undergoing fMRI scanning for a particular session.
The goal is to provide one record for every acquisition collected at an fMRI research center where audio/visual stimulation was presented.
The ultimate goal of the project is to incorporate ReproStim within the ReproIn/heudiconv data conversion pipeline and to have all stimulus records stored within respective BIDS datasets (see also: https://github.com/bids-standard/bids-specification/issues/751).  While the development of the ReproStim project targets data collection for fRMI research, such a system may also be employed for purely behavioral experiments, which are supported by BIDS as well.
Within its current scope, ReproStim is meant to serve as a center-wide resource for a brain imaging center.
Thus, the setup and maintenance of ReproStim is expected to fall under the purview of an authorized IT specialist charged with center operations and data archiving.
The goal of this project is to make establishing such a setup very easy and turnkey as much as possible.
End users, including researchers who collect and analyze data at the center, ideally need not interact with ReproStim in any way except to benefit from having access to stimulus records associated with their fMRI data as procured by the center.
Given this general overview of the scope and purpose of the ReproStim project, there are four major components to the project that must be considered.
These include hardware requirements and setup, server software configuration, tools for record procurement, and documentation.

Setting up ReproStim requires an initial investment in hardware, including a video capture device, a computer that runs the ReproStim capture server software,
a USB “sniffer” device to capture scanner trigger pulses for use by the capture service,
and necessary cables and connectors including audio and video splitter cables.
[These details will be filled in later, and there is a reasonable sketch of the hardware set up already in the README.md file.]

The server software runs continuously on a dedicated computer that is connected to audio/video capturing device interjected between the stimulus presentation system (SPS) at the fMRI scanner suite.
The software monitors the audio and video streams that are sent over the SPS so that whenever there is a video feed to the projector in the scanner,
all content is recorded and time-stamped.
Any change in the parameter of captured video (connect/disconnect, change of resolution) triggers creation of a new captured content file.
These recordings are not yet considered “records” in that they are not matched to specific fMRI scans.
The server simply monitors the SPS for content and records everything.
These raw recordings will often contain long periods of screen capture that show the content of the display on experimenter’s stimulus presentation computer (often a lab laptop).
**Warning: as a result, captured video could contain sensitive data if it was displayed.**
Therefore, it is necessary to take some precautions to store these files securely to protect experimenters information and privacy in case some personal information is exposed, such as an email inbox.
Consideration should be taken as to how long these raw recordings are kept, when they should be deleted, and where they will be stored.
For example, operators will need to provide sufficient hard drive space for this data and implement some policies about how long to keep the original raw data, after “records” parsed and procured to the fMRI archive.
