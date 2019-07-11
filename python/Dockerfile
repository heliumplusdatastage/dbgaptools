FROM amancevice/pandas:0.24.2-slim

# =====================================================================
# Add scripts included in directory
# =====================================================================

# Add to /opt folder
RUN mkdir /opt/dbgap_dd_to_json

# Add R helper script
ADD constants.py /
ADD read_functions.py /
ADD write_functions.py /
ADD dbgap_dd_to_json.py /

# Move scripts to dbgap_dd_to_json folder
RUN mv constants.py /opt/dbgap_dd_to_json
RUN mv read_functions.py /opt/dbgap_dd_to_json
RUN mv write_functions.py /opt/dbgap_dd_to_json
RUN mv dbgap_dd_to_json.py /opt/dbgap_dd_to_json

# Change permissions to make things exectuable
RUN chmod -R u+x /opt/dbgap_dd_to_json

# Set wrkdir
RUN mkdir /data
WORKDIR /data

# Create entrypoint that runs dbgap_dd_to_json utility
ENTRYPOINT ["python", "/opt/dbgap_dd_to_json/dbgap_dd_to_json.py"]
