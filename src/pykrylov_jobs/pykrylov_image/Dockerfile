FROM hub.tess.io/coreai/genai-suit:latest

RUN apt-get update -y && apt-get upgrade -y

COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

ENV NO_PROXY=krylov,ams,ems,mms,localhost,127.0.0.1,.vip.ebay.com,github.ebay.com,.tess.io,.corp.ebay.com,.ebayc3.com,.krylov-prod.svc
ENV no_proxy=krylov,ams,ems,mms,localhost,127.0.0.1,.vip.ebay.com,github.ebay.com,.tess.io,.corp.ebay.com,.ebayc3.com,.krylov-prod.svc
ENV ENV_CHOMSKY_KRYLOV_WORKSPACE=1