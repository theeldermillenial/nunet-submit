ADDRESS=addr_test1qqgqhwjzz45527pml3z6mxc0n956tlp56xrfznx49r6rn0cwhcyl0mndx0a7r54l806cth5x7thrdrn9g0dugyze249qc2hjp8

systemctl start nunet-dms.service
nunet onboard -m 8000 -c 6000 -n nunet-test -a ${ADDRESS}
echo "Aggregating peers, sleeping for 30s..."
sleep 30s
python3 test_cuda.py