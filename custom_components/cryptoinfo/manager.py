import time


class CryptoInfoDataFetchType:
    PRICE_MAIN = "price_main"
    PRICE_SIMPLE = "price_simple"
    DOMINANCE = "dominance"


class CryptoInfoEntityManager:
    _instance = None

    def __init__(self):
        self._entities = dict()
        self._api_data = dict()
        self._fetch_frequency = dict()
        self._last_fetch = dict()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_entities(self, entities):
        for entity in entities:
            self._entities[entity.unique_id] = entity
            current_frequency = self._fetch_frequency.get(entity.fetch_type)
            if current_frequency is None or entity.update_frequency < current_frequency:
                self._fetch_frequency[entity.fetch_type] = entity.update_frequency

    def get_last_fetch(self, fetch_type):
        return self._last_fetch.get(fetch_type, 0)

    def get_fetch_frequency(self, fetch_type):
        tdelta = self._fetch_frequency.get(fetch_type)
        return tdelta.seconds if tdelta else 0

    def should_fetch_entity(self, entity):
        if entity.fetch_type != CryptoInfoDataFetchType.DOMINANCE:
            return True
        if entity.fetch_type not in self._api_data:
            return True
        if self._api_data[entity.fetch_type] is None:
            return True
        last_fetch = self.get_last_fetch(entity.fetch_type)
        if last_fetch + self.get_fetch_frequency(entity.fetch_type) < int(time.time()):
            return True
        return False

    def set_cached_entity_data(self, entity, data):
        self._api_data[entity.fetch_type] = data
        self._last_fetch[entity.fetch_type] = int(time.time())

    def fetch_cached_entity_data(self, entity):
        return self._api_data[entity.fetch_type]
