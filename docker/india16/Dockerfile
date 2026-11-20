# Odoo 16 image for India, used by docker-compose-india-uat.yml (build context: this folder only).
# Adds the Python libraries that India modules import when they load. Without them these modules fail
# to load and the database does not open:
#   report_aeroo                 aeroolib, Genshi, html2text
#   sd_india_inventory,
#   sd_india_security_gate       currency2text
#   restful_api                  odoorpc, PyJWT
# PyJWT stays below 2.10: from 2.10 on, decode() rejects tokens whose "sub" claim is not a string, and
# restful_api puts the numeric user id there.
# aeroolib and currency2text are pinned to the current master commits on GitHub and downloaded as
# tarballs, so no git and no apt-get are needed (odoo:16 is Debian bullseye, whose apt mirrors are
# no longer reliable after end of support).
FROM odoo:16

USER root
RUN pip3 install --no-cache-dir \
        Genshi \
        html2text \
        odoorpc \
        "PyJWT==2.9.0" \
        "aeroolib @ https://github.com/aeroo/aeroolib/archive/1c3af00570f772cd77ce81690c4646c88663e798.tar.gz" \
        "currency2text @ https://github.com/aeroo/currency2text/archive/e666e17eb54f5a49f5cfb3825d8513a4d1510249.tar.gz"
USER odoo
