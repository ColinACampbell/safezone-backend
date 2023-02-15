# 
FROM python:3.9

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./app /code/app
COPY ./docker-run.sh /code
COPY . /code
#Enable permission
RUN chmod +x docker-run.sh 
RUN chmod -R 0777 .
RUN sed -i -e 's/\r$//' docker-run.sh

CMD ["./docker-run.sh"]