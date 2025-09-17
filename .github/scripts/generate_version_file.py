import sys

file_name = sys.argv[1]
version = file_name.split("_")[2].split(".")[0][1:]
xsi = "http://www.w3.org/2001/XMLSchema-instance"
xsd = "http://www.w3.org/2001/XMLSchema"
xml = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="{xsi}" xmlns:xsd="{xsd}">
  <soap:Body>
    <getSignatureFileVersionV1Response xmlns="http://pronom.nationalarchives.gov.uk">
      <Version>
        <Version>{version}</Version>
      </Version>
      <Deprecated>false</Deprecated>
    </getSignatureFileVersionV1Response>
  </soap:Body>
</soap:Envelope>
"""
with open("version", "w") as version_file:
    version_file.write(xml)
