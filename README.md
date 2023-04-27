## Cryptoinfo Advanced - Cryptocurrency Home Assistant sensor component
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
### Powered by CoinGecko, CryptoID, Mempool.space APIs

#### Provides Home Assistant sensors for all cryptocurrencies offered by the supporting services

If you like my work, please buy me an aubergine or donate some BTC.

<a href="https://www.buymeacoffee.com/TheHoliestRoger" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me an Aubergine" style="height: 60px !important;width: 217px !important;"></a><details>
  <summary>BTC address</summary>
bc1qpq4djuxgxsk0zrkg9y2rye8fyz7e0mjx64gzq0
</details>

This project originally started from [Cryptoinfo](https://github.com/heyajohnny/cryptoinfo), adding lot's more features.

## Installation:
### Installation step 1:
There are 2 ways to install Cryptoinfo Advanced:
1. Download 'Cryptoinfo Advanced' from the HACS store
2. Copy the files in the /custom_components/cryptoinfo_advanced/ folder to: [homeassistant]/config/custom_components/cryptoinfo_advanced/

### Installation step 2:
The next step is to add cryptoinfo_advanced to your configuration.yaml. You can do that in 2 ways:
1. Copy and paste the values from this [configuration.yaml](https://github.com/TheHolyRoger/hass-cryptoinfo/blob/master/example/configuration.yaml) and adjust it according to your needs
2. Copy and paste the values (and adjust according to your needs) from the configutation you see next

Example config:
```Configuration.yaml:
  sensor:
    - platform: cryptoinfo_advanced
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

## Common Sensor Parameters
All sensors have the following parameters as a base.

| Parameter | Default  | Description |
| --- | -- | ------------------- |
| id | `""` | The name for the sensor. |
| unique_id | `<generated>` | A custom unique_id for the sensor. |
| cryptocurrency_name | `bitcoin` | The cryptocurrency name/symbol for the sensor. For some APIs this must be the symbol, others the name. |
| update_frequency | `1` | The update frequency in minutes for the sensor (accepts floats). |
| unit_of_measurement | `$` | The unit_of_measurement for the sensor. |
| api_mode | `price_main` | The API mode for the sensor, see below. |
| extra_sensors | `None` | The extra sensors for the sensor, see below. |

## API mode
There are extra yet-to-be-documented `api_mode`s, see [configuration example](https://github.com/TheHolyRoger/hass-cryptoinfo/blob/master/example/configuration.yaml) for now:

| Mode | Source | Description |
| --- | --- | ----------- |
| price_main | CoinGecko | Main price fetching with the extended attributes. |
| price_simple | CoinGecko | Simple price fetching without the extended attributes. |
| dominance | CoinGecko | Dominance fetching. |
| chain_summary | CryptoID | Chain Summary fetching. |
| chain_control | CryptoID | Chain Hashrate Control fetching. |
| chain_orphans | CryptoID | Chain Orphans fetching. |
| chain_block_time | CryptoID | Chain Block Timestamp fetching, can be used in conjunction with `chain_summary` for difficulty calculations. |
| nomp_pool_stats | NOMP | Pool stats fetching from any NOMP based mining pool. |
| mempool_stats | Mempool.space | Mempool stats fetching (Bitcoin only). |

## State, Attributes and Extra Sensors

All attributes can added as additional sensors with the `extra_sensors`, see [examples](https://github.com/TheHolyRoger/hass-cryptoinfo/blob/master/example/configuration.yaml)

### Price (Main) - `price_main`
#### State
This will return the `base_price` multiplied by the configured `multiplier`.

#### Attributes

| Attribute | Source |
| --- | ------------------- |
| base_price | This will return the price of 1 coin / token in `currency_name` of the `cryptocurrency_name` |
| 24h_volume | This will return the 24 hour volume in `currency_name` of the `cryptocurrency_name` |
| 24h_change | This will return the 24 hour change in percentage of the `cryptocurrency_name` |
| 24h_low | This will return the 24 hour low in `currency_name` of the `cryptocurrency_name` |
| 24h_high | This will return the 24 hour high in `currency_name` of the `cryptocurrency_name` |
| 1h_change | This will return the 1 hour change in percentage of the `cryptocurrency_name` |
| 7d_change | This will return the 7 day change in percentage of the `cryptocurrency_name` |
| 30d_change | This will return the 30 day change in percentage of the `cryptocurrency_name` |
| circulating_supply | This will return the circulating supply of the `cryptocurrency_name` |
| total_supply | This will return the total supply of the `cryptocurrency_name` |
| market_cap | This will return the total market cap of the `cryptocurrency_name` displayed in `currency_name` |
| all_time_high | This will return the all time high in `currency_name` of the `cryptocurrency_name` |
| all_time_low | This will return the all time low in `currency_name` of the `cryptocurrency_name` |
| image_url | This will return a link to the icon for `cryptocurrency_name` |

#### Parameters

| Parameter | Default  | Description |
| --- | -- | ------------------- |
| currency_name | `usd` | The conversion currency name for the sensor. |

#### Extra Sensor Properties

| Property | Description |
| --- | ------------------- |
| all_time_high_distance | This will return the all time high distance in `currency_name` of the `cryptocurrency_name` |


### Price (Simple) - `price_simple`
#### State
This will return the `base_price` multiplied by the configured `multiplier`.

#### Attributes

| Attribute | Source |
| --- | ------------------- |
| base_price | This will return the price of 1 coin / token in `currency_name` of the `cryptocurrency_name` |
| 24h_volume | This will return the 24 hour volume in `currency_name` of the `cryptocurrency_name` |
| 24h_change | This will return the 24 hour change in percentage of the `cryptocurrency_name` |

#### Parameters

| Parameter | Default  | Description |
| --- | -- | ------------------- |
| currency_name | `usd` | The conversion currency name for the sensor. |


### Market Dominance - `dominance`
#### State
This will return the `dominance` as a percentage rounded to 2 places.

#### Attributes

| Attribute | Source |
| --- | ------------------- |
| market_cap | This will return the total market cap of the `cryptocurrency_name` displayed in USD |


### Blockchain Summary - `chain_summary`
#### State
This will return the current `height` of the blockchain in blocks.

#### Attributes

| Attribute | Source |
| --- | ------------------- |
| circulating_supply | This will return the circulating supply of the `cryptocurrency_name` |
| hashrate | This will return the hashrate of the `cryptocurrency_name` |
| difficulty | This will return the hashrate of the `cryptocurrency_name` |
| diff_multiplier | This will return the configured diff_multiplier of the `cryptocurrency_name` |
| block_time_minutes | This will return the configured block_time_minutes of the `cryptocurrency_name` |
| difficulty_window | This will return the configured difficulty_window of the `cryptocurrency_name` |
| halving_window | This will return the configured halving_window of the `cryptocurrency_name` |

#### Parameters

| Parameter | Default  | Description |
| --- | -- | ------------------- |
| difficulty_window | `2016` | The number of blocks for a difficulty retarget window. |
| diff_multiplier | `4294967296` | A special number for difficulty calculations - maximum nonces. Equal to 2³² |
| block_time_minutes | `10.0` | The number of minutes between blocks. |
| halving_window | `210000` | The number of blocks for the halving window. |

#### Extra Sensor Properties

| Property | Description |
| --- | ------------------- |
| difficulty_calc |  |
| hashrate_calc |  |
| block_time_in_seconds |  |
| difficulty_block_progress |  |
| difficulty_retarget_height |  |
| difficulty_retarget_seconds |  |
| difficulty_retarget_percent_change |  |
| difficulty_retarget_estimated_diff |  |
| halving_block_progress |  |
| halving_blocks_remaining |  |
| next_halving_height |  |
| total_halvings_to_date |  |


### Blockchain Hashrate Control - `chain_control`
#### State
This will return the total blocks mined in last 100 for the configured `pool_prefix` and `cryptocurrency_name`.

#### Attributes

| Attribute | Source |
| --- | ------------------- |
| pool_control_1000b | This will return the total blocks mined in last 1000 for the configured `pool_prefix` and `cryptocurrency_name`.|

#### Parameters

| Parameter | Default  | Description |
| --- | -- | ------------------- |
| pool_prefix | `None` | The pool prefix(es) to be included in the sensor. (accepts lists) |

#### Extra Sensor Properties

| Property | Description |
| --- | ------------------- |
| pool_control_1000b_perc |  |


### Blockchain Orphans - `chain_orphans`
#### State
This will return the total orphaned blocks in the past 24 hours of the `cryptocurrency_name`.


### Blockchain Timestamp - `chain_block_time`
#### State
This will return the `timestamp` as a Unix epoch of the configured `fetch_args_template` if supplied, otherwise the last difficulty retarget block timestamp.

#### Attributes

| Attribute | Source |
| --- | ------------------- |
| block_height | This will return block_height of the current `timestamp`. Used to stop repeated fetching. |

#### Parameters

| Parameter | Default  | Description |
| --- | -- | ------------------- |
| fetch_args_template | `""` | The block height to be used for timestamp fetching. Accepts templates. |


### NOMP Pool Stats - `nomp_pool_stats`
#### State
This will return the current `hashrate` of the NOMP pool specified with `api_domain_name` and `pool_name`.

#### Attributes

| Attribute | Source |
| --- | ------------------- |
| hashrate | This will return the hashrate of the pool. |
| block_height | This will return the current block_height of the pool. |
| worker_count | This will return the total workers mining on the pool. |
| last_block | This will return the last block mined by the pool. |
| blocks_pending | This will return the total blocks pending for the pool. |
| blocks_confirmed | This will return the total blocks confirmed for the pool. |
| blocks_orphaned | This will return the total blocks orphaned for the pool. |

#### Parameters

| Parameter | Default  | Description |
| --- | -- | ------------------- |
| api_domain_name | `""` | The domain name of the NOMP pool for the sensor. Must include the subdomain if there is one. |
| pool_name | `""` | The pool name to be used for the sensor. |

#### Extra Sensor Properties

| Property | Description |
| --- | ------------------- |
| hashrate_calc |  |


### Market Dominance - `mempool_stats`
#### State
This will return 

#### Attributes

| Attribute | Source |
| --- | ------------------- |
| mempool_tx_count | This will return the total TX count in the mempool. |
| mempool_total_fee | This will return the total fee of all TXs in the mempool. |

#### Extra Sensor Properties

| Property | Description |
| --- | ------------------- |
| mempool_size_calc |  |
| mempool_average_fee_per_tx |  |


## Issues and new functionality
If there are any problems, please create an issue in https://github.com/TheHolyRoger/hass-cryptoinfo/issues
If you want new functionality added, please create an issue with a description of the new functionality that you want in: https://github.com/TheHolyRoger/hass-cryptoinfo/issues
