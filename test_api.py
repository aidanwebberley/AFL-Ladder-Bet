import urllib.request, json
req = urllib.request.Request('https://api.squiggle.com.au/?q=standings&year=2024', headers={'User-Agent': 'AFL_Dashboard_App/1.0'})
with urllib.request.urlopen(req) as url:
    data = json.load(url)
    print([t['name'] for t in data['standings']])
