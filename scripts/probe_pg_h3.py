from h3lib import create_store

s = create_store(
    "postgres",
    dsn="postgresql://h3lib:h3lib@127.0.0.1:5432/h3lib",
    table="h3_probe",
    enable_postgis=True,
    enable_h3=True,
    enable_h3_postgis=True,
    require_postgis=True,
    require_h3=True,
)
print("enabled:", s.extension_status.enabled)
print("messages:", s.extension_status.messages)
print("native:", s.supports_native_h3)
print(s.query_sql("SELECT h3_latlng_to_cell(POINT(37.7749, -122.4194), 9)::text"))
print(s.query_sql("SELECT h3_grid_disk('89283082803ffff'::h3index, 1)"))
s.close()
