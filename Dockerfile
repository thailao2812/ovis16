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

FROM python:3.11-slim-bullseye

# Prevent Python from writing pyc files and from buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    nodejs \
    npm \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libldap2-dev \
    libsasl2-dev \
    libpq-dev \
    build-essential \
    wget \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-venv \
    fonts-liberation \
    libfreetype6 \
    libfontconfig1 \
    xfonts-75dpi \
    xfonts-base \
    zlib1g-dev \
    libpng-dev \
    libjpeg62-turbo-dev \
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.bullseye_amd64.deb && \
    dpkg -i wkhtmltox_0.12.6.1-2.bullseye_amd64.deb || true && \
    apt-get -f install -y && \
    rm wkhtmltox_0.12.6.1-2.bullseye_amd64.deb

# Create Odoo user
RUN useradd -m -d /opt/odoo -U -r -s /bin/bash odoo

# Clone Odoo 16.0
RUN git clone --depth=1 -b 16.0 https://github.com/odoo/odoo.git /opt/odoo/odoo

# Install Odoo Python dependencies
RUN pip3 install --no-cache-dir \
    Babel==2.9.1 \
    chardet==3.0.4 \
    decorator==4.4.2 \
    docutils==0.16 \
    ebaysdk==2.1.5 \
    freezegun==0.3.15 \
    gevent==22.10.2 \
    greenlet==2.0.2 \
    idna==2.8 \
    Jinja2==3.1.2 \
    libsass==0.22.0 \
    lxml==4.9.1 \
    MarkupSafe==2.1.1 \
    num2words==0.5.12 \
    ofxparse==0.19 \
    passlib==1.7.4 \
    Pillow==9.3.0 \
    polib==1.1.1 \
    psutil==5.9.4 \
    psycopg2==2.9.5 \
    pydot==1.4.2 \
    python-dateutil==2.8.2 \
    python-ldap==3.4.3 \
    python-stdnum==1.18 \
    pytz==2022.6 \
    pyusb==1.2.1 \
    qrcode==7.4.2 \
    reportlab==3.6.12 \
    requests==2.28.1 \
    urllib3==1.26.13 \
    vobject==0.9.6.1 \
    Werkzeug==2.2.3 \
    xlrd==1.2.0 \
    XlsxWriter==3.0.3 \
    xlwt==1.3.0 \
    zeep==4.2.1 \
    PyPDF2==2.12.1

# Set permissions
RUN chown -R odoo:odoo /opt/odoo

# Create Odoo data directory
RUN mkdir -p /var/lib/odoo /etc/odoo && \
    chown -R odoo:odoo /var/lib/odoo /etc/odoo

# Create default Odoo configuration
RUN echo '[options]' > /etc/odoo/odoo.conf && \
    echo 'addons_path = /opt/odoo/odoo/addons,/opt/odoo/odoo/odoo/addons' >> /etc/odoo/odoo.conf && \
    echo 'data_dir = /var/lib/odoo' >> /etc/odoo/odoo.conf && \
    chown odoo:odoo /etc/odoo/odoo.conf

# Set the default user
USER odoo

# Expose Odoo ports
EXPOSE 8069 8071 8072

# Set default command
CMD ["python3", "/opt/odoo/odoo/odoo-bin", "-c", "/etc/odoo/odoo.conf"]
