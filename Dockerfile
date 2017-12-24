from python:3.6
RUN bash -c "apt-get update && apt-get install -y redis-server"
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt
COPY ./main.py ./main.py
CMD bash -c "service redis-server start && python ./main.py"
