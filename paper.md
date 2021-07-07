---
title: 'Methodnet: Formal Semantic Representations of Methods in Automatic Control'
tags:
  - Python
  - automatic control
  - knowledge representation
  - method net
  - semantic data
authors:
  - name: Robert Heedt
    affiliation: 1 
  - name: Carsten Knoll
    affiliation: 1
affiliations:
 - name: Institut of Control Theory, TU Dresden
   index: 1
date: 07 July 2021
bibliography: paper.bib
---

# Summary

Written knowledge about automatic control theory is hard to access as it requires knowledge of the exact terminology. The *method net* acts as a supplement to classical knowledge representation, consisting of types and methods typically occurring in automatic control, stored in a graph structure. Using the *method net* web interface, users can explore the stored data, as well as generate a schematic solution procedure by formulating a query for a specific problem.

# Statement of need

The field of automatic control theory consist of a wealth of mathematical methods, of which only a small fraction are actually used in practice however. One major reason might be accessibility of suitable literature for working engineers. The *method net* should demonstrate how semantic methods can help the user to navigate a stored knowledge base. This goes beyond just searching for semantically tagged data. Instead, the program provides a web interface where users can explore the stored data by entering a query pertaining to their current practical problem. After specifying the available data and a desired result, a search algorithm tries to build a path using the methods available in the knowledge base, that transforms one into the other.

![Screenshot of the web interface. Left: overview of available methods and types, right: generated solution procedure for triple pendulum swingup.\label{fig:screenshot}](screenshot.png)

In @HeedtKnoll2021Methodnet we used the *method net* to find a suitable combination of methods to ==make a triple pendulum perform a swing up trajectory==. By openly publishing the software and code, we encourage other students and researchers to try modeling their domain knowledge using the provided structure, in order to explore potential uses and limits, while improving it for future applications.

# References