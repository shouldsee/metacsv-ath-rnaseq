export GH_TOKEN=${1:-$GH_TOKEN}
false && {
docker build -t metacsv-ath-rnaseq . &&\
docker run -e APP_MODULE="api:app" -p 9001:80 -e GH_TOKEN="$GH_TOKEN" --attach STDERR \
metacsv-ath-rnaseq
}
uvicorn --port 9001 api:app --reload
