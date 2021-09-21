# docker image used in kubernetes agent's deployment
FROM prefecthq/prefect:0.15.5-python3.8

# copy custom job template
COPY job_template.yaml /etc/prefect/job_template.yaml