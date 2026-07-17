# ProseccoFlow
Source code and data for the ARES'26 paper "Content for Everyone: Detecting Misconfigurations of Android Content Providers"

## Paper link
The paper is available [here](https://www.plai.ifi.lmu.de/publications/ares26-content.pdf).

## BibTex citation
```
@inproceedings{ares26-content,
  author    = {Christopher Lenk and Tim Lange and Johannes Kinder},
  title     = {Content for Everyone: Detecting Misconfigurations of Android Content Providers},
  booktitle = {Int. Conf. Availability, Reliability and Security (ARES)},
  year      = {2026},
  note      = {To appear},
}
```

## Directories
- DynamicValidator: Scripts for collecting, analyzing and dynamically validating the Android packages
- ProseccoApp: Custom Android application for testing apps with misconfigured content providers
- StaticValidator: Static data flow analysis tool FlowDroid with extensions for content providers
