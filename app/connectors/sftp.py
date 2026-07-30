import io
from pathlib import Path

import paramiko


def upload_file(
    source_path: str,
    remote_path: str,
    host: str,
    port: int,
    username: str,
    password: str | None = None,
    private_key: str | None = None,
) -> None:
    local_path = Path(source_path)
    if not local_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    transport = paramiko.Transport((host, port))
    try:
        if private_key:
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(private_key))
            transport.connect(username=username, pkey=pkey)
        elif password:
            transport.connect(username=username, password=password)
        else:
            raise ValueError("Either 'password' or 'private_key' must be provided")

        sftp = paramiko.SFTPClient.from_transport(transport)
        try:
            sftp.put(str(local_path), remote_path)
        finally:
            sftp.close()
    finally:
        transport.close()