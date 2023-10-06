import json
import os
import pprint
import requests
from dataclasses import dataclass
from pathlib import Path
from websockets.sync.client import connect

import blockfrost
import pycardano
from dotenv import load_dotenv
from minswap.models import Address, Assets, asset_to_value
from minswap.wallets import Wallet

DMS = "localhost:9999"
REQUEST_SERVICE_ENDPOINT = f"http://{DMS}/api/v1/run/request-service"
DMS_ENDPOINT = f"http://{DMS}/api/v1/onboarding"
SEND_STATUS = f"ws://{DMS}/api/v1/run/deploy"
PEERS_ENDPOINT = f"http://{DMS}/api/v1/peers/dht/dump"

load_dotenv()

context: pycardano.ChainContext = pycardano.BlockFrostChainContext(
    os.environ["PROJECT_ID"],
    base_url=getattr(blockfrost.ApiUrls, os.environ["NETWORK"]).value,
)


@dataclass
class ContractDatum(pycardano.PlutusData):
    CONSTR_ID = 0
    address: bytes
    provider_address: bytes
    signature: bytes
    oracle_message: bytes
    slot: int
    timeout: int
    ntx: int


postData = {
    "address_user": "addr_test1qqgqhwjzz45527pml3z6mxc0n956tlp56xrfznx49r6rn0cwhcyl0mndx0a7r54l806cth5x7thrdrn9g0dugyze249qc2hjp8",
    "max_ntx": 10,
    "blockchain": "Cardano",
    "service_type": "ml-training-gpu",
    "params": {
        "machine_type": "gpu",
        "image_id": "registry.gitlab.com/nunet/ml-on-gpu/ml-on-gpu-service/develop/pytorch",
        "model_url": "https://raw.githubusercontent.com/theeldermillenial/nunet-cuda-tuna/master/run_cuda.py",
        "packages": ["requests", "pycardano"],
    },
    "constraints": {
        "CPU": 500,
        "RAM": 2000,
        "VRAM": 2000,
        "power": 170,
        "complexity": "Moderate",
        "time": 1,
    },
}

wallet = Wallet(path="seed.txt")

with open("script.txt", "r") as fr:
    script = pycardano.PlutusV2Script(bytes.fromhex(fr.read()))
script_address = Address(
    bech32="addr_test1wq4np8jgwtty7wpmxw6j3mx6cytq95p97g2qdqyq2d095ucay7upj"
)


def send_job(tx: str):
    with connect(SEND_STATUS) as websocket:
        try:
            websocket.send(
                json.dumps(
                    {
                        "message": {
                            "transaction_status": "success",
                            "transaction_type": "fund",
                            "tx_hash": tx,
                        },
                        "action": "send-status",
                    }
                )
            )
            for message in websocket:
                print(message)
        finally:
            websocket.send(
                json.dumps(
                    {
                        "action": {"terminate-job"},
                    }
                )
            )


def address(address: Address):
    payment = bytes.fromhex(str(address.payment.payment_part))

    return payment


if __name__ == "__main__":
    print(requests.get(PEERS_ENDPOINT).json())
    while True:
        try:
            job_info = requests.post(
                REQUEST_SERVICE_ENDPOINT,
                data=json.dumps(postData),
                headers={"Content-Type": "application/json"},
            ).json()
            pprint.pprint(job_info)

            if job_info["compute_provider_addr"].endswith("jrz36z"):
                print(f"Found blacklisted address: {job_info['compute_provider_addr']}")
                continue

            provider_address = Address(bech32=job_info["compute_provider_addr"])
            datum = ContractDatum(
                address=address(wallet.address),
                provider_address=address(provider_address),
                signature=bytes.fromhex(job_info["signature"]),
                oracle_message=bytes(job_info["oracle_message"], encoding="utf-8"),
                slot=context.last_block_slot + 86400,
                timeout=10,
                ntx=1,
            )
            break
        except:
            print(f"Error in datum construction.")
            if (
                job_info["compute_provider_addr"]
                != "0x87DA03a4C593FE69fe98440B6c3d37348c93A8FB"
            ):
                raise

    metadata = {674: {"msg": [f"nunet-py: 0.0.0"]}}
    message = pycardano.AuxiliaryData(
        data=pycardano.AlonzoMetadata(metadata=pycardano.Metadata(metadata))
    )

    tx_builder = pycardano.TransactionBuilder(context=context)
    tx_builder.add_input_address(wallet.address.address)

    asset = asset_to_value(
        Assets(
            **{
                "lovelace": 2000000 + int(job_info["estimated_price"] * 10**7),
                "8cafc9b387c9f6519cacdce48a8448c062670c810d8da4b232e563136d4e5458": 10,
            }
        )
    )

    tx_builder.add_output(
        pycardano.TransactionOutput(
            address=script_address.address, amount=asset, datum=datum
        )
    )

    tx = tx_builder.build_and_sign(
        [wallet.payment_signing_key], change_address=wallet.address.address
    )

    path = Path(str(tx.id) + ".cbor")
    with open(path, "wb") as fw:
        fw.write(tx.to_cbor())

    try:
        context.submit_tx(tx)
    except Exception:
        path.unlink()
        raise

    send_job(str(tx.id))
