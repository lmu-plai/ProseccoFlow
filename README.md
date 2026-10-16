# ProseccoFlow
Source code and data for the ARES'26 paper "Content for Everyone: Detecting Misconfigurations of Android Content Providers"

## Paper link
The paper is available [here](https://www.plai.ifi.lmu.de/publications/ares26-content.pdf).

## BibTeX citation
```
@inproceedings{ares26-content,
  author    = {Christopher Lenk and Tim Lange and Johannes Kinder},
  title     = {Content for Everyone: Detecting Misconfigurations of Android Content Providers},
  booktitle = {Int. Conf. Availability, Reliability and Security (ARES)},
  doi       = {https://doi.org/10.1007/978-3-032-36885-0_13},
  series    = {LNCS},
  volume    = {16899},
  year      = {2026},
}
```

## Directories
- DynamicValidator: Scripts for collecting, analyzing and dynamically validating the Android packages
- ProseccoApp: Custom Android application for testing apps with misconfigured content providers
- StaticValidator: Static data flow analysis tool FlowDroid with extensions for content providers
