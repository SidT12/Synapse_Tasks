from requests import exceptions
import argparse
import requests
import cv2
import os


# set up arguments
ap = argparse.ArgumentParser()
ap.add_argument('-q', '--query', required=True, help='search query Bing Image API')
ap.add_argument('-o', '--output', required=True, help='path to output directory of images')
args = vars(ap.parse_args())

# set API key
API_KEY = '1ce803afffe448308d04682ba6ffeb79'
MAX_RESULTS = 100
GROUP_SIZE = 25

# endpoint API URL
URL = 'https://api.cognitive.microsoft.com/bing/v7.0/images/search'

# handling exceptions
EXCEPTIONS = set([IOError, FileNotFoundError, exceptions.RequestException,
                  exceptions.HTTPError, exceptions.ConnectionError, exceptions.Timeout])

# initialize parameters
term = args['query']
headers = {'Ocp-Apim-Subscription-Key': API_KEY}
params = {'q': term, 'offset': 0, 'count': GROUP_SIZE}

# make the search
print(f'[INFO] Searching for... {term}')
search = requests.get(URL, headers=headers, params=params)
search.raise_for_status()

# grab the results
results = search.json()
estNumResults = min(results['totalEstimatedMatches'], MAX_RESULTS)
print(f'[INFO] {estNumResults} total results for {term}')

total = 0
corrupted_images = []

# loop over the results
for offset in range(0, estNumResults, GROUP_SIZE):
    print(f'[INFO] Making request for group {offset}-{offset + GROUP_SIZE} of {estNumResults}')
    params['offset'] = offset
    search = requests.get(URL, headers=headers, params=params)
    search.raise_for_status()
    results = search.json()
    print(f'[INFO] saving images for group {offset}-{offset + GROUP_SIZE} of {estNumResults}')

    for v in results['value']:
        try:
            print(f"[INFO] fetching: {v['contentUrl']}")
            r = requests.get(v['contentUrl'], timeout=30)

            ext = v["contentUrl"][v["contentUrl"].rfind("."):]
            p = os.path.sep.join([args["output"], "{}{}".format(str(total).zfill(8), ext)])
            print(p)

            f = open(p, 'wb')
            f.write(r.content)
            f.close()

        except Exception as e:
            if type(e) in EXCEPTIONS:
                print(e)
                print(type(e))
                print(f"[INFO] skipping: {v['contentUrl']}")
                continue

        image = cv2.imread(p)

        if image is None:
            print(f'[INFO] deleting: {p}')
            try:
                os.remove(p)
            except OSError:
                corrupted_images.append(p)

            continue

        total += 1
