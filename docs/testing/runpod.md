## Testing your RunPod Endpoint

### Configure your RunPod Credentials

1. Copy the `.env.example` file to `.env`:
```bash
cd tests
cp .env.example .env
```
2. Edit the `.env` file and add your RunPod API key to
`RUNPOD_API_KEY` and your RunPod Endpoint ID to
`RUNPOD_ENDPOINT_ID`.
3. Run the test script:
```bash
python3 test_runpod_endpoint.py
```
4. This will display the HTTP status code and the filename
   of the output image, for example:
```
Status code: 200
Saving image: 792a7e9f-9c36-4d35-b408-0d45d8e2bbcb.jpg
```

You can then open the output image (in this case
`792a7e9f-9c36-4d35-b408-0d45d8e2bbcb.jpg`) to view the
results of the face swap.
