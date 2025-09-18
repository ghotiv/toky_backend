import time
from web3_call import call_fill_relay_by_etherscan
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chain_id', type=int)
    parser.add_argument('--limit', type=str, default=1)
    parser.add_argument('--time_sleep', type=int, default=2)
    args = parser.parse_args()
    while True:
        print(f"call_fill_relay_by_etherscan time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        call_fill_relay_by_etherscan(chain_id=args.chain_id,limit=args.limit)
        time.sleep(args.time_sleep)

if __name__ == '__main__':
    main()