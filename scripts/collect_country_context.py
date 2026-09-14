"""Acquire comparable material-country context without treating statistics as preferences."""
from pathlib import Path
from urllib.parse import urlencode
from country_persona.acquire import download
from country_persona.io import write_json
import json

ROOT = Path('data/raw/country-extension-20260914/context')
INDICATORS = {
    'SP.POP.TOTL': 'persons',
    'NY.GDP.MKTP.CD': 'current_USD',
    'NE.TRD.GNFS.ZS': 'percent_of_GDP',
    'NV.AGR.TOTL.ZS': 'percent_of_GDP',
    'NV.IND.MANF.ZS': 'percent_of_GDP',
    'EG.IMP.CONS.ZS': 'percent_of_energy_use',
    'EG.ELC.RNEW.ZS': 'percent_of_electricity_output',
    'MS.MIL.XPND.GD.ZS': 'percent_of_GDP',
}


def main():
    url = 'https://api.worldbank.org/v2/country/bra;chn;deu;fra;gbr;ind/indicator/'
    url += ';'.join(INDICATORS) + '?' + urlencode({'source': 2, 'date': '2020:2024', 'format': 'json', 'per_page': 1000})
    receipt = download(url, ROOT / 'wdi-2020-2024.json', source_id='world_bank_wdi', max_bytes=5_000_000)
    response = json.loads((ROOT / 'wdi-2020-2024.json').read_text())
    if len(response) != 2 or response[0]['pages'] != 1 or response[0]['total'] != 240:
        raise ValueError('Unexpected or incomplete country-indicator response')
    metadata = []
    for indicator, unit in INDICATORS.items():
        path = ROOT / f'{indicator}.json'
        info = download(f'https://api.worldbank.org/v2/indicator/{indicator}?source=2&format=json',
                        path, source_id='world_bank_indicator_metadata', max_bytes=5_000_000)
        data = json.loads(path.read_text())
        if len(data) != 2 or len(data[1]) != 1 or data[1][0]['id'] != indicator or data[1][0]['source']['id'] != '2':
            raise ValueError(f'Unexpected indicator metadata: {indicator}')
        metadata.append({'indicator': indicator, 'unit': unit, 'raw_file': str(path), **info})
    write_json(ROOT / 'collection.json', {'observations': {'raw_file': str(ROOT / 'wdi-2020-2024.json'), **receipt},
                                        'metadata': metadata})
    print('Indicator cells:', len(response[1]), 'nonmissing:', sum(r['value'] is not None for r in response[1]))


if __name__ == '__main__':
    main()
