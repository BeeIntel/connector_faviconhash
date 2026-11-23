import yaml
from pathlib import Path
from typing import Dict
import stix2
from pycti import Identity, OpenCTIConnectorHelper, get_config_variable

from .client import FaviconHashClient
from .builder import FaviconHashBuilder

class FaviconHashConnector:
    _SOURCE_NAME = "FaviconHash"
    BEE_INTELLIGENCE_ID = "identity--dcf8262b-b996-598b-9723-7ee1b3c6d573"

    def __init__(self):
        config_file_path = Path(__file__).parent.parent.resolve() / "config.yml"
        config = (
            yaml.load(open(config_file_path, encoding="utf-8"), Loader=yaml.FullLoader)
            if config_file_path.is_file()
            else {}
        )
        self.helper = OpenCTIConnectorHelper(config, playbook_compatible=True)

        self.api_url = get_config_variable(
            "FAVICON_HASH_API_URL", ["favicon_hash", "api_url"], config,
            default="https://favicon-hash.kmsec.uk/api/"
        )
        self.max_tlp = get_config_variable(
            "FAVICON_HASH_MAX_TLP", ["favicon_hash", "max_tlp"], config,
            default="TLP:AMBER"
        )
        self.request_timeout = get_config_variable(
            "FAVICON_HASH_REQUEST_TIMEOUT", ["favicon_hash", "request_timeout"], config,
            default=10, isNumber=True
        )
        delay_str = get_config_variable(
            "FAVICON_HASH_DELAY", ["favicon_hash", "delay"], config,
            default="0.5", isNumber=False
        )
        try:
            self.delay = float(delay_str)
        except ValueError:
            self.helper.log_warning(f"Некорректное значение delay: {delay_str}, используем 0.5")
            self.delay = 0.5

        self.ca_bundle = get_config_variable(
            "FAVICON_HASH_CA_BUNDLE", ["favicon_hash", "ca_bundle"], config,
            default=None
        )

        self.author = stix2.Identity(
            id=self.BEE_INTELLIGENCE_ID,
            name="BeeIntelligence",
            identity_class="organization",
            description="BeeIntelligence - Favicon Hash Enrichment",
            confidence=self.helper.connect_confidence_level,
        )

        self.client = FaviconHashClient(
            self.helper, self.api_url, self.request_timeout, self.ca_bundle
        )

    def find_existing_file_by_name(self, name: str):
        """Ищет существующий Observable File с заданным именем (murmur-хэш)."""
        filters = [
            {"key": "entity_type", "values": ["File"]},
            {"key": "name", "values": [name]}
        ]
        try:
            files = self.helper.api.stix_cyber_observable.list(filters=filters)
            if files and len(files) > 0:
                self.helper.log_info(f"Найден существующий файл с именем {name}, ID: {files[0]['id']}")
                return files[0]['id']
        except Exception as e:
            self.helper.log_warning(f"Ошибка при поиске файла по имени {name}: {e}")
        return None

    def _process_message(self, data: Dict):
        self.helper.metric.inc("run_count")
        self.helper.metric.state("running")

        stix_objects = data["stix_objects"]
        stix_entity = data["stix_entity"]
        opencti_entity = data["enrichment_entity"]

        tlp = "TLP:CLEAR"
        for marking_definition in opencti_entity.get("objectMarking", []):
            if marking_definition["definition_type"] == "TLP":
                tlp = marking_definition["definition"]

        if not OpenCTIConnectorHelper.check_max_tlp(tlp, self.max_tlp):
            raise ValueError(f"TLP {tlp} превышает максимально допустимый {self.max_tlp}")

        domain = opencti_entity["observable_value"]
        self.helper.log_debug(f"Обогащение домена: {domain}")

        favicon_data = self.client.get_favicon_data(domain)
        if not favicon_data:
            self.helper.log_warning(f"Не удалось получить данные favicon для {domain}")
            return "Нет данных о favicon"

        murmur_hash = favicon_data["favicon_hash"]
        existing_file_id = self.find_existing_file_by_name(murmur_hash)

        builder = FaviconHashBuilder(
            helper=self.helper,
            author_identity_id=self.author.id,
            domain_stix_entity=stix_entity,
            favicon_data=favicon_data
        )
        file_stix, relationship = builder.build_file_and_relationship(existing_file_id)

        bundle_objects = stix_objects + [self.author, relationship]
        if file_stix:
            bundle_objects.append(file_stix)

        serialized_bundle = self.helper.stix2_create_bundle(bundle_objects)
        bundles_sent = self.helper.send_stix2_bundle(serialized_bundle)

        self.helper.metric.state("idle")
        return f"Отправлено {len(bundles_sent)} STIX-пакетов"

    def start(self):
        self.helper.metric.state("idle")
        self.helper.listen(message_callback=self._process_message)
