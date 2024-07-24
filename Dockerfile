FROM docker.reach.com.vn/reach-odoo:16c
WORKDIR /opt/odoo

# chạy thử viện của dự án
COPY requirements.txt /usr/local/
RUN /opt/odoo/odoo-venv/bin/pip install -r /usr/local/requirements.txt

# tạo folder chứa source dự án
RUN mkdir /opt/odoo/sud16c
RUN chown -R odoo:odoo /opt/odoo/sud16c

COPY . sud16c
ADD config/odoo.conf /etc/odoo/odoo.conf
RUN chown odoo /etc/odoo/odoo.conf

#Stream logs to stdout
RUN ln -sf /proc/self/fd/1 /var/log/odoo/odoo-server.log

# Expose Odoo services
EXPOSE 8069

# Set default user when running the container
#USER odoo

ENTRYPOINT ["/opt/odoo/odoo-venv/bin/python3", "/opt/odoo/odoo-server/odoo-bin", "-c" , "/etc/odoo/odoo.conf"]