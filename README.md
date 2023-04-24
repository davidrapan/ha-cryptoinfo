## Home Assistant sensor component for cryptocurrencies
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
### Powered by CoinGecko, CryptoID, Mempool.space APIs

#### Provides Home Assistant sensors for all cryptocurrencies supported by CoinGecko

If you like my work, please buy me an aubergine or donate some BTC.

<a href="https://www.buymeacoffee.com/TheHoliestRoger" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me an Aubergine" style="height: 60px !important;width: 217px !important;"></a><details>
  <summary>BTC address</summary>
bc1qpq4djuxgxsk0zrkg9y2rye8fyz7e0mjx64gzq0
</details>

### Installation step 1:
There are 2 ways to install cryptoinfo:
1. Copy the files in the /custom_components/cryptoinfo/ folder to: [homeassistant]/config/custom_components/cryptoinfo/

### Installation step 2:
The next step is to add cryptoinfo to your configuration.yaml. You can do that in 2 ways:
1. Copy and paste the values from this [configuration.yaml](https://github.com/TheHolyRoger/hass-cryptoinfo/blob/master/example/configuration.yaml) and adjust it according to your needs
2. Copy and paste the values (and adjust according to your needs) from the configutation you see next

Example config:
```Configuration.yaml:
  sensor:
    - platform: cryptoinfo
      id: "main wallet"                (optional, default = '') add some extra naming to the sensor
      cryptocurrency_name: "bitcoin"  (default = "bitcoin")
      currency_name: "eur"             (default = "usd")
      unit_of_measurement: "\u200b"    (default = "$")
      multiplier: 1                    (default = 1) the currency value multiplied by this number
      update_frequency: 15             (default = 60) number of minutes to refresh data of the sensor
```

For the complete list of supported values for 'cryptocurrency_name', visit this page:
https://api.coingecko.com/api/v3/coins/list and copy / paste the "id" value to use as 'cryptocurrency_name'

For the complete list of supported values for 'currency_name', visit this page:
https://api.coingecko.com/api/v3/simple/supported_vs_currencies and copy / paste the value to use as 'currency_name'

### API mode
There are extra yet-to-be-documented `api_mode`s, see [configuration example](https://github.com/TheHolyRoger/hass-cryptoinfo/blob/master/example/configuration.yaml) for now:
- price_simple          (CoinGecko) Simple price fetching without the extended attributes.
- dominance             (CoinGecko) Dominance fetching.
- chain_summary         (CryptoID) Chain Summary fetching.
- chain_control         (CryptoID) Chain Hashrate Control fetching.
- chain_orphans         (CryptoID) Chain Orphans fetching.
- chain_block_time      (CryptoID) Chain Block Timestamp fetching, can be used in conjunction with `chain_summary` for difficulty calculations.
- nomp_pool_stats       (NOMP) Pool stats fetching from any NOMP based mining pool.
- mempool_stats         (Mempool.space) Mempool stats fetching (Bitcoin only).

### Attributes
There are 9 important attributes for the main price mode:
- base_price          This will return the price of 1 coin / token in 'currency_name'(default = "usd") of the 'cryptocurrency_name'(default = "bitcoin")
- 24h_volume          This will return the 24 hour volume in 'currency_name'(default = "usd") of the 'cryptocurrency_name'(default = "bitcoin")
- 1h_change           This will return the 1 hour change in percentage of the 'cryptocurrency_name'(default = "bitcoin")
- 24h_change          This will return the 24 hour change in percentage of the 'cryptocurrency_name'(default = "bitcoin")
- 7d_change           This will return the 7 day change in percentage of the 'cryptocurrency_name'(default = "bitcoin")
- 30d_change          This will return the 30 day change in percentage of the 'cryptocurrency_name'(default = "bitcoin")
- market_cap          This will return the total market cap of the 'cryptocurrency_name'(default = "bitcoin") displayed in 'currency_name'(default = "usd")
- circulating_supply  This will return the circulating supply of the 'cryptocurrency_name'(default = "bitcoin")
- total_supply        This will return the total supply of the 'cryptocurrency_name'(default = "bitcoin")

All attributes can added as additional sensors with the `extra_sensors`, see [examples](https://github.com/TheHolyRoger/hass-cryptoinfo/blob/master/example/configuration.yaml)

### Issues and new functionality
If there are any problems, please create an issue in https://github.com/TheHolyRoger/hass-cryptoinfo/issues
If you want new functionality added, please create an issue with a description of the new functionality that you want in: https://github.com/TheHolyRoger/hass-cryptoinfo/issues
