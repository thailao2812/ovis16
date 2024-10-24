#FROM docker.reach.com.vn/reach-odoo:16c
#WORKDIR /opt/odoo
#
## chạy thử viện của dự án
#COPY requirements.txt /usr/local/
#RUN /opt/odoo/odoo-venv/bin/pip install -r /usr/local/requirements.txt
#
## tạo folder chứa source dự án
#RUN mkdir /opt/odoo/sud16c
#RUN chown -R odoo:odoo /opt/odoo/sud16c
#
#COPY . sud16c
#ADD config/odoo.conf /etc/odoo/odoo.conf
#RUN chown odoo /etc/odoo/odoo.conf
#
##Stream logs to stdout
#RUN ln -sf /proc/self/fd/1 /var/log/odoo/odoo-server.log
#
## Expose Odoo services
#EXPOSE 8069
#
## Set default user when running the container
##USER odoo
#
#ENTRYPOINT ["/opt/odoo/odoo-venv/bin/python3", "/opt/odoo/odoo-server/odoo-bin", "-c" , "/etc/odoo/odoo.conf"]

# Sử dụng hình ảnh chính thức của Odoo nhưng không cài sẵn Python 3.11
FROM odoo:16

# Cài đặt các dependencies cần thiết và Python 3.11
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-venv python3.11-dev && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    apt-get clean

# Đảm bảo các thư viện và dependencies của Odoo được cài đặt cho Python 3.11
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r /requirements.txt