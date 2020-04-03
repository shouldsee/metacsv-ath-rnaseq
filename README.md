metacsv-ath-rnaseq
--------------------------

An open-source community-managed meta-data sheet for Arabidopsis thaliana.

See http://shouldsee.github.io/metacsv-ath-rnaseq

### Overview

This project aims to provide a better API for retriving meta-data for a public Ath-RNASEQ dataset. 
Notably this API can be improved by creating Github PR.

### API endpoints

1. GET http://shouldsee.github.io/metacsv-ath-rnaseq/current.csv

A csv sheet with fields

| Name      | Type   | Comment | Example |
| ---       | ---    | ------- | ------  | 
| SAMPLE_ID | str    | main index of the object | SRS942274 |
| RUN_ID_LIST_CONCAT | str | whitespace-separated values of run id | SRR2073144 SRR2073145 | 
| tag_source_name | str  | describe sample source name. Overrides tags| shoot apical meristem
| tag_tissue    |  str   |  describe sample tissue. Overrides tags|  NA |
| tags      |  str   | whitespace-separated brackted values.  | [age:11 day after germination] [ecotype:Col-0 (CS70000)] [geo_loc_name:Russia: Moscow] [tissue:shoot apical meristem] [BioSampleModel:Plant] |

