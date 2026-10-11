import pathlib
p = pathlib.Path("presentation/components/widgets.py")
p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n"))
print("widgets.py normalized to LF")
