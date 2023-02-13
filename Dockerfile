FROM apache/airflow:2.5.1rc2-python3.10
USER root
RUN sed 's/main/main non-free/' -i /etc/apt/sources.list
RUN apt update && apt install unrar curl -y
RUN curl -O https://dl.google.com/go/go1.20.linux-amd64.tar.gz
RUN rm -rf /usr/local/go && tar -C /usr/local -xzf go1.20.linux-amd64.tar.gz
USER airflow
ENV PATH=$PATH:/usr/local/go/bin
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt
