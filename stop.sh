docker stop $(docker ps|grep metacsv-ath-rnaseq |cut -d' ' -f1)
