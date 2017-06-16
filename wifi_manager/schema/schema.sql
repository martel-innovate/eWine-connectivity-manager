CREATE TABLE IF NOT EXISTS networks (
  nic text,
  ssid text,
  passkey text,
  lat real,
  lng real,
  PRIMARY KEY (nic, ssid)
);