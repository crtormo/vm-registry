import re
import glob
import os
from typing import Dict, Optional, NamedTuple, List, Any
import logging
import frontmatter

logger = logging.getLogger(__name__)

class RegistryHost(NamedTuple):
    name: str
    type: str
    description: str
    ip: str
    tags: List[str]
    specs: Dict[str, Any]
    is_critical: bool

class RegistryParser:
    def __init__(self, registry_path: str = "../vm-registry/machines"):
        self.registry_path = registry_path
        self.known_hosts: Dict[str, RegistryHost] = {}

    def parse_all(self) -> Dict[str, RegistryHost]:
        """Parses all markdown files in the registry path."""
        self.known_hosts = {}
        
        search_path = os.path.join(self.registry_path, "**/*.md")
        files = glob.glob(search_path, recursive=True)
        
        if not files:
            logger.warning(f"No registry files found in {search_path}")
            return {}

        for file_path in files:
            # Skip readme or templates if necessary
            if os.path.basename(file_path).upper() in ['README.MD', 'ARCHITECTURE.MD', 'VM-TEMPLATE.MD']:
                continue
            self._parse_file(file_path)
            
        return self.known_hosts

    def _parse_file(self, file_path: str):
        try:
            post = frontmatter.load(file_path)
            metadata = post.metadata
            content = post.content
            
            # --- Strategy 1: Frontmatter ---
            if 'ip' in metadata:
                ip = metadata.get('ip')
                if ip and ip.lower() != 'dhcp':
                    self._add_host(
                        ip=ip,
                        name=metadata.get('hostname', metadata.get('name', 'Unknown')),
                        type=metadata.get('type', 'Unknown'),
                        description=metadata.get('description', ''),
                        tags=metadata.get('tags', []),
                        specs=metadata.get('specs', {}),
                        critical=metadata.get('critical', False)
                    )
                    return # Si hay frontmatter, confiamos en él y terminamos

            # --- Strategy 2: Regex Fallback (Legacy) ---
            # Si no hay IP en frontmatter, intentamos regex
            filename = os.path.basename(file_path)
            name_match = re.search(r'^#\s+.*?\s+(.*)$', content, re.MULTILINE)
            display_name = name_match.group(1).strip() if name_match else filename.replace('.md', '')
            
            ip_pattern = re.compile(r'\|\s*\*\*IP.*?\*\*\s*\|\s*([\d\.]+)\s*\|', re.IGNORECASE)
            
            for match in ip_pattern.finditer(content):
                ip = match.group(1).strip()
                if ip.count('.') == 3 and not ip.endswith('.x'):
                    self._add_host(
                        ip=ip,
                        name=display_name,
                        type="Infrastructure",
                        description=f"From {filename}",
                        tags=[],
                        specs={},
                        critical=False
                    )

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")

    def _add_host(self, ip, name, type, description, tags, specs, critical):
        self.known_hosts[ip] = RegistryHost(
            name=name,
            type=type,
            description=description,
            ip=ip,
            tags=tags,
            specs=specs,
            is_critical=critical
        )

    def get_host_info(self, ip: str) -> Optional[RegistryHost]:
        if not self.known_hosts:
            self.parse_all()
        return self.known_hosts.get(ip)
