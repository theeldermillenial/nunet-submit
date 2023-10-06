# NuNet Containerized Job Submit

This repo shows an example of how to build a docker container that will start the DMS
and submit a job to mine fortuna. Currently it will only look for GPU nodes and try to
mine on Cuda.

## Setup

### Add a seed phrase

This code uses `minswap-py` to send payment to the smart contract, so a seed phrase is
needed to initialize 

Open `example.seed.txt` and past your seed phrase into it. Save it as `seed.txt`.

NOTE: Obviously you should be careful sharing your seed phrase. This is for preprod
testnet. The `seed.txt` file is ignored, but tread lightly.

### Setup BlockFrost

Payment submission are done using `minswap-py` via BlockFrost. You will need to get a
project ID from BlockFrost. Once you get that, open `sample.env`, paste the project id
into the appropriate place. Save the file as `.env`.

### Build the container

Run `./build.sh`

Once this is done, the container is built and ready to submit the Fortuna job.

### Submit a job

Run `./run.sh`

This will run one fortuna job.

Once you do this, you can open additional terminals and use `./run.sh` until you run
out of GPU nodes.