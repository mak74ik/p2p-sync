# Project: p2p-sync

## Концепт
"Синхронайзер". 

Утилита для P2P шифрованной синхронизации файлов между ПК без сторонних серверов. 

Стек: Python + libp2p + cryptography. 

Выкатим консольную утилиту с поддержкой TUI для простого использования. 

Будем использовать libp2p для P2P соединений и cryptography для шифрования данных.

## Правки
Макс, хорош фантазировать. Звучит бодро, но... 

- Используя libp2p и cryptography, мы точно можем создать P2P шифрованную синхронизацию файлов, но не забывай, что libp2p еще не опубликовал последние версии для Python. Звезды на нашем боку не должны сверкать. Используем версию 0.2.x и готовимся к обновлению.
- ТИПИЧЕСКИЙ костыль - libp2p требует много конфигурации и настройки для работы в простом режиме. Мы оставляем только минимум необходимой настройки для

## Исходники
SLUG: p2p-sync
РЕЗЮМЕ_ДЛЯ_ЧАТА: Утилита для P2P шифрованной синхронизации файлов между ПК без сторонних серверов, используя libp2p и cryptography. Используем версию 0.2.x libp2p и минимизируем конфигурацию.
КОД:
```
# p2p-sync/libp2p_config.py
from libp2p import connectivity

class P2PSyncConfig:
    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 8080
        self.listen_addresses = [(self.host, self.port)]
        self.protocol = 'p2p-sync'
        self.max_connections = 10

    def get_config(self):
        return {
            'listen_addresses': self.listen_addresses,
            'protocol': self.protocol,
            'max_connections': self.max_connections
        }

# p2p-sync/main.py
import logging
from cryptography.fernet import Fernet
from libp2p import connectivity
from p2p-sync.libp2p_config import P2PSyncConfig

class P2PSync:
    def __init__(self):
        self.config = P2PSyncConfig()
        self.logger = logging.getLogger('p2p-sync')
        self.crypto_key = Fernet.generate_key()
        self.crypto = Fernet(self.crypto_key)

    def start(self):
        self.logger.info('Starting P2P Sync...')
        self.connectivity = connectivity.connect(self.config.get_config())
        self.logger.info('P2P Sync started.')

# p2p-sync/cli.py
import argparse
from p2p-sync.main import P2PSync

def main():
    parser = argparse.ArgumentParser(description='P2P Sync CLI')
    parser.add_argument('--start', action='store_true', help='Start P2P Sync')
    args = parser.parse_args()
    if args.start:
        p2p_sync = P2PSync()
        p2p_sync.start()

if __name__ == '__main__':
    main()
```
