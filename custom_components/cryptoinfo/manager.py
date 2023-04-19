import time


class CryptoInfoFetchProp:
    def __init__(self, slug):
        self._slug = slug
        self._name = self._build_name()
        self._id_slug = self._build_id_slug()

    def _build_name(self):
        return self._slug.replace("extrasensor_", "").replace("_", " ").title()

    def _build_id_slug(self):
        split_slug = self._slug.split("_")
        if len(split_slug) > 1 and split_slug[0] == "extrasensor":
            split_slug = split_slug[1:]
            if len(split_slug) > 1:
                return "es_" + "".join([s[0] for s in split_slug[:-1]]) + split_slug[-1][:2]
            return "es_" + split_slug[:3]
        elif len(split_slug) > 1:
            return self._slug[0] + split_slug[1][:2]
        return self._slug[:3]

    @property
    def slug(self):
        return self._slug

    @property
    def id_slug(self):
        return self._id_slug

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return self._slug

    def __hash__(self):
        return hash(self._slug)

    def __eq__(self, other):
        try:
            return self.slug == other.slug
        except Exception:
            return self.slug == str(other)

    def __lt__(self, other):
        try:
            return self.slug < other.slug
        except Exception:
            return self.slug < str(other)


class CryptoInfoDataFetchType:
    PRICE_MAIN = CryptoInfoFetchProp("price_main")
    PRICE_SIMPLE = CryptoInfoFetchProp("price_simple")
    DOMINANCE = CryptoInfoFetchProp("dominance")
    CHAIN_SUMMARY = CryptoInfoFetchProp("chain_summary")
    CHAIN_CONTROL = CryptoInfoFetchProp("chain_control")
    CHAIN_ORPHANS = CryptoInfoFetchProp("chain_orphans")
    CHAIN_BLOCK_TIME = CryptoInfoFetchProp("chain_block_time")


class CryptoInfoEntityManager:
    _instance = None

    def __init__(self):
        self._entities = dict()
        self._api_data = dict()
        self._fetch_frequency = dict()
        self._last_fetch = dict()
        self._extra_sensor_types = list()

    @property
    def fetch_types(self):
        return [
            CryptoInfoDataFetchType.PRICE_MAIN,
            CryptoInfoDataFetchType.PRICE_SIMPLE,
            CryptoInfoDataFetchType.DOMINANCE,
            CryptoInfoDataFetchType.CHAIN_SUMMARY,
            CryptoInfoDataFetchType.CHAIN_CONTROL,
            CryptoInfoDataFetchType.CHAIN_ORPHANS,
            CryptoInfoDataFetchType.CHAIN_BLOCK_TIME,
        ]

    @property
    def fetch_market_cap_types(self):
        return [
            CryptoInfoDataFetchType.PRICE_MAIN,
            CryptoInfoDataFetchType.PRICE_SIMPLE,
            CryptoInfoDataFetchType.DOMINANCE,
        ]

    @property
    def fetch_supply_types(self):
        return [
            CryptoInfoDataFetchType.PRICE_MAIN,
            CryptoInfoDataFetchType.CHAIN_SUMMARY,
        ]

    @property
    def fetch_price_types(self):
        return [
            CryptoInfoDataFetchType.PRICE_MAIN,
            CryptoInfoDataFetchType.PRICE_SIMPLE,
        ]

    @property
    def fetch_time_types(self):
        return [
            CryptoInfoDataFetchType.CHAIN_BLOCK_TIME,
        ]

    @property
    def fetch_shared_types(self):
        return [
            CryptoInfoDataFetchType.DOMINANCE,
            CryptoInfoDataFetchType.CHAIN_SUMMARY,
        ]

    def get_extra_sensor_fetch_type_from_str(self, attribute_key):
        for t in self._extra_sensor_types:
            if t == attribute_key:
                return t
        t = CryptoInfoFetchProp("extrasensor_" + attribute_key)
        self._extra_sensor_types.append(t)
        return t

    def get_fetch_type_from_str(self, fetch_type):
        if isinstance(fetch_type, CryptoInfoFetchProp):
            return fetch_type
        for t in self.fetch_types:
            if t == fetch_type:
                return t
        return CryptoInfoDataFetchType.PRICE_MAIN

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
        if entity.fetch_type not in self.fetch_shared_types:
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
        if entity.fetch_type not in self.fetch_shared_types:
            return
        self._api_data[entity.fetch_type] = data
        self._last_fetch[entity.fetch_type] = int(time.time())

    def fetch_cached_entity_data(self, entity):
        return self._api_data[entity.fetch_type]
