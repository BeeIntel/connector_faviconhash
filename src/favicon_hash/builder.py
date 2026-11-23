import stix2
from pycti import StixCoreRelationship

class FaviconHashBuilder:
    def __init__(self, helper, author_identity_id: str, domain_stix_entity: dict, favicon_data: dict):
        self.helper = helper
        self.author_id = author_identity_id
        self.domain_stix_entity = domain_stix_entity
        self.favicon_data = favicon_data

    def build_file_and_relationship(self, existing_file_id: str = None):
        """Создаёт файл (если не передан existing_file_id) и связь с доменом."""
        murmur_hash = self.favicon_data["favicon_hash"]

        if existing_file_id:
            file_stix = None
            target_id = existing_file_id
        else:
            file_stix = stix2.File(
                name=murmur_hash,   # идентификатор = murmur-хэш
                hashes={
                    "MD5": self.favicon_data["md5"],
                    "SHA-256": self.favicon_data["sha256"]
                },
                custom_properties={
                    "author": "BeeIntelligence",
                    "description": "Хэш favicon",
                    "labels": ["favicon"]
                }
            )
            target_id = file_stix.id

        relationship = stix2.Relationship(
            id=StixCoreRelationship.generate_id(
                "related-to",
                self.domain_stix_entity["id"],
                target_id
            ),
            relationship_type="related-to",
            created_by_ref=self.author_id,
            source_ref=self.domain_stix_entity["id"],
            target_ref=target_id,
            confidence=self.helper.connect_confidence_level,
            allow_custom=True
        )
        return (file_stix, relationship) if file_stix else (None, relationship)
