from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
import requests
import json
import time

bayc_address = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"
contract_address = Web3.toChecksumAddress(bayc_address)

#You will need the ABI to connect to the contract
#The file 'abi.json' has the ABI for the bored ape contract
#In general, you can get contract ABIs from etherscan
#https://api.etherscan.io/api?module=contract&action=getabi&address=0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D
with open('/home/codio/workspace/abi.json', 'r') as f:
	abi = json.load(f) 

############################
#Connect to an Ethereum node
api_url = f"https://mainnet.infura.io/v3/2BtY3QjKPh6aC1pUxDSM0w1W4hg"
provider = HTTPProvider(api_url)
web3 = Web3(provider)

def get_ape_info(apeID):
	assert isinstance(apeID,int), f"{apeID} is not an int"
	assert 1 <= apeID, f"{apeID} must be at least 1"

	data = {'owner': "", 'image': "", 'eyes': "" }
	
	#YOUR CODE HERE	
	
	contract = web3.eth.contract(address=contract_address, abi=abi)
	
	data['owner'] = contract.functions.ownerOf(apeID).call()
	
	response = requests.post('https://ipfs.infura.io:5001/api/v0/cat?arg=QmeSjSinHpPnmXmspMjwiXyN6zS4E9zccariGR3jxcaWtq/'+ str(apeID), auth =  ('2AU3yrWCRD4foAWoUgyiqNdE1Py', '5e24ddc1ecfcddfba6cadcaad1fb61dd'))

	responsedata = json.loads(response.text)
	
	data['image'] = responsedata['image']
	
	for instance in ipfs_res['attributes']:	
		if instance['trait_type'] == 'Eyes':
			data['eyes'] = instance['value']
			break
	
	assert isinstance(data,dict), f'get_ape_info{apeID} should return a dict' 
	assert all( [a in data.keys() for a in ['owner','image','eyes']] ), f"return value should include the keys 'owner','image' and 'eyes'"
	return data

