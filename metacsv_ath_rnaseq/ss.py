s = "[sample_name:DRS014222] [sample comment:Arabidopsis thaliana ros1-3 mutant plant [Penterman et al. 2007 [PMID 17409185]) was used in this experiment. Seedlings grown on Murashige-Skoog media for 12 days were collected and incubated at various stress conditions. The total RNA was extracted by TRIzol(R) with helps of manufacture''s manual. Following DNase treatment was adapted to purify the RNA.]"
import re
lst = re.split('\[([a-zA-Z\-_ ]*):',s)
