export GH_TOKEN=${1:-$GH_TOKEN}
false && {
docker build -t metacsv-ath-rnaseq . &&\
docker run -e APP_MODULE="api:app" -p 9000:80 -e GH_TOKEN="$GH_TOKEN" --attach STDERR \
metacsv-ath-rnaseq
}
uvicorn --port 9000 api:app --reload
