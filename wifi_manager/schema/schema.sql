CREATE TABLE IF NOT EXISTS networks (
  iface text,
  ssid text,
  passkey text,
  lat real,
  lng real,
  PRIMARY KEY (iface, ssid)
);