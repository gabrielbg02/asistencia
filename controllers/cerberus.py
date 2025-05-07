from fastapi import HTTPException
from ldap3 import Server, Connection, SAFE_SYNC, ALL,AUTO_BIND_NO_TLS
from ldap3.utils.dn import parse_dn
from ldap3.core.exceptions import LDAPBindError

server = Server('172.16.10.159', get_info=ALL)

def validate_ad_credentials(user_name, password):
    return  Connection(
        server,
        user=user_name,
        password=password,
        client_strategy=SAFE_SYNC,
        auto_bind=AUTO_BIND_NO_TLS
    )

class User:
    username: str
    password: str
    full_name: str
    unit: str

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def authenticate_user(self):
        try:
            conn = validate_ad_credentials(f"{self.username}@cmch.local", self.password)
            status, result, response, _ = conn.search('dc=cmch,dc=local',
                                                      f'(&(objectclass=user)(sAMAccountName={self.username}))')
            self.full_name, _, self.unit = [_[1] for _ in parse_dn(response[0]['dn'])[:3]]
        except LDAPBindError as e:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid credentials")