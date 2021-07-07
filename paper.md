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

Written knowledge about automatic control theory is hard to access for practitioners as it requires knowledge of a lot of specialized terminology. The interactive application *method net* aims to supplement classical knowledge representation and thereby lower that barrier of access. More precisely, knowledge is represented as a collection of *types* and *methods* which typically occurr during problem solving in automatic control, stored in a graph structure. Using the *method net* web interface, users can explore the stored data, as well as generate a schematic solution procedure by formulating a query for a specific problem.

# Statement of need

The field of automatic control theory consists of a wealth of analysis and design methods which are often derived and presented with strong emphasis on mathematics. However, despite their potential to solve practical problems, they are often neglected in favor of simpler but less effective methods. A plausible reason for this is the suboptimal accessibility of associated literature for working engineers. The application *method net* aims to improve accessibility: By usage of semantic methods it helps the user to navigate a stored knowledge base on how to solve control problems. This goes beyond just searching for semantically tagged data. Instead, the program provides a web interface where users can explore the stored data by entering a query pertaining to their problem of interest. After specifying the available input data (e. g. a nonlinear differential equation) and the desired output result (e. g. a stabilizing controller), a search algorithm builds a path using the *methods* and *types* available in the knowledge base. This path, called *solution procedure*, transforms the available input into the desired output. Each step of this procedure applies one well defined method (e. g. linearizing a nonlinear differential equation), where each method has formally defined input and output data (types).

![Screenshot of the web interface. Left: overview of available methods and types, right: generated solution procedure for triple pendulum swingup.\label{fig:screenshot}](screenshot.png)

In @HeedtKnoll2021Methodnet we used the *method net* to find a suitable combination of methods to design a tracking controller for a cart-mounted triple pendulum to perform a swing up maneuver. This complements our earlier approach for control-related knowledge representation, see @KnollHeedt2020ACKREP and @KnollHeedt2021ACKREP. By openly publishing the code and the knowledge base, we encourage other researchers and students to model their domain knowledge using the provided structure. That way, we aim to explore potential uses and limitations, while also gathering insights for future improvements.

# References
