FROM python:3.10

COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY ./demos /demos
COPY ./src  /src

ENTRYPOINT ["streamlit", "run", "demos/demo_v0/main_app.py", "--browser.gatherUsageStats", "false"]