FROM python:3
RUN mkdir -p /opt/vmi_upload/resources
RUN mkdir -p /opt/vmi_upload/logs/prod
RUN mkdir /opt/vmi_upload/logs/stg
RUN mkdir /opt/vmi_upload/logs/qa
COPY *.py /opt/vmi_upload/
COPY requirements.txt /
COPY resources/* /opt/vmi_upload/resources/
RUN pip install -r requirements.txt
CMD python -u /opt/vmi_upload/vmi_main.py $TP_ID $CONFIG_PATH
