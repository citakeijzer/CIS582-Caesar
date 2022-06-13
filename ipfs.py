import requests
import json

def pin_to_ipfs(data):
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
  
  dictionary = json.dumps(data)
  
  files = {
    'file': dictionary
  }
  
  response = requests.post('https://ipfs.infura.io:5001/api/v0/add', files=files, auth=('2AWehNaZa5724pkR0LqHIldBv6i','e6d02b35efb61e52f7f1f3b5d6dc667f'))
  
  cid = response.json()['ipfsHash']

	return cid

def get_from_ipfs(cid,content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"

  params = (
    ('arg', cid),
  )
  
  response = requests.post('https://ipfs.infura.io:5001/api/v0/cat', params=params, auth=('2AWehNaZa5724pkR0LqHIldBv6i','e6d02b35efb61e52f7f1f3b5d6dc667f'))
  
  data = json.loads(response.text)
  
	assert isinstance(data,dict), f"get_from_ipfs should return a dict"
	
  return data
